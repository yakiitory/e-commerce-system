from __future__ import annotations
from typing import TYPE_CHECKING

from models.orders import CartItem, Cart
from repositories.base_repository import BaseRepository

if TYPE_CHECKING:
    from database.database import Database
    from repositories.product_repository import ProductMetadataRepository
    


class CartRepository(BaseRepository):
    """Repository for managing shopping carts and their contents in the database.

    This class provides methods to create carts, add/update items in a cart,
    and handles the transactional integrity of these operations.
    """

    def __init__(self, db: Database, product_meta_repo: ProductMetadataRepository):
        """Initializes the CartRepository.

        Args:
            db: An instance of the Database class for database interactions.
            product_meta_repo: An instance of ProductMetadataRepository for product metadata.
        """
        self.db = db
        self.product_meta_repo = product_meta_repo

    def get_or_create_active_cart_id(self, user_id: int) -> int | None:
        """Retrieves the ID of a user's active cart, creating one if it doesn't exist.

        This method is designed to be called within a database transaction to ensure
        atomicity when creating a new cart.

        Args:
            user_id: The ID of the user whose cart is to be retrieved or created.

        Returns:
            The ID of the user's active cart, or None if creation fails.
        """
        # Find existing cart
        cart = self.db.fetch_one("SELECT id FROM carts WHERE user_id = %s", (user_id,))
        if cart:
            return cart['id']

        # Create a new cart if one doesn't exist
        new_cart_id = self.db.execute_query("INSERT INTO carts (user_id) VALUES (%s)", (user_id,))
        return new_cart_id

    def add_or_update_item(self, user_id: int, product_id: int, quantity: int, price: float) -> tuple[bool, str]:
        """Adds a product to the cart or updates its quantity if it already exists.

        This entire operation is wrapped in a transaction to ensure atomicity. If the
        product is already in the cart, its quantity is updated. Otherwise, a new
        item is created and linked to the user's cart.

        Args:
            user_id: The ID of the user.
            product_id: The ID of the product to add.
            quantity: The quantity of the product to add.
            price: The current price of the product.

        Returns:
            A tuple containing a boolean indicating success and a string message.
        """
        transaction_committed = False
        try:
            self.db.begin_transaction()

            # 1. Get the user's cart ID
            cart_id = self.get_or_create_active_cart_id(user_id)
            if not cart_id:
                return (False, "Could not find or create a cart for the user.")

            # 2. Check if an item for this product already exists in the cart
            find_item_query = """
                SELECT i.id, i.product_quantity
                FROM items i
                JOIN cart_items ci ON i.id = ci.item_id
                WHERE ci.cart_id = %s AND i.product_id = %s
            """
            existing_item = self.db.fetch_one(find_item_query, (cart_id, product_id))

            if existing_item:
                # --- Case 1: Item exists. Update its quantity and total price. ---
                item_id = existing_item['id']
                new_quantity = existing_item['product_quantity'] + quantity
                new_total_price = new_quantity * price

                update_query = """
                    UPDATE items
                    SET product_quantity = %s, total_price = %s
                    WHERE id = %s
                """
                self.db.execute_query(update_query, (new_quantity, new_total_price, item_id))
                message = f"Updated quantity in cart."

            else:
                # --- Case 2: Item does not exist. Create a new item and link it to the cart. ---
                total_price = quantity * price
                insert_item_query = """
                    INSERT INTO items (product_id, product_quantity, product_price, total_price, applied_discounts)
                    VALUES (%s, %s, %s, %s, 0)
                """
                new_item_id = self.db.execute_query(insert_item_query, (product_id, quantity, price, total_price))

                if not new_item_id:
                    # If item creation fails, we can't proceed.
                    self.db.rollback()
                    return (False, "Failed to create a new item for the cart.")

                # Link the new item to the cart
                self.db.execute_query(
                    "INSERT INTO cart_items (cart_id, item_id) VALUES (%s, %s)",
                    (cart_id, new_item_id)
                )
                message = f"Product added to cart."

            # Step 3: Commit the transaction to make all changes permanent.
            self.db.commit()
            transaction_committed = True
            return (True, message)

        except Exception as e:
            print(f"[CartRepository ERROR] Failed to add/update item: {e}")
            return (False, "An internal error occurred while updating the cart.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def get_cart(self, user_id: int) -> Cart | None:
        cart_id = self.get_or_create_active_cart_id(user_id)
        if not cart_id:
            return None
        cart_items = self.get_cart_contents(user_id)
        user_cart = Cart(id=cart_id, user_id=user_id, items=cart_items)
        return user_cart
    def get_cart_contents(self, user_id: int) -> list[CartItem]:
        """
        Retrieves all items in a user's cart, enriched with product details.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of CartItem objects with additional product info.
        """
        query = """
            SELECT
                i.id,
                i.product_id,
                i.product_quantity as quantity,
                i.product_price as price,
                i.total_price,
                p.name as product_name,
                p.brand as product_brand,
                img.url as thumbnail_url
            FROM items i
            JOIN cart_items ci ON i.id = ci.item_id
            JOIN carts c ON ci.cart_id = c.id
            JOIN products p ON i.product_id = p.id
            LEFT JOIN (
                SELECT pi.product_id, im.url
                FROM product_images pi
                JOIN images im ON pi.image_id = im.id
                WHERE pi.is_thumbnail = TRUE
            ) AS img ON p.id = img.product_id
            WHERE c.user_id = %s
        """
        rows = self.db.fetch_all(query, (user_id,))
        return [CartItem(**row) for row in rows] if rows else []

    def update_item_quantity(self, user_id: int, item_id: int, quantity: int) -> tuple[bool, str]:
        """
        Updates the quantity of an item in the user's cart. Deletes if quantity is 0.
        """
        if quantity < 0:
            return (False, "Quantity cannot be negative.")
        if quantity == 0:
            return self.remove_item(user_id, item_id)

        transaction_committed = False
        try:
            self.db.begin_transaction()
            # Verify item belongs to user's cart and get price
            item_query = """
                SELECT i.product_price FROM items i
                JOIN cart_items ci ON i.id = ci.item_id
                JOIN carts c ON ci.cart_id = c.id
                WHERE i.id = %s AND c.user_id = %s
            """
            item_row = self.db.fetch_one(item_query, (item_id, user_id))
            if not item_row:
                return (False, "Item not found in your cart.")

            price = item_row['product_price']
            new_total_price = quantity * price

            update_query = "UPDATE items SET product_quantity = %s, total_price = %s WHERE id = %s"
            self.db.execute_query(update_query, (quantity, new_total_price, item_id))

            self.db.commit()
            transaction_committed = True
            return (True, "Cart updated successfully.")
        except Exception as e:
            print(f"[CartRepository ERROR] Failed to update item quantity: {e}")
            return (False, "An internal error occurred while updating the cart.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def remove_item(self, user_id: int, item_id: int) -> tuple[bool, str]:
        """Removes an item completely from the user's cart."""
        transaction_committed = False
        try:
            self.db.begin_transaction()
            # Verify item belongs to user's cart before deleting
            delete_query = """
                DELETE i FROM items i
                JOIN cart_items ci ON i.id = ci.item_id
                JOIN carts c ON ci.cart_id = c.id
                WHERE i.id = %s AND c.user_id = %s
            """
            affected_rows = self.db.execute_query(delete_query, (item_id, user_id))
            self.db.commit()
            transaction_committed = True
            return (True, "Item removed from cart.") if affected_rows > 0 else (False, "Item not found in your cart.")
        except Exception as e:
            print(f"[CartRepository ERROR] Failed to remove item: {e}")
            return (False, "An internal error occurred while removing the item.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def clear_cart(self, user_id: int) -> tuple[bool, str]:
        """
        Removes all items from a user's cart. This is typically called after a successful checkout.
        """
        transaction_committed = False
        try:
            self.db.begin_transaction()
            # This query deletes from the 'items' table, and the ON DELETE CASCADE
            # on 'cart_items' will automatically remove the linking records.
            delete_query = """
                DELETE i FROM items i
                JOIN cart_items ci ON i.id = ci.item_id
                JOIN carts c ON ci.cart_id = c.id
                WHERE c.user_id = %s
            """
            self.db.execute_query(delete_query, (user_id,))
            self.db.commit()
            transaction_committed = True
            return (True, "Cart cleared successfully.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def create(self, data):
        """Not implemented. Use 'add_or_update_item' to manage cart contents."""
        raise NotImplementedError("CartRepository does not implement a direct 'create' method. Use 'add_or_update_item'.")

    def read(self, identifier):
        """Not implemented. Specific query methods should be used instead."""
        raise NotImplementedError("CartRepository does not implement a direct 'read' method.")

    def update(self, identifier, data):
        """Not implemented. Use 'add_or_update_item' to manage cart contents."""
        raise NotImplementedError("CartRepository does not implement a direct 'update' method. Use 'add_or_update_item'.")

    def delete(self, identifier):
        """Not implemented. Specific deletion methods should be created if needed."""
        raise NotImplementedError("CartRepository does not implement a direct 'delete' method.")