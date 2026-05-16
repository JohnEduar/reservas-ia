from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AmenityCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    icon: str | None = Field(default=None, max_length=50)


class AmenityResponse(BaseModel):
    id: int
    name: str
    icon: str | None

    model_config = {"from_attributes": True}


class AccommodationImageResponse(BaseModel):
    id: int
    url: str
    is_primary: bool
    sort_order: int

    model_config = {"from_attributes": True}


class AccommodationCreate(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    description: str | None = None
    location: str = Field(min_length=3, max_length=255)
    price_per_night: Decimal = Field(gt=0, decimal_places=2)
    max_guests: int = Field(ge=1, le=50)
    amenity_ids: list[int] = []


class AccommodationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, min_length=3, max_length=255)
    price_per_night: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    max_guests: int | None = Field(default=None, ge=1, le=50)
    amenity_ids: list[int] | None = None
    is_active: bool | None = None


class AccommodationResponse(BaseModel):
    id: int
    title: str
    description: str | None
    location: str
    price_per_night: Decimal
    max_guests: int
    owner_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: list[AccommodationImageResponse] = []
    amenities: list[AmenityResponse] = []

    model_config = {"from_attributes": True}
