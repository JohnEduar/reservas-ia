from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AvailabilityBlockCreate(BaseModel):
    dates: list[date] = Field(min_length=1, max_length=90)
    reason: str | None = Field(default=None, max_length=255)


class AvailabilityBlockResponse(BaseModel):
    id: int
    accommodation_id: int
    date: date
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityCalendarDayResponse(BaseModel):
    date: date
    is_available: bool
    reason: str | None
    price_per_night: Decimal

    model_config = {"from_attributes": True}


class AvailabilityCheckResponse(BaseModel):
    accommodation_id: int
    check_in: date
    check_out: date
    is_available: bool
    nights: int
    total_price: Decimal


class SeasonalPriceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    start_date: date
    end_date: date
    price_per_night: Decimal = Field(gt=0, decimal_places=2)


class SeasonalPriceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    price_per_night: Decimal | None = Field(default=None, gt=0, decimal_places=2)


class SeasonalPriceResponse(BaseModel):
    id: int
    accommodation_id: int
    name: str
    start_date: date
    end_date: date
    price_per_night: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}
