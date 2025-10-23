from typing import override
from controllers.base_controller import BaseController
from database.database import Database
import bcrypt

from models.accounts import User, UserCreate, Merchant, MerchantCreate, Admin, AdminCreate


class AccountController(BaseController):
    def __init__(self, db: Database, table_name: str):
        """Initializes the AccountController.

        Args:
            db (Database): The database instance.
            table_name (str): The name of the database table this controller manages.
        """
        self.db = db
        self.table_name = table_name

    def _create_account(
        self, data, fields: list[str], does_exist_func, password_field: str = "hash"
    ) -> tuple[bool, str]:
        """Generic create method for any account-type table.

        Automatically logs using the caller's class name.

        Args:
            data: An object containing the account data, expected to have attributes
                corresponding to `fields` and `password_field`.
            fields (list[str]): A list of field names to insert into the database.
            does_exist_func (callable): A function to check if an account with the
                given username already exists.
            password_field (str, optional): The attribute name in `data` that holds
                the plain password. Defaults to "hash".

        Returns:
            tuple[bool, str]: A tuple where the first element is `True` if creation
                was successful, `False` otherwise. The second element is a message.
        """
        caller_name = self.__class__.__name__

        # Check if username already exists
        if does_exist_func(data.username):
            return (False, f"{caller_name} username already exists!")

        # Hash password
        plain_password = getattr(data, password_field)
        hashed_pw = self.hash_pw(plain_password)

        # Build dynamic query
        # Create a temporary object to pass to _create_record with the hashed password
        temp_data_dict = {f: getattr(data, f) for f in fields if f != "hash"}
        temp_data_dict["hash"] = hashed_pw # Set the hashed password
        temp_data_object = type('TempData', (object,), temp_data_dict)()

        new_id, message = self._create_record(temp_data_object, fields, self.table_name, self.db)
        # Convert the (id | None, str) from _create_record to (bool, str) for _create_account's return
        return (new_id is not None, message)

    def hash_pw(self, password: str):
        """Hashes a plain-text password using bcrypt.

        Args:
            password (str): The plain-text password to hash.

        Returns:
            bytes: The hashed password.
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def does_account_exist(self, query: str, identifier: str, error: str) -> bool:
        """Checks if an account exists based on a given query and identifier.

        Args:
            query (str): The SQL query to execute for checking existence.
            identifier (str): The value to use in the query (e.g., username).
            error (str): An error message to print if an exception occurs.

        Returns:
            bool: `True` if an account exists, `False` otherwise.
        """
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
        """Initializes the UserController.

        Args:
            db (Database): The database instance.
        """
        super().__init__(db, "users")

    @override
    def create(self, data: UserCreate) -> tuple[bool, str]:
        """Creates a new user account.

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
        return self._create_account(
            data=data,
            fields=fields,
            does_exist_func=self.does_user_exist,
            password_field="hash",
        )

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
    
    def login(self, username: str, password: str) -> tuple[bool, str | User]:
        """Authenticates a user.

        Args:
            username (str): The username of the user.
            password (str): The plain-text password of the user.

        Returns:
            tuple[bool, str | User]: A tuple where the first element is `True` on
                successful login and the second is the User object, or `False` and
                an error message on failure.
        """
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
            user = self._map_to_user(row if row else {})
            return (True, user) if user else (False, "Error mapping user data.")
        else:
            return (False, "Incorrect password!")
        
    def does_user_exist(self, username: str) -> bool:
        """Checks if a user with the given username exists.

        Args:
            username (str): The username to check.

        Returns:
            bool: `True` if the user exists, `False` otherwise.
        """
        query = "SELECT 1 FROM users WHERE username = %s LIMIT 1"
        error = "[UserController ERROR] Failed to find by username"
        return super().does_account_exist(query, username, error)

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


class MerchantController(AccountController):
    def __init__(self, db: Database):
        """Initializes the MerchantController.

        Args:
            db (Database): The database instance.
        """
        super().__init__(db, "merchants")

    @override
    def create(self, data: MerchantCreate) -> tuple[bool, str]:
        """Creates a new merchant account.

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
        return self._create_account(
            data=data,
            fields=fields,
            does_exist_func=self.does_merchant_exist,
            password_field="hash",
        )

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

    def login(self, username: str, password: str) -> tuple[bool, str | Merchant]:
        """Authenticates a merchant.

        Args:
            username (str): The username of the merchant.
            password (str): The plain-text password of the merchant.

        Returns:
            tuple[bool, str | Merchant]: A tuple where the first element is `True` on
                successful login and the second is the Merchant object, or `False` and
                an error message on failure.
        """
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
            merchant = self._map_to_merchant(row if row else {})
            return (True, merchant) if merchant else (False, "Error mapping merchant data.")
        else:
            return (False, "Incorrect password!")

    def does_merchant_exist(self, username: str) -> bool:
        """Checks if a merchant with the given username exists.

        Args:
            username (str): The username to check.

        Returns:
            bool: `True` if the merchant exists, `False` otherwise.
        """
        query = "SELECT 1 FROM merchants WHERE username = %s LIMIT 1"
        error = "[MerchantController ERROR] Failed to find by username"
        return super().does_account_exist(query, username, error)

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


class AdminController(AccountController):
    def __init__(self, db: Database):
        """Initializes the AdminController.

        Args:
            db (Database): The database instance.
        """
        super().__init__(db, "admins")

    @override
    def create(self, data: AdminCreate) -> tuple[bool, str]:
        """Creates a new admin account.

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
        return self._create_account(
            data=data,
            fields=fields,
            does_exist_func=self.does_admin_exist,
            password_field="hash",
        )

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

    def does_admin_exist(self, username: str) -> bool:
        """Checks if an admin with the given username exists.

        Args:
            username (str): The username to check.

        Returns:
            bool: `True` if the admin exists, `False` otherwise.
        """
        query = "SELECT 1 FROM admins WHERE username = %s LIMIT 1"
        error = "[AdminController ERROR] Failed to find by username"
        return super().does_account_exist(query, username, error)

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
