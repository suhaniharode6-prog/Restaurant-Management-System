"""
database.py
------------
Central database layer for the Restaurant Management System.
Both the Console App (console_app.py) and the GUI App (gui_app.py)
use this same module, so data stays in sync between them.

Uses SQLite (restaurant.db) - no extra installation required.
"""

import sqlite3
import os
import hashlib
import hmac
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "restaurant.db")


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they do not already exist, and seed sample menu."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            available INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_no INTEGER NOT NULL UNIQUE,
            capacity INTEGER NOT NULL DEFAULT 4,
            status TEXT NOT NULL DEFAULT 'Free'   -- Free / Occupied
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id INTEGER,
            customer_name TEXT,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',   -- Open / Billed / Cancelled
            discount_percent REAL NOT NULL DEFAULT 0,
            tax_percent REAL NOT NULL DEFAULT 5,
            FOREIGN KEY (table_id) REFERENCES tables (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price_at_order REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        )
    """)

    # New professional features. Existing databases are upgraded safely.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Manager'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'pcs',
            quantity REAL NOT NULL DEFAULT 0,
            reorder_level REAL NOT NULL DEFAULT 5
        )
    """)

    # Add payment_method to old orders databases without deleting existing data.
    cur.execute("PRAGMA table_info(orders)")
    order_columns = {row[1] for row in cur.fetchall()}
    if "payment_method" not in order_columns:
        cur.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT ''")

    # Create the first manager account only when the users table is empty.
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            conn.close()
            raise RuntimeError(
                "ADMIN_PASSWORD is not set. Set it in your terminal before first run; "
                "see README.md for instructions."
            )
        if len(admin_password) < 10:
            conn.close()
            raise ValueError("ADMIN_PASSWORD must contain at least 10 characters.")

        password_hash = _hash_password(admin_password)
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", password_hash, "Manager")
        )

    conn.commit()

    # Seed menu items only if table is empty
    cur.execute("SELECT COUNT(*) AS c FROM menu_items")
    if cur.fetchone()["c"] == 0:
        sample_menu = [
            ("Paneer Tikka", "Starters", 220.0),
            ("Veg Spring Roll", "Starters", 180.0),
            ("Chicken 65", "Starters", 260.0),
            ("Butter Chicken", "Main Course", 320.0),
            ("Paneer Butter Masala", "Main Course", 280.0),
            ("Dal Makhani", "Main Course", 220.0),
            ("Veg Biryani", "Main Course", 240.0),
            ("Chicken Biryani", "Main Course", 300.0),
            ("Butter Naan", "Breads", 45.0),
            ("Tandoori Roti", "Breads", 30.0),
            ("Gulab Jamun", "Desserts", 90.0),
            ("Ice Cream", "Desserts", 80.0),
            ("Masala Chai", "Beverages", 40.0),
            ("Cold Coffee", "Beverages", 110.0),
            ("Fresh Lime Soda", "Beverages", 70.0),
        ]
        cur.executemany(
            "INSERT INTO menu_items (name, category, price) VALUES (?, ?, ?)",
            sample_menu
        )

    # Seed tables only if empty
    cur.execute("SELECT COUNT(*) AS c FROM tables")
    if cur.fetchone()["c"] == 0:
        sample_tables = [(i, 4) for i in range(1, 11)]  # 10 tables, capacity 4
        cur.executemany(
            "INSERT INTO tables (table_no, capacity) VALUES (?, ?)",
            sample_tables
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# MENU OPERATIONS
# ---------------------------------------------------------------------------
def get_menu(category=None, only_available=False):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM menu_items"
    conditions = []
    params = []
    if category:
        conditions.append("category = ?")
        params.append(category)
    if only_available:
        conditions.append("available = 1")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY category, name"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_categories():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM menu_items ORDER BY category")
    rows = [r["category"] for r in cur.fetchall()]
    conn.close()
    return rows


