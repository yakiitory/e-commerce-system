from dataclasses import dataclass
from datetime import datetime

from models.mixins import AuthMixin, ContactMixin, DateMixin

@dataclass
class VirtualCard(AuthMixin, ContactMixin, DateMixin):
    balance: float

@dataclass
class Payment(DateMixin):
    id: int
    sender_id: int
    receiver_id: int
    type: str


@dataclass
class Voucher(DateMixin):
    id: int
    store_id: int
    type: str
    active_until: datetime
    cashback: float
