from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    accommodation_id: int
    check_in: date
    check_out: date
    guest_count: int = Field(ge=1)
    notes: str | None = Field(default=None, max_length=1000)


class ReservationResponse(BaseModel):
    id: int
    accommodation_id: int
    guest_id: int
    check_in: date
    check_out: date
    guest_count: int
    status: str
    total_price: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
