from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.user import UserResponse


class KPISummary(BaseModel):
    total_users: int
    active_users: int
    total_accommodations: int
    active_accommodations: int
    total_reservations: int
    confirmed_reservations: int
    cancelled_reservations: int
    total_revenue: Decimal
    revenue_this_month: Decimal
    reservations_this_month: int


class OccupancyStats(BaseModel):
    accommodation_id: int
    accommodation_title: str
    total_nights_booked: int
    total_reservations: int
    occupancy_rate: float


class RevenueByPeriod(BaseModel):
    period: str
    revenue: Decimal
    reservations_count: int


class AccommodationRevenue(BaseModel):
    accommodation_id: int
    accommodation_title: str
    total_revenue: Decimal
    reservations_count: int


class AdminReservationResponse(BaseModel):
    id: int
    accommodation_id: int
    accommodation_title: str
    guest_id: int
    guest_email: str
    guest_name: str | None
    check_in: date
    check_out: date
    guest_count: int
    status: str
    total_price: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AdminAccommodationResponse(BaseModel):
    id: int
    title: str
    location: str
    price_per_night: Decimal
    max_guests: int
    owner_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActivityReport(BaseModel):
    recent_reservations: list[AdminReservationResponse]
    recent_cancellations: list[AdminReservationResponse]
    recent_registrations: list[UserResponse]
