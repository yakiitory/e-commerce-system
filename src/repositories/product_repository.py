from typing import override, Any
from types import SimpleNamespace
from models.products import ProductCreate, Product, ProductMetadata, ProductEntry
from repositories.base_repository import BaseRepository
from repositories.metadata_repository import ProductMetadataRepository
from database.database import Database

class ProductRepository(BaseRepository):
    def __init__(self, db: Database):
        self.db = db
        self.table_name = "products"
        self.metadata_repo = ProductMetadataRepository(db)

    @override
    def create(self, data: ProductCreate, metadata: ProductMetadata) -> tuple[int, str]:
        """
        Creates a new product.

        Args:
            data (ProductCreate): The ProductCreate object containing the new product's data.
            metadata (ProductMetadata): The ProductMetadata object containing the product's metadata.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        fields = [
            "name",
            "brand",
            "category_id",
            "description",
            "price",
            "original_price",
            "discount_rate",
            "quantity_available",
            "merchant_id",
            "address_id",
        ]

        # Create the product record
        new_product_id, message = self._create_record(
            data=data,
            fields=fields,
            table_name=self.table_name,
            db=self.db
        )

        if not new_product_id:
            return (0, message) # Return failure message from _create_record
        
        # Handle image record creation and its junction table
        if data.images:
            is_first_image = False
            for image_url in data.images:
                # Insert into 'images' table
                image_id, img_msg = self._create_record(
                    data=SimpleNamespace(url=image_url),
                    fields=['url'],
                    table_name='images',
                    db=self.db
                )
                if not image_id:
                    return (0, f"Product created, but failed to save image: {img_msg}")
                
                # Checks if thumbnail or not
                if is_first_image:
                    is_thumbnail = True
                    is_first_image = False
                else:
                    is_thumbnail = False
                # Link in 'product_images' junction table
                link_data = SimpleNamespace(
                    product_id=new_product_id, 
                    image_id=image_id, 
                    is_thumbnail=is_thumbnail
                )
                link_id, link_msg = self._create_record(link_data, ['product_id', 'image_id', 'is_thumbnail'], 'product_images', self.db)
                if not link_id:
                    return (0, f"Product and image created, but failed to link them: {link_msg}")
                
        if metadata:
            # Use the metadata repository to create the metadata record
            setattr(metadata, 'product_id', new_product_id) # Set the foreign key
            new_metadata_id, metadata_msg = self.metadata_repo.create(metadata)
            if not new_metadata_id:
                # Rollback: Delete the product that was just created
                self._delete_by_id(new_product_id, self.table_name, self.db)
                return (0, f"Product created, but failed to save metadata: {metadata_msg}")

        return (new_product_id, f"Product '{data.name}' created successfully with ID {new_product_id}.")

    @override
    def read(self, identifier: int) -> Product | None:
        """
        Reads a product record by ID.

        Args:
            identifier (int): The ID of the product in `products` table to retrieve.

        Returns:
            Product | None: The Product object if found, otherwise `None`.
        """
        return self._id_to_dataclass(identifier=identifier, table_name=self.table_name, db=self.db, map_func=self._map_to_product)
    
    @override
    def update(self, identifier: int, data: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> bool:
        """
        Updates an existing product and/or its metadata.
        Accepts dictionaries for partial updates.

        Args:
            identifier (int): The ID of the product to update.
            data (dict | None): A dictionary of product fields to update.
            metadata (dict | None): A dictionary of metadata fields to update.

        Returns:
            bool: `True` if the update was successful, `False` otherwise.
        """
        allowed_product_fields = [
            "name",
            "brand",
            "category_id",
            "description",
            "price",
            "original_price",
            "discount_rate",
            "quantity_available",
            "merchant_id",
            "address_id",
        ]

        product_updated = True
        metadata_updated = True

        # Update the product record if data is provided
        if data:
            product_updated = self._update_by_id(
                identifier=identifier,
                data=data,
                table_name=self.table_name,
                db=self.db,
                allowed_fields=allowed_product_fields
            )

        # Update the product metadata if metadata is provided
        if metadata:
            # Use the metadata repository to perform the update
            metadata_updated = self.metadata_repo.update(identifier, metadata)

        return product_updated and metadata_updated

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """
        Deletes an existing product record by ID.

        Args:
            identifier (int): The ID of the product to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        # Deleting a product should also delete its metadata to avoid orphaned records.
        metadata_deleted, _ = self.metadata_repo.delete(identifier)
        if not metadata_deleted:
            return (False, f"Failed to delete product metadata for product ID {identifier}. Product not deleted.")
        return self._delete_by_id(identifier, self.table_name, self.db, id_field="id")
    
    def delete_images_for_product(self, product_id: int, db: Database) -> None:
        """
        Deletes all images and their junction table links for a specific product.
        This method assumes it's being called within an existing transaction.
        Note: This does not delete the physical files, only the DB records.
        """
        # Find all image IDs linked to the product
        image_ids_query = "SELECT image_id FROM product_images WHERE product_id = %s"
        image_id_rows = db.fetch_all(image_ids_query, (product_id,))
        
        if image_id_rows:
            image_ids = tuple(row['image_id'] for row in image_id_rows)
            # Delete from the junction table (handled by cascade on images table)
            # Delete from the images table
            db.execute_query(f"DELETE FROM images WHERE id IN ({',%s' * len(image_ids)})", image_ids)

    def _map_to_product(self, row: dict) -> Product | None:
        """
        Maps a database row (dictionary) to a Product dataclass object.

        Args:
            row (dict): A dictionary representing a row from the `products` table.
        
        Returns:
            Product | None: A Product object if the row is not empty, otherwise `None`.
        """
        if not row:
            return None
        return Product(**row)
    
    def read_all_by_merchant_id(self, merchant_id: int) -> list[Product]:
        """
        Reads all products for a specific merchant, including their images.

        Args:
            merchant_id (int): The ID of the merchant whose products to retrieve.

        Returns:
            list[Product]: A list of Product objects, ordered by creation date.
        """
        products_query = f"SELECT * FROM {self.table_name} WHERE merchant_id = %s ORDER BY created_at DESC"
        product_rows = self.db.fetch_all(products_query, (merchant_id,))

        if not product_rows:
            return []

        products = []
        for row in product_rows:
            product_id = row['id']

            # Fetch associated image URLs for the current product
            images_query = """
                SELECT i.url FROM images i
                JOIN product_images pi ON i.id = pi.image_id
                WHERE pi.product_id = %s
                ORDER BY pi.is_thumbnail DESC, i.id
            """
            image_rows = self.db.fetch_all(images_query, (product_id,))
            image_urls = [img_row['url'] for img_row in image_rows] if image_rows else []

            # Add the list of image URLs to the product data before creating the object
            row['images'] = image_urls
            products.append(self._map_to_product(row))

        return products

    def get_product_entry(self, identifier: int) -> ProductEntry | None:
        """
        Retrieves a 'product entry' for usage with the front end, such as a for you page entry.
        Runs multiple queries on multiple tables.

        Args:
            identifier (int): The ID of the product to retrieve.

        Returns:
            ProductEntry | None: A ProductEntry object if found, otherwise `None`.
        """
        from_products_query = f"""
            SELECT id, merchant_id, category_id, name, brand, price, original_price, address_id 
            FROM {self.table_name}
            WHERE id = %s
        """
        from_product_images_query = f"""
            SELECT image_id FROM product_images 
            WHERE product_id = %s
            AND is_thumbnail = 1
            LIMIT 1
        """
        from_product_metadata_query = f"""
            SELECT sold_count, rating_avg 
            FROM product_metadata
            WHERE product_id = %s
        """
        from_images_query = f"""
            SELECT url FROM images
            WHERE id = %s
        """
        from_address_query = f"""
            SELECT city
            FROM addresses
            WHERE id = %s
        """
        products_params = (identifier,)
        products_dict = self.db.fetch_one(from_products_query, products_params)
        if not products_dict:
            return None

        metadata_dict = self.db.fetch_one(from_product_metadata_query, products_params)
        if not metadata_dict:
            return None
        
        thumbnail_dict = self.db.fetch_one(from_product_images_query, products_params)
        if not thumbnail_dict:
            return None
        
        image_params = (thumbnail_dict["image_id"],)
        image_dict = self.db.fetch_one(from_images_query, image_params,)
        if not image_dict:
            return None

        address_params = (products_dict["address_id"], )
        address_dict = self.db.fetch_one(from_address_query, address_params)
        if not address_dict:
            return None

        return ProductEntry(
            product_id=products_dict["id"],
            merchant_id=products_dict["merchant_id"],
            category_id=products_dict["category_id"],
            address_id=products_dict["address_id"],
            name=products_dict["name"],
            brand=products_dict["brand"],
            price=products_dict["price"],
            original_price=products_dict["original_price"],
            ratings=metadata_dict["rating_avg"],
            warehouse=address_dict["city"],
            thumbnail=image_dict["url"],
            sold_count=metadata_dict["sold_count"]
        )

    def search(self, search_term: str, limit: int = 20) -> list[ProductEntry]:
        """
        Searches for products by name or description and returns them as ProductEntry objects.

        Args:
            search_term (str): The term to search for.
            limit (int): The maximum number of results to return.

        Returns:
            list[ProductEntry]: A list of matching product entry objects.
        """
        query = """
            SELECT
                p.id AS product_id,
                p.merchant_id,
                p.category_id,
                p.address_id,
                p.name,
                p.brand,
                p.price,
                p.original_price,
                pm.rating_avg AS ratings,
                a.city AS warehouse,
                i.url AS thumbnail,
                pm.sold_count
            FROM
                products p
            JOIN product_metadata pm ON p.id = pm.product_id
            JOIN addresses a ON p.address_id = a.id
            LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_thumbnail = TRUE
            LEFT JOIN images i ON pi.image_id = i.id
            WHERE
                p.name LIKE %s OR p.description LIKE %s
            LIMIT %s
        """
        # Add wildcards for a 'contains' search
        term = f"%{search_term}%"
        rows = self.db.fetch_all(query, (term, term, limit))

        return [ProductEntry(**row) for row in rows] if rows else []

    def get_entries(self, limit: int, offset: int = 0, sort_by: str | None = None) -> list[ProductEntry]:
        """
        Retrieves a list of product entries with sorting and pagination.

        Args:
            limit (int): The maximum number of entries to return.
            offset (int): The number of entries to skip (for pagination).
            sort_by (str | None): The sorting criteria. Supported values:
                                  'sold_count', 'price_asc', 'price_desc', 'ratings'.

        Returns:
            list[ProductEntry]: A list of product entry objects.
        """
        base_query = """
            SELECT
                p.id AS product_id,
                p.merchant_id,
                p.category_id,
                p.address_id,
                p.name,
                p.brand,
                p.price,
                p.original_price,
                pm.rating_avg AS ratings,
                a.city AS warehouse,
                i.url AS thumbnail,
                pm.sold_count
            FROM
                products p
            JOIN product_metadata pm ON p.id = pm.product_id
            JOIN addresses a ON p.address_id = a.id
            LEFT JOIN product_images pi ON p.id = pi.product_id AND pi.is_thumbnail = TRUE
            LEFT JOIN images i ON pi.image_id = i.id
        """

        # --- Sorting Logic ---
        order_clause = "ORDER BY p.created_at DESC" # Default sort
        if sort_by == 'sold_count':
            order_clause = "ORDER BY pm.sold_count DESC"
        elif sort_by == 'price_asc':
            order_clause = "ORDER BY p.price ASC"
        elif sort_by == 'price_desc':
            order_clause = "ORDER BY p.price DESC"
        elif sort_by == 'ratings':
            order_clause = "ORDER BY pm.rating_avg DESC"

        # --- Pagination Logic ---
        pagination_clause = "LIMIT %s OFFSET %s"

        # --- Final Query ---
        final_query = f"{base_query} {order_clause} {pagination_clause}"
        params = (limit, offset)

        rows = self.db.fetch_all(final_query, params)
        return [ProductEntry(**row) for row in rows] if rows else []

        
