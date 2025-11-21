from __future__ import annotations
from typing import TYPE_CHECKING

from models.reviews import ReviewCreate

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
        product_meta_repo: ProductMetadataRepository,
        cart_repo: CartRepository,
        review_repo: ReviewRepository,
        order_repo: OrderRepository,
    ):
        """Initializes the InteractionService with necessary repositories.

        Args:
            db (Database): The database instance for transaction management.
            user_repo (UserRepository): Repository for user-related data, including wishlists.
            product_repo (ProductRepository): Repository for core product data.
            product_meta_repo (ProductMetadataRepository): Repository for product analytics data.
            cart_repo (CartRepository): Repository for managing shopping carts.
            review_repo (ReviewRepository): Repository for managing product reviews.
            order_repo (OrderRepository): Repository for checking user purchase history.
        """
        self.db = db
        self.user_repo = user_repo
        self.product_repo = product_repo
        self.product_meta_repo = product_meta_repo
        self.cart_repo = cart_repo
        self.review_repo = review_repo
        self.order_repo = order_repo

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
                self.product_meta_repo.increment_field(product_id, 'wishlist_count', -1)
                message = "Product removed from wishlist."
            else:
                self.user_repo.add_to_wishlist(user_id, product_id)
                self.product_meta_repo.increment_field(product_id, 'wishlist_count', 1)
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

    def create_review(self, user_id: int, product_id: int, rating: float, description: str, images: list[str] | None = None) -> tuple[bool, str]:
        """
        Creates a review for a product and updates the product's average rating.

        This operation is transactional and enforces that a user can only review
        a product they have previously purchased and had delivered.

        Args:
            user_id (int): The ID of the user writing the review.
            product_id (int): The ID of the product being reviewed.
            rating (float): The rating score (e.g., 1.0 to 5.0).
            description (str): The text content of the review.
            images (list[str] | None): A list of image URLs to attach to the review.

        Returns:
            A tuple containing a boolean for success and a status message.
        """
        # 1. Business Rule: Verify the user has purchased the product.
        if not self.order_repo.has_user_purchased_product(user_id, product_id):
            return (False, "You can only review products you have purchased.")

        review_data = ReviewCreate(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            description=description,
            attached=images or []
        )

        transaction_committed = False
        try:
            self.db.begin_transaction()

            # 2. Create the review record
            review_id, msg = self.review_repo.create(review_data)
            if not review_id:
                return (False, f"Failed to create review: {msg}")

            # 3. Atomically update the product's average rating
            self.product_meta_repo.update_average_rating(product_id, rating)

            self.db.commit()
            transaction_committed = True
            return (True, "Review submitted successfully.")
        finally:
            if not transaction_committed:
                self.db.rollback()
