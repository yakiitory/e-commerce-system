from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from repositories.account_repository import UserRepository
    from repositories.product_repository import ProductRepository, ProductMetadataRepository
    from repositories.cart_repository import CartRepository
    from repositories.review_repository import ReviewRepository
    from repositories.order_repository import OrderRepository
    from database.database import Database


class InteractionService:
    """
    Handles business logic for user interactions like carts, likes, and reviews.
    """

    def __init__(
        self,
        db: Database,
        user_repo: UserRepository,
        product_repo: ProductRepository,
        cart_repo: CartRepository,
    ):
        """Initializes the InteractionService with necessary repositories.

        Args:
            db (Database): The database instance for transaction management.
            user_repo (UserRepository): Repository for user-related data, including wishlists.
            product_repo (ProductRepository): Repository for core product data.
            cart_repo (CartRepository): Repository for managing shopping carts.
        """
        self.db = db
        self.user_repo = user_repo
        self.product_repo = product_repo
        self.cart_repo = cart_repo

    def toggle_wishlist_status(self, user_id: int, product_id: int) -> tuple[bool, str]:
        """
        Adds or removes a product from a user's wishlist.

        This operation is transactional, ensuring that both the user's wishlist
        and the product's wishlist count are updated atomically.

        Args:
            user_id (int): The ID of the user.
            product_id (int): The ID of the product to add or remove.

        Returns:
            A tuple containing a boolean for success and a status message.
        """
        if not self.product_repo.read(product_id):
            return (False, "Product not found.")

        transaction_committed = False
        try:
            self.db.begin_transaction()
            wishlist = self.user_repo.get_wishlist(user_id)
            is_in_wishlist = product_id in wishlist

            if is_in_wishlist:
                self.user_repo.remove_from_wishlist(user_id, product_id)
                self.product_repo.metadata_repo.increment_field(product_id, 'wishlist_count', -1)
                message = "Product removed from wishlist."
            else:
                self.user_repo.add_to_wishlist(user_id, product_id)
                self.product_repo.metadata_repo.increment_field(product_id, 'wishlist_count', 1)
                message = "Product added to wishlist."

            self.db.commit()
            transaction_committed = True
            return (True, message)
        finally:
            if not transaction_committed:
                self.db.rollback()

    def add_to_cart(self, user_id: int, product_id: int, quantity: int) -> tuple[bool, str]:
        """
        Adds a product to the user's shopping cart after validating stock.

        This method checks for product existence and sufficient quantity before
        delegating the core cart update logic to the CartRepository.

        Args:
            user_id (int): The ID of the user.
            product_id (int): The ID of the product to add.
            quantity (int): The number of units to add to the cart.

        Returns:
            A tuple containing a boolean for success and a status message.
        """
        if quantity <= 0:
            return (False, "Quantity must be positive.")

        # 1. Validate product and stock
        product = self.product_repo.read(product_id)

        if not product:
            return (False, "Product not found.")
        # 2. Delegate to the cart repository to handle the complex logic
        # of finding the cart, and adding/updating the item within a transaction.
        success, message = self.cart_repo.add_or_update_item(
            user_id=user_id, product_id=product_id, quantity=quantity, price=product.price
        )

        return (success, message)
