from typing import override
from controllers.base_controller import BaseController
from database.database import Database
import bcrypt

from models.accounts import User, Merchant, Admin


class AccountController(BaseController):
    def __init__(self, db: Database, table_name: str):
        self.db = db
        self.table_name = table_name

    @override
    def create(
        self, table_name: str, data, fields: list[str], does_exist_func
    ) -> tuple[bool, str]:
        """
        Generic create method for any account-type table.
        Automatically logs using the caller's class name.
        """
        caller_name = self.__class__.__name__

        # Check if username already exists
        if does_exist_func(data.username):
            return (False, f"{caller_name} username already exists!")

        # Hash password
        hashed_pw = self.hash_pw(data.hash)

        # Build dynamic query
        placeholders = ", ".join(["%s"] * len(fields))
        columns = ", ".join(fields)
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        params = [getattr(data, f) if f != "hash" else hashed_pw for f in fields]

        try:
            self.db.execute_query(query, tuple(params))
            print(f"[{caller_name}] {table_name} record created successfully.")
            return (True, f"{caller_name} has been created!")
        except Exception as e:
            print(f"[{caller_name} ERROR] Create failed: {e}")
            return (False, f"Failed to create {caller_name.lower()} record.")

    @override
    def read(self, table_name: str, identifier: int, map_func, id_field: str = "id"):
        """
        Generic read method for any table.
        Automatically logs using the caller's class name.
        """
        caller_name = self.__class__.__name__
        query = f"SELECT * FROM {table_name} WHERE {id_field} = %s"
        params = (identifier,)

        try:
            result = self.db.fetch_one(query, params)
            if result:
                return map_func(result)
            else:
                print(f"[{caller_name}] No record found with {id_field} = {identifier}")
                return None
        except Exception as e:
            print(f"[{caller_name} ERROR] Read failed: {e}")
            return None

    @override
    def update(
        self, table_name: str, identifier: int, data: dict, allowed_fields: list[str]
    ) -> bool:
        """
        Generic update method for any account-type table.
        Dynamically logs the name of the calling controller.
        """
        caller_name = self.__class__.__name__

        # Filter only valid fields
        fields_to_update = {k: v for k, v in data.items() if k in allowed_fields}
        if not fields_to_update:
            print(f"[{caller_name}] No valid fields provided for update.")
            return False

        # Build SQL dynamically
        set_clause = ", ".join(f"{key} = %s" for key in fields_to_update.keys())
        values = list(fields_to_update.values())
        values.append(identifier)

        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"

        try:
            self.db.execute(query, tuple(values))
            print(f"[{caller_name}] {table_name} ID {identifier} updated successfully.")
            return True
        except Exception as e:
            print(f"[{caller_name} ERROR] Failed to update {table_name}: {e}")
            return False

    @override
    def delete(
        self, table_name: str, identifier: int, id_field: str = "id"
    ) -> tuple[bool, str]:
        """
        Generic delete method for any table.
        Automatically logs using the caller's class name.
        """
        caller_name = self.__class__.__name__
        query = f"DELETE FROM {table_name} WHERE {id_field} = %s"
        params = (identifier,)

        try:
            self.db.execute_query(query, params)
            print(f"[{caller_name}] Record deleted from {table_name} (ID={identifier})")
            return (True, f"{caller_name} record deleted successfully.")
        except Exception as e:
            print(f"[{caller_name} ERROR] Delete failed: {e}")
            return (False, f"Failed to delete {caller_name.lower()} record.")

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
        super().__init__(db, "users")

    def create(self, data: User) -> tuple[bool, str]:
        fields = [
            "username",
            "email",
            "hash",
            "first_name",
            "last_name",
            "phone_number",
            "gender",
            "age",
        ]
        return super().create(
            table_name=self.table_name,
            data=data,
            fields=fields,
            does_exist_func=self.does_user_exist,
        )

    def read(self, identifier: int):
        return super().read(
            table_name=self.table_name,
            identifier=identifier,
            map_func=self._map_to_user,
            id_field="id",
        )

    def update(self, identifier: int, data: dict) -> bool:
        allowed_fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "gender",
            "age",
        ]
        return super().update(
            table_name=self.table_name,
            identifier=identifier,
            data=data,
            allowed_fields=allowed_fields,
        )

    def delete(self, identifier: int):
        return super().delete(self.table_name, identifier, id_field="id")

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
        return super().does_account_exist(query, username, error)

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
    def __init__(self, db: Database):
        super().__init__(db, "merchants")

    def create(self, data: Merchant) -> tuple[bool, str]:
        fields = [
            "username",
            "email",
            "hash",
            "first_name",
            "last_name",
            "phone_number",
            "store_name",
        ]
        return super().create(
            table_name=self.table_name,
            data=data,
            fields=fields,
            does_exist_func=self.does_merchant_exist,
        )

    @override
    def read(self, identifier: int):
        query = "SELECT * FROM merchants WHERE id = %s"
        params = (f"{identifier}",)
        try:
            return self.db.fetch_one(query, params)
        except Exception as e:
            print(f"[MerchantController ERROR] Read by ID failed : {e}")

    def update(self, identifier: int, data: dict) -> bool:
        allowed_fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "store_name",
        ]
        return self.account_controller.update(
            table_name=self.table_name,
            identifier=identifier,
            data=data,
            allowed_fields=allowed_fields,
        )

    def delete(self, identifier: int):
        return super().delete(self.table_name, identifier, id_field="id")

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
        return super().does_account_exist(query, username, error)

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
