from dataclasses import dataclass

@dataclass
class ReviewCreate():
    user_id: int
    product_id: int
    ratings: float
    description: str
    attached: list[str]

@dataclass
class Review(ReviewCreate):
    id: int
    likes: int