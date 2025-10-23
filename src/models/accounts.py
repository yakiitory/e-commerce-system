from __future__ import annotations
from .mixins import ContactMixin, AuthMixin, DateMixin
from dataclasses import dataclass, field

"""
Defines the dataclasses for anything related for user models
Any list[ints] represent multiple indices of an entity in a database
"""


@dataclass
class Account(AuthMixin, DateMixin):
    id: int
    role: str


@dataclass
class User(Account, ContactMixin):
    gender: str
    age: int


@dataclass
class UserCreate(AuthMixin, ContactMixin):
    gender: str
    age: int


@dataclass
class UserMetadata:
    id: int
    user_id: int
    # basic persistent collections
    addresses: tuple[int, ...] = field(default_factory=tuple)
    order_history: tuple[int, ...] = field(default_factory=tuple)
    view_history: tuple[int, ...] = field(default_factory=tuple)
    liked_products: tuple[int, ...] = field(default_factory=tuple)
    reviews: tuple[int, ...] = field(default_factory=tuple)
    voucher_inventory: tuple[int, ...] = field(default_factory=tuple)

    # recommender / analytic fields
    favorite_categories: tuple[int, ...] = field(default_factory=tuple)
    favorite_brands: tuple[str, ...] = field(default_factory=tuple)
    price_sensitivity: float = 0.0
    engagement_score: float = 0.0
    recency_decay_factor: float = 1.0

    # context & demographics
    gender: str | None = None

    # ML features
    interest_vector: tuple[float, ...] | None = None
    segment_label: str | None = None
    churn_risk_score: float = 0.0


@dataclass
class Merchant(Account, ContactMixin):
    store_name: str


@dataclass
class MerchantCreate(AuthMixin, ContactMixin):
    store_name: str


@dataclass
class MerchantMetadata:
    products: tuple[int, ...]
    ratings: float
    vouchers: tuple[int, ...]
    addresses: tuple[int, ...]
    inventories: tuple[int, ...]


@dataclass
class Admin(Account):
    pass


@dataclass
class AdminCreate(AuthMixin):
    role: str


@dataclass
class Preferences:
    # Should have whatever settings soon
    settings: dict[str, bool]
