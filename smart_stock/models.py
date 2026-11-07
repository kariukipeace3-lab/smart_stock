"""Smart Stock - data models."""

from datetime import date, datetime


class InsufficientStockError(Exception):
    """Raised when trying to remove more stock than is available."""


class Item:
    """General blueprint for any product in the inventory."""

    def __init__(self, name, quantity, price, reorder_level, category=""):
        if quantity < 0 or price < 0 or reorder_level < 0:
            raise ValueError("Quantity, price and reorder level cannot be negative.")
        self.name = name
        self._quantity = quantity  # protected: change only via add/remove
        self.price = price
        self.reorder_level = reorder_level
        self.category = category.strip()

    @property
    def quantity(self):
        return self._quantity

    def add_stock(self, amount):
        if amount <= 0:
            raise ValueError("Amount to add must be greater than zero.")
        self._quantity += amount

    def remove_stock(self, amount):
        if amount <= 0:
            raise ValueError("Amount to remove must be greater than zero.")
        if amount > self._quantity:
            raise InsufficientStockError(
                f"Cannot remove {amount} of '{self.name}'. Only {self._quantity} in stock."
            )
        self._quantity -= amount

    def is_low(self):
        return self._quantity <= self.reorder_level

    def stock_value(self):
        return self._quantity * self.price

    def describe(self):
        text = (f"{self.name} | Qty: {self._quantity} | Price: {self.price:.2f} "
                f"| Reorder at: {self.reorder_level}")
        if self.category:
            text += f" | Category: {self.category}"
        return text


class PerishableItem(Item):
    """An item that expires (food, medicine, etc.)."""

    def __init__(self, name, quantity, price, reorder_level, expiry_date, category=""):
        super().__init__(name, quantity, price, reorder_level, category)
        # expiry_date is a string like "2026-12-31"
        self.expiry_date = date.fromisoformat(expiry_date)

    def is_expired(self):
        return self.expiry_date < date.today()

    def days_to_expiry(self):
        return (self.expiry_date - date.today()).days

    def describe(self):
        status = "EXPIRED" if self.is_expired() else f"{self.days_to_expiry()} days left"
        return f"{super().describe()} | Expires: {self.expiry_date} ({status})"


class ElectronicItem(Item):
    """An item that comes with a warranty."""

    def __init__(self, name, quantity, price, reorder_level, warranty_months, category=""):
        super().__init__(name, quantity, price, reorder_level, category)
        if warranty_months < 0:
            raise ValueError("Warranty cannot be negative.")
        self.warranty_months = warranty_months

    def describe(self):
        return f"{super().describe()} | Warranty: {self.warranty_months} months"


class Supplier:
    """A business we buy from, and the items they supply."""

    def __init__(self, name, phone="", email=""):
        # Tidy the name so "  acme  ltd " and "Acme Ltd" count as the same supplier
        self.name = " ".join(name.split()).title()
        if not self.name:
            raise ValueError("Supplier name cannot be empty.")
        self.phone = phone.strip()
        self.email = email.strip().lower()
        self.items_supplied = []  # list of item names

    def add_item(self, item_name):
        item_name = item_name.strip()
        if not item_name:
            raise ValueError("Item name cannot be empty.")
        if not self.supplies(item_name):
            self.items_supplied.append(item_name)

    def remove_item(self, item_name):
        for existing in self.items_supplied:
            if existing.lower() == item_name.strip().lower():
                self.items_supplied.remove(existing)
                return
        raise ValueError(f"{self.name} does not supply '{item_name}'.")

    def supplies(self, item_name):
        return item_name.strip().lower() in (i.lower() for i in self.items_supplied)

    def describe(self):
        items = ", ".join(self.items_supplied) if self.items_supplied else "none yet"
        return f"{self.name} | Phone: {self.phone} | Email: {self.email} | Supplies: {items}"


class StockTransaction:
    """A record of stock coming in (IN) or going out (OUT)."""

    VALID_TYPES = ("IN", "OUT")

    def __init__(self, item_name, trans_type, quantity, performed_by="", note="", timestamp=None):
        trans_type = trans_type.strip().upper()
        if trans_type not in self.VALID_TYPES:
            raise ValueError("Transaction type must be 'IN' or 'OUT'.")
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        self.item_name = item_name
        self.trans_type = trans_type
        self.quantity = quantity
        self.performed_by = performed_by  # username of the employee
        self.note = note
        # timestamp can be passed in later when loading from CSV
        self.timestamp = timestamp or datetime.now().replace(microsecond=0)

    def describe(self):
        sign = "+" if self.trans_type == "IN" else "-"
        text = (f"{self.timestamp} | {self.item_name} | {sign}{self.quantity} "
                f"({self.trans_type}) | by {self.performed_by or 'unknown'}")
        if self.note:
            text += f" | {self.note}"
        return text


class PurchaseOrder:
    """An order placed with a supplier. Receiving it adds stock to the item."""

    PENDING = "Pending"
    RECEIVED = "Received"
    CANCELLED = "Cancelled"

    def __init__(self, order_id, supplier, item_name, quantity,
                 status="Pending", date_ordered=None, date_received=None,
                 check_supplier=True):
        if quantity <= 0:
            raise ValueError("Order quantity must be greater than zero.")
        # Only new orders are checked; old records loaded from file are kept as they were
        if check_supplier and not supplier.supplies(item_name):
            raise ValueError(f"{supplier.name} does not supply '{item_name}'.")
        self.order_id = order_id
        self.supplier = supplier
        self.item_name = item_name
        self.quantity = quantity
        self.status = status
        self.date_ordered = date_ordered or date.today()
        self.date_received = date_received

    def receive(self, item, received_by=""):
        """Mark as received, add the stock, and return a StockTransaction."""
        if self.status != self.PENDING:
            raise ValueError(f"Order {self.order_id} is already {self.status.lower()}.")
        if item.name.lower() != self.item_name.lower():
            raise ValueError(f"Order is for '{self.item_name}', not '{item.name}'.")
        item.add_stock(self.quantity)
        self.status = self.RECEIVED
        self.date_received = date.today()
        return StockTransaction(
            item.name, "IN", self.quantity, received_by,
            note=f"Order {self.order_id} from {self.supplier.name}",
        )

    def cancel(self):
        if self.status != self.PENDING:
            raise ValueError(f"Only pending orders can be cancelled (this one is {self.status.lower()}).")
        self.status = self.CANCELLED

    def describe(self):
        return (f"Order {self.order_id} | {self.item_name} x{self.quantity} | "
                f"{self.supplier.name} | {self.status} | Ordered: {self.date_ordered}")