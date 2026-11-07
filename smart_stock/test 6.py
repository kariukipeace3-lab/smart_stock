import os
import tempfile
from models import (Item, PerishableItem, ElectronicItem,
                    Supplier, PurchaseOrder)
from file_handler import FileHandler

folder = tempfile.mkdtemp()
fh = FileHandler(folder)

# Nothing saved yet: should load empty lists, not crash
print("Empty load:", fh.load_all())

# Build some data
rice = Item("Rice 2kg", 3, 250, 5, "Groceries")
milk = PerishableItem("Milk 500ml", 15, 65.5, 5, "2030-01-01", "Dairy")
cable = ElectronicItem("USB Cable", 25, 300, 5, 12, "Electronics")
acme = Supplier("Acme Traders Ltd", "0712345678", "sales@acme.co.ke")
acme.add_item("Rice 2kg")
acme.add_item("Milk 500ml")

o1 = PurchaseOrder(1, acme, "Rice 2kg", 50)
t1 = o1.receive(rice, "peace")          # rice now 53, order Received
o2 = PurchaseOrder(2, acme, "Milk 500ml", 20)   # stays Pending

fh.save_all([rice, milk, cable], [acme], [o1, o2], [t1])
print("Files:", sorted(os.listdir(folder)))

# "Restart": load everything back
items, suppliers, orders, trans = FileHandler(folder).load_all()
for it in items:
    print(type(it).__name__, "->", it.describe())
print(suppliers[0].describe())
for o in orders:
    print(o.describe(), "| received:", o.date_received)
print(trans[0].describe())

# Loaded orders point to the loaded Supplier object
print("Order supplier is loaded supplier:", orders[0].supplier is suppliers[0])

# Corrupted row should be skipped with a warning, not crash
with open(fh.items_file, "a") as f:
    f.write("general,Broken Item,abc,10,5,,\n")
print("Items after corrupt row:", len(FileHandler(folder).load_items()))