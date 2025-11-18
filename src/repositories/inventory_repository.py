from typing import override, Any
from repositories.base_repository import BaseRepository
from database.database import Database
from models.products import Inventory, InventoryCreate


class InventoryRepository(BaseRepository):
    def __init__(self, db: Database):
        """Initializes the InventoryRepository."""
        self.db = db
        self.table_name = "inventories"

    @override
    def create(self, data: InventoryCreate) -> tuple[int | None, str]:
        """This is likely handled by product creation, but implemented for completeness."""
        fields = ["product_id", "quantity_available", "quantity_reserved"]
        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        return (new_id, message)

    @override
    def read(self, identifier: int) -> Inventory | None:
        """Reads an inventory record by product_id."""
        return self._id_to_dataclass(
            identifier=identifier,
            table_name=self.table_name,
            db=self.db,
            map_func=lambda row: Inventory(**row) if row else None,
            id_field="product_id"
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """Updates an inventory record by product_id."""
        allowed_fields = ["quantity_available", "quantity_reserved"]
        return self._update_by_id(identifier, data, self.table_name, self.db, allowed_fields, id_field="product_id")

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """Deletes an inventory record by product_id."""
        return self._delete_by_id(identifier, self.table_name, self.db, id_field="product_id")

    def adjust_quantity(self, product_id: int, quantity_change: int) -> bool:
        """
        Atomically adjusts the available quantity of a product's inventory.

        Args:
            product_id (int): The ID of the product.
            quantity_change (int): The amount to change the quantity by (can be negative).

        Returns:
            bool: True if successful, False otherwise (e.g., insufficient stock).
        """
        query = f"""
            UPDATE {self.table_name}
            SET quantity_available = quantity_available + %s
            WHERE product_id = %s AND quantity_available + %s >= 0
        """
        params = (quantity_change, product_id, quantity_change)

        try:
            affected_rows = self.db.execute_query(query, params, return_row_count=True)

            if affected_rows is not None and affected_rows > 0:
                print(f"[{self.__class__.__name__}] Adjusted inventory for product ID {product_id} by {quantity_change}.")
                return True
            else:
                print(f"[{self.__class__.__name__} INFO] Inventory adjustment for product ID {product_id} failed. Insufficient stock or inventory not found.")
                return False
        except Exception as e:
            print(f"[{self.__class__.__name__} ERROR] Failed to adjust inventory for product ID {product_id}: {e}")
            return False