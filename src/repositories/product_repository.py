from typing import override, Any
from types import SimpleNamespace
from models.products import ProductCreate, Product, ProductMetadata, ProductEntry
from models.images import ImageCreate, Image
from repositories.base_repository import BaseRepository
from repositories.metadata_repository import ProductMetadataRepository
from repositories.image_repository import ImageRepository
from database.database import Database

class ProductRepository(BaseRepository):
    def __init__(self, db: Database):
        self.db = db
        self.table_name = "products"
        self.metadata_repo = ProductMetadataRepository(db)
        self.image_repo = ImageRepository(db)


    @override
    def create(self, data: ProductCreate, urls: list[str]) -> tuple[int, str]:
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
            "quantity_available",
            "merchant_id",
            "address_id",
        ]

        try:
            self.db.begin_transaction()

            # Create the product record
            new_product_id, message = self._create_record(
                data=data,
                fields=fields,
                table_name=self.table_name,
                db=self.db
            )

            if not new_product_id:
                raise Exception(message)
            
            # Handle image record creation and its junction table
            if urls:
                is_first_image = 1
                for url in urls:
                    image = ImageCreate(url=url)
                    image_id, message = self.image_repo.create(image)
                    if not image_id:
                        raise Exception(message)
                    query = "INSERT INTO product_images (product_id, image_id, is_thumbnail) VALUES (%s, %s, %s)"
                    self.db.execute_query(query, (new_product_id, image_id, is_first_image))
                    is_first_image = 0
            self.db.commit()
            return (new_product_id, f"Product '{data.name}' created successfully with ID {new_product_id}.")

        except Exception as e:
            self.db.rollback()
            return (0, f"Failed to create product. Transaction rolled back. Reason: {e}")

    @override
    def read(self, identifier: int) -> Product | None:
        """
        Reads a product record by ID.

        Args:
            identifier (int): The ID of the product in `products` table to retrieve.

        Returns:
            Product | None: The Product object if found, otherwise `None`.
        """
        # Fetch the main product details
        product_query = f"SELECT * FROM {self.table_name} WHERE id = %s"
        product_row = self.db.fetch_one(product_query, (identifier,))

        if not product_row:
            return None

        # Fetch associated image URLs
        images_query = """
            SELECT i.url FROM images i
            JOIN product_images pi ON i.id = pi.image_id
            WHERE pi.product_id = %s
            ORDER BY pi.is_thumbnail DESC, i.id
        """
        image_rows = self.db.fetch_all(images_query, (identifier,))
        image_urls = [row['url'] for row in image_rows] if image_rows else []

        # Fetch metadata for ratings
        metadata = self.metadata_repo.read(identifier)

        # Add the extra data to the product row before mapping
        product_row['images'] = image_urls
        return self._map_to_product(product_row)
    
    @override
    def update(self, identifier: int, data: dict[str, Any] | None = None, urls: list[str] | None = None) -> tuple[bool, str]:
        """
        Updates an existing product and its images in a transactional way.

        Args:
            identifier (int): The ID of the product to update.
            data (dict | None): A dictionary of product fields to update.
            urls (list[str] | None): List of new image URLs to replace existing ones.

        Returns:
            tuple[bool, str]: (success, message)
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

        try:
            self.db.begin_transaction()

            # Update product fields if provided
            if data:
                updated = self._update_by_id(
                    identifier=identifier,
                    data=data,
                    table_name=self.table_name,
                    db=self.db,
                    allowed_fields=allowed_product_fields
                )
                if not updated:
                    raise Exception("Failed to update product fields.")

            # Replace product images if URLs are provided
            if urls is not None:
                # Delete old image links
                delete_query = "DELETE FROM product_images WHERE product_id = %s"
                self.db.execute_query(delete_query, (identifier,))

                # Insert new images and junctions
                is_first_image = 1
                for url in urls:
                    image = ImageCreate(url=url)
                    image_id, message = self.image_repo.create(image)
                    if not image_id:
                        raise Exception(message)
                    insert_query = "INSERT INTO product_images (product_id, image_id, is_thumbnail) VALUES (%s, %s, %s)"
                    self.db.execute_query(insert_query, (identifier, image_id, is_first_image))
                    is_first_image = 0

            self.db.commit()
            return (True, f"Product ID {identifier} updated successfully.")

        except Exception as e:
            self.db.rollback()
            return (False, f"Failed to update product. Transaction rolled back. Reason: {e}")


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
            SELECT id, merchant_id, category_id, name, brand, price, rating_score, rating_count, address_id, quantity_available 
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
            SELECT sold_count
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
        from_category_query = f"""
            SELECT name
            FROM categories
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
        
        category_params = (products_dict["category_id"], )
        category_dict = self.db.fetch_one(from_category_query, category_params)
        if not category_dict:
            return None

        if products_dict["rating_score"] and products_dict["rating_count"]:
            rating_avg = products_dict["rating_score"] / products_dict["rating_count"]
        else:
            rating_avg = 0

        
        return ProductEntry(
            product_id=products_dict["id"],
            merchant_id=products_dict["merchant_id"],
            category_id=products_dict["category_id"],
            address_id=products_dict["address_id"],
            name=products_dict["name"],
            brand=products_dict["brand"],
            price=products_dict["price"],
            ratings=str(rating_avg),
            warehouse=address_dict["city"],
            thumbnail=image_dict["url"],
            sold_count=metadata_dict["sold_count"],
            quantity_available=products_dict["quantity_available"],
            category_name=category_dict["name"]
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
                p.id AS product_id,self.db.fetch_all(final_product_query, (limit, offset))
                p.merchant_id, p.category_id, p.address_id,
                p.name, p.brand, p.price, p.original_price,
                pm.rating_avg AS ratings,
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
        if filters.get('min_rating') is not None:
            where_clauses.append("pm.rating_avg >= %s")
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
            order_clause = "ORDER BY pm.rating_avg DESC"

        # --- Pagination Logic ---
        offset = (page - 1) * per_page
        pagination_clause = "LIMIT %s OFFSET %s"

        # --- Final Query ---
        final_query = f"{base_query} {order_clause} {pagination_clause}"
        final_params = tuple(params) + (per_page, offset)

        rows = self.db.fetch_all(final_query, final_params)
        
        product_entries = [ProductEntry(**row) for row in rows] if rows else []

        return product_entries, total_products

    def get_product_entries(self, limit: int, offset: int = 0, sort_by: str | None = None) -> list[ProductEntry]:
        ### 1: Base query
        product_query = "SELECT products.id FROM products"

        ### 2: Sorting options
        if sort_by == 'price_asc':
            order_clause = "ORDER BY price ASC"
        elif sort_by == 'price_desc':   
            order_clause = "ORDER BY price DESC"
        elif sort_by == 'rating_score':
            order_clause = "ORDER BY rating_score DESC"
        elif sort_by == 'sold_count':
            order_clause = """
                JOIN product_metadata m ON products.id = m.product_id
                ORDER BY m.sold_count DESC
        """
        else:
            order_clause = ""

        ### 3: Pagination
        pagination_clause = "LIMIT %s OFFSET %s"
        final_query = f"{product_query} {order_clause} {pagination_clause}"

        ### 3.1: Fetch IDs
        rows = self.db.fetch_all(final_query, (limit, offset))

        if not rows:
            return []

        ### 4: Build ProductEntry list with comprehension
        product_entry_list = [
            entry
            for entry in (
                self.get_product_entry(row["id"]) for row in rows
            )
            if entry is not None
        ]

        return product_entry_list
    
    def get_product_entries_by_merchant_id(self, merchant_id: int) -> list[ProductEntry]:
        ### 1: Base query
        product_query = "SELECT products.id FROM products WHERE merchant_id = %s"

        ### 3.1: Fetch IDs
        rows = self.db.fetch_all(product_query, (merchant_id,))

        if not rows:
            return []

        ### 4: Build ProductEntry list with comprehension
        product_entry_list = [
            entry
            for entry in (
                self.get_product_entry(row["id"]) for row in rows
            )
            if entry is not None
        ]

        return product_entry_list
    
    def update_ratings(self, product_id: int, new_rating: float) -> bool:
        query = """
            UPDATE products
            SET rating_count = rating_count + 1,
                rating_score = rating_score + %s
            WHERE id = %s
        """
        params = (new_rating, product_id)
        self.db.execute_query(query, params)
        return True

        
