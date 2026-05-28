from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_superuser
from app.db.deps import get_db
from app.models.user import User
from app.schemas.admin import (
    AccommodationRevenue,
    ActivityReport,
    AdminAccommodationResponse,
    AdminReservationResponse,
    KPISummary,
    OccupancyStats,
    RevenueByPeriod,
)
from app.services.admin import AdminService

router = APIRouter()


@router.get(
    "/kpis",
    response_model=KPISummary,
    summary="KPI summary",
    description="Global KPIs: user counts, accommodation counts, reservation counts, and revenue. Superuser only.",
)
def get_kpis(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> KPISummary:
    return AdminService(db).get_kpi_summary()


@router.get(
    "/stats/occupancy",
    response_model=list[OccupancyStats],
    summary="Occupancy statistics",
    description="Nights booked and occupancy rate per accommodation for the given date range. Superuser only.",
)
def get_occupancy(
    start_date: date = Query(..., description="Start of the analysis period (inclusive)"),
    end_date: date = Query(..., description="End of the analysis period (exclusive)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[OccupancyStats]:
    return AdminService(db).get_occupancy_stats(start_date, end_date)


@router.get(
    "/stats/revenue/period",
    response_model=list[RevenueByPeriod],
    summary="Revenue by month",
    description="Monthly revenue breakdown from confirmed reservations. Optionally filtered by year. Superuser only.",
)
def get_revenue_by_period(
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[RevenueByPeriod]:
    return AdminService(db).get_revenue_by_period(year=year)


@router.get(
    "/stats/revenue/accommodation",
    response_model=list[AccommodationRevenue],
    summary="Revenue by accommodation",
    description="Total revenue and confirmed reservation count per accommodation (top N). Superuser only.",
)
def get_revenue_by_accommodation(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[AccommodationRevenue]:
    return AdminService(db).get_revenue_by_accommodation(limit=limit)


@router.get(
    "/reservations",
    response_model=list[AdminReservationResponse],
    summary="List all reservations",
    description="All reservations with guest and accommodation details. Optionally filtered by status. Superuser only.",
)
def list_reservations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    status: str | None = Query(default=None, pattern="^(confirmed|cancelled)$"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[AdminReservationResponse]:
    return AdminService(db).list_all_reservations(skip=skip, limit=limit, status=status)


@router.get(
    "/accommodations",
    response_model=list[AdminAccommodationResponse],
    summary="List all accommodations",
    description="All accommodations including inactive ones. Superuser only.",
)
def list_accommodations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    include_inactive: bool = Query(default=True),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[AdminAccommodationResponse]:
    return AdminService(db).list_all_accommodations(
        skip=skip, limit=limit, include_inactive=include_inactive
    )


@router.get(
    "/reports/activity",
    response_model=ActivityReport,
    summary="Activity report",
    description="Recent reservations, cancellations, and new user registrations. Superuser only.",
)
def get_activity_report(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> ActivityReport:
    return AdminService(db).get_activity_report(limit=limit)
