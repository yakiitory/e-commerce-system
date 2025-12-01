from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ReviewCreate():
    user_id: int
    product_id: int
    rating: float
    description: str

@dataclass
class Review(ReviewCreate):
    id: int
    likes: int
    created_at: datetime = field(default_factory=datetime.now)