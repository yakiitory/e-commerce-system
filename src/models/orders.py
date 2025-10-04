from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from .addresses import Address

class Status(Enum):
    PENDING = 1
    PAID = 2
    SHIPPED = 3
    DELIVERED = 4
    CANCELLED = 5
    REFUNDED = 6
    RETURNED = 7

@dataclass
class Order():
    id: int
    orders: list["OrderItem"]
    payment_type: str
    shipment_id: str
    order_status: Status
    order_created: datetime

@dataclass
class OrderItem():
    id: int
    product_id: int
    product_quantity: int
    product_price: float
    applied_discounts: list[str]
    total_price: float

@dataclass
class Invoice():
    id: int
    order_id: int
    payment_summary: dict # Should have subtotal, tax, discounts, total
    billing_address: Address
    issue_date: datetime
    status: Status



