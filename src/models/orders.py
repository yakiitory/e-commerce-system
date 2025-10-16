from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .addresses import Address
from .status import Status

@dataclass
class Item():
    id: int
    product_id: int
    product_quantity: int
    product_price: float

@dataclass
class Cart():
    id: int
    user_id: int
    items: list["CartItem"]
   

@dataclass
class CartItem(Item):
    added_at: datetime


@dataclass
class Order():
    id: int
    orders: list["OrderItem"]
    payment_type: str
    shipment_id: int 
    order_status: Status
    order_created: datetime


@dataclass
class OrderItem(Item):
    applied_discounts: list[int]
    total_price: float


@dataclass
class Invoice():
    """TODO: Should probably fix how this can be easily printed and contain all the info needed"""
    id: int
    order_id: int
    billing_address: Address
    issue_date: datetime
    status: Status
    payment_summary: dict[str, float]
