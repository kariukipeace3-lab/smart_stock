"""Smart Stock - the InventoryManager connects all the classes together."""

from file_handler import FileHandler
from models import PurchaseOrder, StockTransaction


class InventoryError(Exception):
    """Raised for problems like 'item not found' or 'duplicate item'."""


class InventoryManager:
    """The 'brain': holds all the data and carries out the user's requests.

    Every change is saved to the CSV files straight away.
    """

    def __init__(self, file_handler=None):
        self.file_handler = file_handler or FileHandler()
        (self.items, self.suppliers,
         self.orders, self.transactions) = self.file_handler.load_all()

    def save(self):
        self.file_handler.save_all(self.items, self.suppliers,
                                   self.orders, self.transactions)

    # ================= lookups =================
    def find_item(self, name):
        key = name.strip().lower()
        for item in self.items:
            if item.name.lower() == key:
                return item
        return None

    def get_item(self, name):
        item = self.find_item(name)
        if item is None:
            raise InventoryError(f"Item '{name.strip()}' not found.")
        return item

    def get_supplier(self, name):
        key = " ".join(name.split()).lower()
        for s in self.suppliers:
            if s.name.lower() == key:
                return s
        raise InventoryError(f"Supplier '{name.strip()}' not found.")

    def get_order(self, order_id):
        try:
            order_id = int(order_id)
        except (ValueError, TypeError):
            raise InventoryError("Order ID must be a number.")
        for o in self.orders:
            if o.order_id == order_id:
                return o
        raise InventoryError(f"Order {order_id} not found.")

    def _next_order_id(self):
        return max((o.order_id for o in self.orders), default=0) + 1

    def _pending_orders_for(self, item_name=None, supplier=None):
        return [o for o in self.orders
                if o.status == PurchaseOrder.PENDING
                and (item_name is None or o.item_name.lower() == item_name.lower())
                and (supplier is None or o.supplier is supplier)]

    def _record(self, item_name, trans_type, quantity, user, note):
        trans = StockTransaction(item_name, trans_type, quantity, user, note)
        self.transactions.append(trans)
        return trans

    # ================= items =================
    def add_item(self, item, user=""):
        if self.find_item(item.name):
            raise InventoryError(f"Item '{item.name}' already exists.")
        self.items.append(item)
        if item.quantity > 0:
            self._record(item.name, "IN", item.quantity, user, "Opening stock")
        self.save()

    def edit_item(self, name, price=None, reorder_level=None, category=None):
        item = self.get_item(name)
        if price is not None and price < 0:
            raise ValueError("Price cannot be negative.")
        if reorder_level is not None and reorder_level < 0:
            raise ValueError("Reorder level cannot be negative.")
        if price is not None:
            item.price = price
        if reorder_level is not None:
            item.reorder_level = reorder_level
        if category is not None:
            item.category = category.strip()
        self.save()
        return item

    def delete_item(self, name):
        item = self.get_item(name)
        if self._pending_orders_for(item_name=item.name):
            raise InventoryError(
                f"Cannot delete '{item.name}': it has pending purchase orders.")
        self.items.remove(item)
        for s in self.suppliers:
            if s.supplies(item.name):
                s.remove_item(item.name)
        self.save()

    # ================= suppliers =================
    def add_supplier(self, supplier):
        if any(s.name.lower() == supplier.name.lower() for s in self.suppliers):
            raise InventoryError(f"Supplier '{supplier.name}' already exists.")
        self.suppliers.append(supplier)
        self.save()

    def assign_item_to_supplier(self, supplier_name, item_name):
        supplier = self.get_supplier(supplier_name)
        item = self.get_item(item_name)
        supplier.add_item(item.name)
        self.save()

    def delete_supplier(self, name):
        supplier = self.get_supplier(name)
        if self._pending_orders_for(supplier=supplier):
            raise InventoryError(
                f"Cannot delete '{supplier.name}': it has pending purchase orders.")
        self.suppliers.remove(supplier)
        self.save()

    # ================= purchase orders =================
    def create_order(self, supplier_name, item_name, quantity):
        supplier = self.get_supplier(supplier_name)
        item = self.get_item(item_name)
        order = PurchaseOrder(self._next_order_id(), supplier, item.name, quantity)
        self.orders.append(order)
        self.save()
        return order

    def receive_order(self, order_id, user=""):
        """Mark an order received: stock goes up and the movement is recorded."""
        order = self.get_order(order_id)
        item = self.get_item(order.item_name)
        trans = order.receive(item, user)
        self.transactions.append(trans)
        self.save()
        return trans

    def cancel_order(self, order_id):
        order = self.get_order(order_id)
        order.cancel()
        self.save()
        return order

    def list_orders(self, status=None):
        if status is None:
            return list(self.orders)
        return [o for o in self.orders if o.status.lower() == status.lower()]

    # ================= stock movements =================
    def add_stock(self, item_name, quantity, user="", note=""):
        """Manual stock-in (not from an order)."""
        item = self.get_item(item_name)
        item.add_stock(quantity)
        trans = self._record(item.name, "IN", quantity, user, note)
        self.save()
        return trans

    def issue_stock(self, item_name, quantity, user="", note=""):
        """Stock-out. Raises InsufficientStockError if there isn't enough."""
        item = self.get_item(item_name)
        item.remove_stock(quantity)
        trans = self._record(item.name, "OUT", quantity, user, note)
        self.save()
        return trans

    def item_history(self, item_name):
        key = item_name.strip().lower()
        records = [t for t in self.transactions if t.item_name.lower() == key]
        if not records and self.find_item(item_name) is None:
            raise InventoryError(f"Item '{item_name.strip()}' not found.")
        return records

    # ================= search =================
    def search_items(self, query):
        """Match by item name, category, or supplier name."""
        q = query.strip().lower()
        if not q:
            return list(self.items)
        from_supplier = set()
        for s in self.suppliers:
            if q in s.name.lower():
                from_supplier.update(i.lower() for i in s.items_supplied)
        return [it for it in self.items
                if q in it.name.lower()
                or q in it.category.lower()
                or it.name.lower() in from_supplier]

    # ================= reports =================
    def total_stock_value(self):
        return sum(i.stock_value() for i in self.items)

    def low_stock_items(self):
        return [i for i in self.items if i.is_low()]

    def supplier_summary(self):
        summary = []
        for s in self.suppliers:
            mine = [o for o in self.orders if o.supplier is s]
            summary.append({
                "name": s.name,
                "items": len(s.items_supplied),
                "pending": sum(o.status == PurchaseOrder.PENDING for o in mine),
                "received": sum(o.status == PurchaseOrder.RECEIVED for o in mine),
            })
        return summary