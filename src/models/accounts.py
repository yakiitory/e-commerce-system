from __future__ import annotations
from .addresses import Address
from .mixins import ContactMixin, AuthMixin, DateMixin
from dataclasses import dataclass

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
    addresses: list[Address]
    order_history: list[int]
    view_history: list[int]
    liked_products: list[int]
    reviews: list[int]
    voucher_inventory: list[int]
    cart_id: int
    preferences: "Preferences"


@dataclass
class Merchant(Account, ContactMixin):
    store_name: str
    products: list[int]
    ratings: float
    vouchers: list[int]


@dataclass
class Admin(Account):
    log_ids: list[int]


@dataclass
class Preferences():
    # Should have whatever settings soon
    settings: dict[str, bool]
