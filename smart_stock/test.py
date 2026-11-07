from models import Item, PerishableItem, ElectronicItem, InsufficientStockError

items = [
    Item("Notebook", 40, 120, 10),
    PerishableItem("Milk 500ml", 15, 65, 5, "2030-01-01"),
    PerishableItem("Old Yoghurt", 8, 50, 3, "2020-01-01"),
    ElectronicItem("USB Cable", 25, 300, 5, 12),
]

# Polymorphism: same call, different output per type
for it in items:
    print(it.describe())

# Subclasses still inherit stock rules
phone_charger = ElectronicItem("Charger", 2, 900, 3, 6)
print("Low stock?", phone_charger.is_low())
try:
    phone_charger.remove_stock(5)
except InsufficientStockError as e:
    print("Caught:", e)

print("isinstance checks:", isinstance(items[1], Item), isinstance(items[3], PerishableItem))