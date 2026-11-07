import os
import tempfile

from auth import AuthManager, AuthError

path = os.path.join(tempfile.mkdtemp(), "users.csv")
auth = AuthManager(path)

auth.register("peace", "admin123", "admin")
auth.register("john", "stock456", "staff")

# Good login
u = auth.login("peace", "admin123")
print("Logged in:", u.username, u.role, "| can delete:", u.can("delete"))

s = auth.login("john", "stock456")
print("Logged in:", s.username, s.role, "| can delete:", s.can("delete"))

# Bad logins
for name, pw in [("peace", "wrong"), ("nobody", "x")]:
    try:
        auth.login(name, pw)
    except AuthError as e:
        print("Rejected:", e)

# Duplicate and short password
for name, pw in [("john", "another1"), ("amy", "123")]:
    try:
        auth.register(name, pw)
    except AuthError as e:
        print("Rejected:", e)

# Persistence: reload from file
auth2 = AuthManager(path)
print("Users after reload:", sorted(auth2.users))
print("Password stored as plain text?", "admin123" in open(path).read())