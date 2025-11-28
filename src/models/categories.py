from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SubCategory:
    """Represents an immutable sub-category."""
    name: str


@dataclass(frozen=True)
class MainCategory:
    """Represents an immutable main category with its sub-categories."""
    name: str
    sub_categories: Tuple[SubCategory, ...]


ALL_CATEGORIES: Tuple[MainCategory, ...] = (
    MainCategory(
        name="Beauty and Personal Care",
        sub_categories=(
            SubCategory(name="Bath & Body"),
            SubCategory(name="Fragrances"),
            SubCategory(name="Haircare"),
            SubCategory(name="Makeup"),
            SubCategory(name="Skincare"),
        ),
    ),
    MainCategory(
        name="Electronics",
        sub_categories=(
            SubCategory(name="Audio & Headphones"),
            SubCategory(name="Cameras & Photography"),
            SubCategory(name="Laptops & Computers"),
            SubCategory(name="Smartphones"),
            SubCategory(name="Wearable Technology"),
        ),
    ),
    MainCategory(
        name="Fashion and Apparel",
        sub_categories=(
            SubCategory(name="Accessories (Bags, Belts, Jewelry)"),
            SubCategory(name="Kids’ Clothing"),
            SubCategory(name="Men’s Clothing"),
            SubCategory(name="Shoes"),
            SubCategory(name="Women’s Clothing"),
        ),
    ),
)
