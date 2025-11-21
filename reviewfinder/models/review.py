from pydantic import BaseModel
from typing import List, Optional


class Review(BaseModel):
    user: str
    rating: float
    review: str
    date: str
    reviewCreatedVersion: str = None
    reply: dict = None
    thumbsUpCount: int = None


class ReviewsResponse(BaseModel):
    platform: str
    reviews: List[Review]
    message: Optional[str] = None
