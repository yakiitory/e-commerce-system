from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from .status import Status

@dataclass
class ItemCreate():
    product_id: int
    product_quantity: int
    product_price: float

@dataclass
class Item(ItemCreate):
    id: int

@dataclass
class CartCreate():
    user_id: int

@dataclass
class Cart(CartCreate):
    id: int
    items: list["CartItem"]
   

@dataclass
class CartItem(Item):
    added_at: datetime


@dataclass
class OrderCreate():
    orders: tuple["OrderItem", ...]
    payment_type: str
    order_created: datetime

@dataclass
class Order(OrderCreate):
    id: int
    user_id: int
    status: Status
    order_created: datetime

@dataclass
class OrderItem(Item):
    applied_discounts: list[int]
    total_price: float


@dataclass
class InvoiceCreate():
    order_id: int
    address_id: int
    issue_date: datetime = field(default_factory=datetime.now)
    status: Status = Status.PENDING
    payment_summary: str | None = None

@dataclass
class Invoice():
    id: int
    order_id: int
    address_id: int
    issue_date: datetime
    status: Status
    payment_summary: str | None = None
