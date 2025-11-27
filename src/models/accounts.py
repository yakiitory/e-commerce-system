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
    """
    Represents a user's metadata, primarily for analytics and machine learning features.
    This directly maps to the `user_metadata` table in the database.
    """
    user_id: int
    price_sensitivity: float = 0.0
    engagement_score: float = 0.0
    recency_decay_factor: float = 1.0
    interest_vector: str | None = None  
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
