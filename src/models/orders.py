from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from .status import Status

# --- Order Item Models ---
# Represents an item within an order.

@dataclass
class OrderItemCreate:
    """Data needed to create a new item within an order."""
    product_id: int
    product_quantity: int
    product_price: float
    order_id: int | None = None # Set by the repository during creation

@dataclass
class OrderItem(OrderItemCreate):
    """Represents a fully formed order item record from the database."""
    id: int = field(default_factory=int)
    applied_discounts: int = 0
    total_price: float = 0

# --- Order Models ---
# Represents a customer's order.

@dataclass
class OrderCreate:
    """Data needed to create a new order."""
    user_id: int
    merchant_id: int
    shipping_address_id: int
    billing_address_id: int
    total_amount: float
    items: list[OrderItemCreate] = field(default_factory=list)
    status: Status = Status.PENDING
    order_date: datetime = field(default_factory=datetime.now)

@dataclass
class Order(OrderCreate):
    """Represents a fully formed order record from the database, including its items."""
    id: int = field(default_factory=int)
    items: list[OrderItem] = field(default_factory=list)

# --- Cart Item Models ---
# Represents an item within a shopping cart.

@dataclass
class CartItemCreate:
    """Data needed to add an item to a cart."""
    product_id: int
    quantity: int
    price: float
    total_price: float

@dataclass
class CartItem(CartItemCreate):
    """Represents a cart item record from the database."""
    id: int
    product_brand: str
    product_name: str
    thumbnail_url: str

# --- Cart Models ---
# Represents a user's shopping cart.

@dataclass
class CartCreate:
    """Data needed to create a new shopping cart."""
    user_id: int

@dataclass
class Cart(CartCreate):
    """Represents a user's shopping cart with its items."""
    id: int
    items: list[CartItem] = field(default_factory=list)

# --- Invoice Models ---

@dataclass
class InvoiceCreate:
    address_id: int
    order_id: int
    issue_date: datetime = field(default_factory=datetime.now)
    status: Status = Status.PENDING
    payment_summary: str | None = None

@dataclass
class Invoice(InvoiceCreate):
    """Represents a fully formed invoice record from the database."""
    id: int = field(default_factory=int)
