from __future__ import annotations
from .addresses import Address
from .mixins import ContactMixin, AuthMixin, DateMixin
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import override

"""
Defines the dataclasses for anything related for user models
Any list[ints] represent multiple indices of an entity in a database
"""

@dataclass
class Account(ABC, AuthMixin, DateMixin):
    id: int
    role: str

    @abstractmethod
    def permissions(self) -> list[str]:
        """Return list of permissions for this account"""
        pass
    
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
    
    @override
    def permissions(self) -> list[str]:
        return ["read"]

@dataclass
class Merchant(Account):
    store_name: str
    products: list[int]
    ratings: float
    vouchers: list[int]
    
    @override
    def permissions(self) -> list[str]:
        return ["read", "write"] 

@dataclass
class Admin(Account):
    log_ids: list[int]

    @override
    def permissions(self) -> list[str]:
        return ["read", "write", "execute"]

@dataclass
class Preferences():
    # Should have whatever settings soon
    settings: dict[str, bool]
