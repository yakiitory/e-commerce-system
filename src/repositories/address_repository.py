from __future__ import annotations
from typing import override, Any, TYPE_CHECKING

from repositories.base_repository import BaseRepository
from models.addresses import Address, AddressCreate

if TYPE_CHECKING:
    from database.database import Database


class AddressRepository(BaseRepository):
    """
    Handles database operations for addresses and their links to users/merchants.
    """

    def __init__(self, db: Database):
        self.db = db
        self.table_name = "addresses"

    @override
    def create(self, data: AddressCreate) -> tuple[int | None, str]:
        fields = ["house_no", "street", "city", "postal_code", "additional_notes"]
        return self._create_record(data, fields, self.table_name, self.db)

    @override
    def read(self, identifier: int) -> Address | None:
        return self._id_to_dataclass(
            identifier, self.table_name, self.db, lambda row: Address(**row) if row else None
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        allowed_fields = ["house_no", "street", "city", "postal_code", "additional_notes"]
        return self._update_by_id(identifier, data, self.table_name, self.db, allowed_fields)

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        # First, unlink from all users
        unlink_user_query = "DELETE FROM user_addresses WHERE address_id = %s"
        self.db.execute_query(unlink_user_query, (identifier,))

        # Then, unlink from all merchants
        unlink_merchant_query = "DELETE FROM merchant_addresses WHERE address_id = %s"
        self.db.execute_query(unlink_merchant_query, (identifier,))
        
        # Then, delete the address itself
        return self._delete_by_id(identifier, self.table_name, self.db) # type: ignore

    def get_addresses_for_user(self, user_id: int) -> list[Address]:
        """
        Retrieves all addresses linked to a specific user.
        """
        query = """
            SELECT a.* FROM addresses a
            JOIN user_addresses ua ON a.id = ua.address_id
            WHERE ua.user_id = %s
        """
        rows = self.db.fetch_all(query, (user_id,))
        return [Address(**row) for row in rows] if rows else []

    def get_addresses_for_merchant(self, merchant_id: int) -> list[Address]:
        """
        Retrieves all addresses linked to a specific merchant.
        """
        query = """
            SELECT a.* FROM addresses a
            JOIN merchant_addresses ma ON a.id = ma.address_id
            WHERE ma.merchant_id = %s
        """
        rows = self.db.fetch_all(query, (merchant_id,))
        return [Address(**row) for row in rows] if rows else []

    def link_address_to_user(self, user_id: int, address_id: int) -> bool:
        """
        Creates a record in the user_addresses junction table.
        """
        query = "INSERT INTO user_addresses (user_id, address_id) VALUES (%s, %s)"
        try:
            self.db.execute_query(query, (user_id, address_id))
            return True
        except Exception as e:
            print(f"[AddressRepository ERROR] Failed to link address {address_id} to user {user_id}: {e}")
            return False

    def link_address_to_merchant(self, merchant_id: int, address_id: int) -> bool:
        """
        Creates a record in the merchant_addresses junction table.
        """
        query = "INSERT INTO merchant_addresses (merchant_id, address_id) VALUES (%s, %s)"
        try:
            self.db.execute_query(query, (merchant_id, address_id))
            return True
        except Exception as e:
            print(f"[AddressRepository ERROR] Failed to link address {address_id} to merchant {merchant_id}: {e}")
            return False

    def does_user_own_address(self, user_id: int, address_id: int) -> bool:
        """
        Checks if a specific address is linked to a specific user.
        """
        query = "SELECT 1 FROM user_addresses WHERE user_id = %s AND address_id = %s LIMIT 1"
        result = self.db.fetch_one(query, (user_id, address_id))
        return result is not None

    def does_merchant_own_address(self, merchant_id: int, address_id: int) -> bool:
        """
        Checks if a specific address is linked to a specific merchant.
        """
        query = "SELECT 1 FROM merchant_addresses WHERE merchant_id = %s AND address_id = %s LIMIT 1"
        result = self.db.fetch_one(query, (merchant_id, address_id))
        return result is not None