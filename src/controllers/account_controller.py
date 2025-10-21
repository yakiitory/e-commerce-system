from typing import override
from controllers.base_controller import BaseController
from database.database import Database
import bcrypt

from models.accounts import User, Merchant, Admin


class AccountController(BaseController):
    def __init__(self, db: Database):
        self.db = db

    @override
    def create(self, data) -> tuple:
        return

    @override
    def read(self, identifier):
        return

    @override
    def update(self, identifier, data):
        return

    @override
    def delete(self, identifier):
        return

    def hash_pw(self, password: str):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def does_account_exist(self, query: str, identifier: str, error: str) -> bool:
        try:
            row = self.db.fetch_one(query, (identifier,))
            if row:
                return True
            else:
                return False
        except Exception as e:
            print(f"{error} : {e}")
            return False


class UserController(AccountController):
    def __init__(self, db: Database):
        self.db = db

    @override
    def create(self, data: User) -> tuple:
        """
        Returns a tuple of (bool, str) for status of user creation.
        """
        if self.does_user_exist(data.username) is True:
            return (
                False,
                "Username already exists!",
            )

        hash = self.hash_pw(data.hash)
        query = """
            INSERT INTO users 
            (username, email, hash, first_name, last_name, phone_number, gender, age)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            params = (
                data.username,
                data.email,
                hash,
                data.first_name,
                data.last_name,
                data.phone_number,
                data.gender,
                data.age,
            )
            self.db.execute_query(query, params)
            return (
                True,
                "User has been created!",
            )
        except Exception as e:
            print(f"[UserController ERROR] Create failed: {e}")

    @override
    def read(self, identifier: int):
        query = "SELECT * FROM users WHERE id = %s"
        params = (f"{identifier}",)
        try:
            return self._map_to_user(self.db.fetch_one(query, params))
        except Exception as e:
            print(f"[UserController ERROR] Read by ID failed: {e}")

    @override
    def update(self, identifier: int, data: User):
        return super().update(identifier, data)

    @override
    def delete(self, identifier: int):
        return super().delete(identifier)

    def login(self, username: str, password: str) -> tuple[bool, str | User]:
        # Check if user exists
        if not self.does_user_exist(username):
            return (False, "User does not exist!")

        # Fetch hashed password
        pw_query = "SELECT hash FROM users WHERE username = %s LIMIT 1"
        row = self.db.fetch_one(pw_query, (username,))

        if not row or "hash" not in row:
            return (False, "Error retrieving user data.")

        # Compare passwords (convert both to bytes)
        stored_hash = row["hash"]
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            success_query = "SELECT * FROM users WHERE username = %s"
            row = self.db.fetch_one(success_query, (username,))
            user = self._map_to_user(row)
            return (True, user)
        else:
            return (False, "Incorrect password!")

    def does_user_exist(self, username: str) -> bool:
        query = "SELECT 1 FROM users WHERE username = %s LIMIT 1"
        error = "[UserController ERROR] Failed to find by username"
        return self.does_account_exist(query, username, error)

    def _map_to_user(self, row: dict) -> User | None:
        """
        Map a database row (dict) to a User dataclass.
        Returns None if row is None.
        """
        if not row:
            return None

        return User(
            id=row["id"],
            role=row["role"],
            username=row["username"],
            hash=row["hash"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            phone_number=row["phone_number"],
            email=row["email"],
            gender=row["gender"],
            age=row["age"],
            created_at=row["created_at"],
        )


class MerchantController(AccountController):
    @override
    def create(self, data: Merchant) -> tuple:
        """
        Returns a tuple of (bool, str) for status of creation.
        """
        if self.does_merchant_exist(data.username) is False:
            return (
                False,
                "Merchant already exists!",
            )
        hash = self.hash_pw(data.hash)
        query = """
            INSERT INTO merchants 
            (username, email, hash, first_name, last_name, phone_number, store_name) 
            VALUES
            (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            params = (
                data.username,
                data.email,
                hash,
                data.first_name,
                data.last_name,
                data.phone_number,
                data.store_name,
            )
            self.db.execute_query(query, params)
            return (
                True,
                "Merchant has been created!",
            )
        except Exception as e:
            print(f"[MerchantController ERROR] Create failed: {e}")

    @override
    def read(self, identifier: int):
        query = "SELECT * FROM merchants WHERE id = %s"
        params = (f"{identifier}",)
        try:
            return self.db.fetch_one(query, params)
        except Exception as e:
            print(f"[MerchantController ERROR] Read by ID failed : {e}")

    @override
    def update(self, identifier: int, data: Merchant):
        return super().update(identifier, data)

    @override
    def delete(self, identifier: int):
        return super().delete(identifier)

    def login(self, username: str, password: str) -> tuple[bool, str | Merchant]:
        # Check if user exists
        if not self.does_merchant_exist(username):
            return (False, "Merchant does not exist!")

        # Fetch hashed password
        pw_query = "SELECT hash FROM merchants WHERE username = %s LIMIT 1"
        row = self.db.fetch_one(pw_query, (username,))

        if not row or "hash" not in row:
            return (False, "Error retrieving user data.")

        # Compare passwords (convert both to bytes)
        stored_hash = row["hash"]
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            success_query = "SELECT * FROM merchants WHERE username = %s"
            row = self.db.fetch_one(success_query, (username,))
            merchant = self._map_to_merchant(row)
            return (True, merchant)
        else:
            return (False, "Incorrect password!")

    def does_merchant_exist(self, username: str) -> bool:
        query = "SELECT 1 FROM merchants WHERE username = %s LIMIT 1"
        error = "[MerchantController ERROR] Failed to find by username"
        return self.does_account_exist(query, username, error)

    def _map_to_merchant(self, row: dict) -> Merchant | None:
        if not row:
            return None

        return Merchant(
            id=row["id"],
            role=row["role"],
            username=row["username"],
            hash=row["hash"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            phone_number=row["phone_number"],
            email=row["email"],
            store_name=row["store_name"],
        )


class AdminController(AccountController):
    @override
    def create(self, data: Admin):
        return super().create(data)

    @override
    def read(self, identifier: int):
        return super().read(identifier)

    @override
    def update(self, identifier: int, data: Admin):
        return super().update(identifier, data)

    @override
    def delete(self, identifier: int):
        return super().delete(identifier)