def add_menu_item(name, category, price):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO menu_items (name, category, price) VALUES (?, ?, ?)",
        (name, category, price)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_menu_item(item_id, name=None, category=None, price=None, available=None):
    conn = get_connection()
    cur = conn.cursor()
    fields, params = [], []
    if name is not None:
        fields.append("name = ?"); params.append(name)
    if category is not None:
        fields.append("category = ?"); params.append(category)
    if price is not None:
        fields.append("price = ?"); params.append(price)
    if available is not None:
        fields.append("available = ?"); params.append(1 if available else 0)
    if not fields:
        conn.close()
        return
    params.append(item_id)
    cur.execute(f"UPDATE menu_items SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    conn.close()


def delete_menu_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# TABLE OPERATIONS
# ---------------------------------------------------------------------------
def get_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tables ORDER BY table_no")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_table(table_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tables WHERE id = ?", (table_id,))
    row = cur.fetchone()
    conn.close()
    return row


def set_table_status(table_id, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tables SET status = ? WHERE id = ?", (status, table_id))
    conn.commit()
    conn.close()


def add_table(table_no, capacity=4):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tables (table_no, capacity) VALUES (?, ?)", (table_no, capacity))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


# ---------------------------------------------------------------------------
# ORDER OPERATIONS
# ---------------------------------------------------------------------------
def create_order(table_id, customer_name=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (table_id, customer_name, order_date, status) VALUES (?, ?, ?, 'Open')",
        (table_id, customer_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    order_id = cur.lastrowid
    if table_id:
        cur.execute("UPDATE tables SET status = 'Occupied' WHERE id = ?", (table_id,))
        conn.commit()
    conn.close()
    return order_id


def add_item_to_order(order_id, menu_item_id, quantity):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT price FROM menu_items WHERE id = ?", (menu_item_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Menu item not found")
    price = row["price"]

    # If item already in order, just increase quantity
    cur.execute(
        "SELECT id, quantity FROM order_items WHERE order_id = ? AND menu_item_id = ?",
        (order_id, menu_item_id)
    )
    existing = cur.fetchone()
    if existing:
        cur.execute(
            "UPDATE order_items SET quantity = quantity + ? WHERE id = ?",
            (quantity, existing["id"])
        )
    else:
        cur.execute(
            "INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_order) VALUES (?, ?, ?, ?)",
            (order_id, menu_item_id, quantity, price)
        )
    conn.commit()
    conn.close()


def remove_item_from_order(order_item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM order_items WHERE id = ?", (order_item_id,))
    conn.commit()
    conn.close()


def get_order_items(order_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT oi.id, oi.menu_item_id, oi.quantity, oi.price_at_order, mi.name, mi.category
        FROM order_items oi
        JOIN menu_items mi ON mi.id = oi.menu_item_id
        WHERE oi.order_id = ?
        ORDER BY oi.id
    """, (order_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_open_order_for_table(table_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM orders WHERE table_id = ? AND status = 'Open' ORDER BY id DESC LIMIT 1",
        (table_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_order(order_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_all_orders(status=None):
    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM orders WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cur.execute("SELECT * FROM orders ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def calculate_bill(order_id):
    """Returns dict with subtotal, tax, discount, total for the given order."""
    items = get_order_items(order_id)
    order = get_order(order_id)
    subtotal = sum(item["quantity"] * item["price_at_order"] for item in items)
    discount_amount = subtotal * (order["discount_percent"] / 100.0)
    taxable = subtotal - discount_amount
    tax_amount = taxable * (order["tax_percent"] / 100.0)
    total = taxable + tax_amount
    return {
        "subtotal": round(subtotal, 2),
        "discount_percent": order["discount_percent"],
        "discount_amount": round(discount_amount, 2),
        "tax_percent": order["tax_percent"],
        "tax_amount": round(tax_amount, 2),
        "total": round(total, 2),
    }


def set_order_discount(order_id, discount_percent):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET discount_percent = ? WHERE id = ?", (discount_percent, order_id))
    conn.commit()
    conn.close()


def close_order(order_id, payment_method="Cash"):
    """Mark order as Billed, store payment method and free up its table."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT table_id FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    cur.execute("UPDATE orders SET status = 'Billed', payment_method = ? WHERE id = ?", (payment_method, order_id))
    if row and row["table_id"]:
        cur.execute("UPDATE tables SET status = 'Free' WHERE id = ?", (row["table_id"],))
    conn.commit()
    conn.close()


def cancel_order(order_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT table_id FROM orders WHERE id = ?", (order_id,))
    row = cur.fetchone()
    cur.execute("UPDATE orders SET status = 'Cancelled' WHERE id = ?", (order_id,))
    if row and row["table_id"]:
        cur.execute("UPDATE tables SET status = 'Free' WHERE id = ?", (row["table_id"],))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# LOGIN / USER OPERATIONS
# ---------------------------------------------------------------------------
def _hash_password(password, salt=None):
    """Hash a password using PBKDF2-HMAC-SHA256 with a unique salt."""
    import secrets

    salt_bytes = salt if salt is not None else secrets.token_bytes(16)
    iterations = 310_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, iterations)
    return f"pbkdf2_sha256${iterations}${salt_bytes.hex()}${digest.hex()}"


def _verify_password(password, stored_hash):
    """Verify current PBKDF2 hashes and legacy SHA-256 hashes."""
    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
            calculated = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
            )
            return hmac.compare_digest(calculated.hex(), digest_hex)
        except (ValueError, TypeError):
            return False

    # Backward compatibility for accounts created by the earlier project version.
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored_hash)


def authenticate_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, role, password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row or not _verify_password(password, row["password_hash"]):
        conn.close()
        return None

    # Upgrade older unsalted SHA-256 hashes after a successful login.
    if not row["password_hash"].startswith("pbkdf2_sha256$"):
        cur.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_password(password), row["id"])
        )
        conn.commit()

    conn.close()
    return row["role"]


