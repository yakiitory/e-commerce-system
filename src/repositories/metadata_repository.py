from typing import override, Any, Literal
from repositories.base_repository import BaseRepository
from database.database import Database
from models.accounts import UserMetadata
from models.products import ProductMetadata, ProductMetadataCreate
import json
from types import SimpleNamespace
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
        fields = [f.name for f in dataclasses.fields(UserMetadata)]
        new_id, message = self._create_record(data, fields, self.table_name, self.db)
        if new_id is not None:
            return (data.user_id, message)
        return (None, message)

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
        allowed_fields = [f.name for f in dataclasses.fields(UserMetadata) if f.name != 'user_id']
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
    def create(self, data: ProductMetadataCreate) -> tuple[int | None, str]:
        """
        Creates a new product metadata record.

        Args:
            data (ProductMetadataCreate): The ProductMetadataCreate object to create.

        Returns:
            tuple[int | None, str]: A tuple with the new ID and a message.
        """
        # Create a mutable copy of the data to avoid altering the original object
        data_for_db = SimpleNamespace(**vars(data))

        # Serialize complex types to JSON strings
        if isinstance(data_for_db.demographics_fit, dict):
            data_for_db.demographics_fit = json.dumps(data_for_db.demographics_fit)
        if isinstance(data_for_db.seasonal_relevance, list):
            data_for_db.seasonal_relevance = json.dumps(data_for_db.seasonal_relevance)
        if isinstance(data_for_db.embedding_vector, list):
            data_for_db.embedding_vector = json.dumps(data_for_db.embedding_vector)
        if isinstance(data_for_db.keywords, list):
            data_for_db.keywords = json.dumps(data_for_db.keywords)
        if isinstance(data_for_db.tags, list):
            data_for_db.tags = json.dumps(data_for_db.tags)

        fields = [
            "product_id", "view_count", "sold_count", "add_to_cart_count",
            "wishlist_count", "click_through_rate", "popularity_score",
            "demographics_fit", "seasonal_relevance", "embedding_vector",
            "keywords", "tags"
        ]
        return self._create_record(data_for_db, fields, self.table_name, self.db)

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
            map_func=self._map_to_product_metadata,
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
            "click_through_rate",
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

    def increment_field(self, product_id: int, field: Literal["view_count", "sold_count", "add_to_cart_count", "wishlist_count"], value: int = 1) -> bool:
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

    def decrement_field(self, product_id: int, field: Literal["view_count", "sold_count", "add_to_cart_count", "wishlist_count"], value: int = 1) -> bool:
        """
        Atomically decrements a numeric field for a product's metadata.

        Args:
            product_id (int): The ID of the product.
            field (str): The metadata field to decrement.
            value (int): The value to decrement by. Defaults to 1.

        Returns:
            bool: True if successful, False otherwise.
        """
        valid_fields = {f.name for f in dataclasses.fields(ProductMetadata)}
        if field not in valid_fields:
            print(f"[{self.__class__.__name__} ERROR] Invalid field to decrement: {field}")
            return False

        query = f"UPDATE {self.table_name} SET {field} = GREATEST(0, {field} - %s) WHERE product_id = %s"
        try:
            self.db.execute_query(query, (value, product_id))
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__} ERROR] Failed to decrement {field} for product {product_id}: {e}")
            return False

    def _map_to_product_metadata(self, row: dict) -> ProductMetadata | None:
        """
        Maps a database row to a ProductMetadata object, deserializing JSON fields.
        """
        if not row:
            return None

        # Create a mutable copy to work with
        data = row.copy()

        # List of fields that are stored as JSON strings
        json_fields = [
            'demographics_fit', 'seasonal_relevance', 'embedding_vector',
            'keywords', 'tags'
        ]

        for field in json_fields:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    # If deserialization fails, default to an empty list/dict
                    # based on the dataclass definition to prevent errors.
                    field_type = ProductMetadata.__annotations__.get(field)
                    data[field] = {} if 'dict' in str(field_type) else []

        return ProductMetadata(**data)