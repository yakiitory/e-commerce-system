from __future__ import annotations
from typing import override, Any, TYPE_CHECKING

from repositories.base_repository import BaseRepository
from models.images import Image, ImageCreate

if TYPE_CHECKING:
    from database.database import Database


class ImageRepository(BaseRepository):
    """
    Handles database operations for images.
    """

    def __init__(self, db: Database):
        """Initializes the ImageRepository."""
        self.db = db
        self.table_name = "images"

    @override
    def create(self, data: ImageCreate) -> tuple[int | None, str]:
        """
        Creates a new image record in the database.

        Args:
            data (ImageCreate): The ImageCreate object with the URL.

        Returns:
            A tuple containing the new image ID and a status message.
        """
        fields = ["url"]
        return self._create_record(data, fields, self.table_name, self.db)

    @override
    def read(self, identifier: int) -> Image | None:
        """Reads an image record by its ID."""
        return self._id_to_dataclass(
            identifier, self.table_name, self.db, lambda row: Image(**row) if row else None
        )

    @override
    def update(self, identifier: int, data: dict[str, Any]) -> bool:
        """Updates an image's URL."""
        allowed_fields = ["url"]
        return self._update_by_id(identifier, data, self.table_name, self.db, allowed_fields)

    @override
    def delete(self, identifier: int) -> tuple[bool, str]:
        """Deletes an image record by its ID."""
        return self._delete_by_id(identifier, self.table_name, self.db)
