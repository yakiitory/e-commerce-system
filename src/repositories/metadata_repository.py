from typing import override, Any, Literal
from repositories.base_repository import BaseRepository
from database.database import Database
from models.accounts import UserMetadata
from models.products import ProductMetadata
import dataclasses


class UserMetadataRepository(BaseRepository):
    def __init__(self, db: Database):
        """Initializes the UserMetadataRepository."""
        self.db = db
        self.table_name = "user_metadata"

    @override
    def create(self, data: UserMetadata) -> tuple[int | None, str]:
        """
        Creates a new user metadata record.

        Args:
            data (UserMetadata): The UserMetadata object to create.

        Returns:
            tuple[int | None, str]: A tuple with the new ID and a message.
        """
        fields = [
            "user_id", "addresses", "order_history", "view_history",
            "liked_products", "reviews", "favorite_categories", "favorite_brands",
            "price_sensitivity", "engagement_score", "recency_decay_factor",
            "gender", "interest_vector", "segment_label", "churn_risk_score"
        ]
        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        return (new_id, message)

    @override
    def read(self, identifier: int) -> UserMetadata | None:
        """
        Reads a user metadata record by user_id.

        Args:
            identifier (int): The user_id to retrieve metadata for.

        Returns:
            UserMetadata | None: The UserMetadata object if found, otherwise None.
        """
        return self._id_to_dataclass(
            identifier=identifier,
            table_name=self.table_name,
            db=self.db,
            map_func=self._map_to_user_metadata,
            id_field="user_id"
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """
        Updates a user metadata record by user_id.

        Args:
            identifier (int): The user_id of the record to update.
            data (dict[str, Any]): A dictionary of fields to update.

        Returns:
            bool: True if successful, False otherwise.
        """
        allowed_fields = [
            "addresses", "order_history", "view_history", "liked_products",
            "reviews", "favorite_categories", "favorite_brands", "price_sensitivity",
            "engagement_score", "recency_decay_factor", "gender", "interest_vector",
            "segment_label", "churn_risk_score"
        ]
        return self._update_by_id(identifier, data, self.table_name, self.db, allowed_fields, id_field="user_id")

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """
        Deletes a user metadata record by user_id.

        Args:
            identifier (int): The user_id of the record to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        return self._delete_by_id(identifier, self.table_name, self.db, id_field="user_id")

    def _map_to_user_metadata(self, row: dict) -> UserMetadata | None:
        if not row:
            return None
        return UserMetadata(**row)


class ProductMetadataRepository(BaseRepository):
    def __init__(self, db: Database):
        """Initializes the ProductMetadataRepository."""
        self.db = db
        self.table_name = "product_metadata"

    @override
    def create(self, data: ProductMetadata) -> tuple[int | None, str]:
        """
        Creates a new product metadata record.

        Args:
            data (ProductMetadata): The ProductMetadata object to create.

        Returns:
            tuple[int | None, str]: A tuple with the new ID and a message.
        """
        fields = [
            "view_count", "sold_count", "add_to_cart_count", "wishlist_count",
            "click_through_rate", "rating_avg", "rating_count",
            "popularity_score", "demographics_fit", "seasonal_relevance",
            "embedding_vector", "keywords", "tags"
        ]
        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        return (new_id, message)

    @override
    def read(self, identifier: int) -> ProductMetadata | None:
        """
        Reads a product metadata record by product_id.

        Args:
            identifier (int): The product_id to retrieve metadata for.

        Returns:
            ProductMetadata | None: The ProductMetadata object if found, otherwise None.
        """
        return self._id_to_dataclass(
            identifier=identifier,
            table_name=self.table_name,
            db=self.db,
            map_func=lambda row: ProductMetadata(**row) if row else None,
            id_field="product_id"
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """
        Updates a product metadata record by product_id.

        Args:
            identifier (int): The product_id of the record to update.
            data (dict[str, Any]): A dictionary of fields to update.

        Returns:
            bool: True if successful, False otherwise.
        """
        allowed_fields = [
            "view_count", "sold_count", "add_to_cart_count", "wishlist_count",
            "click_through_rate", "rating_avg", "rating_count",
            "popularity_score", "demographics_fit", "seasonal_relevance",
            "embedding_vector", "keywords", "tags"
        ]
        return self._update_by_id(identifier, data, self.table_name, self.db, allowed_fields, id_field="product_id")

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """
        Deletes a product metadata record by product_id.

        Args:
            identifier (int): The product_id of the record to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        return self._delete_by_id(identifier, self.table_name, self.db, id_field="product_id")

    def increment_field(self, product_id: int, field: Literal["view_count", "sold_count", "add_to_cart_count", "wishlist_count", "rating_count"], value: int = 1) -> bool:
        """
        Atomically increments a numeric field for a product's metadata.

        Args:
            product_id (int): The ID of the product.
            field (str): The metadata field to increment.
            value (int): The value to increment by. Defaults to 1.

        Returns:
            bool: True if successful, False otherwise.
        """
        # Validate that the field is a valid field in the dataclass
        valid_fields = {f.name for f in dataclasses.fields(ProductMetadata)}
        if field not in valid_fields:
            print(f"[{self.__class__.__name__} ERROR] Invalid field to increment: {field}")
            return False

        query = f"UPDATE {self.table_name} SET {field} = {field} + %s WHERE product_id = %s"
        try:
            self.db.execute_query(query, (value, product_id))
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__} ERROR] Failed to increment {field} for product {product_id}: {e}")
            return False
 
