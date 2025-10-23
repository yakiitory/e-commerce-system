from typing import override
from controllers.base_controller import BaseController
from types import SimpleNamespace
from database.database import Database
from models.products import ProductCreate, ProductMetadata, Product


class ProductController(BaseController):
    def __init__(self, db: Database):
        self.db = db
        self.table_name = "products"

    @override
    def create(self, data: ProductCreate, metadata: ProductMetadata) -> tuple[bool, str]:
        """Creates a new product.

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

        # Handle image creation and linking
        if data.images:
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

                # Link in 'product_images' junction table
                link_data = SimpleNamespace(product_id=new_product_id, image_id=image_id)
                link_id, link_msg = self._create_record(link_data, ['product_id', 'image_id'], 'product_images', self.db)
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
        """Reads a product record by ID.

        Args:
            identifier (int): The ID of the product to retrieve.

        Returns:
            Product | None: The Product object if found, otherwise `None`.
        """
        return self._id_to_dataclass(identifier=identifier, table_name=self.table_name, db=self.db, map_func=self._map_to_product)


    @override
    def update(self, identifier: int, data: ProductCreate) -> bool:
        """Updates an existing product record.

        Args:
            identifier (int): The ID of the product to update.
            data (ProductCreate): (Assuming) A newly created ProductCreate object that will replace the fields of the existing record.

        Returns:
            bool: `True` if the update was successful, `False` otherwise.
        """
        allowed_fields = [
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
        return self._update_by_id(
            identifier=identifier, data=data, table_name=self.table_name, db=self.db, allowed_fields=allowed_fields
        )

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """Deletes an existing product record by ID

        Args:
            identifier (int): The ID of the product to delete.

        Returns:
            tuple[bool, str]: A tuple indicating success/failure and a message.
        """
        return self._delete_by_id(identifier, table_name=self.table_name, db=self.db, id_field="id")
    
    def _map_to_product(self, row: dict) -> Product | None:
        """Maps a database row (dictionary) to a Product dataclass object.

        Args:
            row (dict): A dictionary representing a row from the 'products' table.

        Returns:
            Product | None: A Product object if the row is not empty, otherwise `None`.
        """
        if not row:
            return None
        return Product(**row)
