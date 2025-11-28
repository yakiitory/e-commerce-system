from __future__ import annotations
from typing import override, TYPE_CHECKING

from repositories.base_repository import BaseRepository
from models.products import Category, CategoryCreate

if TYPE_CHECKING:
    from database.database import Database


class CategoryRepository(BaseRepository):
    """
    Handles database operations for product categories.
    """

    def __init__(self, db: Database):
        self.db = db
        self.table_name = "categories"

    @override
    def create(self, data: CategoryCreate) -> tuple[int | None, str]:
        """Creates a new category record."""
        fields = ["name", "parent_id", "description"]
        return self._create_record(data, fields, self.table_name, self.db)

    def get_by_name(self, name: str) -> Category | None:
        """Retrieves a category by its name."""
        query = f"SELECT * FROM {self.table_name} WHERE name = %s"
        row = self.db.fetch_one(query, (name,))
        return Category(**row) if row else None

    # The following methods are not used for seeding but are included for completeness.
    @override
    def read(self, identifier: int):
        """Reads a category by its ID."""
        return self._id_to_dataclass(
            identifier, self.table_name, self.db, lambda row: Category(**row) if row else None
        )

    @override
    def update(self, identifier: int, data):
        raise NotImplementedError("Category updates are not implemented.")

    @override
    def delete(self, identifier: int):
        raise NotImplementedError("Category deletion is not implemented.")