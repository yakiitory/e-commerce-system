from __future__ import annotations
from typing import TYPE_CHECKING, Any

from models.reviews import Review, ReviewCreate

if TYPE_CHECKING:
    from repositories.review_repository import ReviewRepository
    from repositories.order_repository import OrderRepository
    from repositories.metadata_repository import ProductMetadataRepository
    from database.database import Database


class ReviewService:
    """
    Handles the business logic for managing product reviews.
    """

    def __init__(
        self,
        db: Database,
        review_repo: ReviewRepository,
        order_repo: OrderRepository,
        product_meta_repo: ProductMetadataRepository,
    ):
        """
        Initializes the ReviewService.

        Args:
            db (Database): The database instance for transaction management.
            review_repo (ReviewRepository): Repository for review data.
            order_repo (OrderRepository): Repository to verify user purchases.
            product_meta_repo (ProductMetadataRepository): Repository to update product ratings.
        """
        self.db = db
        self.review_repo = review_repo
        self.order_repo = order_repo
        self.product_meta_repo = product_meta_repo

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
            ratings=rating,
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
        except Exception as e:
            print(f"[ReviewService ERROR] An unexpected error occurred during review creation: {e}")
            return (False, "An unexpected error occurred during review creation.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def get_reviews_for_product(self, product_id: int) -> tuple[bool, str | list[Review]]:
        """
        Retrieves all reviews for a specific product.

        Args:
            product_id (int): The ID of the product.

        Returns:
            tuple[bool, str | list[Review]]: A tuple containing success status and the list of reviews or an error message.
        """
        try:
            reviews = self.review_repo.read_all_by_product_id(product_id)
            return (True, reviews)
        except Exception as e:
            print(f"[ReviewService ERROR] Failed to fetch reviews for product {product_id}: {e}")
            return (False, "An unexpected error occurred while fetching reviews.")
