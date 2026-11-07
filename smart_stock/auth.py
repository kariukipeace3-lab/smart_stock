"""Smart Stock - employee login and user management."""

import csv
import getpass
import hashlib
import os
import secrets


class AuthError(Exception):
    """Raised for login or user-management problems."""


def hash_password(password, salt_hex):
    """Return a PBKDF2 hash of the password as a hex string."""
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), 200_000
    ).hex()


class User:
    """A system user. Subclasses decide what each role is allowed to do."""

    role = "user"
    permissions = set()

    def __init__(self, username, password_hash, salt):
        self.username = username
        self.password_hash = password_hash
        self.salt = salt

    def check_password(self, password):
        attempt = hash_password(password, self.salt)
        return secrets.compare_digest(attempt, self.password_hash)

    def can(self, action):
        return action in self.permissions


class AdminUser(User):
    role = "admin"
    permissions = {"view", "add", "edit", "delete", "receive", "issue",
                   "reports", "manage_users"}


class StaffUser(User):
    role = "staff"
    permissions = {"view", "add", "edit", "receive", "issue", "reports"}


ROLES = {"admin": AdminUser, "staff": StaffUser}


class AuthManager:
    """Stores users in a CSV file and handles registration and login."""

    MAX_ATTEMPTS = 3

    def __init__(self, filepath="data/users.csv"):
        self.filepath = filepath
        self.users = {}
        self.load()

    # ---------- storage ----------
    def load(self):
        self.users = {}
        if not os.path.exists(self.filepath):
            return
        with open(self.filepath, newline="") as f:
            for row in csv.DictReader(f):
                cls = ROLES[row["role"]]
                self.users[row["username"]] = cls(
                    row["username"], row["password_hash"], row["salt"]
                )

    def save(self):
        folder = os.path.dirname(self.filepath)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(self.filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password_hash", "salt", "role"])
            for u in self.users.values():
                writer.writerow([u.username, u.password_hash, u.salt, u.role])

    # ---------- users ----------
    def register(self, username, password, role="staff"):
        username = username.strip().lower()
        if not username:
            raise AuthError("Username cannot be empty.")
        if username in self.users:
            raise AuthError(f"User '{username}' already exists.")
        if len(password) < 6:
            raise AuthError("Password must be at least 6 characters.")
        if role not in ROLES:
            raise AuthError("Role must be 'admin' or 'staff'.")
        salt = secrets.token_hex(16)
        user = ROLES[role](username, hash_password(password, salt), salt)
        self.users[username] = user
        self.save()
        return user

    def delete_user(self, username):
        if username not in self.users:
            raise AuthError(f"User '{username}' not found.")
        del self.users[username]
        self.save()

    def login(self, username, password):
        user = self.users.get(username.strip().lower())
        # Same message for wrong username or wrong password
        if user is None or not user.check_password(password):
            raise AuthError("Invalid username or password.")
        return user

    # ---------- console flow ----------
    def first_run_setup(self):
        """If no users exist yet, force creation of the first admin."""
        if self.users:
            return
        print("First run: create the admin account.")
        while True:
            username = input("Admin username: ")
            password = getpass.getpass("Admin password: ")
            try:
                self.register(username, password, "admin")
                print("Admin created.\n")
                return
            except AuthError as e:
                print(e)

    def login_prompt(self):
        """Ask for credentials up to MAX_ATTEMPTS times. Returns User or None."""
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            try:
                user = self.login(username, password)
                print(f"\nWelcome, {user.username} ({user.role}).\n")
                return user
            except AuthError as e:
                left = self.MAX_ATTEMPTS - attempt
                print(f"{e} ({left} attempt(s) left)")
        print("Too many failed attempts. Exiting.")
        return None