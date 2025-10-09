from __future__ import annotations
from .addresses import Address
from .status import Status
from .mixins import DateMixin
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Product(DateMixin):
    id: str
    sku_id: str
    merchant_id: int
    name: str
    description: str
    brand: str
    category_id: int
    items_sold: int
    ratings: float
    price: float


@dataclass
class Category():
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
    locations: list[Address] = []

    
@dataclass
class Shipment():
    id: int
    order_id: int
    status: Status
    estimated_date: datetime
    address: list[Address] 
    carrier_information: dict[str, str]
