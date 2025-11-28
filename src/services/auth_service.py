from __future__ import annotations
from typing import TYPE_CHECKING
import bcrypt

if TYPE_CHECKING:
    from models.accounts import Account, User, UserCreate, Merchant, MerchantCreate, Admin, AdminCreate
    from repositories.account_repository import UserRepository, MerchantRepository, AdminRepository


class AuthService:
    """
    Handles the business logic for account authentication and registration.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        merchant_repo: MerchantRepository,
        admin_repo: AdminRepository,
    ):
        """
        Initializes the AuthService with necessary repositories.

        Args:
            user_repo (UserRepository): Repository for user account data.
            merchant_repo (MerchantRepository): Repository for merchant account data.
            admin_repo (AdminRepository): Repository for admin account data.
        """
        self.user_repo = user_repo
        self.merchant_repo = merchant_repo
        self.admin_repo = admin_repo

    # --- User Specific Methods ---
    def register_user(self, data: UserCreate) -> tuple[bool, str]:
        """
        Registers a new user.

        Args:
            data (UserCreate): The user data to register.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        if self.user_repo.does_account_exist(data.username):
            return (False, "User username already exists!")
        hashed_pw = bcrypt.hashpw(data.hash.encode(), bcrypt.gensalt())
        data.hash = hashed_pw.decode('utf-8')
        return self.user_repo.create(data)

    def register(self, form_data: dict) -> tuple[bool, str]:
        """
        Registers a new account, dispatching to the correct type (user or merchant).

        This method expects a dictionary of form data that includes an 'account_type'
        field to determine whether to register a user or a merchant.

        Args:
            form_data (dict): A dictionary containing all necessary fields for registration.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        account_type = form_data.get('account_type')
        password = form_data.get('password', '')
        confirm_password = form_data.get('confirm_password', '')

        # --- Common Validations ---
        if not all([form_data.get('username'), password]):
            return (False, "Username and password are required.")
        if password != confirm_password:
            return (False, "Passwords do not match.")
        if len(password) < 6:
            return (False, "Password must be at least 6 characters long.")

        try:
            if account_type == 'user':
                user_create = UserCreate(
                    username=form_data['username'],
                    email=form_data['email'],
                    hash=password,
                    first_name=form_data['first_name'],
                    last_name=form_data['last_name'],
                    phone_number=form_data.get('phone_number', ''),
                    gender=form_data.get('gender', ''),
                    age=int(form_data['age']) if form_data.get('age') else 0,
                )
                return self.register_user(user_create)
            elif account_type == 'merchant':
                merchant_create = MerchantCreate(
                    first_name=form_data['first_name'],
                    last_name=form_data['last_name'],
                    username=form_data['username'],
                    email=form_data['email'],
                    phone_number=form_data['phone_number'],
                    hash=password,
                    store_name=form_data['store_name'],
                )
                return self.register_merchant(merchant_create)
            else:
                return (False, "Invalid account type specified.")
        except (KeyError, ValueError) as e:
            return (False, f"Missing or invalid required field: {e}")

    def login(self, username: str, password: str) -> tuple[bool, Account | None]:
        """
        Logs in any type of account (User, Merchant, or Admin) by checking each
        repository sequentially.

        Args:
            username (str): The account's username.
            password (str): The account's password.

        Returns:
            tuple[bool, Account | None]: A tuple where the first element is `True` on
                successful login and the second is the specific account object
                (User, Merchant, or Admin), or `False` and `None` on failure.
        """
        # Sequentially check each repository for the username
        account: Account | None = self.user_repo.get_by_username(username)
        if not account:
            account = self.merchant_repo.get_by_username(username)
        if not account:
            account = self.admin_repo.get_by_username(username)

        # If no account was found in any repository
        if not account:
            return (False, None)

        # Check password
        stored_hash = account.hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return (True, account)  # On success, return the full account object
        else:
            return (False, None)

    def change_password(self, username: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """
        Changes the password for any account type after verifying the old password.

        Args:
            username (str): The username of the account.
            old_password (str): The current password to verify.
            new_password (str): The new password to set.

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        # 1. Find the account across all repositories
        account: Account | None = self.user_repo.get_by_username(username)
        repo = self.user_repo
        if not account:
            account = self.merchant_repo.get_by_username(username)
            repo = self.merchant_repo
        if not account:
            account = self.admin_repo.get_by_username(username)
            repo = self.admin_repo

        if not account:
            return (False, "Account not found.")

        # 2. Verify the old password
        stored_hash = account.hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")

        if not bcrypt.checkpw(old_password.encode("utf-8"), stored_hash):
            return (False, "Incorrect current password.")

        # 3. Validate the new password
        if len(new_password) < 6:
            return (False, "New password must be at least 6 characters long.")
        if new_password == old_password:
            return (False, "New password cannot be the same as the old password.")

        # 4. Hash the new password
        new_hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode('utf-8')

        # 5. Update the hash in the database using the correct repository
        update_success = repo.update_hash(account.id, new_hashed_pw)

        if update_success:
            return (True, "Password changed successfully.")
        else:
            # This would indicate a database issue.
            return (False, "Failed to update password. Please try again later.")

    def login_user(self, username: str, password: str) -> tuple[bool, User | None]:
        """
        Logs in a user.

        Args:
            username (str): The user's username.
            password (str): The user's password.

        Returns:
            tuple[bool, User | None]: A tuple where the first element is `True` on
                successful login and the second is the User object, or `False` and `None`
                on failure.
        """
        user = self.user_repo.get_by_username(username)

        # Check existence and password
        if not user:
            return (False, None)
        stored_hash = user.hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            # On success, return the full user object
            return (True, user)
        else:
            return (False, None)

    # --- Merchant Specific Methods ---
    def register_merchant(self, data: MerchantCreate) -> tuple[bool, str]:
        """
        Registers a new merchant.

        Args:
            data (MerchantCreate): The merchant data to register.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        # Check if username already exists
        if self.merchant_repo.does_account_exist(data.username):
            return (False, "Merchant username already exists!")

        # Hash the password
        hashed_pw = bcrypt.hashpw(data.hash.encode(), bcrypt.gensalt())
        data.hash = hashed_pw.decode('utf-8')

        return self.merchant_repo.create(data)

    def login_merchant(self, username: str, password: str) -> tuple[bool, Merchant | None]:
        """
        Logs in a merchant.

        Args:
            username (str): The merchant's username.
            password (str): The merchant's password.

        Returns:
            tuple[bool, Merchant | None]: A tuple where the first element is `True` on
                successful login and the second is the Merchant object, or `False` and `None`
                on failure.
        """
        merchant = self.merchant_repo.get_by_username(username)

        # Business Logic: Check existence and password
        if not merchant:
            return (False, None)

        stored_hash = merchant.hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            # On success, return the full merchant object
            return (True, merchant)
        else:
            return (False, None)

    # --- Admin Specific Methods ---
    def register_admin(self, data: AdminCreate) -> tuple[bool, str]:
        """
        Registers a new admin.

        Args:
            data (AdminCreate): The admin data to register.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        
        # Business Logic: Check if username already exists
        if self.admin_repo.does_account_exist(data.username):
            return (False, "Admin username already exists!")

        # Business Logic: Hash the passwords
        hashed_pw = bcrypt.hashpw(data.hash.encode(), bcrypt.gensalt())
        data.hash = hashed_pw.decode('utf-8')

        return self.admin_repo.create(data)

    def login_admin(self, username: str, password: str) -> tuple[bool, Admin | None]:
        """
        Logs in an admin.

        Args:
            username (str): The admin's username.
            password (str): The admin's password.

        Returns:
            tuple[bool, Admin | None]: A tuple where the first element is `True` on
                successful login and the second is the Admin object, or `False` and `None`
                on failure.
        """
        admin = self.admin_repo.get_by_username(username)

        # Business Logic: Check existence and password
        if not admin:
            return (False, None)

        stored_hash = admin.hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return (True, admin)
        else:
            return (False, None)
