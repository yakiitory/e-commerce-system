from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from repositories.product_repository import ProductRepository
    from database.database import Database
    from models.products import ProductCreate, ProductMetadata, Product, ProductEntry


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

    def get_product(self, product_id: int) -> tuple[bool, str | Product | None]:
        """
        Retrieves a single product by its ID.

        Args:
            product_id (int): The ID of the product to retrieve.

        Returns:
            tuple[bool, str | Product | None]: A tuple indicating success, and either the
                                               Product object or an error message.
        """
        product = self.product_repo.read(product_id)
        if not product:
            return (False, f"Product with ID {product_id} not found.")
        return (True, product)

    def get_product_for_display(self, product_id: int) -> tuple[bool, str | ProductEntry | None]:
        """
        Retrieves a simplified product entry for display purposes (e.g., on a product card).

        Args:
            product_id (int): The ID of the product.

        Returns:
            tuple[bool, str | ProductEntry | None]: A tuple indicating success, and either the
                                                    ProductEntry object or an error message.
        """
        product_entry = self.product_repo.get_product_entry(product_id)
        if not product_entry:
            return (False, f"Could not retrieve display entry for product with ID {product_id}.")
        return (True, product_entry)

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

    def search_products(self, search_term: str) -> tuple[bool, str | list[ProductEntry]]:
        """
        Searches for products based on a search term.

        Args:
            search_term (str): The term to search for in product names and descriptions.

        Returns:
            tuple[bool, str | list[ProductEntry]]: A tuple indicating success, and either a
                                              list of products or an error message.
        """
        try:
            products = self.product_repo.search(search_term)
            return (True, products)
        except Exception as e:
            print(f"[ProductService ERROR] An unexpected error occurred during product search: {e}")
            return (False, "An unexpected error occurred during product search.")