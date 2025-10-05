from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from models.status import Status
from models.addresses import Address

@dataclass
class Shipment():
    id: int
    order_id: int
    status: Status
    estimated_date: datetime
    address: list[Address] 
    carrier_information: dict = {"courier": str, "method": str}

@dataclass
)
