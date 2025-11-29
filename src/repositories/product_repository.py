from typing import override, Any
from types import SimpleNamespace
from models.products import ProductCreate, Product, ProductMetadataCreate, ProductMetadata, ProductEntry
from repositories.base_repository import BaseRepository
from repositories.metadata_repository import ProductMetadataRepository
from database.database import Database

class ProductRepository(BaseRepository):
    def __init__(self, db: Database):
        self.db = db
        self.table_name = "products"
        self.metadata_repo = ProductMetadataRepository(db)

    @override
    def create(self, data: ProductCreate) -> tuple[int, str]:
        """
        Creates a new product.

        Args:
            data (ProductCreate): The ProductCreate object containing the new product's data.

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

    def delete_images_for_product(self, product_id: int, db: Database) -> list[str]:
        """
        Deletes all image DB records and their junction table links for a specific product.
        This method assumes it's being called within an existing transaction.
        It returns the URLs of the deleted images so the physical files can be removed.
        """
        # Find all image IDs and URLs linked to the product
        image_query = "SELECT i.id, i.url FROM images i JOIN product_images pi ON i.id = pi.image_id WHERE pi.product_id = %s"
        image_rows = db.fetch_all(image_query, (product_id,))
        
        if image_rows:
            image_ids = tuple(row['id'] for row in image_rows)
            image_urls = [row['url'] for row in image_rows]
            # The 'product_images' junction table has ON DELETE CASCADE for image_id,
            # so we only need to delete from the 'images' table.
            # Delete from the images table
            db.execute_query(f"DELETE FROM images WHERE id IN ({','.join(['%s'] * len(image_ids))})", image_ids)
            return image_urls
        return []

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
            SELECT id, merchant_id, category_id, name, brand, price, original_price, address_id, rating_score, rating_count 
            FROM {self.table_name}
            WHERE id = %s
        """
        from_product_images_query = """
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
            rating_score=products_dict["rating_score"],
            rating_count=products_dict["rating_count"],
            warehouse=address_dict["city"],
            thumbnail=image_dict["url"],
            sold_count=metadata_dict["sold_count"]
        )

    def search(self, filters: dict[str, Any], page: int, per_page: int) -> tuple[list[ProductEntry], int]:
        """
        Searches, filters, sorts, and paginates products, returning them as ProductEntry objects.

        Args:
            filters (dict[str, Any]): A dictionary of filters (query, category, price, etc.).
            page (int): The current page number for pagination.
            per_page (int): The number of items per page.

        Returns:
            tuple[list[ProductEntry], int]: A tuple containing the list of paginated
                                            ProductEntry objects and the total number of
                                            products matching the criteria.
        """
        base_query = """
            SELECT
                p.id AS product_id,
                p.merchant_id, p.category_id, p.address_id,
                p.name, p.brand, p.price, p.original_price,
                p.rating_score,
                p.rating_count,
                a.city AS warehouse,
                i.url AS thumbnail,
                pm.sold_count
            FROM
                products p
            INNER JOIN product_metadata pm ON p.id = pm.product_id
            INNER JOIN addresses a ON p.address_id = a.id
            LEFT JOIN (
                SELECT pi.product_id, im.url
                FROM product_images pi
                JOIN images im ON pi.image_id = im.id
                WHERE pi.is_thumbnail = TRUE
            ) AS i ON p.id = i.product_id
        """
        count_query = "SELECT COUNT(p.id) as total FROM products p INNER JOIN product_metadata pm ON p.id = pm.product_id"

        where_clauses = []
        params = []

        # Build WHERE clauses from filters
        if filters.get('query'):
            where_clauses.append("(p.name LIKE %s OR p.description LIKE %s)")
            term = f"%{filters['query']}%"
            params.extend([term, term])
        if filters.get('category'):
            where_clauses.append("p.category_id = %s")
            params.append(filters['category'])
        if filters.get('min_price') is not None:
            where_clauses.append("p.price >= %s")
            params.append(filters['min_price'])
        if filters.get('max_price') is not None:
            where_clauses.append("p.price <= %s")
            params.append(filters['max_price'])
        if filters.get('min_rating') is not None: # rating_avg is now calculated
            where_clauses.append("(p.rating_score / p.rating_count) >= %s")
            params.append(filters['min_rating'])

        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)
            base_query += where_sql
            count_query += where_sql

        # Get total count for pagination
        total_row = self.db.fetch_one(count_query, tuple(params))
        total_products = total_row['total'] if total_row else 0

        # --- Sorting Logic ---
        sort_by = filters.get('sort_by')
        order_clause = "ORDER BY p.created_at DESC" # Default sort
        if sort_by == 'sold_count':
            order_clause = "ORDER BY pm.sold_count DESC"
        elif sort_by == 'price_asc':
            order_clause = "ORDER BY p.price ASC"
        elif sort_by == 'price_desc':
            order_clause = "ORDER BY p.price DESC"
        elif sort_by == 'ratings':
            order_clause = "ORDER BY (p.rating_score / p.rating_count) DESC"

        # --- Pagination Logic ---
        offset = (page - 1) * per_page
        pagination_clause = "LIMIT %s OFFSET %s"

        # --- Final Query ---
        final_query = f"{base_query} {order_clause} {pagination_clause}"
        final_params = tuple(params) + (per_page, offset)

        rows = self.db.fetch_all(final_query, final_params)
        
        product_entries = [ProductEntry(**row) for row in rows] if rows else []

        return product_entries, total_products

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
                p.rating_score,
                p.rating_count,
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
            order_clause = "ORDER BY (p.rating_score / p.rating_count) DESC"

        # --- Pagination Logic ---
        pagination_clause = "LIMIT %s OFFSET %s"

        # --- Final Query ---
        final_query = f"{base_query} {order_clause} {pagination_clause}"
        params = (limit, offset)

        rows = self.db.fetch_all(final_query, params)
        return [ProductEntry(**row) for row in rows] if rows else []

    def get_full_products(self, limit: int, offset: int = 0, sort_by: str | None = None) -> list[Product]:
        """
        Retrieves a list of full product objects with sorting and pagination.

        Args:
            limit (int): The maximum number of products to return.
            offset (int): The number of products to skip (for pagination).
            sort_by (str | None): The sorting criteria. Supported values:
                                  'sold_count', 'price_asc', 'price_desc', 'ratings'.

        Returns:
            list[Product]: A list of full Product objects.
        """
        base_query = f"SELECT p.* FROM {self.table_name} p"
        params = []

        # --- Sorting Logic ---
        # Default sort is by creation date
        order_clause = "ORDER BY p.id DESC"
        if sort_by == 'sold_count' or sort_by == 'ratings':
            # Join with metadata for sorting by sold_count or ratings
            base_query += " JOIN product_metadata pm ON p.id = pm.product_id"
            if sort_by == 'sold_count':
                order_clause = "ORDER BY pm.sold_count DESC"
            else: # 'ratings'
                # Avoid division by zero if rating_count is 0. Also, join products table.
                order_clause = "ORDER BY (CASE WHEN p.rating_count > 0 THEN p.rating_score / p.rating_count ELSE 0 END) DESC"
        elif sort_by == 'price_asc':
            order_clause = "ORDER BY p.price ASC"
        elif sort_by == 'price_desc':
            order_clause = "ORDER BY p.price DESC"

        # --- Pagination Logic ---
        pagination_clause = "LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        # --- Final Query to get main product data ---
        final_query = f"{base_query} {order_clause} {pagination_clause}"
        product_rows = self.db.fetch_all(final_query, tuple(params))

        if not product_rows:
            return []

        # Fetch images for all retrieved products in a single query to avoid N+1 problem
        product_ids = tuple(row['id'] for row in product_rows)
        if not product_ids:
            image_rows = []
        else:
            placeholders = ', '.join(['%s'] * len(product_ids))
            images_query = f"""
                SELECT pi.product_id, i.url
                FROM product_images pi JOIN images i ON pi.image_id = i.id
                WHERE pi.product_id IN ({placeholders}) ORDER BY pi.product_id, pi.is_thumbnail DESC, i.id
            """
            image_rows = self.db.fetch_all(images_query, product_ids)

        # Map images to their respective products
        for p_row in product_rows:
            p_row['images'] = [i_row['url'] for i_row in image_rows if i_row['product_id'] == p_row['id']]

        return [product for row in product_rows if (product := self._map_to_product(row)) is not None]
        
