[README.md](https://github.com/user-attachments/files/34525617/README.md)
# Smart Stock: A Simple Inventory and Ordering System

**Name:** Kariuki Peace | **Adm No:** 251351dit | **Language:** Python 3 (standard library only)

## What it does

Smart Stock is a menu-driven console program that helps a small shop keep accurate stock records. It warns the user when an item is running low, records every stock movement with who did it and when, and saves everything in CSV files so nothing is lost when the program closes.

## How to run

1. Install Python 3.8 or newer. No extra packages are needed.
2. Put all the `.py` files in one folder.
3. Run `python main.py` (or press Run in VS Code with `main.py` open).
4. On the first run you are asked to create the admin account. After that, log in with your username and password.

A `data/` folder is created automatically next to the code. Delete it to start with a clean system.

## Features

- Log in with a username and password (3 attempts). Passwords are stored as salted hashes, never as plain text.
- Two roles: **admin** (everything, including deleting and managing users) and **staff** (everything except deleting and managing users). Options a user is not allowed to use are hidden from their menu.
- Add, view, edit, delete and search items (search by name, category or supplier).
- Three kinds of item: general, perishable (expiry date) and electronic (warranty).
- Add and manage suppliers, and link each supplier to the items they supply.
- Create purchase orders and mark them as received, which updates stock automatically. Orders can also be cancelled.
- Issue stock, blocked with a clear message when there isn't enough.
- Add stock manually, for example after a stock count.
- Low-stock alert at login and right after any stock-out that reaches the reorder level.
- Stock history for any item, showing quantity, user and time.
- Reports: total stock value, low-stock list and supplier summary.
- Bad input never crashes the program: it shows a message and asks again.

## The classes

| Class | File | Job |
|---|---|---|
| `Item` | models.py | Blueprint for any product: name, quantity, price, reorder level, category |
| `PerishableItem` | models.py | An item with an expiry date |
| `ElectronicItem` | models.py | An item with a warranty period |
| `Supplier` | models.py | Who we buy from and what they supply |
| `PurchaseOrder` | models.py | What was ordered and whether it has arrived |
| `StockTransaction` | models.py | A record of stock going in or out |
| `InsufficientStockError` | models.py | Raised when removing more stock than exists |
| `InventoryManager` | manager.py | The "brain": connects everything and carries out requests |
| `InventoryError` | manager.py | Raised for rule problems such as duplicates or items not found |
| `FileHandler` | file_handler.py | Reads and writes the CSV files |
| `User`, `AdminUser`, `StaffUser` | auth.py | Employees and what each role may do |
| `AuthManager` | auth.py | Registration, login and the users file |
| `SmartStockApp` | main.py | The console menus |

## OOP concepts shown

- **Encapsulation:** an item's quantity is stored as `_quantity` and can only change through `add_stock()` and `remove_stock()`, which check every change. A user's password is stored only as a hash.
- **Inheritance:** `PerishableItem` and `ElectronicItem` extend `Item`; `AdminUser` and `StaffUser` extend `User`. Subclasses reuse the parent's code through `super()`.
- **Polymorphism:** `describe()` is overridden in each item type, so the same call prints different details. Each user role has its own set of permissions behind the same `can()` method.
- **Composition:** `InventoryManager` holds items, suppliers, orders and transactions; a `PurchaseOrder` holds its `Supplier`.
- **Abstraction:** the menu only talks to `InventoryManager`, and the manager only talks to `FileHandler`. Neither needs to know how the CSV files are laid out.
- **Exception handling:** custom errors for stock, inventory and login problems are caught in the menu and shown as plain messages.

## Data files (in `data/`)

| File | Holds |
|---|---|
| `items.csv` | Items, with their type and extra detail |
| `suppliers.csv` | Suppliers and the items they supply |
| `orders.csv` | Purchase orders and their status |
| `transactions.csv` | Every stock-in and stock-out |
| `users.csv` | Usernames, password hashes and roles |

## Testing

Each build step has a test script (`test_step1.py` to `test_step8.py`, plus `test_auth.py`). Run any of them to check that part on its own. `test_step8.py` plays a full admin session, a staff session and a failed login using scripted keyboard input, and it uses a temporary folder so it never touches real data.

## Possible future improvements

- A graphical interface instead of the console.
- A database such as SQLite instead of CSV files.
- Renaming items, and expiry-date alerts for perishable stock.
- Printable or exported reports.
