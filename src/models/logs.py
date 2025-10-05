from abc import ABC
from dataclasses import dataclass

from .mixins import DateMixin

@dataclass
class History(ABC, DateMixin):
    id: int
    user_id: str
    interaction_type: str


@dataclass
class Interaction(History):
    product_id: int
    weight: float = 1.0


@dataclass
class AdminLog(History):
    target_type: str
    target_id: int
    details: str
    status: str
