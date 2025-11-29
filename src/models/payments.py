from dataclasses import dataclass, field
from datetime import datetime
from models.mixins import DateMixin
from .status import Status

@dataclass
class VirtualCardCreate():
    balance: float

@dataclass
class VirtualCard(VirtualCardCreate):
    id: int = 0

@dataclass
class PaymentCreate:
    """Data needed to create a new payment."""
    sender_id: int
    sender_type: str
    receiver_id: int
    receiver_type: str
    amount: float

@dataclass
class Payment(PaymentCreate, DateMixin):
    """Represents a fully formed payment record from the database."""
    id: int = field(default_factory=int)