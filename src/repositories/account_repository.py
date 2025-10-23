from typing import override, TypeVar, Callable
from repositories.base_repository import BaseRepository
from database.database import Database

from models.accounts import User, UserCreate, Merchant, MerchantCreate, Admin, AdminCreate

T_Account = TypeVar("T_Account")

class AccountRepository(BaseRepository):
    def __init__(self, db: Database, table_name: str):
        """Initializes the AccountRepository.

        Args:
            db (Database): The database instance.
            table_name (str): The name of the database table this repository manages.
        """
        self.db = db
        self.table_name = table_name

    def get_by_username(self, username: str, map_func: Callable[[dict], T_Account | None]) -> T_Account | None:
        """
        Fetches a single account record from the database by username.

        Args:
            username (str): The username of the account to fetch.
            map_func (Callable): The function to map the database row to a dataclass.

        Returns:
            The mapped account object if found, otherwise None.
        """
        query = f"SELECT * FROM {self.table_name} WHERE username = %s"
        row = self.db.fetch_one(query, (username,))
        return map_func(row) if row else None
    
    def does_account_exist(self, username: str) -> bool:
        """
        Checks if an account with the given username exists.

        Args:
            username (str): The username to check.
        
        Returns:
            bool: `True` if the account exists, `False` otherwise.
        """
        query = f"SELECT 1 FROM {self.table_name} WHERE username = %s LIMIT 1"
        try:
            row = self.db.fetch_one(query, (username,))
            if row:
                return True
            else:
                return False
        except Exception as e:
            print(f"[AccountRepository ERROR] Failed to find by username: {e}")
            return False


