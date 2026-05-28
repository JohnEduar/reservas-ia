from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    accommodation_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    accommodation_id: int
    reviewer_id: int | None
    rating: int
    comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewSummary(BaseModel):
    reviews: list[ReviewResponse]
    average_rating: float | None
    total_reviews: int
