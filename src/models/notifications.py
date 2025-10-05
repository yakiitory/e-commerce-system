from abc import ABC
from dataclasses import dataclass

@dataclass
class Notification(ABC):
    id: int
    target_id: int
    type: str
