from collections import defaultdict
from datetime import date as date_type
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.models.accommodation import Accommodation
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User


class AdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Counts ────────────────────────────────────────────────────────────────

    def count_users(self, *, active_only: bool = False) -> int:
        stmt = select(func.count(User.id))
        if active_only:
            stmt = stmt.where(User.is_active == True)  # noqa: E712
        return self.db.scalar(stmt) or 0

    def count_accommodations(self, *, active_only: bool = False) -> int:
        stmt = select(func.count(Accommodation.id))
        if active_only:
            stmt = stmt.where(Accommodation.is_active == True)  # noqa: E712
        return self.db.scalar(stmt) or 0

    def count_reservations(self, *, status: str | None = None) -> int:
        stmt = select(func.count(Reservation.id))
        if status is not None:
            stmt = stmt.where(Reservation.status == status)
        return self.db.scalar(stmt) or 0

    def count_reservations_in_range(
        self, start_date: date_type, end_date: date_type
    ) -> int:
        stmt = select(func.count(Reservation.id)).where(
            func.date(Reservation.created_at) >= start_date,
            func.date(Reservation.created_at) < end_date,
        )
        return self.db.scalar(stmt) or 0

    # ── Revenue aggregates ────────────────────────────────────────────────────

    def sum_revenue(
        self,
        *,
        start_date: date_type | None = None,
        end_date: date_type | None = None,
    ) -> Decimal:
        stmt = select(func.sum(Reservation.total_price)).where(
            Reservation.status == ReservationStatus.confirmed
        )
        if start_date is not None:
            stmt = stmt.where(func.date(Reservation.created_at) >= start_date)
        if end_date is not None:
            stmt = stmt.where(func.date(Reservation.created_at) < end_date)
        result = self.db.scalar(stmt)
        return Decimal(str(result)) if result is not None else Decimal("0")

    def revenue_by_month(self, *, year: int | None = None) -> list[dict]:
        year_col = extract("year", Reservation.created_at).label("yr")
        month_col = extract("month", Reservation.created_at).label("mo")
        stmt = (
            select(
                year_col,
                month_col,
                func.sum(Reservation.total_price).label("revenue"),
                func.count(Reservation.id).label("count"),
            )
            .where(Reservation.status == ReservationStatus.confirmed)
            .group_by(year_col, month_col)
            .order_by(year_col.desc(), month_col.desc())
        )
        if year is not None:
            stmt = stmt.where(extract("year", Reservation.created_at) == year)

        rows = self.db.execute(stmt).fetchall()
        return [
            {
                "period": f"{int(r.yr):04d}-{int(r.mo):02d}",
                "revenue": Decimal(str(r.revenue)) if r.revenue else Decimal("0"),
                "reservations_count": r.count,
            }
            for r in rows
        ]

    def revenue_by_accommodation(self, *, limit: int = 10) -> list[dict]:
        stmt = (
            select(
                Reservation.accommodation_id,
                Accommodation.title.label("accommodation_title"),
                func.sum(Reservation.total_price).label("total_revenue"),
                func.count(Reservation.id).label("reservations_count"),
            )
            .join(Accommodation, Reservation.accommodation_id == Accommodation.id)
            .where(Reservation.status == ReservationStatus.confirmed)
            .group_by(Reservation.accommodation_id, Accommodation.title)
            .order_by(func.sum(Reservation.total_price).desc())
            .limit(limit)
        )
        rows = self.db.execute(stmt).fetchall()
        return [
            {
                "accommodation_id": r.accommodation_id,
                "accommodation_title": r.accommodation_title,
                "total_revenue": Decimal(str(r.total_revenue)) if r.total_revenue else Decimal("0"),
                "reservations_count": r.reservations_count or 0,
            }
            for r in rows
        ]

    # ── Occupancy ─────────────────────────────────────────────────────────────

    def occupancy_stats(
        self, start_date: date_type, end_date: date_type
    ) -> list[dict]:
        """Return per-accommodation occupancy within [start_date, end_date)."""
        stmt = select(
            Reservation.accommodation_id,
            Reservation.check_in,
            Reservation.check_out,
        ).where(
            Reservation.status == ReservationStatus.confirmed,
            Reservation.check_in < end_date,
            Reservation.check_out > start_date,
        )
        rows = self.db.execute(stmt).fetchall()

        nights_by_acc: dict[int, int] = defaultdict(int)
        count_by_acc: dict[int, int] = defaultdict(int)
        for r in rows:
            overlap_start = max(r.check_in, start_date)
            overlap_end = min(r.check_out, end_date)
            nights = (overlap_end - overlap_start).days
            if nights > 0:
                nights_by_acc[r.accommodation_id] += nights
                count_by_acc[r.accommodation_id] += 1

        if not nights_by_acc:
            return []

        period_days = max((end_date - start_date).days, 1)
        acc_stmt = select(Accommodation.id, Accommodation.title).where(
            Accommodation.id.in_(nights_by_acc.keys())
        )
        titles = {r.id: r.title for r in self.db.execute(acc_stmt).fetchall()}

        return [
            {
                "accommodation_id": acc_id,
                "accommodation_title": titles.get(acc_id, f"Accommodation #{acc_id}"),
                "total_nights_booked": nights,
                "total_reservations": count_by_acc[acc_id],
                "occupancy_rate": round(nights / period_days * 100, 2),
            }
            for acc_id, nights in sorted(nights_by_acc.items(), key=lambda x: -x[1])
        ]

    # ── Listing helpers ───────────────────────────────────────────────────────

    def list_all_reservations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[dict]:
        stmt = (
            select(
                Reservation,
                Accommodation.title.label("accommodation_title"),
                User.email.label("guest_email"),
                User.full_name.label("guest_name"),
            )
            .join(Accommodation, Reservation.accommodation_id == Accommodation.id)
            .join(User, Reservation.guest_id == User.id)
            .order_by(Reservation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(Reservation.status == status)

        rows = self.db.execute(stmt).fetchall()
        return [
            {
                "id": row.Reservation.id,
                "accommodation_id": row.Reservation.accommodation_id,
                "accommodation_title": row.accommodation_title,
                "guest_id": row.Reservation.guest_id,
                "guest_email": row.guest_email,
                "guest_name": row.guest_name,
                "check_in": row.Reservation.check_in,
                "check_out": row.Reservation.check_out,
                "guest_count": row.Reservation.guest_count,
                "status": row.Reservation.status,
                "total_price": row.Reservation.total_price,
                "notes": row.Reservation.notes,
                "created_at": row.Reservation.created_at,
                "updated_at": row.Reservation.updated_at,
            }
            for row in rows
        ]

    def list_all_accommodations(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = True,
    ) -> list[Accommodation]:
        stmt = (
            select(Accommodation)
            .order_by(Accommodation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if not include_inactive:
            stmt = stmt.where(Accommodation.is_active == True)  # noqa: E712
        return list(self.db.scalars(stmt).all())

    def get_recent_users(self, *, limit: int = 10) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())
