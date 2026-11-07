from models import Supplier

s = Supplier("  acme   traders ltd ", "0712345678", "Sales@Acme.co.ke")
print(s.describe())

s.add_item("Rice 2kg")
s.add_item("Sugar 1kg")
s.add_item("rice 2kg")  # duplicate, ignored
print("Items:", s.items_supplied)
print("Supplies sugar 1kg?", s.supplies("SUGAR 1KG"))
print("Supplies milk?", s.supplies("Milk"))

s.remove_item("Sugar 1kg")
print("After removal:", s.items_supplied)

try:
    s.remove_item("Milk")
except ValueError as e:
    print("Caught:", e)

try:
    Supplier("   ")
except ValueError as e:
    print("Caught:", e)