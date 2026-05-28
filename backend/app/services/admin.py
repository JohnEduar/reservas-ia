from datetime import date as date_type, date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.reservation import ReservationStatus
from app.repositories.admin import AdminRepository
from app.schemas.admin import (
    AccommodationRevenue,
    ActivityReport,
    AdminAccommodationResponse,
    AdminReservationResponse,
    KPISummary,
    OccupancyStats,
    RevenueByPeriod,
)
from app.schemas.user import UserResponse


class AdminService:
    def __init__(self, db: Session) -> None:
        self.repo = AdminRepository(db)

    def get_kpi_summary(self) -> KPISummary:
        today = date.today()
        month_start = today.replace(day=1)
        if month_start.month == 12:
            next_month_start = date(month_start.year + 1, 1, 1)
        else:
            next_month_start = date(month_start.year, month_start.month + 1, 1)

        return KPISummary(
            total_users=self.repo.count_users(),
            active_users=self.repo.count_users(active_only=True),
            total_accommodations=self.repo.count_accommodations(),
            active_accommodations=self.repo.count_accommodations(active_only=True),
            total_reservations=self.repo.count_reservations(),
            confirmed_reservations=self.repo.count_reservations(
                status=ReservationStatus.confirmed
            ),
            cancelled_reservations=self.repo.count_reservations(
                status=ReservationStatus.cancelled
            ),
            total_revenue=self.repo.sum_revenue(),
            revenue_this_month=self.repo.sum_revenue(
                start_date=month_start, end_date=next_month_start
            ),
            reservations_this_month=self.repo.count_reservations_in_range(
                start_date=month_start, end_date=next_month_start
            ),
        )

    def get_occupancy_stats(
        self, start_date: date_type, end_date: date_type
    ) -> list[OccupancyStats]:
        rows = self.repo.occupancy_stats(start_date, end_date)
        return [OccupancyStats(**r) for r in rows]

    def get_revenue_by_period(self, *, year: int | None = None) -> list[RevenueByPeriod]:
        rows = self.repo.revenue_by_month(year=year)
        return [RevenueByPeriod(**r) for r in rows]

    def get_revenue_by_accommodation(self, *, limit: int = 10) -> list[AccommodationRevenue]:
        rows = self.repo.revenue_by_accommodation(limit=limit)
        return [AccommodationRevenue(**r) for r in rows]

    def list_all_reservations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[AdminReservationResponse]:
        rows = self.repo.list_all_reservations(skip=skip, limit=limit, status=status)
        return [AdminReservationResponse(**r) for r in rows]

    def list_all_accommodations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = True,
    ) -> list[AdminAccommodationResponse]:
        accs = self.repo.list_all_accommodations(
            skip=skip, limit=limit, include_inactive=include_inactive
        )
        return [AdminAccommodationResponse.model_validate(acc) for acc in accs]

    def get_activity_report(self, *, limit: int = 10) -> ActivityReport:
        recent = self.repo.list_all_reservations(limit=limit)
        cancellations = self.repo.list_all_reservations(
            limit=limit, status=ReservationStatus.cancelled
        )
        users = self.repo.get_recent_users(limit=limit)
        return ActivityReport(
            recent_reservations=[AdminReservationResponse(**r) for r in recent],
            recent_cancellations=[AdminReservationResponse(**r) for r in cancellations],
            recent_registrations=[UserResponse.model_validate(u) for u in users],
        )
