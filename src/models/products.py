from __future__ import annotations
from .addresses import Address
from .status import Status
from .mixins import DateMixin
from datetime import datetime
from dataclasses import dataclass, field, KW_ONLY


@dataclass
class ProductCreate:
    """Data for creating a new product entry."""

    name: str
    merchant_id: int
    brand: str
    category_id: int
    description: str
    address_id: int

    images: list[str] = field(default_factory=list)

    price: float = 0.0
    original_price: float = 0.0
    discount_rate: float = 0.0
    quantity_available: int = 0

@dataclass
class Product(ProductCreate):
    id: int = 0

@dataclass
class ProductEntry:
    """
    For usage with the front end, such as a for you page entry.
    Does not exist as a database entry.
    """
    product_id: int
    merchant_id: int
    category_id: int
    address_id: int
    name: str
    brand: str
    price: float
    original_price: float
    ratings: float
    warehouse: str
    thumbnail: str
    sold_count: int
    _: KW_ONLY
    category_name: str | None = None
    city: str | None = None

@dataclass
class ProductMetadata:
    product_id: int
    view_count: int = 0
    sold_count: int = 0
    add_to_cart_count: int = 0
    wishlist_count: int = 0
    click_through_rate: float = 0
    rating_avg: float = 0
    rating_count: int = 0
    popularity_score: float = 0
    demographics_fit: dict[str, float] = field(default_factory=dict)
    seasonal_relevance: list[str] = field(default_factory=list)
    embedding_vector: list[float] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

@dataclass
class CategoryCreate:
    name: str
    parent_id: int | None
    description: str

@dataclass
class Category(CategoryCreate):
    id: int

@dataclass
class Shipment:
    """
    Represents a shipment record retrieved from the database.
    The 'addresses' field is populated by joining with the 'addresses' table
    via the 'shipment_addresses' junction table.
    """
    id: int
    order_id: int
    status: Status
    estimated_date: datetime | None
    addresses: dict[str, int]

@dataclass
class ShipmentCreate:
    order_id: int
    addresses: dict[str, int]
    status: Status = Status.SHIPPED
    estimated_date: datetime | None = None