# ---------------------------------------------------------------------------
# CUSTOMER OPERATIONS
# ---------------------------------------------------------------------------
def get_customers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_customer(name, phone="", email=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)", (name, phone, email))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def delete_customer(customer_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# INVENTORY OPERATIONS
# ---------------------------------------------------------------------------
def get_inventory():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory ORDER BY item_name")
    rows = cur.fetchall()
    conn.close()
    return rows


def add_inventory_item(item_name, unit, quantity, reorder_level):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO inventory (item_name, unit, quantity, reorder_level) VALUES (?, ?, ?, ?)",
        (item_name, unit, quantity, reorder_level)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_inventory_item(item_id, quantity, reorder_level=None):
    conn = get_connection()
    cur = conn.cursor()
    if reorder_level is None:
        cur.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (quantity, item_id))
    else:
        cur.execute("UPDATE inventory SET quantity = ?, reorder_level = ? WHERE id = ?", (quantity, reorder_level, item_id))
    conn.commit()
    conn.close()


def delete_inventory_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def dashboard_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM tables")
    total_tables = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM tables WHERE status = 'Occupied'")
    occupied_tables = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM orders WHERE status = 'Open'")
    open_orders = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM customers")
    customers = cur.fetchone()["c"]
    conn.close()
    report = sales_report()
    return {
        "total_tables": total_tables,
        "occupied_tables": occupied_tables,
        "free_tables": total_tables - occupied_tables,
        "open_orders": open_orders,
        "customers": customers,
        "total_sales": report["total_sales"],
    }


# ---------------------------------------------------------------------------
# REPORTS
# ---------------------------------------------------------------------------
def sales_report():
    """Returns total sales, order count and top selling items for Billed orders."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM orders WHERE status = 'Billed'")
    billed_ids = [r["id"] for r in cur.fetchall()]

    total_sales = 0.0
    for oid in billed_ids:
        bill = calculate_bill(oid)
        total_sales += bill["total"]

    cur.execute("""
        SELECT mi.name, SUM(oi.quantity) AS qty, SUM(oi.quantity * oi.price_at_order) AS revenue
        FROM order_items oi
        JOIN menu_items mi ON mi.id = oi.menu_item_id
        JOIN orders o ON o.id = oi.order_id
        WHERE o.status = 'Billed'
        GROUP BY mi.id
        ORDER BY qty DESC
        LIMIT 5
    """)
    top_items = cur.fetchall()
    conn.close()
    return {
        "total_orders": len(billed_ids),
        "total_sales": round(total_sales, 2),
        "top_items": top_items,
    }


if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DB_NAME)
