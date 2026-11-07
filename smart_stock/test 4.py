from datetime import datetime
from models import StockTransaction

t1 = StockTransaction("Rice 2kg", "in", 30, "peace", "Received from Acme")
t2 = StockTransaction("Rice 2kg", "OUT", 5, "john")
print(t1.describe())
print(t2.describe())

# Loading an old record keeps its original time
old = StockTransaction("Sugar 1kg", "IN", 10, "peace", timestamp=datetime(2026, 10, 1, 9, 30))
print(old.describe())

for args in [("Rice", "MOVE", 5), ("Rice", "IN", 0), ("Rice", "OUT", -3)]:
    try:
        StockTransaction(*args)
    except ValueError as e:
        print("Caught:", e)