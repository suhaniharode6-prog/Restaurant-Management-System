"""
console_app.py
----------------
Console (Command-Line) version of the Restaurant Management System.
Run this file directly:

    python console_app.py

Works on Windows / macOS / Linux - no extra libraries needed.
"""

import os
import database as db


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress Enter to continue...")


def print_header(title):
    clear_screen()
    print("=" * 60)
    print(f"  RESTAURANT MANAGEMENT SYSTEM - {title}".upper())
    print("=" * 60)


# ---------------------------------------------------------------------------
# MENU MANAGEMENT
# ---------------------------------------------------------------------------
def view_menu():
    print_header("Menu")
    items = db.get_menu()
    if not items:
        print("No menu items found.")
    else:
        current_cat = None
        for item in items:
            if item["category"] != current_cat:
                current_cat = item["category"]
                print(f"\n-- {current_cat} --")
            status = "" if item["available"] else "  (Unavailable)"
            print(f"  [{item['id']:>3}] {item['name']:<25} Rs.{item['price']:.2f}{status}")
    pause()


def manage_menu():
    while True:
        print_header("Manage Menu")
        print("1. View Menu")
        print("2. Add Menu Item")
        print("3. Update Menu Item")
        print("4. Delete Menu Item")
        print("5. Toggle Availability")
        print("0. Back")
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            view_menu()
        elif choice == "2":
            print_header("Add Menu Item")
            name = input("Item name: ").strip()
            category = input("Category: ").strip()
            try:
                price = float(input("Price: ").strip())
            except ValueError:
                print("Invalid price.")
                pause()
                continue
            db.add_menu_item(name, category, price)
            print(f"'{name}' added successfully!")
            pause()
        elif choice == "3":
            print_header("Update Menu Item")
            view_menu_inline()
            try:
                item_id = int(input("\nEnter item ID to update: ").strip())
            except ValueError:
                print("Invalid ID.")
                pause()
                continue
            name = input("New name (leave blank to keep same): ").strip()
            category = input("New category (leave blank to keep same): ").strip()
            price_str = input("New price (leave blank to keep same): ").strip()
            price = float(price_str) if price_str else None
            db.update_menu_item(
                item_id,
                name=name if name else None,
                category=category if category else None,
                price=price
            )
            print("Item updated.")
            pause()
        elif choice == "4":
            print_header("Delete Menu Item")
            view_menu_inline()
            try:
                item_id = int(input("\nEnter item ID to delete: ").strip())
            except ValueError:
                print("Invalid ID.")
                pause()
                continue
            db.delete_menu_item(item_id)
            print("Item deleted.")
            pause()
        elif choice == "5":
            print_header("Toggle Availability")
            view_menu_inline()
            try:
                item_id = int(input("\nEnter item ID to toggle: ").strip())
            except ValueError:
                print("Invalid ID.")
                pause()
                continue
            items = {i["id"]: i for i in db.get_menu()}
            if item_id in items:
                db.update_menu_item(item_id, available=not items[item_id]["available"])
                print("Availability toggled.")
            else:
                print("Item not found.")
            pause()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")
            pause()


def view_menu_inline():
    items = db.get_menu()
    current_cat = None
    for item in items:
        if item["category"] != current_cat:
            current_cat = item["category"]
            print(f"\n-- {current_cat} --")
        print(f"  [{item['id']:>3}] {item['name']:<25} Rs.{item['price']:.2f}")


# ---------------------------------------------------------------------------
# TABLE MANAGEMENT
# ---------------------------------------------------------------------------
def view_tables():
    print_header("Tables")
    tables = db.get_tables()
    for t in tables:
        print(f"  Table {t['table_no']:<3} | Capacity: {t['capacity']:<3} | Status: {t['status']}")
    pause()


def manage_tables():
    while True:
        print_header("Manage Tables")
        print("1. View Tables")
        print("2. Add Table")
        print("0. Back")
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            view_tables()
        elif choice == "2":
            print_header("Add Table")
            try:
                table_no = int(input("Table number: ").strip())
                capacity = int(input("Capacity (default 4): ").strip() or 4)
            except ValueError:
                print("Invalid input.")
                pause()
                continue
            db.add_table(table_no, capacity)
            print("Table added.")
            pause()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")
            pause()


# ---------------------------------------------------------------------------
# ORDER TAKING / BILLING
# ---------------------------------------------------------------------------
def new_order():
    print_header("New Order")
    tables = db.get_tables()
    free_tables = [t for t in tables if t["status"] == "Free"]
    if not free_tables:
        print("No free tables available!")
        pause()
        return

    print("Free Tables:")
    for t in free_tables:
        print(f"  Table {t['table_no']} (capacity {t['capacity']})")

    try:
        table_no = int(input("\nEnter table number to seat: ").strip())
    except ValueError:
        print("Invalid table number.")
        pause()
        return

    table = next((t for t in tables if t["table_no"] == table_no), None)
    if not table or table["status"] != "Free":
        print("Table not available.")
        pause()
        return

    customer_name = input("Customer name (optional): ").strip()
    order_id = db.create_order(table["id"], customer_name)
    print(f"\nOrder #{order_id} created for Table {table_no}.")
    take_order(order_id)


