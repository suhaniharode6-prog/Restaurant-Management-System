"""
gui_app.py
-----------
Window (GUI) version of the Restaurant Management System, built with
Tkinter (comes built-in with Python - no extra installation needed).

Run this file directly:

    python gui_app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import database as db
from login import LoginWindow


BG_COLOR = "#1e2a38"
PANEL_COLOR = "#f4f6f8"
ACCENT_COLOR = "#e07a1f"
TEXT_COLOR = "#1e2a38"
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_BOLD = ("Segoe UI", 11, "bold")


class RestaurantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Restaurant Management System")
        self.geometry("1100x680")
        self.minsize(950, 600)
        self.configure(bg=BG_COLOR)

        db.init_db()

        self.current_order_id = None
        self.current_table_id = None
        self.current_user = None
        self.current_role = None

        # Keep the main window available so the login dialog is visible.
        self.deiconify()
        self.after(100, self.show_login)

    # ------------------------------------------------------------------
    # LOGIN / LOGOUT
    # ------------------------------------------------------------------
    def show_login(self):
        login = LoginWindow(self, self.on_login_success)
        login.lift()
        login.attributes("-topmost", True)
        login.after(500, lambda: login.attributes("-topmost", False))

    def on_login_success(self, username, role):
        self.current_user = username
        self.current_role = role
        self.title(f"Restaurant Management System - {username}")
        self.deiconify()
        self._build_layout()
        self.user_label.config(text=f"👤 {username}\n   {role}")
        self.show_dashboard()

    def logout(self):
        if not messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=self):
            return
        for widget in self.winfo_children():
            widget.destroy()
        self.current_user = None
        self.current_role = None
        self.title("Restaurant Management System")
        # Keep the main window available so the login dialog is visible.
        self.deiconify()
        self.after(100, self.show_login)

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build_layout(self):
        # Sidebar
        sidebar = tk.Frame(self, bg=BG_COLOR, width=220)
        sidebar.pack(side="left", fill="y")

        title = tk.Label(sidebar, text="🍽  Restro\nManager", bg=BG_COLOR, fg="white",
                          font=FONT_TITLE, justify="left")
        title.pack(pady=(30, 40), padx=20, anchor="w")

        nav_buttons = [
            ("🏠  Dashboard / Tables", self.show_dashboard),
            ("📋  Menu Management", self.show_menu_management),
            ("👤  Customers", self.show_customers),
            ("📦  Inventory", self.show_inventory),
            ("🧾  Orders (Open)", self.show_open_orders),
            ("📊  Sales Report", self.show_reports),
        ]
        for text, cmd in nav_buttons:
            b = tk.Button(sidebar, text=text, command=cmd, bg=BG_COLOR, fg="white",
                          font=FONT_NORMAL, bd=0, anchor="w", padx=20, pady=10,
                          activebackground=ACCENT_COLOR, activeforeground="white",
                          cursor="hand2")
            b.pack(fill="x")

        self.user_label = tk.Label(sidebar, text="", bg=BG_COLOR, fg="#d7dee5",
                                   font=("Segoe UI", 9), justify="left", anchor="w", padx=20)
        self.user_label.pack(side="bottom", fill="x", pady=(0, 8))
        tk.Button(sidebar, text="🚪  Logout", command=self.logout, bg=BG_COLOR, fg="white",
                  font=FONT_NORMAL, bd=0, anchor="w", padx=20, pady=12,
                  activebackground="#c94f45", activeforeground="white", cursor="hand2").pack(side="bottom", fill="x")

        # Main content area
        self.content = tk.Frame(self, bg=PANEL_COLOR)
        self.content.pack(side="right", fill="both", expand=True)

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _page_title(self, text):
        lbl = tk.Label(self.content, text=text, bg=PANEL_COLOR, fg=TEXT_COLOR,
                        font=FONT_TITLE, anchor="w")
        lbl.pack(fill="x", padx=30, pady=(25, 15))
        return lbl

    # ------------------------------------------------------------------
    # DASHBOARD - TABLES
    # ------------------------------------------------------------------
    def show_dashboard(self):
        self._clear_content()
        self._page_title("Tables Overview")

        top_bar = tk.Frame(self.content, bg=PANEL_COLOR)
        top_bar.pack(fill="x", padx=30)
        tk.Button(top_bar, text="+ Add Table", command=self.add_table_dialog,
                  bg=ACCENT_COLOR, fg="white", font=FONT_BOLD, bd=0, padx=15, pady=6,
                  cursor="hand2").pack(side="left")

        stats = db.dashboard_stats()
        stats_frame = tk.Frame(self.content, bg=PANEL_COLOR)
        stats_frame.pack(fill="x", padx=30, pady=(15, 0))
        stat_items = [
            ("Tables", stats["total_tables"]),
            ("Occupied", stats["occupied_tables"]),
            ("Free", stats["free_tables"]),
            ("Open Orders", stats["open_orders"]),
            ("Customers", stats["customers"]),
            ("Sales", f"Rs.{stats['total_sales']:.0f}"),
        ]
        for label, value in stat_items:
            card = tk.Frame(stats_frame, bg="white", highlightbackground="#dfe5ea", highlightthickness=1)
            card.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(card, text=str(value), bg="white", fg=ACCENT_COLOR, font=("Segoe UI", 15, "bold")).pack(pady=(8, 0))
            tk.Label(card, text=label, bg="white", fg="#66717d", font=("Segoe UI", 8)).pack(pady=(0, 8))

        grid_frame = tk.Frame(self.content, bg=PANEL_COLOR)
        grid_frame.pack(fill="both", expand=True, padx=30, pady=15)

        tables = db.get_tables()
        cols = 5
        for idx, t in enumerate(tables):
            r, c = divmod(idx, cols)
            color = "#5cb85c" if t["status"] == "Free" else "#d9534f"
            card = tk.Frame(grid_frame, bg=color, width=160, height=110, cursor="hand2")
            card.grid(row=r, column=c, padx=10, pady=10)
            card.grid_propagate(False)
            tk.Label(card, text=f"Table {t['table_no']}", bg=color, fg="white",
                     font=FONT_BOLD).pack(pady=(15, 5))
            tk.Label(card, text=f"Cap: {t['capacity']}", bg=color, fg="white",
                     font=FONT_NORMAL).pack()
            tk.Label(card, text=t["status"], bg=color, fg="white",
                     font=FONT_NORMAL).pack()
            card.bind("<Button-1>", lambda e, tbl=t: self.on_table_click(tbl))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, tbl=t: self.on_table_click(tbl))

    def add_table_dialog(self):
        table_no = simpledialog.askinteger("Add Table", "Enter table number:")
        if not table_no:
            return
        capacity = simpledialog.askinteger("Add Table", "Enter seating capacity:", initialvalue=4)
        try:
            db.add_table(table_no, capacity or 4)
            messagebox.showinfo("Success", f"Table {table_no} added.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.show_dashboard()

    def on_table_click(self, table):
        if table["status"] == "Free":
            name = simpledialog.askstring("New Order", f"Customer name for Table {table['table_no']} (optional):") or ""
            order_id = db.create_order(table["id"], name)
            self.open_order_screen(order_id)
        else:
            order = db.get_open_order_for_table(table["id"])
            if order:
                self.open_order_screen(order["id"])
            else:
                messagebox.showinfo("Info", "Table occupied but no open order found.")

    # ------------------------------------------------------------------
    # ORDER TAKING SCREEN
    # ------------------------------------------------------------------
    def show_open_orders(self):
        self._clear_content()
        self._page_title("Open Orders")

        frame = tk.Frame(self.content, bg=PANEL_COLOR)
        frame.pack(fill="both", expand=True, padx=30, pady=10)

        cols = ("ID", "Table", "Customer", "Date")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=150)
        tree.pack(fill="both", expand=True)

        tables = {t["id"]: t["table_no"] for t in db.get_tables()}
        for o in db.get_all_orders(status="Open"):
            table_label = f"Table {tables.get(o['table_id'], '-')}" if o["table_id"] else "-"
            tree.insert("", "end", iid=o["id"],
                        values=(o["id"], table_label, o["customer_name"] or "Walk-in", o["order_date"]))

        def on_double_click(event):
            selected = tree.focus()
            if selected:
                self.open_order_screen(int(selected))

        tree.bind("<Double-1>", on_double_click)
        
        tk.Label(self.content, text="Double-click an order to open it.",
                 bg=PANEL_COLOR, fg="#777", font=FONT_NORMAL).pack(padx=30, anchor="w")

    def open_order_screen(self, order_id):
        self.current_order_id = order_id
        self._clear_content()

        order = db.get_order(order_id)
        table_no = None
        if order["table_id"]:
            t = db.get_table(order["table_id"])
            table_no = t["table_no"] if t else None

        header = f"Order #{order_id}" + (f"  |  Table {table_no}" if table_no else "") + \
                 f"  |  {order['customer_name'] or 'Walk-in'}"
        self._page_title(header)

        main_frame = tk.Frame(self.content, bg=PANEL_COLOR)
        main_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Left: Menu selection
        left = tk.Frame(main_frame, bg=PANEL_COLOR)
        left.pack(side="left", fill="both", expand=True, padx=(0, 15))

        tk.Label(left, text="Menu", bg=PANEL_COLOR, font=FONT_BOLD).pack(anchor="w")

        menu_cols = ("ID", "Item", "Category", "Price")
        menu_tree = ttk.Treeview(left, columns=menu_cols, show="headings", height=16)
        for c in menu_cols:
            menu_tree.heading(c, text=c)
        menu_tree.column("ID", width=40)
        menu_tree.column("Item", width=180)
        menu_tree.column("Category", width=120)
        menu_tree.column("Price", width=80)
        menu_tree.pack(fill="both", expand=True)

        for item in db.get_menu(only_available=True):
            menu_tree.insert("", "end", iid=item["id"],
                             values=(item["id"], item["name"], item["category"], f"{item['price']:.2f}"))

        qty_frame = tk.Frame(left, bg=PANEL_COLOR)
        qty_frame.pack(fill="x", pady=8)
        tk.Label(qty_frame, text="Qty:", bg=PANEL_COLOR, font=FONT_NORMAL).pack(side="left")
        qty_var = tk.IntVar(value=1)
        tk.Spinbox(qty_frame, from_=1, to=50, width=5, textvariable=qty_var).pack(side="left", padx=8)

        def add_to_order():
            selected = menu_tree.focus()
            if not selected:
                messagebox.showwarning("Select item", "Please select a menu item first.")
                return
            db.add_item_to_order(order_id, int(selected), qty_var.get())
            refresh_order_items()

        tk.Button(qty_frame, text="Add to Order →", command=add_to_order,
                  bg=ACCENT_COLOR, fg="white", font=FONT_BOLD, bd=0, padx=12, pady=6,
                  cursor="hand2").pack(side="left", padx=10)

        # Right: Current order + bill
        right = tk.Frame(main_frame, bg=PANEL_COLOR)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="Current Order", bg=PANEL_COLOR, font=FONT_BOLD).pack(anchor="w")

        order_cols = ("RowID", "Item", "Qty", "Amount")
        order_tree = ttk.Treeview(right, columns=order_cols, show="headings", height=10)
        for c in order_cols:
            order_tree.heading(c, text=c)
        order_tree.column("RowID", width=0, stretch=False)  # hidden
        order_tree.column("Item", width=180)
        order_tree.column("Qty", width=60)
        order_tree.column("Amount", width=90)
        order_tree.pack(fill="both", expand=True)

        bill_label = tk.Label(right, text="", bg=PANEL_COLOR, font=FONT_NORMAL, justify="left", anchor="w")
        bill_label.pack(fill="x", pady=10, anchor="w")

        def refresh_order_items():
            for row in order_tree.get_children():
                order_tree.delete(row)
            items = db.get_order_items(order_id)
            for oi in items:
                amt = oi["quantity"] * oi["price_at_order"]
                order_tree.insert("", "end", iid=oi["id"],
                                  values=(oi["id"], oi["name"], oi["quantity"], f"{amt:.2f}"))
            bill = db.calculate_bill(order_id)
            bill_label.config(text=(
                f"Subtotal: Rs.{bill['subtotal']:.2f}\n"
                f"Discount ({bill['discount_percent']}%): -Rs.{bill['discount_amount']:.2f}\n"
                f"Tax ({bill['tax_percent']}%): +Rs.{bill['tax_amount']:.2f}\n"
                f"TOTAL: Rs.{bill['total']:.2f}"
            ))

        def remove_selected():
            selected = order_tree.focus()
            if not selected:
                messagebox.showwarning("Select row", "Select an order row to remove.")
                return
            db.remove_item_from_order(int(selected))
            refresh_order_items()

        def apply_discount():
            disc = simpledialog.askfloat("Discount", "Enter discount percentage:", initialvalue=0, minvalue=0, maxvalue=100)
            if disc is not None:
                db.set_order_discount(order_id, disc)
                refresh_order_items()

        payment_frame = tk.Frame(right, bg=PANEL_COLOR)
        payment_frame.pack(fill="x", pady=(0, 8))
        tk.Label(payment_frame, text="Payment:", bg=PANEL_COLOR, font=FONT_NORMAL).pack(side="left")
        payment_var = tk.StringVar(value=(order["payment_method"] if "payment_method" in order.keys() and order["payment_method"] else "Cash"))
        payment_combo = ttk.Combobox(payment_frame, textvariable=payment_var, values=["Cash", "UPI", "Card"], state="readonly", width=12)
        payment_combo.pack(side="left", padx=8)

        def finish_bill():
            items = db.get_order_items(order_id)
            if not items:
                messagebox.showwarning("Empty order", "Add at least one item before billing.")
                return
            bill = db.calculate_bill(order_id)
            confirm = messagebox.askyesno(
                "Confirm Bill",
                f"Total amount: Rs.{bill['total']:.2f}\n\nConfirm and close this order?"
            )
            if confirm:
                db.close_order(order_id, payment_var.get())
                messagebox.showinfo("Success", f"Order billed successfully.\nPayment: {payment_var.get()}\nTable is now free.")
                self.show_dashboard()

        def cancel_this_order():
            confirm = messagebox.askyesno("Cancel Order", "Are you sure you want to cancel this order?")
            if confirm:
                db.cancel_order(order_id)
                self.show_dashboard()

        btn_frame = tk.Frame(right, bg=PANEL_COLOR)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="Remove Selected", command=remove_selected,
                  bg="#d9534f", fg="white", font=FONT_NORMAL, bd=0, padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="Apply Discount", command=apply_discount,
                  bg="#5bc0de", fg="white", font=FONT_NORMAL, bd=0, padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel Order", command=cancel_this_order,
                  bg="#777", fg="white", font=FONT_NORMAL, bd=0, padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=6)
        tk.Button(right, text="✓  Finish & Generate Bill", command=finish_bill,
                  bg="#5cb85c", fg="white", font=FONT_BOLD, bd=0, padx=15, pady=10,
                  cursor="hand2").pack(fill="x", pady=(10, 0))

        refresh_order_items()

    # ------------------------------------------------------------------
    # CUSTOMER MANAGEMENT
    # ------------------------------------------------------------------
    def show_customers(self):
        self._clear_content()
        self._page_title("Customer Management")

        top = tk.Frame(self.content, bg=PANEL_COLOR)
        top.pack(fill="x", padx=30)
        tk.Button(top, text="+ Add Customer", command=self.add_customer_dialog,
                  bg=ACCENT_COLOR, fg="white", font=FONT_BOLD, bd=0, padx=15, pady=6,
                  cursor="hand2").pack(side="left")

        frame = tk.Frame(self.content, bg=PANEL_COLOR)
        frame.pack(fill="both", expand=True, padx=30, pady=15)
        cols = ("ID", "Name", "Phone", "Email")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=60)
        tree.column("Name", width=220)
        tree.column("Phone", width=160)
        tree.column("Email", width=260)
        tree.pack(fill="both", expand=True, side="left")

        def load():
            tree.delete(*tree.get_children())
            for c in db.get_customers():
                tree.insert("", "end", iid=c["id"], values=(c["id"], c["name"], c["phone"] or "", c["email"] or ""))
        def delete_selected():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Select customer", "Please select a customer.")
                return
            if messagebox.askyesno("Delete", "Delete selected customer?"):
                db.delete_customer(int(selected)); load()
        tk.Button(frame, text="Delete", command=delete_selected, bg="#d9534f", fg="white",
                  font=FONT_NORMAL, bd=0, padx=15, pady=8, cursor="hand2").pack(side="left", padx=15)
        load()

    def add_customer_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Customer")
        dialog.geometry("380x330")
        dialog.configure(bg=PANEL_COLOR)
        vars_ = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        for label, var in zip(("Name", "Phone", "Email"), vars_):
            tk.Label(dialog, text=label + ":", bg=PANEL_COLOR, font=FONT_NORMAL).pack(anchor="w", padx=20, pady=(18, 2))
            tk.Entry(dialog, textvariable=var, font=FONT_NORMAL).pack(fill="x", padx=20, ipady=5)
        def save():
            name, phone, email = [v.get().strip() for v in vars_]
            if not name:
                messagebox.showerror("Error", "Customer name is required.", parent=dialog); return
            db.add_customer(name, phone, email); dialog.destroy(); self.show_customers()
        tk.Button(dialog, text="Save Customer", command=save, bg=ACCENT_COLOR, fg="white",
                  font=FONT_BOLD, bd=0, padx=15, pady=8, cursor="hand2").pack(pady=22)

    # ------------------------------------------------------------------
    # INVENTORY MANAGEMENT
    # ------------------------------------------------------------------
    def show_inventory(self):
        self._clear_content()
        self._page_title("Inventory / Stock Management")
        top = tk.Frame(self.content, bg=PANEL_COLOR)
        top.pack(fill="x", padx=30)
        tk.Button(top, text="+ Add Stock Item", command=self.add_inventory_dialog,
                  bg=ACCENT_COLOR, fg="white", font=FONT_BOLD, bd=0, padx=15, pady=6,
                  cursor="hand2").pack(side="left")
        tk.Label(top, text="Track ingredients and low-stock levels", bg=PANEL_COLOR, fg="#777", font=("Segoe UI", 9)).pack(side="left", padx=15)

        frame = tk.Frame(self.content, bg=PANEL_COLOR)
        frame.pack(fill="both", expand=True, padx=30, pady=15)
        cols = ("ID", "Item", "Unit", "Quantity", "Reorder Level", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=50); tree.column("Item", width=220); tree.column("Unit", width=100)
        tree.column("Quantity", width=110); tree.column("Reorder Level", width=130); tree.column("Status", width=130)
        tree.pack(fill="both", expand=True, side="left")

        def load():
            tree.delete(*tree.get_children())
            for item in db.get_inventory():
                status = "LOW STOCK" if item["quantity"] <= item["reorder_level"] else "Normal"
                tree.insert("", "end", iid=item["id"], values=(item["id"], item["item_name"], item["unit"], item["quantity"], item["reorder_level"], status))
        def update_stock():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Select item", "Please select a stock item."); return
            current = next((x for x in db.get_inventory() if x["id"] == int(selected)), None)
            if not current: return
            qty = simpledialog.askfloat("Update Stock", f"Enter new quantity for {current['item_name']}:", initialvalue=float(current["quantity"]), minvalue=0)
            if qty is not None:
                db.update_inventory_item(current["id"], qty); load()
        def delete_stock():
            selected = tree.focus()
            if not selected: return
            if messagebox.askyesno("Delete", "Delete selected stock item?"):
                db.delete_inventory_item(int(selected)); load()
        btns = tk.Frame(frame, bg=PANEL_COLOR); btns.pack(side="left", fill="y", padx=15)
        tk.Button(btns, text="Update Stock", command=update_stock, bg="#5bc0de", fg="white", font=FONT_NORMAL, bd=0, padx=12, pady=8).pack(fill="x", pady=4)
        tk.Button(btns, text="Delete", command=delete_stock, bg="#d9534f", fg="white", font=FONT_NORMAL, bd=0, padx=12, pady=8).pack(fill="x", pady=4)
        load()

    def add_inventory_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Stock Item")
        dialog.geometry("400x420")
        dialog.configure(bg=PANEL_COLOR)
        labels = ["Item Name", "Unit (kg/litre/pcs)", "Quantity", "Reorder Level"]
        vars_ = [tk.StringVar(), tk.StringVar(value="pcs"), tk.StringVar(value="0"), tk.StringVar(value="5")]
        for label, var in zip(labels, vars_):
            tk.Label(dialog, text=label + ":", bg=PANEL_COLOR, font=FONT_NORMAL).pack(anchor="w", padx=20, pady=(16, 2))
            tk.Entry(dialog, textvariable=var, font=FONT_NORMAL).pack(fill="x", padx=20, ipady=5)
        def save():
            name, unit = vars_[0].get().strip(), vars_[1].get().strip()
            try:
                qty, reorder = float(vars_[2].get()), float(vars_[3].get())
            except ValueError:
                messagebox.showerror("Error", "Quantity and reorder level must be numbers.", parent=dialog); return
            if not name or not unit or qty < 0 or reorder < 0:
                messagebox.showerror("Error", "Enter valid stock details.", parent=dialog); return
            db.add_inventory_item(name, unit, qty, reorder); dialog.destroy(); self.show_inventory()
        tk.Button(dialog, text="Save Stock Item", command=save, bg=ACCENT_COLOR, fg="white", font=FONT_BOLD, bd=0, padx=15, pady=8).pack(pady=24)

    # ------------------------------------------------------------------
    # MENU MANAGEMENT
    # ------------------------------------------------------------------
    def show_menu_management(self):
        self._clear_content()
        self._page_title("Menu Management")

        top_bar = tk.Frame(self.content, bg=PANEL_COLOR)
        top_bar.pack(fill="x", padx=30)
        tk.Button(top_bar, text="+ Add Item", command=lambda: self.menu_item_dialog(),
                  bg=ACCENT_COLOR, fg="white", font=FONT_BOLD, bd=0, padx=15, pady=6,
                  cursor="hand2").pack(side="left")

        frame = tk.Frame(self.content, bg=PANEL_COLOR)
        frame.pack(fill="both", expand=True, padx=30, pady=15)

        cols = ("ID", "Name", "Category", "Price", "Available")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        for c in cols:
            tree.heading(c, text=c)
        tree.column("ID", width=50)
        tree.pack(fill="both", expand=True, side="left")

        def load():
            for row in tree.get_children():
                tree.delete(row)
            for item in db.get_menu():
                tree.insert("", "end", iid=item["id"], values=(
                    item["id"], item["name"], item["category"],
                    f"{item['price']:.2f}", "Yes" if item["available"] else "No"
                ))

        btns = tk.Frame(frame, bg=PANEL_COLOR)
        btns.pack(side="left", fill="y", padx=15)

        def edit_selected():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Select item", "Please select a menu item.")
                return
            item_id = int(selected)
            item = next((i for i in db.get_menu() if i["id"] == item_id), None)
            if item:
                self.menu_item_dialog(item)
                load()

        def delete_selected():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Select item", "Please select a menu item.")
                return
            if messagebox.askyesno("Delete", "Delete this menu item?"):
                db.delete_menu_item(int(selected))
                load()

        def toggle_selected():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Select item", "Please select a menu item.")
                return
            item_id = int(selected)
            item = next((i for i in db.get_menu() if i["id"] == item_id), None)
            if item:
                db.update_menu_item(item_id, available=not item["available"])
                load()

        tk.Button(btns, text="Edit", command=edit_selected, bg="#5bc0de", fg="white",
                  font=FONT_NORMAL, bd=0, padx=15, pady=8, cursor="hand2").pack(fill="x", pady=4)
        tk.Button(btns, text="Delete", command=delete_selected, bg="#d9534f", fg="white",
                  font=FONT_NORMAL, bd=0, padx=15, pady=8, cursor="hand2").pack(fill="x", pady=4)
        tk.Button(btns, text="Toggle Available", command=toggle_selected, bg="#f0ad4e", fg="white",
                  font=FONT_NORMAL, bd=0, padx=15, pady=8, cursor="hand2").pack(fill="x", pady=4)

        load()
        self._menu_reload = load  # keep reference for dialog callback

    def menu_item_dialog(self, item=None):
        dialog = tk.Toplevel(self)
        dialog.title("Edit Item" if item else "Add Item")
        dialog.geometry("320x260")
        dialog.configure(bg=PANEL_COLOR)
        dialog.grab_set()

        tk.Label(dialog, text="Name:", bg=PANEL_COLOR, font=FONT_NORMAL).pack(anchor="w", padx=20, pady=(20, 0))
        name_var = tk.StringVar(value=item["name"] if item else "")
        tk.Entry(dialog, textvariable=name_var, font=FONT_NORMAL).pack(fill="x", padx=20)

        tk.Label(dialog, text="Category:", bg=PANEL_COLOR, font=FONT_NORMAL).pack(anchor="w", padx=20, pady=(10, 0))
        category_var = tk.StringVar(value=item["category"] if item else "")
        tk.Entry(dialog, textvariable=category_var, font=FONT_NORMAL).pack(fill="x", padx=20)

        tk.Label(dialog, text="Price:", bg=PANEL_COLOR, font=FONT_NORMAL).pack(anchor="w", padx=20, pady=(10, 0))
        price_var = tk.StringVar(value=str(item["price"]) if item else "")
        tk.Entry(dialog, textvariable=price_var, font=FONT_NORMAL).pack(fill="x", padx=20)

        def save():
            name = name_var.get().strip()
            category = category_var.get().strip()
            try:
                price = float(price_var.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Price must be a number.")
                return
            if not name or not category:
                messagebox.showerror("Error", "Name and category are required.")
                return
            if item:
                db.update_menu_item(item["id"], name=name, category=category, price=price)
            else:
                db.add_menu_item(name, category, price)
            dialog.destroy()
            if hasattr(self, "_menu_reload"):
                self._menu_reload()

        tk.Button(dialog, text="Save", command=save, bg=ACCENT_COLOR, fg="white",
                  font=FONT_BOLD, bd=0, padx=15, pady=8, cursor="hand2").pack(pady=20)

    # ------------------------------------------------------------------
    # REPORTS
    # ------------------------------------------------------------------
    def show_reports(self):
        self._clear_content()
        self._page_title("Sales Report")

        report = db.sales_report()
        summary = tk.Frame(self.content, bg=PANEL_COLOR)
        summary.pack(fill="x", padx=30, pady=10)

        tk.Label(summary, text=f"Total Billed Orders: {report['total_orders']}",
                 bg=PANEL_COLOR, font=FONT_BOLD).pack(anchor="w")
        tk.Label(summary, text=f"Total Sales Revenue: Rs.{report['total_sales']:.2f}",
                 bg=PANEL_COLOR, font=FONT_BOLD, fg=ACCENT_COLOR).pack(anchor="w", pady=(5, 20))

        tk.Label(summary, text="Top Selling Items", bg=PANEL_COLOR, font=FONT_BOLD).pack(anchor="w")

        frame = tk.Frame(self.content, bg=PANEL_COLOR)
        frame.pack(fill="both", expand=True, padx=30, pady=10)

        cols = ("Item", "Qty Sold", "Revenue")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill="both", expand=True)

        for item in report["top_items"]:
            tree.insert("", "end", values=(item["name"], item["qty"], f"Rs.{item['revenue']:.2f}"))


if __name__ == "__main__":
    app = RestaurantApp()
    app.mainloop()