class UserRepository(AccountRepository):
    def __init__(self, db: Database):
        """Initializes the UserRepository.

        Args:
            db (Database): The database instance.
        """
        super().__init__(db, "users")

    @override
    def create(self, data: UserCreate) -> tuple[bool, str]:
        """Creates a new user record in the database.
        Assumes data is pre-validated and password is pre-hashed.

        Args:
            data (UserCreate): The UserCreate object containing the new user's data.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
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
        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        return (new_id is not None, message)

    @override
    def read(self, identifier: int) -> User | None:
        """Reads a user record by ID.

        Args:
            identifier (int): The ID of the user to retrieve.

        Returns:
            User | None: The User object if found, otherwise `None`.
        """
        return self._id_to_dataclass(
            identifier=identifier, table_name=self.table_name, db=self.db, map_func=self._map_to_user, id_field="id"
        )

    @override
    def update(self, identifier: int, data: dict) -> bool:
        """Updates an existing user record.

        Args:
            identifier (int): The ID of the user to update.
            data (dict): A dictionary of fields to update and their new values.

        Returns:
            bool: `True` if the update was successful, `False` otherwise.
        """
        allowed_fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "gender",
            "age",
        ]
        return self._update_by_id(
            identifier=identifier, data=data, table_name=self.table_name, db=self.db, allowed_fields=allowed_fields
        )

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """Deletes a user record by ID.

        Args:
            identifier (int): The ID of the user to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        return self._delete_by_id(identifier, table_name=self.table_name, db=self.db, id_field="id")

    def get_by_username(self, username: str) -> User | None:
        return super().get_by_username(username, self._map_to_user)

    def add_address_by_id(self, user_id: int, address_id: int) -> bool:
        """Adds an address to a user.

        Args:
            user_id (int): The ID of the user.
            address_id (int): The ID of the address to add.

        Returns:
            bool: `True` if the address was added, `False` otherwise.
        """
        query = "INSERT INTO user_addresses (user_id, address_id) VALUES (%s, %s)"
        try:
            self.db.execute_query(query, (user_id, address_id))
            return True
        except Exception as e:
            print(f"[UserRepository ERROR] Failed to add address: {e}")
            return False

    def _map_to_user(self, row: dict) -> User | None:
        """Maps a database row (dictionary) to a User dataclass object.

        Args:
            row (dict): A dictionary representing a row from the 'users' table.

        Returns:
            User | None: A User object if the row is not empty, otherwise `None`.
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


class MerchantRepository(AccountRepository):
    def __init__(self, db: Database):
        """Initializes the MerchantRepository.

        Args:
            db (Database): The database instance.
        """
        super().__init__(db, "merchants")

    @override
    def create(self, data: MerchantCreate) -> tuple[bool, str]:
        """Creates a new merchant record in the database.
        Assumes data is pre-validated and password is pre-hashed.
        
        Args:
            data (MerchantCreate): The Merchant object containing the new merchant's data.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        fields = [
            "username",
            "email",
            "hash",
            "first_name",
            "last_name",
            "phone_number",
            "store_name",
        ]
        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        return (new_id is not None, message)

    @override
    def read(self, identifier: int) -> Merchant | None:
        """Reads a merchant record by ID.

        Args:
            identifier (int): The ID of the merchant to retrieve.

        Returns:
            Merchant | None: The Merchant object if found, otherwise `None`.
        """
        return self._id_to_dataclass(identifier=identifier, table_name=self.table_name, db=self.db, map_func=self._map_to_merchant)

    @override
    def update(self, identifier: int, data: dict) -> bool:
        """Updates an existing merchant record.

        Args:
            identifier (int): The ID of the merchant to update.
            data (dict): A dictionary of fields to update and their new values.

        Returns:
            bool: `True` if the update was successful, `False` otherwise.
        """
        allowed_fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "store_name",
        ]
        return self._update_by_id(
            identifier=identifier, data=data, table_name=self.table_name, db=self.db, allowed_fields=allowed_fields
        )

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """Deletes a merchant record by ID.

        Args:
            identifier (int): The ID of the merchant to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        return self._delete_by_id(identifier, table_name=self.table_name, db=self.db, id_field="id")

    def get_by_username(self, username: str) -> Merchant | None:
        return super().get_by_username(username, self._map_to_merchant)

    def add_address_by_id(self, merchant_id: int, address_id: int) -> bool:
        """Adds an address to a merchant.

        Args:
            merchant_id (int): The ID of the merchant.
            address_id (int): The ID of the address to add.

        Returns:
            bool: `True` if the address was added, `False` otherwise.
        """
        query = "INSERT INTO merchant_addresses (merchant_id, address_id) VALUES (%s, %s)"
        try:
            self.db.execute_query(query, (merchant_id, address_id))
            return True
        except Exception as e:
            print(f"[MerchantRepository ERROR] Failed to add address: {e}")
            return False

    def _map_to_merchant(self, row: dict) -> Merchant | None:
        """Maps a database row (dictionary) to a Merchant dataclass object.

        Args:
            row (dict): A dictionary representing a row from the 'merchants' table.

        Returns:
            Merchant | None: A Merchant object if the row is not empty, otherwise `None`.
        """
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
            created_at=row["created_at"],
        )


class AdminRepository(AccountRepository):
    def __init__(self, db: Database):
        """Initializes the AdminRepository.

        Args:
            db (Database): The database instance.
        """
        super().__init__(db, "admins")

    @override
    def create(self, data: AdminCreate) -> tuple[bool, str]:
        """Creates a new admin record in the database.
        Assumes data is pre-validated and password is pre-hashed.

        Args:
            data (AdminCreate): The Admin object containing the new admin's data.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        fields = [
            "username",
            "hash",
            "role",
        ]
        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        return (new_id is not None, message)

    @override
    def read(self, identifier: int) -> Admin | None:
        """Reads an admin record by ID.

        Args:
            identifier (int): The ID of the admin to retrieve.

        Returns:
            Admin | None: The Admin object if found, otherwise `None`.
        """
        return self._id_to_dataclass(
            identifier=identifier, table_name=self.table_name, db=self.db, map_func=self._map_to_admin, id_field="id"
        )

    @override
    def update(self, identifier: int, data: dict) -> bool:
        """Updates an existing admin record.

        Args:
            identifier (int): The ID of the admin to update.
            data (dict): A dictionary of fields to update and their new values.

        Returns:
            bool: `True` if the update was successful, `False` otherwise.
        """
        allowed_fields = ["role"]
        return self._update_by_id(
            identifier=identifier, data=data, table_name=self.table_name, db=self.db, allowed_fields=allowed_fields
        )

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """Deletes an admin record by ID.

        Args:
            identifier (int): The ID of the admin to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        return self._delete_by_id(identifier, table_name=self.table_name, db=self.db, id_field="id")

    def get_by_username(self, username: str) -> Admin | None:
        return super().get_by_username(username, self._map_to_admin)
    
    def _map_to_admin(self, row: dict) -> Admin | None:
        """Maps a database row (dictionary) to an Admin dataclass object.

        Args:
            row (dict): A dictionary representing a row from the 'admins' table.

        Returns:
            Admin | None: An Admin object if the row is not empty, otherwise `None`.
        """
        if not row:
            return None
        return Admin(**row)