def take_order(order_id):
    while True:
        print_header(f"Taking Order #{order_id}")
        view_menu_inline()
        current_items = db.get_order_items(order_id)
        if current_items:
            print("\n-- Current Order --")
            for oi in current_items:
                print(f"  {oi['name']:<25} x{oi['quantity']}  Rs.{oi['price_at_order']*oi['quantity']:.2f}")

        print("\n1. Add item to order")
        print("2. Remove item from order")
        print("3. Finish & Generate Bill")
        print("4. Cancel Order")
        print("0. Save & Back to Main Menu")
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            try:
                item_id = int(input("Enter menu item ID: ").strip())
                qty = int(input("Quantity: ").strip())
            except ValueError:
                print("Invalid input.")
                pause()
                continue
            try:
                db.add_item_to_order(order_id, item_id, qty)
                print("Item added.")
            except ValueError as e:
                print(f"Error: {e}")
            pause()
        elif choice == "2":
            items = db.get_order_items(order_id)
            if not items:
                print("No items to remove.")
                pause()
                continue
            for oi in items:
                print(f"  [{oi['id']}] {oi['name']} x{oi['quantity']}")
            try:
                remove_id = int(input("Enter row ID to remove: ").strip())
                db.remove_item_from_order(remove_id)
                print("Item removed.")
            except ValueError:
                print("Invalid input.")
            pause()
        elif choice == "3":
            generate_bill(order_id)
            return
        elif choice == "4":
            confirm = input("Are you sure you want to cancel this order? (y/n): ").strip().lower()
            if confirm == "y":
                db.cancel_order(order_id)
                print("Order cancelled.")
                pause()
                return
        elif choice == "0":
            return
        else:
            print("Invalid choice.")
            pause()


def generate_bill(order_id):
    print_header("Bill")
    items = db.get_order_items(order_id)
    order = db.get_order(order_id)
    if not items:
        print("No items in this order. Add items before billing.")
        pause()
        return

    disc = input("Apply discount % (leave blank for 0): ").strip()
    if disc:
        try:
            db.set_order_discount(order_id, float(disc))
        except ValueError:
            pass

    bill = db.calculate_bill(order_id)

    print(f"\nOrder #{order_id}  |  Customer: {order['customer_name'] or 'Walk-in'}")
    print("-" * 50)
    print(f"{'Item':<25}{'Qty':>5}{'Amount':>15}")
    print("-" * 50)
    for oi in items:
        amt = oi["quantity"] * oi["price_at_order"]
        print(f"{oi['name']:<25}{oi['quantity']:>5}{'Rs.' + format(amt, '.2f'):>15}")
    print("-" * 50)
    print(f"{'Subtotal':<30}{'Rs.' + format(bill['subtotal'], '.2f'):>20}")
    print(f"{'Discount (' + str(bill['discount_percent']) + '%)':<30}{'-Rs.' + format(bill['discount_amount'], '.2f'):>20}")
    print(f"{'Tax (' + str(bill['tax_percent']) + '%)':<30}{'+Rs.' + format(bill['tax_amount'], '.2f'):>20}")
    print("=" * 50)
    print(f"{'TOTAL':<30}{'Rs.' + format(bill['total'], '.2f'):>20}")
    print("=" * 50)

    confirm = input("\nConfirm and close this order? (y/n): ").strip().lower()
    if confirm == "y":
        db.close_order(order_id)
        print("Order billed and closed. Table is now free.")
    else:
        print("Order left open (not billed yet).")
    pause()


def continue_order():
    print_header("Continue Existing Order")
    open_orders = db.get_all_orders(status="Open")
    if not open_orders:
        print("No open orders.")
        pause()
        return
    for o in open_orders:
        table = None
        if o["table_id"]:
            for t in db.get_tables():
                if t["id"] == o["table_id"]:
                    table = t
                    break
        table_label = f"Table {table['table_no']}" if table else "N/A"
        print(f"  Order #{o['id']}  |  {table_label}  |  Customer: {o['customer_name'] or 'Walk-in'}")

    try:
        order_id = int(input("\nEnter Order ID to continue: ").strip())
    except ValueError:
        print("Invalid input.")
        pause()
        return
    take_order(order_id)


# ---------------------------------------------------------------------------
# REPORTS
# ---------------------------------------------------------------------------
def view_reports():
    print_header("Sales Report")
    report = db.sales_report()
    print(f"Total Billed Orders : {report['total_orders']}")
    print(f"Total Sales Revenue : Rs.{report['total_sales']:.2f}")
    print("\nTop Selling Items:")
    if not report["top_items"]:
        print("  No sales data yet.")
    else:
        for item in report["top_items"]:
            print(f"  {item['name']:<25} Qty: {item['qty']:<5} Revenue: Rs.{item['revenue']:.2f}")
    pause()


# ---------------------------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------------------------
def main_menu():
    db.init_db()
    while True:
        print_header("Main Menu")
        print("1. New Order (Seat Customer & Take Order)")
        print("2. Continue Existing Open Order")
        print("3. View Menu")
        print("4. Manage Menu (Add/Edit/Delete Items)")
        print("5. Manage Tables")
        print("6. Sales Report")
        print("0. Exit")
        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            new_order()
        elif choice == "2":
            continue_order()
        elif choice == "3":
            view_menu()
        elif choice == "4":
            manage_menu()
        elif choice == "5":
            manage_tables()
        elif choice == "6":
            view_reports()
        elif choice == "0":
            print("\nThank you! Exiting Restaurant Management System.")
            break
        else:
            print("Invalid choice.")
            pause()


if __name__ == "__main__":
    main_menu()
