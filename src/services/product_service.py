from __future__ import annotations
from typing import TYPE_CHECKING, Any
from types import SimpleNamespace

if TYPE_CHECKING:
    from repositories.product_repository import ProductRepository
    from database.database import Database
    from models.products import ProductCreate, ProductMetadata, Product, ProductEntry, Category, Address
    from services.media_service import MediaService
    from fastapi import UploadFile

class ProductService:
    """
    Handles the business logic for managing products.
    """

    def __init__(self, db: Database, product_repo: ProductRepository, media_service: MediaService):
        """
        Initializes the ProductService.

        Args:
            db (Database): The database instance for transaction management.
            product_repo (ProductRepository): The repository for product data.
            media_service (MediaService): The service for handling media files.
        """
        self.db = db
        self.product_repo = product_repo
        self.media_service = media_service

    def create_product(self, product_data: ProductCreate, metadata: ProductMetadata, images: list[UploadFile]) -> tuple[int | None, str]:
        """
        Creates a new product, saves its images, and links them.

        Args:
            product_data (ProductCreate): The data for the new product.
            metadata (ProductMetadata): The metadata for the new product.
            images (list[UploadFile]): A list of uploaded image files.

        Returns:
            tuple[int | None, str]: A tuple containing the new product ID and a message.
        """
        transaction_committed = False
        try:
            self.db.begin_transaction()

            # 1. Create the product record to get its ID.
            # The product_data.images list is initially empty.
            new_product_id, message = self.product_repo.create(product_data, metadata)
            if not new_product_id:
                self.db.rollback()
                return (None, message)

            # 2. Process and save each uploaded image.
            image_urls = []
            is_first_image = True
            for image_file in images:
                # Create a placeholder in 'images' to get an ID
                image_id, _ = self.product_repo._create_record(
                    data=SimpleNamespace(url='placeholder'),
                    fields=['url'], table_name='images', db=self.db
                )
                if not image_id:
                    raise Exception("Failed to create placeholder image record.")

                # Save the physical image file using the new ID
                saved, path_or_none = self.media_service.save_image(image_file, image_id)
                if not saved or not path_or_none:
                    raise Exception(f"Failed to save image file for image ID {image_id}.")

                # Update the image record with the actual file path
                self.product_repo._update_by_id(image_id, {'url': path_or_none}, 'images', self.db, ['url'])
                image_urls.append(path_or_none)

                # Link image to product in the junction table
                link_data = SimpleNamespace(product_id=new_product_id, image_id=image_id, is_thumbnail=is_first_image)
                link_id, link_msg = self.product_repo._create_record(link_data, ['product_id', 'image_id', 'is_thumbnail'], 'product_images', self.db)
                if not link_id:
                    raise Exception(f"Failed to link image to product: {link_msg}")
                
                is_first_image = False # Only the first image is the thumbnail

            self.db.commit()
            transaction_committed = True
            return (new_product_id, f"Product '{product_data.name}' created successfully.")

        except Exception as e:
            print(f"[ProductService ERROR] Product creation failed: {e}")
            if not transaction_committed:
                self.db.rollback()
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

    def get_all_categories(self) -> list[Category] | None:
        """
        Retrieves all product categories.

        Returns:
            list[Category] | None: A list of Category objects, or None on failure.
        """
        query = "SELECT id, name, parent_id, description FROM categories ORDER BY name"
        try:
            category_data = self.db.fetch_all(query)
            if category_data:
                from models.products import Category
                return [Category(**cat) for cat in category_data]
            return []
        except Exception as e:
            print(f"[ProductService ERROR] An unexpected error occurred while fetching all categories: {e}")
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

    def get_products_by_merchant_id(self, merchant_id: int) -> tuple[bool, list[Product] | str]:
        """
        Retrieves all products for a specific merchant.

        Args:
            merchant_id (int): The ID of the merchant.

        Returns:
            tuple[bool, list[Product] | str]: A tuple containing a boolean for success,
                                             and either a list of products or an error message.
        """
        try:
            # Assuming the product repository has a method to fetch products by merchant ID.
            products = self.product_repo.read_all_by_merchant_id(merchant_id)
            return (True, products)
        except Exception as e:
            print(f"[ProductService ERROR] Failed to get products for merchant {merchant_id}: {e}")
            return (False, "Could not retrieve products for the specified merchant.")