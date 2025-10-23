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
        # This will eventually use a _read_by_id method from BaseController
        raise NotImplementedError("Product read logic is not yet implemented.")


    @override
    def update(self, identifier, data):
        return 
    
    @override
    def delete(self, identifier):
        raise NotImplementedError("Product delete logic is not yet implemented.")