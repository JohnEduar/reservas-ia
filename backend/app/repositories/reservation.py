from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reservation import Reservation, ReservationStatus
from app.repositories.base import BaseRepository



class ReservationRepository(BaseRepository[Reservation]):
    def __init__(self, db: Session) -> None:
        super().__init__(Reservation, db)

    def get_by_guest(
        self, guest_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Reservation]:
        stmt = (
            select(Reservation)
            .where(Reservation.guest_id == guest_id)
            .order_by(Reservation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_accommodation(
        self, accommodation_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Reservation]:
        stmt = (
            select(Reservation)
            .where(Reservation.accommodation_id == accommodation_id)
            .order_by(Reservation.check_in.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_overlapping(
        self,
        accommodation_id: int,
        check_in: date_type,
        check_out: date_type,
        exclude_id: int | None = None,
    ) -> list[Reservation]:
        """Return active reservations that overlap [check_in, check_out)."""
        stmt = select(Reservation).where(
            Reservation.accommodation_id == accommodation_id,
            Reservation.status != ReservationStatus.cancelled,
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        )
        if exclude_id is not None:
            stmt = stmt.where(Reservation.id != exclude_id)
        return list(self.db.scalars(stmt).all())

    def has_completed_reservation(self, guest_id: int, accommodation_id: int) -> bool:
        stmt = (
            select(Reservation)
            .where(
                Reservation.guest_id == guest_id,
                Reservation.accommodation_id == accommodation_id,
                Reservation.status == ReservationStatus.confirmed,
                Reservation.check_out < date_type.today(),
            )
            .limit(1)
        )
        return self.db.scalars(stmt).first() is not None
