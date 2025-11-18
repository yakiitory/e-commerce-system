from dataclasses import dataclass, field
from datetime import datetime
from models.mixins import DateMixin
from .status import Status

@dataclass
class VirtualCardCreate():
    owner_id: int
    balance: float

@dataclass
class VirtualCard(VirtualCardCreate):
    id: int

@dataclass
class PaymentCreate:
    """Data needed to create a new payment."""
    sender_id: int
    receiver_id: int
    type: str
    amount: float
    status: Status = Status.PENDING

@dataclass
class Payment(PaymentCreate, DateMixin):
    """Represents a fully formed payment record from the database."""
    id: int = field(default_factory=int)