from __future__ import annotations
from typing import TYPE_CHECKING, Any

from models.addresses import Address, AddressCreate

if TYPE_CHECKING:
    from repositories.address_repository import AddressRepository
    from database.database import Database


class AddressService:
    """
    Handles business logic for managing user addresses.
    """

    def __init__(self, db: Database, address_repo: AddressRepository):
        self.db = db
        self.address_repo = address_repo

    def get_user_addresses(self, user_id: int) -> tuple[bool, list[Address] | str]:
        """
        Retrieves all addresses for a given user.
        """
        try:
            addresses = self.address_repo.get_addresses_for_user(user_id)
            return (True, addresses)
        except Exception as e:
            print(f"[AddressService ERROR] Failed to get addresses for user {user_id}: {e}")
            return (False, "Could not retrieve addresses.")

    def get_merchant_addresses(self, merchant_id: int) -> tuple[bool, list[Address] | str]:
        """
        Retrieves all addresses for a given merchant.
        """
        try:
            addresses = self.address_repo.get_addresses_for_merchant(merchant_id)
            return (True, addresses)
        except Exception as e:
            print(f"[AddressService ERROR] Failed to get addresses for merchant {merchant_id}: {e}")
            return (False, "Could not retrieve merchant addresses.")

    def add_address_for_user(self, user_id: int, address_data: dict[str, Any]) -> tuple[bool, str]:
        """
        Creates a new address and links it to the user in a single transaction.
        """
        try:
            address_create = AddressCreate(**address_data)
        except TypeError as e:
            return (False, f"Invalid address data provided: {e}")

        transaction_committed = False
        try:
            self.db.begin_transaction()
            
            new_address_id, msg = self.address_repo.create(address_create)
            if not new_address_id:
                return (False, f"Failed to create address record: {msg}")

            if not self.address_repo.link_address_to_user(user_id, new_address_id):
                return (False, "Failed to link new address to your account.")

            self.db.commit()
            transaction_committed = True
            return (True, "Address added successfully.")
        except Exception as e:
            print(f"[AddressService ERROR] Transaction failed while adding address for user {user_id}: {e}")
            return (False, "An unexpected error occurred while adding the address.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def add_address_for_merchant(self, merchant_id: int, address_data: dict[str, Any]) -> tuple[bool, str]:
        """
        Creates a new address and links it to the merchant in a single transaction.
        """
        try:
            address_create = AddressCreate(**address_data)
        except TypeError as e:
            return (False, f"Invalid address data provided: {e}")

        transaction_committed = False
        try:
            self.db.begin_transaction()
            
            new_address_id, msg = self.address_repo.create(address_create)
            if not new_address_id:
                return (False, f"Failed to create address record: {msg}")

            if not self.address_repo.link_address_to_merchant(merchant_id, new_address_id):
                return (False, "Failed to link new address to your account.")

            self.db.commit()
            transaction_committed = True
            return (True, "Address added successfully.")
        except Exception as e:
            print(f"[AddressService ERROR] Transaction failed while adding address for merchant {merchant_id}: {e}")
            return (False, "An unexpected error occurred while adding the address.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def update_merchant_address(self, merchant_id: int, address_id: int, address_data: dict[str, Any]) -> tuple[bool, str]:
        """
        Updates a merchant's address after verifying ownership.
        """
        # 1. Verify ownership
        if not self.address_repo.does_merchant_own_address(merchant_id, address_id):
            return (False, "Address not found or you do not have permission to edit it.")

        # 2. Perform update
        try:
            success = self.address_repo.update(address_id, address_data)
            if success:
                return (True, "Address updated successfully.")
            else:
                return (False, "Failed to update address.")
        except Exception as e:
            print(f"[AddressService ERROR] Failed to update address {address_id}: {e}")
            return (False, "An unexpected error occurred while updating the address.")

    def delete_merchant_address(self, merchant_id: int, address_id: int) -> tuple[bool, str]:
        """
        Deletes a merchant's address after verifying ownership.
        """
        # 1. Verify ownership
        if not self.address_repo.does_merchant_own_address(merchant_id, address_id):
            return (False, "Address not found or you do not have permission to delete it.")

        # 2. Perform deletion
        try:
            # The repository method handles unlinking and deleting.
            success, message = self.address_repo.delete(address_id)
            if success:
                return (True, "Address deleted successfully.")
            else:
                return (False, message)
        except Exception as e:
            print(f"[AddressService ERROR] Failed to delete address {address_id}: {e}")
            return (False, "An unexpected error occurred while deleting the address.")

    def update_user_address(self, user_id: int, address_id: int, address_data: dict[str, Any]) -> tuple[bool, str]:
        """
        Updates a user's address after verifying ownership.
        """
        # 1. Verify ownership
        if not self.address_repo.does_user_own_address(user_id, address_id):
            return (False, "Address not found or you do not have permission to edit it.")

        # 2. Perform update
        try:
            success = self.address_repo.update(address_id, address_data)
            if success:
                return (True, "Address updated successfully.")
            else:
                return (False, "Failed to update address.")
        except Exception as e:
            print(f"[AddressService ERROR] Failed to update address {address_id}: {e}")
            return (False, "An unexpected error occurred while updating the address.")

    def delete_user_address(self, user_id: int, address_id: int) -> tuple[bool, str]:
        """
        Deletes a user's address after verifying ownership.
        """
        # 1. Verify ownership
        if not self.address_repo.does_user_own_address(user_id, address_id):
            return (False, "Address not found or you do not have permission to delete it.")

        # 2. Perform deletion
        try:
            # The repository method handles unlinking and deleting.
            success, message = self.address_repo.delete(address_id)
            if success:
                return (True, "Address deleted successfully.")
            else:
                return (False, message)
        except Exception as e:
            print(f"[AddressService ERROR] Failed to delete address {address_id}: {e}")
            return (False, "An unexpected error occurred while deleting the address.")