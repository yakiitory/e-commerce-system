from __future__ import annotations
from .addresses import Address
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Product():
    id: str
    sku_id: str
    name: str
    description: str
    brand: str
    category_id: int
    price: float
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

@dataclass
class Category():
    id: int
    name: str
    parent_id: Optional[int] = None
    description: str = "" 

@dataclass
class Inventory():
    id: int
    product_id: int
    quantity_available: int = 0
    quantity_reserved: int = 0
    locations: list[Address] = []
    updated_at: datetime = datetime.now()
