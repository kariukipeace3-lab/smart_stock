"""Smart Stock - console menu. Run this file to start the program."""

import getpass
import os
from datetime import date

from auth import AuthManager, AuthError
from file_handler import FileHandler
from manager import InventoryManager, InventoryError
from models import (Item, PerishableItem, ElectronicItem, Supplier,
                    InsufficientStockError)

# The data folder sits next to this file, wherever the program is started from
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Errors we expect from bad input or broken rules: show the message, don't crash
HANDLED_ERRORS = (InventoryError, InsufficientStockError, AuthError, ValueError)


# ===================== input helpers =====================
def ask(prompt, required=True):
    """Ask for text. If required, keep asking until something is typed."""
    while True:
        text = input(prompt).strip()
        if text or not required:
            return text
        print("This cannot be empty.")


def ask_number(prompt, cast, minimum=0, allow_blank=False):
    while True:
        text = input(prompt).strip()
        if allow_blank and text == "":
            return None
        try:
            value = cast(text)
        except ValueError:
            print("Please enter a valid number.")
            continue
        if value < minimum:
            print(f"Value must be at least {minimum}.")
            continue
        return value


def ask_int(prompt, minimum=0, allow_blank=False):
    return ask_number(prompt, int, minimum, allow_blank)


def ask_float(prompt, minimum=0, allow_blank=False):
    return ask_number(prompt, float, minimum, allow_blank)


def ask_date(prompt):
    while True:
        text = input(prompt).strip()
        try:
            date.fromisoformat(text)
            return text
        except ValueError:
            print("Use the format YYYY-MM-DD, for example 2026-12-31.")


def confirm(prompt):
    return input(f"{prompt} (y/n): ").strip().lower() == "y"


