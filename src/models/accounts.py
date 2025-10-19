from __future__ import annotations
from .addresses import Address
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
    preferences: "Preferences" 
    card_id: int
    # basic persistent collections
    addresses: list[int] = field(default_factory=list)
    order_history: list[int] = field(default_factory=list)
    view_history: list[int] = field(default_factory=list)
    liked_products: list[int] = field(default_factory=list)
    reviews: list[int] = field(default_factory=list)
    voucher_inventory: list[int] = field(default_factory=list)
    cart_id: int | None = None


    # recommender / analytic fields
    favorite_categories: list[int] = field(default_factory=list)
    favorite_brands: list[str] = field(default_factory=list)
    price_sensitivity: float = 0.5
    engagement_score: float = 0.0
    recency_decay_factor: float = 1.0

    # context & demographics
    age_group: str | None = None
    gender: str | None = None

    # ML features
    interest_vector: list[float] | None = None
    segment_label: str | None = None
    churn_risk_score: float = 0.0


@dataclass
class Merchant(Account, ContactMixin):
    card_id: int
    store_name: str
    products: list[int]
    ratings: float
    vouchers: list[int]
    addresses: list[int]
    inventories: list[int]


@dataclass
class Admin(Account):
    log_ids: list[int]


@dataclass
class Preferences():
    # Should have whatever settings soon
    settings: dict[str, bool]
