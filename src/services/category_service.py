from __future__ import annotations
from typing import TYPE_CHECKING

from models.categories import ALL_CATEGORIES
from models.products import CategoryCreate

if TYPE_CHECKING:
    from repositories.category_repository import CategoryRepository


class CategoryService:
    """
    Handles business logic for managing product categories, including seeding.
    """

    def __init__(self, category_repo: CategoryRepository):
        """Initializes the CategoryService."""
        self.category_repo = category_repo

    def seed_categories(self) -> tuple[bool, str]:
        """
        Populates the database with the predefined categories from models.categories.

        This method is idempotent; it will not create duplicate categories if they
        already exist by name.

        Returns:
            A tuple containing a boolean for success and a status message.
        """
        print("[CategoryService] Starting to seed categories...")
        try:
            for main_cat_data in ALL_CATEGORIES:
                # 1. Check for or create the main category
                main_cat = self.category_repo.get_by_name(main_cat_data.name)
                if not main_cat:
                    print(f"  Creating main category: {main_cat_data.name}")
                    main_cat_create = CategoryCreate(name=main_cat_data.name, parent_id=None, description="")
                    main_cat_id, _ = self.category_repo.create(main_cat_create)
                else:
                    main_cat_id = main_cat.id

                # 2. Check for or create sub-categories
                for sub_cat_data in main_cat_data.sub_categories:
                    if not self.category_repo.get_by_name(sub_cat_data.name):
                        print(f"    Creating sub-category: {sub_cat_data.name}")
                        sub_cat_create = CategoryCreate(name=sub_cat_data.name, parent_id=main_cat_id, description="")
                        self.category_repo.create(sub_cat_create)
            
            return (True, "Category seeding completed successfully.")
        except Exception as e:
            print(f"[CategoryService ERROR] An error occurred during category seeding: {e}")
            return (False, "An error occurred during category seeding.")