from __future__ import annotations
from typing import override, Any, TYPE_CHECKING

from repositories.base_repository import BaseRepository
from models.reviews import Review, ReviewCreate

if TYPE_CHECKING:
    from database.database import Database


class ReviewRepository(BaseRepository):
    """
    Handles database operations for product reviews.
    """

    def __init__(self, db: Database):
        """Initializes the ReviewRepository."""
        self.db = db
        self.table_name = "reviews"

    @override
    def create(self, data: ReviewCreate) -> tuple[int | None, str]:
        """
        Creates a new review.

        Args:
            data (ReviewCreate): The data for the new review.

        Returns:
            tuple[int | None, str]: A tuple with the new review ID and a message.
        """
        review_fields = ["user_id", "product_id", "rating", "description"]
        return self._create_record(data, review_fields, self.table_name, self.db)

    @override
    def read(self, identifier: int) -> Review | None:
        """
        Reads a review by its ID.

        Args:
            identifier (int): The ID of the review to retrieve.

        Returns:
            Review | None: The Review object if found, otherwise None.
        """
        return self._id_to_dataclass(
            identifier, self.table_name, self.db, lambda row: Review(**row) if row else None
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """
        Updates an existing review record.

        Args:
            identifier (int): The ID of the review to update.
            data (dict[str, Any]): A dictionary of fields to update.

        Returns:
            bool: True if successful, False otherwise.
        """
        allowed_fields = ["rating", "description"]
        return self._update_by_id(identifier, data, self.table_name, self.db, allowed_fields)

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """
        Deletes a review by its ID. Associated image links are deleted by the database cascade.
        """
        return self._delete_by_id(identifier, self.table_name, self.db)

    def get_reviews_for_product(self, product_id: int) -> list[Review]:
        """
        Retrieves all reviews for a specific product, ordered by most recent.

        Args:
            product_id (int): The ID of the product.

        Returns:
            list[Review]: A list of Review objects.
        """
        review_ids_query = f"SELECT id FROM {self.table_name} WHERE product_id = %s ORDER BY created_at DESC"
        review_id_rows = self.db.fetch_all(review_ids_query, (product_id,))
        if not review_id_rows:
            return []

        return [review for row in review_id_rows if (review := self.read(row['id'])) is not None]
