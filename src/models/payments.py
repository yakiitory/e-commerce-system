from dataclasses import dataclass
from datetime import datetime

from models.mixins import DateMixin

@dataclass
class VirtualCard():
    id: int
    owner_id: int
    balance: float

@dataclass
class Payment(DateMixin):
    id: int
    sender_id: int
    receiver_id: int
    type: str
    amount: float


@dataclass
class Voucher(DateMixin):
    id: int
    merchant_id: int
    type: str
    active_until: datetime
    cashback: float
