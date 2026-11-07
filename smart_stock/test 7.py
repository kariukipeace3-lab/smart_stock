import tempfile
from models import Item, PerishableItem, ElectronicItem, Supplier, InsufficientStockError
from file_handler import FileHandler
from manager import InventoryManager, InventoryError

folder = tempfile.mkdtemp()
mgr = InventoryManager(FileHandler(folder))

def attempt(label, func):
    """Run func and show the error message if it fails."""
    try:
        func()
    except (InventoryError, InsufficientStockError, ValueError) as e:
        print(f"Caught [{label}]:", e)

print("--- add items ---")
mgr.add_item(Item("Rice 2kg", 3, 250, 5, "Groceries"), "peace")
mgr.add_item(PerishableItem("Milk 500ml", 15, 65.5, 5, "2030-01-01", "Dairy"), "peace")
mgr.add_item(ElectronicItem("USB Cable", 25, 300, 5, 12, "Electronics"), "peace")
print("Items:", [i.name for i in mgr.items])
attempt("duplicate", lambda: mgr.add_item(Item("rice 2kg", 1, 1, 1)))

print("--- suppliers ---")
mgr.add_supplier(Supplier("Acme Traders Ltd", "0712345678", "sales@acme.co.ke"))
mgr.assign_item_to_supplier("acme traders ltd", "Rice 2kg")
mgr.assign_item_to_supplier("Acme Traders Ltd", "Milk 500ml")
attempt("no supplier", lambda: mgr.assign_item_to_supplier("Nobody", "Rice 2kg"))
attempt("no item", lambda: mgr.assign_item_to_supplier("Acme Traders Ltd", "Ghost"))

print("--- low stock ---")
print("Low:", [i.name for i in mgr.low_stock_items()])

print("--- orders ---")
o = mgr.create_order("Acme Traders Ltd", "Rice 2kg", 50)
print(o.describe())
mgr.receive_order(1, "peace")
print("Rice after receive:", mgr.get_item("Rice 2kg").quantity)
attempt("receive twice", lambda: mgr.receive_order(1, "peace"))
attempt("bad order id", lambda: mgr.receive_order("abc"))
attempt("not supplied", lambda: mgr.create_order("Acme Traders Ltd", "USB Cable", 5))

print("--- issue stock ---")
mgr.issue_stock("Rice 2kg", 50, "john", "Sold to customer")
rice = mgr.get_item("Rice 2kg")
print("Rice:", rice.quantity, "| low?", rice.is_low())
attempt("too much", lambda: mgr.issue_stock("Rice 2kg", 10, "john"))
attempt("zero", lambda: mgr.issue_stock("Rice 2kg", 0, "john"))
mgr.add_stock("Rice 2kg", 7, "peace", "Manual count correction")
print("Rice after manual add:", rice.quantity)

print("--- history ---")
for t in mgr.item_history("Rice 2kg"):
    print(t.describe())

print("--- search ---")
print("name 'rice':", [i.name for i in mgr.search_items("rice")])
print("category 'dairy':", [i.name for i in mgr.search_items("dairy")])
print("supplier 'acme':", [i.name for i in mgr.search_items("acme")])
print("no match:", mgr.search_items("zzz"))

print("--- edit ---")
mgr.edit_item("Rice 2kg", price=275, reorder_level=10)
print(rice.describe())
attempt("negative price", lambda: mgr.edit_item("Rice 2kg", price=-5))

print("--- reports ---")
print("Total value:", mgr.total_stock_value())
print("Supplier summary:", mgr.supplier_summary())

print("--- delete rules ---")
mgr.create_order("Acme Traders Ltd", "Milk 500ml", 20)   # order 2, pending
attempt("delete item w/ pending", lambda: mgr.delete_item("Milk 500ml"))
attempt("delete supplier w/ pending", lambda: mgr.delete_supplier("Acme Traders Ltd"))
mgr.cancel_order(2)
mgr.delete_item("Milk 500ml")
print("Items now:", [i.name for i in mgr.items])
print("Acme supplies:", mgr.get_supplier("Acme Traders Ltd").items_supplied)

print("--- restart ---")
mgr2 = InventoryManager(FileHandler(folder))
print("Items:", len(mgr2.items), "| Suppliers:", len(mgr2.suppliers),
      "| Orders:", len(mgr2.orders), "| Transactions:", len(mgr2.transactions))
print("Rice qty:", mgr2.get_item("Rice 2kg").quantity)
print("Next order id:", mgr2.create_order("Acme Traders Ltd", "Rice 2kg", 5).order_id)