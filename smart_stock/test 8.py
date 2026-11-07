"""Runs main.py with scripted keyboard input so the whole menu can be tested."""
import builtins
import getpass
import tempfile

import main


def play(data_dir, answers):
    answers = iter(answers)

    def fake_input(prompt=""):
        try:
            text = next(answers)
        except StopIteration:
            raise EOFError
        print(f"{prompt}{text}")
        return text

    def fake_getpass(prompt=""):
        try:
            next_text = next(answers)
        except StopIteration:
            raise EOFError
        print(f"{prompt}{'*' * len(next_text)}")
        return next_text

    builtins.input = fake_input
    getpass.getpass = fake_getpass
    main.run(data_dir)


folder = tempfile.mkdtemp()

print("################ SESSION 1: admin ################")
play(folder, [
    "peace", "admin123",              # first-run: create admin
    "peace", "admin123",              # login
    # --- Items ---
    "1",
    "3", "1", "Rice 2kg", "3", "250", "5", "Groceries",
    "3", "2", "Milk 500ml", "abc", "15", "65.5", "5", "Dairy", "bad-date", "2030-01-01",
    "3", "3", "USB Cable", "25", "300", "5", "Electronics", "12",
    "3", "1", "Rice 2kg",             # duplicate name -> error
    "1",                              # view all
    "2", "dairy",                     # search
    "4", "Rice 2kg", "275", "", "",   # edit price only
    "0",
    # --- Suppliers ---
    "2",
    "2", "Acme Traders Ltd", "0712345678", "sales@acme.co.ke",
    "3", "Acme Traders Ltd", "Rice 2kg",
    "3", "Acme Traders Ltd", "Milk 500ml",
    "3", "Acme Traders Ltd", "Ghost",  # unknown item -> error
    "1",
    "0",
    # --- Orders ---
    "3",
    "3", "Acme Traders Ltd", "Rice 2kg", "50",
    "2",                              # pending
    "4", "1",                         # receive order 1
    "4", "1",                         # receive again -> error
    "1",
    "0",
    # --- Stock ---
    "4",
    "1", "Rice 2kg", "50", "Sold to customer",
    "1", "Rice 2kg", "10", "",        # too much -> error
    "2", "Rice 2kg", "7", "Count fix",
    "1", "Rice 2kg", "8", "",         # leaves Rice low (2 left)
    "3", "Rice 2kg",
    "0",
    # --- Reports ---
    "5", "1", "2", "3", "0",
    # --- Users ---
    "6",
    "2", "john", "stock456", "stock456", "staff",
    "2", "amy", "stock456", "different",             # mismatch -> error
    "1",
    "3", "peace",                     # delete self -> error
    "0",
    "0",                              # exit
])

print("\n################ SESSION 2: staff (restart) ################")
play(folder, [
    "john", "stock456",               # login -> low-stock alert shown
    "1",                              # Items menu: no 'Delete' option for staff
    "0",
    "6",                              # no Users menu for staff -> invalid
    "0",
])

print("\n################ SESSION 3: wrong passwords ################")
play(folder, [
    "john", "bad1", "john", "bad2", "john", "bad3",
])