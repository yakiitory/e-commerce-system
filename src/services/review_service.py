from __future__ import annotations
from typing import TYPE_CHECKING

from models.reviews import Review, ReviewCreate

if TYPE_CHECKING:
    from repositories.review_repository import ReviewRepository
    from repositories.order_repository import OrderRepository
    from repositories.product_repository import ProductRepository
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
        product_repo: ProductRepository,
    ):
        """
        Initializes the ReviewService.

        Args:
            db (Database): The database instance for transaction management.
            review_repo (ReviewRepository): Repository for review data.
            order_repo (OrderRepository): Repository to verify user purchases.
            media_service (MediaService): Service for handling media files.
            product_repo (ProductRepository): Repository to update product ratings.
        """
        self.db = db
        self.review_repo = review_repo
        self.order_repo = order_repo
        self.product_repo = product_repo

    def create_review(
        self, user_id: int, product_id: int, rating: float, description: str
    ) -> tuple[bool, str]:
        """
        Creates a new review after validating user's purchase and ensuring they haven't
        already reviewed the product. This is a transactional operation.

        Args:
            user_id (int): The ID of the user submitting the review.
            product_id (int): The ID of the product being reviewed.
            rating (float): The rating score (e.g., 1.0 to 5.0).
            description (str): The text content of the review.

        Returns:
            tuple[bool, str]: A tuple indicating success and a message.
        """
        # 1. Validate that the user has purchased the product and it's delivered.
        if not self.order_repo.has_user_purchased_product(user_id, product_id):
            return (False, "You can only review products you have purchased and received.")

        # 2. Check if the user has already reviewed this product.
        existing_reviews = self.review_repo.get_reviews_for_product(product_id)
        if any(review.user_id == user_id for review in existing_reviews):
            return (False, "You have already submitted a review for this product.")

        # 3. Validate rating
        if not (1.0 <= rating <= 5.0):
            return (False, "Rating must be between 1 and 5.")

        review_create = ReviewCreate(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            description=description,
        )

        transaction_committed = False
        try:
            self.db.begin_transaction()

            # 4. Create the review record.
            new_review_id, message = self.review_repo.create(review_create)
            if not new_review_id:
                return (False, message)

            # 5. Update the product's rating score.
            update_success = self.product_repo.update_ratings(product_id, rating)
            if not update_success:
                raise Exception("Failed to update product's rating.")

            self.db.commit()
            transaction_committed = True
            return (True, "Review submitted successfully.")

        except Exception as e:
            print(f"[ReviewService ERROR] Review creation failed: {e}")
            return (False, "An unexpected error occurred while submitting your review.")
        finally:
            if not transaction_committed:
                self.db.rollback()

    def get_reviews_for_product(self, product_id: int) -> tuple[bool, list[Review] | None]:
        """
        Retrieves all reviews for a specific product.

        Args:
            product_id (int): The ID of the product.

        Returns:
            A tuple containing success status, and either a list of Review objects or None.
        """
        try:
            reviews = self.review_repo.get_reviews_for_product(product_id)
            return (True, reviews)
        except Exception as e:
            print(f"[ReviewService ERROR] Failed to get reviews for product {product_id}: {e}")
            return (False, None)