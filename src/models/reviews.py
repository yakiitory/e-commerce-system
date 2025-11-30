from dataclasses import dataclass

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