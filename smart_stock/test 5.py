from models import Item, Supplier, PurchaseOrder

rice = Item("Rice 2kg", quantity=3, price=250, reorder_level=5)
acme = Supplier("Acme Traders Ltd", "0712345678", "sales@acme.co.ke")
acme.add_item("Rice 2kg")

order = PurchaseOrder(1, acme, "Rice 2kg", 50)
print(order.describe())
print("Stock before:", rice.quantity)

trans = order.receive(rice, "peace")
print("Stock after:", rice.quantity)
print(order.describe())
print(trans.describe())

# Receiving twice must fail
try:
    order.receive(rice, "peace")
except ValueError as e:
    print("Caught:", e)

# Cancel a pending order
o2 = PurchaseOrder(2, acme, "Rice 2kg", 10)
o2.cancel()
print(o2.describe())

# Bad orders
for args in [(3, acme, "Milk", 5), (4, acme, "Rice 2kg", 0)]:
    try:
        PurchaseOrder(*args)
    except ValueError as e:
        print("Caught:", e)

# Wrong item
sugar = Item("Sugar 1kg", 5, 180, 5)
o3 = PurchaseOrder(5, acme, "Rice 2kg", 5)
try:
    o3.receive(sugar)
except ValueError as e:
    print("Caught:", e)