# ===================== the application =====================
class SmartStockApp:
    """Ties the login, the InventoryManager and the menus together."""

    def __init__(self, data_dir=DATA_DIR):
        self.auth = AuthManager(os.path.join(data_dir, "users.csv"))
        self.manager = InventoryManager(FileHandler(data_dir))
        self.user = None

    # ---------- start / stop ----------
    def run(self):
        print("=" * 40)
        print("   SMART STOCK - Inventory & Ordering")
        print("=" * 40)
        self.auth.first_run_setup()
        self.user = self.auth.login_prompt()
        if self.user is None:
            return
        self.show_low_stock_alert()
        self.run_menu("MAIN MENU", [
            ("Items", "view", self.items_menu),
            ("Suppliers", "view", self.suppliers_menu),
            ("Purchase orders", "view", self.orders_menu),
            ("Stock movements", "view", self.stock_menu),
            ("Reports", "reports", self.reports_menu),
            ("Users", "manage_users", self.users_menu),
        ], back_label="Exit")
        print("Goodbye! All changes are saved.")

    def run_menu(self, title, options, back_label="Back"):
        """Show only the options this user is allowed to use, then run the choice."""
        allowed = [(label, func) for label, perm, func in options
                   if self.user.can(perm)]
        while True:
            print(f"\n--- {title} ---")
            for n, (label, _) in enumerate(allowed, start=1):
                print(f"{n}. {label}")
            print(f"0. {back_label}")
            choice = input("Choose: ").strip()
            if choice == "0":
                return
            if not choice.isdigit() or not 1 <= int(choice) <= len(allowed):
                print("Invalid choice, try again.")
                continue
            try:
                allowed[int(choice) - 1][1]()
            except HANDLED_ERRORS as e:
                print(f"Error: {e}")

    def show_low_stock_alert(self):
        low = self.manager.low_stock_items()
        if low:
            print("\n*** LOW STOCK ALERT ***")
            for it in low:
                print(f"  {it.name}: {it.quantity} left (reorder level {it.reorder_level})")

    # ---------- submenus ----------
    def items_menu(self):
        self.run_menu("ITEMS", [
            ("View all items", "view", self.view_items),
            ("Search items", "view", self.search_items),
            ("Add item", "add", self.add_item),
            ("Edit item", "edit", self.edit_item),
            ("Delete item", "delete", self.delete_item),
        ])

    def suppliers_menu(self):
        self.run_menu("SUPPLIERS", [
            ("View suppliers", "view", self.view_suppliers),
            ("Add supplier", "add", self.add_supplier),
            ("Assign item to supplier", "edit", self.assign_item),
            ("Delete supplier", "delete", self.delete_supplier),
        ])

    def orders_menu(self):
        self.run_menu("PURCHASE ORDERS", [
            ("View all orders", "view", self.view_orders),
            ("View pending orders", "view", lambda: self.view_orders("Pending")),
            ("Create order", "add", self.create_order),
            ("Mark order as received", "receive", self.receive_order),
            ("Cancel order", "edit", self.cancel_order),
        ])

    def stock_menu(self):
        self.run_menu("STOCK MOVEMENTS", [
            ("Issue stock (stock out)", "issue", self.issue_stock),
            ("Add stock manually (stock in)", "receive", self.add_stock),
            ("Item stock history", "view", self.item_history),
        ])

    def reports_menu(self):
        self.run_menu("REPORTS", [
            ("Total stock value", "reports", self.report_value),
            ("Low-stock list", "reports", self.report_low_stock),
            ("Supplier summary", "reports", self.report_suppliers),
        ])

    def users_menu(self):
        self.run_menu("USERS", [
            ("List users", "manage_users", self.list_users),
            ("Add user", "manage_users", self.add_user),
            ("Delete user", "manage_users", self.delete_user),
        ])

    # ---------- items ----------
    def view_items(self):
        if not self.manager.items:
            print("No items yet.")
            return
        for it in self.manager.items:
            flag = "  <-- LOW STOCK" if it.is_low() else ""
            print(f"- {it.describe()}{flag}")

    def search_items(self):
        query = ask("Search (name, category or supplier): ", required=False)
        results = self.manager.search_items(query)
        if not results:
            print("No matching items.")
        for it in results:
            print(f"- {it.describe()}")

    def add_item(self):
        print("Item type: 1) General   2) Perishable (has expiry)   3) Electronic (has warranty)")
        kind = input("Choose 1-3: ").strip()
        if kind not in ("1", "2", "3"):
            raise ValueError("Item type must be 1, 2 or 3.")
        name = ask("Name: ")
        if self.manager.find_item(name):
            raise InventoryError(f"Item '{name}' already exists.")
        qty = ask_int("Starting quantity: ")
        price = ask_float("Price: ")
        reorder = ask_int("Reorder level: ")
        category = ask("Category (optional): ", required=False)
        if kind == "1":
            item = Item(name, qty, price, reorder, category)
        elif kind == "2":
            expiry = ask_date("Expiry date (YYYY-MM-DD): ")
            item = PerishableItem(name, qty, price, reorder, expiry, category)
        else:
            months = ask_int("Warranty (months): ")
            item = ElectronicItem(name, qty, price, reorder, months, category)
        self.manager.add_item(item, self.user.username)
        print(f"Added '{item.name}'.")

    def edit_item(self):
        item = self.manager.get_item(ask("Item name to edit: "))
        print("Current:", item.describe())
        print("Press Enter to keep a value as it is.")
        price = ask_float("New price: ", allow_blank=True)
        reorder = ask_int("New reorder level: ", allow_blank=True)
        category = ask("New category: ", required=False)
        self.manager.edit_item(item.name, price, reorder, category or None)
        print("Updated:", item.describe())

    def delete_item(self):
        item = self.manager.get_item(ask("Item name to delete: "))
        if confirm(f"Delete '{item.name}'?"):
            self.manager.delete_item(item.name)
            print(f"Deleted '{item.name}'.")
        else:
            print("Cancelled.")

    # ---------- suppliers ----------
    def view_suppliers(self):
        if not self.manager.suppliers:
            print("No suppliers yet.")
        for s in self.manager.suppliers:
            print(f"- {s.describe()}")

    def add_supplier(self):
        name = ask("Supplier name: ")
        phone = ask("Phone: ", required=False)
        email = ask("Email: ", required=False)
        supplier = Supplier(name, phone, email)
        self.manager.add_supplier(supplier)
        print(f"Added supplier '{supplier.name}'.")

    def assign_item(self):
        supplier = ask("Supplier name: ")
        item = ask("Item name: ")
        self.manager.assign_item_to_supplier(supplier, item)
        print("Done.")

    def delete_supplier(self):
        supplier = self.manager.get_supplier(ask("Supplier name to delete: "))
        if confirm(f"Delete '{supplier.name}'?"):
            self.manager.delete_supplier(supplier.name)
            print(f"Deleted '{supplier.name}'.")
        else:
            print("Cancelled.")

    # ---------- purchase orders ----------
    def view_orders(self, status=None):
        orders = self.manager.list_orders(status)
        if not orders:
            print("No orders to show.")
        for o in orders:
            print(f"- {o.describe()}")

    def create_order(self):
        supplier = ask("Supplier name: ")
        item = ask("Item name: ")
        qty = ask_int("Quantity to order: ", minimum=1)
        order = self.manager.create_order(supplier, item, qty)
        print("Created:", order.describe())

    def receive_order(self):
        order_id = ask("Order ID to receive: ")
        trans = self.manager.receive_order(order_id, self.user.username)
        item = self.manager.get_item(trans.item_name)
        print(f"Order received. '{item.name}' stock is now {item.quantity}.")

    def cancel_order(self):
        order = self.manager.cancel_order(ask("Order ID to cancel: "))
        print("Cancelled:", order.describe())

    # ---------- stock movements ----------
    def issue_stock(self):
        name = ask("Item name: ")
        qty = ask_int("Quantity to issue: ", minimum=1)
        note = ask("Note (optional): ", required=False)
        self.manager.issue_stock(name, qty, self.user.username, note)
        item = self.manager.get_item(name)
        print(f"Issued {qty} of '{item.name}'. Remaining: {item.quantity}.")
        if item.is_low():
            print(f"*** LOW STOCK ALERT: '{item.name}' is at {item.quantity} "
                  f"(reorder level {item.reorder_level}). Consider a purchase order.")

    def add_stock(self):
        name = ask("Item name: ")
        qty = ask_int("Quantity to add: ", minimum=1)
        note = ask("Note (optional): ", required=False)
        self.manager.add_stock(name, qty, self.user.username, note)
        item = self.manager.get_item(name)
        print(f"Added {qty} to '{item.name}'. Now: {item.quantity}.")

    def item_history(self):
        records = self.manager.item_history(ask("Item name: "))
        if not records:
            print("No stock movements yet.")
        for t in records:
            print(f"- {t.describe()}")

    # ---------- reports ----------
    def report_value(self):
        print(f"Total stock value: {self.manager.total_stock_value():,.2f}")

    def report_low_stock(self):
        low = self.manager.low_stock_items()
        if not low:
            print("No items are low on stock.")
        for it in low:
            print(f"- {it.name}: {it.quantity} left (reorder level {it.reorder_level})")

    def report_suppliers(self):
        summary = self.manager.supplier_summary()
        if not summary:
            print("No suppliers yet.")
        for row in summary:
            print(f"- {row['name']}: {row['items']} item(s), "
                  f"{row['pending']} pending order(s), {row['received']} received")

    # ---------- users (admin only) ----------
    def list_users(self):
        for u in sorted(self.auth.users.values(), key=lambda u: u.username):
            print(f"- {u.username} ({u.role})")

    def add_user(self):
        username = ask("New username: ")
        password = getpass.getpass("Password: ")
        if password != getpass.getpass("Confirm password: "):
            raise ValueError("Passwords do not match.")
        role = ask("Role (admin/staff) [staff]: ", required=False).lower() or "staff"
        self.auth.register(username, password, role)
        print(f"User '{username.strip().lower()}' created as {role}.")

    def delete_user(self):
        username = ask("Username to delete: ").lower()
        if username == self.user.username:
            raise AuthError("You cannot delete your own account.")
        if confirm(f"Delete user '{username}'?"):
            self.auth.delete_user(username)
            print(f"Deleted user '{username}'.")
        else:
            print("Cancelled.")


def run(data_dir=DATA_DIR):
    try:
        SmartStockApp(data_dir).run()
    except (EOFError, KeyboardInterrupt):
        print("\nProgram closed. All changes were already saved.")


if __name__ == "__main__":
    run()