from typing import override
from types import SimpleNamespace
from models.products import ProductCreate, Product, ProductMetadata, ProductEntry
from repositories.base_repository import BaseRepository
from database.database import Database

class ProductRepository(BaseRepository):
    def __init__(self, db: Database):
        self.db = db
        self.table_name = "products"
        self.metadata_table_name = "product_metadata"

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
        metadata_fields = [
            "view_count",
            "sold_count",
            "add_to_cart_count",
            "wishlist_count",
            "click_through_rate",
            "rating_avg",
            "rating_count",
            "popularity_score",
            "demographics_fit",
            "seasonal_relevance",
            "embedding_vector",
            "keywords",
        ]

        # Create the product record
        new_product_id, message = self._create_record(
            data=data,
            fields=fields,
            table_name=self.table_name,
            db=self.db
        )

        if not new_product_id:
            return (False, message) # Return failure message from _create_record
        
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
                    return (False, f"Product created, but failed to save image: {img_msg}")
                
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
                    return (False, f"Product and image created, but failed to link them: {link_msg}")
                
        if metadata:
            new_metadata_id, metadata_msg = self._create_record(
                data=metadata,
                fields=metadata_fields,
                table_name='product_metadata',
                db=self.db
            )
            if not new_metadata_id:
                return (False, f"Product created, but failed to save metadata: {metadata_msg}")

        # Return success message
        return (True, f"Product '{data.name}' created successfully with ID {new_product_id}.")

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
    def update(self, identifier: int, data: ProductCreate, metadata: ProductMetadata) -> bool:
        """
        Updates an existing product record.
        
        Args:
            identifier (int): The ID of the product to update.
            data (ProductCreate): (Assuming) A newly created ProductCreate object
                that will replace the fields of the existing record.
            metadata (ProductMetadata): (Assuming) Edited tags of the product 
                that will replace the existing tags of the existing record.

        Returns:
            bool: `True` if the update was successful, `False` otherwise.
        """
        product_fields = [
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

        metadata_fields = [
            "view_count",
            "sold_count",
            "add_to_cart_count",
            "wishlist_count",
            "click_through_rate",
            "rating_avg",
            "rating_count",
            "popularity_score",
            "demographics_fit",
            "seasonal_relevance",
            "embedding_vector",
            "keywords",
        ]       

        # Update the product record
        product_id = self._update_by_id(
            identifier=identifier, data=data, table_name=self.table_name, db=self.db, allowed_fields=product_fields
        )
        if not product_id:
            return False 
        
        # Update the product metadata
        metadata_id = self._update_by_id(
            identifier=identifier, data=metadata, table_name=self.metadata_table_name, db=self.db, allowed_fields=metadata_fields
        )
        if not metadata_id:
            return False

        # Finally, 
        return True

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """
        Deletes an existing product record by ID.

        Args:
            identifier (int): The ID of the product to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        return self._delete_by_id(identifier, table_name=self.table_name, db=self.db, id_field="id")
    
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
            SELECT id, merchant_id, category, id, name, brand, price, original_price, address_id 
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
            name=products_dict["name"],
            brand=products_dict["brand"],
            price=products_dict["price"],
            original_price=products_dict["original_price"],
            ratings=metadata_dict["rating_avg"],
            warehouse=address_dict["city"],
            thumbnail=image_dict["url"],
            sold_count=metadata_dict["sold_count"]
        )


        

