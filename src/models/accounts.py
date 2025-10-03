from .addresses import Address
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime

@dataclass
class Account(ABC):
    id: int
    username: str
    email: str
    hash: str
    role: str
    is_active: bool 
    date_created: datetime
    last_login: datetime | None

    @abstractmethod
    def permissions(self) -> list[str]:
        """Return list of permissions for this account"""
        pass
    
@dataclass
class User(Account):
    first_name: str
    last_name: str
    phone_number: str
    addresses: list["Address"]
    order_history: list[int]
    cart_id: int
    wishlist: list[int]
    preferences: dict

    def permissions(self) -> list[str]:
        return ["read"]

@dataclass
class Merchant(Account):
    store_name: str
    products: list[int]
    ratings: float
    
    def permissions(self) -> list[str]:
        return ["read", "write"] 

@dataclass
class Admin(Account):
    log_ids: list[int]

    def permissions(self) -> list[str]:
        return ["read", "write", "execute"]

