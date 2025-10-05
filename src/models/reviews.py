from dataclasses import dataclass

@dataclass
class Review():
    id: int
    creator_id: int
    rating: float
    description: str
    attached: list[str]
    likes: int
