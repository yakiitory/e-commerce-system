from __future__ import annotations
from .addresses import Address
from .status import Status
from .mixins import DateMixin
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Product(DateMixin):
    """
    This class holds a lot of fields because we want to steal data from users,
    it could also be known as recommender algorithms :)
    """

    # Core IDs
    id: int
    sku_id: int
    name: str
    brand: str
    category_id: int

    # Metadata
    description: str
    tags: list[str] = field(default_factory=list)
    attributes: dict[str, str] = field(
        default_factory=dict
    )  # Color: black, kinda stuff
    images: list[str] = field(default_factory=list)

    # Pricing Sales
    price: float = 0.0
    original_price: float | None = None
    discount_rate: float | None = None
    stock: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0

    # Behavioural Signals
    view_count: int = 0
    sold_count: int = 0
    add_to_cart_count: int = 0
    wishlist_count: int = 0
    click_through_rate: float = 0.0

    # Contextual
    keywords: list[str] = field(
        default_factory=list
    )  # TODO: Implement NLP for Title+description
    embedding_vector: list[float] | None = None  # TODO: Sentence transformer maybe?
    popularity_score: float = 0.0  # TODO: Somehow get this

    # Vendor Logistics
    seller_id: int = 0
    warehouse_id: int | None = None

    # Personalization
    demographics_fit: dict[str, float] | None = (
        None  # This could be like "male": 0.9, "teen": 0.4
    )
    seasonal_relevance: list[str] | None = (
        None  # Something like, ["Halloween", "Easter"]
    )


@dataclass
class ProductCreate:
    """Data for creating a new product entry."""

    sku_id: int
    name: str
    brand: str
    category_id: int
    description: str

    # Optional fields
    tags: list[str] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)
    images: list[str] = field(default_factory=list)

    price: float = 0.0
    original_price: float | None = None
    stock: int = 0

    seller_id: int = 0
    warehouse_id: int | None = None


@dataclass
class Category:
    id: int
    name: str
    parent_id: int | None
    description: str = ""


@dataclass
class Inventory(DateMixin):
    id: int
    product_id: int
    quantity_available: int = 0
    quantity_reserved: int = 0
    locations: list[int] = []


@dataclass
class Shipment:
    id: int
    order_id: int
    status: Status
    estimated_date: datetime
    address: list[Address]
