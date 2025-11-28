from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from repositories.product_repository import ProductRepository
    from database.database import Database
    from models.products import ProductCreate, ProductMetadata, Product, ProductEntry, Category, Address


class ProductService:
    """
    Handles the business logic for managing products.
    """

    def __init__(self, db: Database, product_repo: ProductRepository):
        """
        Initializes the ProductService.

        Args:
            db (Database): The database instance for transaction management.
            product_repo (ProductRepository): The repository for product data.
        """
        self.db = db
        self.product_repo = product_repo

    def create_product(self, product_data: ProductCreate, metadata: ProductMetadata) -> tuple[int | None, str]:
        """
        Creates a new product along with its metadata.

        Args:
            product_data (ProductCreate): The data for the new product.
            metadata (ProductMetadata): The metadata for the new product.

        Returns:
            tuple[int | None, str]: A tuple containing the new product ID and a message.
        """
        try:
            new_product_id, message = self.product_repo.create(product_data, metadata)
            if not new_product_id:
                return (None, message)
            return (new_product_id, message)
        except Exception as e:
            print(f"[ProductService ERROR] An unexpected error occurred during product creation: {e}")
            return (None, "An unexpected error occurred during product creation.")

    def get_product(self, product_id: int) -> tuple[bool, Product | None]:
        """
        Retrieves a single product by its ID.

        Args:
            product_id (int): The ID of the product to retrieve.

        Returns:
            tuple[bool, Product | None]: A tuple indicating success, and either the
                                         Product object or `None` on failure.
        """
        product = self.product_repo.read(product_id)
        if not product:
            return (False, None)
        return (True, product)

    def get_product_for_display(self, product_id: int) -> tuple[bool, ProductEntry | None]:
        """
        Retrieves a simplified product entry for display purposes (e.g., on a product card).

        Args:
            product_id (int): The ID of the product.

        Returns:
            tuple[bool, ProductEntry | None]: A tuple indicating success, and either the
                                              ProductEntry object or `None` on failure.
        """
        product_entry = self.product_repo.get_product_entry(product_id)
        if not product_entry:
            return (False, None)
        return (True, product_entry)

    def get_product_metadata(self, product_id: int) -> tuple[bool, ProductMetadata | None]:
        """
        Retrieves the metadata for a single product by its ID.

        Args:
            product_id (int): The ID of the product whose metadata is to be retrieved.

        Returns:
            tuple[bool, ProductMetadata | None]: A tuple indicating success, and either the
                                                 ProductMetadata object or `None` on failure.
        """
        try:
            # Assumes the product repository has a metadata_repo with a read method.
            metadata = self.product_repo.metadata_repo.read(product_id)
            if not metadata:
                return (False, None)
            return (True, metadata)
        except Exception as e:
            print(f"[ProductService ERROR] An unexpected error occurred while fetching metadata for product {product_id}: {e}")
            return (False, None)

    def update_product(self, product_id: int, product_data: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> tuple[bool, str]:
        """
        Updates a product's main data and/or its metadata.

        Args:
            product_id (int): The ID of the product to update.
            product_data (dict | None): A dictionary of product fields to update.
            metadata (dict | None): A dictionary of metadata fields to update.

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        if not self.product_repo.read(product_id):
            return (False, f"Product with ID {product_id} not found.")

        success = self.product_repo.update(product_id, product_data, metadata)
        if success:
            return (True, f"Product {product_id} updated successfully.")
        return (False, f"Failed to update product {product_id}.")

    def delete_product(self, product_id: int) -> tuple[bool, str]:
        """
        Deletes a product and its associated metadata.

        Args:
            product_id (int): The ID of the product to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        if not self.product_repo.read(product_id):
            return (False, f"Product with ID {product_id} not found.")

        return self.product_repo.delete(product_id)

    def search_products(self, search_term: str) -> tuple[bool, list[ProductEntry] | None]:
        """
        Searches for products based on a search term.

        Args:
            search_term (str): The term to search for in product names and descriptions.

        Returns:
            tuple[bool, list[ProductEntry] | None]: A tuple indicating success, and either a
                                                    list of products or `None` on failure.
        """
        try:
            products = self.product_repo.search(search_term)
            return (True, products)
        except Exception as e:
            print(f"[ProductService ERROR] An unexpected error occurred during product search: {e}")
            return (False, None)

    def get_product_entries(self, limit: int, offset: int = 0, sort_by: str | None = None) -> tuple[bool, list[ProductEntry] | None]:
        """
        Retrieves a list of product entries for display, with sorting and pagination.

        Args:
            limit (int): The maximum number of product entries to retrieve.
            offset (int): The number of entries to skip (for pagination).
            sort_by (str | None): The criteria to sort by (e.g., 'sold_count', 'price_asc').

        Returns:
            tuple[bool, list[ProductEntry] | None]: A tuple indicating success, and either a
                                                    list of product entries or `None` on failure.
        """
        try:
            # This assumes a corresponding `get_entries` method exists in the repository
            # that can handle limit, offset, and sorting.
            product_entries = self.product_repo.get_entries(limit=limit, offset=offset, sort_by=sort_by)
            return (True, product_entries)
        except Exception as e:
            print(f"[ProductService ERROR] An unexpected error occurred while fetching product entries: {e}")
            return (False, None)

    def get_product_category(self, category_id: int) -> Category | None:
        """
        Retrieves a single product category by its ID.

        Args:
            category_id (int): The ID of the category to retrieve.

        Returns:
            Category | None: The Category object if found, otherwise None.
        """
        query = "SELECT id, name, parent_id, description FROM categories WHERE id = %s"
        try:
            category_data = self.db.fetch_one(query, (category_id,))
            if category_data:
                return Category(**category_data)
            return None
        except Exception as e:
            print(f"[ProductService ERROR] An unexpected error occurred while fetching category {category_id}: {e}")
            return None

    def get_address_by_id(self, address_id: int) -> Address | None:
        """
        Retrieves a single address by its ID.

        Args:
            address_id (int): The ID of the address to retrieve.

        Returns:
            Address | None: The Address object if found, otherwise None.
        """
        query = "SELECT id, user_id, address_line1, address_line2, city, state_province_region, postal_code, country, address_type, is_default FROM addresses WHERE id = %s"
        try:
            address_data = self.db.fetch_one(query, (address_id,))
            if address_data:
                return Address(**address_data)
            return None
        except Exception as e:
            print(f"[ProductService ERROR] An unexpected error occurred while fetching address {address_id}: {e}")
            return None