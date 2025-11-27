from __future__ import annotations
from typing import TYPE_CHECKING
import bcrypt

if TYPE_CHECKING:
    from models.accounts import User, UserCreate, Merchant, MerchantCreate, Admin, AdminCreate
    from repositories.account_repository import UserRepository, MerchantRepository, AdminRepository


class AuthService:
    """
    Handles the business logic for account authentication and registration.
    """

    # --- User Specific Methods ---
    def register_user(self, user_repo: UserRepository, data: UserCreate) -> tuple[int, str]:
        """
        Registers a new user.

        Args:
            user_repo (UserRepository): The user repository instance.
            data (UserCreate): The user data to register.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        if user_repo.does_account_exist(data.username):
            return (False, "User username already exists!")
        hashed_pw = bcrypt.hashpw(data.hash.encode(), bcrypt.gensalt())
        data.hash = hashed_pw.decode('utf-8')
        return user_repo.create(data)

    def login_user(self, user_repo: UserRepository, username: str, password: str) -> tuple[bool, str | User | None]:
        """
        Logs in a user.

        Args:
            user_repo (UserRepository): The user repository instance.
            username (str): The user's username.
            password (str): The user's password.

        Returns:
            tuple[bool, str | User | None]: A tuple where the first element is `True` on
                successful login and the second is the User object, or `False` and
                an error message on failure.
        """
        user = user_repo.get_by_username(username)

        # Check existence and password
        if not user:
            return (False, "User does not exist!")
        stored_hash = user.hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            # On success, return the full user object
            return (True, user)
        else:
            return (False, "Incorrect password!")

    # --- Merchant Specific Methods ---
    def register_merchant(self, merchant_repo: MerchantRepository, data: MerchantCreate) -> tuple[int, str]:
        """
        Registers a new merchant.

        Args:
            merchant_repo (MerchantRepository): The merchant repository instance.
            data (MerchantCreate): The merchant data to register.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        # Check if username already exists
        if merchant_repo.does_account_exist(data.username):
            return (False, "Merchant username already exists!")

        # Hash the password
        hashed_pw = bcrypt.hashpw(data.hash.encode(), bcrypt.gensalt())
        data.hash = hashed_pw.decode('utf-8')

        return merchant_repo.create(data)

    def login_merchant(self, merchant_repo: MerchantRepository, username: str, password: str) -> tuple[bool, str | Merchant | None]:
        """
        Logs in a merchant.

        Args:
            merchant_repo (MerchantRepository): The merchant repository instance.
            username (str): The merchant's username.
            password (str): The merchant's password.

        Returns:
            tuple[bool, str | Merchant | None]: A tuple where the first element is `True` on
                successful login and the second is the Merchant object, or `False` and
                an error message on failure.
        """
        merchant = merchant_repo.get_by_username(username)

        # Business Logic: Check existence and password
        if not merchant:
            return (False, "Merchant does not exist!")

        stored_hash = merchant.hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            # On success, return the full merchant object
            return (True, merchant)
        else:
            return (False, "Incorrect password!")

    # --- Admin Specific Methods ---
    def register_admin(self, admin_repo: AdminRepository, data: AdminCreate) -> tuple[int, str]:
        """
        Registers a new admin.

        Args:
            admin_repo (AdminRepository): The admin repository instance.
            data (AdminCreate): The admin data to register.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        
        # Business Logic: Check if username already exists
        if admin_repo.does_account_exist(data.username):
            return (False, "Admin username already exists!")

        # Business Logic: Hash the passwords
        hashed_pw = bcrypt.hashpw(data.hash.encode(), bcrypt.gensalt())
        data.hash = hashed_pw.decode('utf-8')

        return admin_repo.create(data)

    def login_admin(self, admin_repo: AdminRepository, username: str, password: str) -> tuple[bool, str | Admin | None]:
        """
        Logs in an admin.

        Args:
            admin_repo (AdminRepository): The admin repository instance.
            username (str): The admin's username.
            password (str): The admin's password.

        Returns:
            tuple[bool, str | Admin | None]: A tuple where the first element is `True` on
                successful login and the second is the Admin object, or `False` and
                an error message on failure.
        """
        admin = admin_repo.get_by_username(username)

        # Business Logic: Check existence and password
        if not admin:
            return (False, "Admin does not exist!")

        stored_hash = admin.hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return (True, admin)
        else:
            return (False, "Incorrect password!")
