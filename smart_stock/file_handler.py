"""Smart Stock - reads and writes the CSV data files."""

import csv
import os
from datetime import date, datetime

from models import (Item, PerishableItem, ElectronicItem,
                    Supplier, PurchaseOrder, StockTransaction)


class FileHandler:
    """Saves and loads items, suppliers, orders and transactions as CSV files."""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.items_file = os.path.join(data_dir, "items.csv")
        self.suppliers_file = os.path.join(data_dir, "suppliers.csv")
        self.orders_file = os.path.join(data_dir, "orders.csv")
        self.transactions_file = os.path.join(data_dir, "transactions.csv")

    # ---------- helpers ----------
    def _write(self, path, header, rows):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    def _read(self, path):
        """Return a list of row dicts. A missing file means no data yet."""
        if not os.path.exists(path):
            return []
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    @staticmethod
    def _skip(filename, row_number, error):
        print(f"Warning: skipped bad row {row_number} in {filename} ({error})")

    # ---------- items ----------
    def save_items(self, items):
        rows = []
        for it in items:
            if isinstance(it, PerishableItem):
                kind, extra = "perishable", it.expiry_date.isoformat()
            elif isinstance(it, ElectronicItem):
                kind, extra = "electronic", it.warranty_months
            else:
                kind, extra = "general", ""
            rows.append([kind, it.name, it.quantity, it.price,
                         it.reorder_level, it.category, extra])
        self._write(self.items_file,
                    ["type", "name", "quantity", "price", "reorder_level", "category", "extra"],
                    rows)

    def load_items(self):
        items = []
        for n, r in enumerate(self._read(self.items_file), start=2):
            try:
                args = (r["name"], int(r["quantity"]), float(r["price"]),
                        int(r["reorder_level"]))
                cat = r["category"]
                if r["type"] == "perishable":
                    items.append(PerishableItem(*args, r["extra"], cat))
                elif r["type"] == "electronic":
                    items.append(ElectronicItem(*args, int(r["extra"]), cat))
                else:
                    items.append(Item(*args, cat))
            except (ValueError, KeyError, TypeError) as e:
                self._skip("items.csv", n, e)
        return items

    # ---------- suppliers ----------
    def save_suppliers(self, suppliers):
        rows = [[s.name, s.phone, s.email, "|".join(s.items_supplied)] for s in suppliers]
        self._write(self.suppliers_file, ["name", "phone", "email", "items_supplied"], rows)

    def load_suppliers(self):
        suppliers = []
        for n, r in enumerate(self._read(self.suppliers_file), start=2):
            try:
                s = Supplier(r["name"], r["phone"], r["email"])
                for item_name in filter(None, r["items_supplied"].split("|")):
                    s.add_item(item_name)
                suppliers.append(s)
            except (ValueError, KeyError) as e:
                self._skip("suppliers.csv", n, e)
        return suppliers

    # ---------- purchase orders ----------
    def save_orders(self, orders):
        rows = [[o.order_id, o.supplier.name, o.item_name, o.quantity, o.status,
                 o.date_ordered.isoformat(),
                 o.date_received.isoformat() if o.date_received else ""]
                for o in orders]
        self._write(self.orders_file,
                    ["order_id", "supplier", "item_name", "quantity", "status",
                     "date_ordered", "date_received"], rows)

    def load_orders(self, suppliers):
        """Needs the loaded supplier list so each order can point to its Supplier."""
        by_name = {s.name.lower(): s for s in suppliers}
        orders = []
        for n, r in enumerate(self._read(self.orders_file), start=2):
            try:
                supplier = by_name[r["supplier"].strip().lower()]
                received = date.fromisoformat(r["date_received"]) if r["date_received"] else None
                orders.append(PurchaseOrder(
                    int(r["order_id"]), supplier, r["item_name"], int(r["quantity"]),
                    r["status"], date.fromisoformat(r["date_ordered"]), received,
                    check_supplier=False))
            except (ValueError, KeyError) as e:
                self._skip("orders.csv", n, f"{type(e).__name__}: {e}")
        return orders

    # ---------- stock transactions ----------
    def save_transactions(self, transactions):
        rows = [[t.timestamp.isoformat(sep=" "), t.item_name, t.trans_type,
                 t.quantity, t.performed_by, t.note] for t in transactions]
        self._write(self.transactions_file,
                    ["timestamp", "item_name", "type", "quantity", "performed_by", "note"], rows)

    def load_transactions(self):
        transactions = []
        for n, r in enumerate(self._read(self.transactions_file), start=2):
            try:
                transactions.append(StockTransaction(
                    r["item_name"], r["type"], int(r["quantity"]),
                    r["performed_by"], r["note"],
                    datetime.fromisoformat(r["timestamp"])))
            except (ValueError, KeyError) as e:
                self._skip("transactions.csv", n, e)
        return transactions

    # ---------- everything at once ----------
    def save_all(self, items, suppliers, orders, transactions):
        self.save_items(items)
        self.save_suppliers(suppliers)
        self.save_orders(orders)
        self.save_transactions(transactions)

    def load_all(self):
        items = self.load_items()
        suppliers = self.load_suppliers()
        orders = self.load_orders(suppliers)
        transactions = self.load_transactions()
        return items, suppliers, orders, transactions