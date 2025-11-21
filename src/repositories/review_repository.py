from __future__ import annotations
from typing import override, Any, TYPE_CHECKING
from types import SimpleNamespace

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
        Creates a new review and links any attached images.

        Args:
            data (ReviewCreate): The review data, including a list of image URLs.

        Returns:
            A tuple containing the new review ID and a status message.
        """
        review_fields = ["user_id", "product_id", "ratings", "description"]

        review_data_for_db = SimpleNamespace(
            user_id=data.user_id,
            product_id=data.product_id,
            ratings=data.rating,
            description=data.description
        )

        new_review_id, message = self._create_record(review_data_for_db, review_fields, self.table_name, self.db)

        if not new_review_id:
            return (None, message)

        # Handle image linking
        if data.attached:
            for image_url in data.attached:
                # 1. Create image record
                image_id, img_msg = self._create_record(
                    SimpleNamespace(url=image_url), ['url'], 'images', self.db
                )
                if not image_id:
                    # Log the error but don't fail the whole review creation
                    print(f"[ReviewRepository WARN] Failed to save image URL '{image_url}': {img_msg}")
                    continue

                # 2. Link image to review
                link_data = SimpleNamespace(review_id=new_review_id, image_id=image_id)
                self._create_record(link_data, ['review_id', 'image_id'], 'review_images', self.db)

        return (new_review_id, f"Review created successfully with ID {new_review_id}.")

    @override
    def read(self, identifier: int) -> Review | None:
        """Reads a review by its ID."""
        return self._id_to_dataclass(
            identifier, self.table_name, self.db, lambda row: Review(**row) if row else None
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """Updates a review's description or likes."""
        allowed_fields = ["description", "likes"]
        return self._update_by_id(identifier, data, self.table_name, self.db, allowed_fields)

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """Deletes a review by its ID."""
        return self._delete_by_id(identifier, self.table_name, self.db)