from datetime import date as date_type, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.reservation import Reservation, ReservationStatus
from app.repositories.accommodation import AccommodationRepository
from app.repositories.availability import AvailabilityRepository, SeasonalPriceRepository
from app.repositories.reservation import ReservationRepository
from app.schemas.reservation import ReservationCreate
from app.services.accommodation import AccommodationNotFoundError


class ReservationNotFoundError(Exception):
    pass


class ReservationForbiddenError(Exception):
    pass


class ReservationConflictError(Exception):
    pass


class ReservationAlreadyCancelledError(Exception):
    pass


class GuestCountExceededError(Exception):
    pass


class InvalidReservationDateError(Exception):
    pass


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.repo = ReservationRepository(db)
        self.acc_repo = AccommodationRepository(db)
        self.avail_repo = AvailabilityRepository(db)
        self.price_repo = SeasonalPriceRepository(db)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_accommodation(self, accommodation_id: int):
        acc = self.acc_repo.get(accommodation_id)
        if not acc or not acc.is_active:
            raise AccommodationNotFoundError(accommodation_id)
        return acc

    def _get_reservation(self, reservation_id: int) -> Reservation:
        reservation = self.repo.get(reservation_id)
        if not reservation:
            raise ReservationNotFoundError(reservation_id)
        return reservation

    def _check_guest_ownership(
        self, reservation: Reservation, requester_id: int, is_superuser: bool
    ) -> None:
        if not is_superuser and reservation.guest_id != requester_id:
            raise ReservationForbiddenError()

    def _calculate_total_price(
        self,
        accommodation_id: int,
        check_in: date_type,
        check_out: date_type,
        base_price: Decimal,
    ) -> Decimal:
        total = Decimal("0")
        current = check_in
        while current < check_out:
            seasonal = self.price_repo.get_price_for_date(accommodation_id, current)
            total += seasonal.price_per_night if seasonal else base_price
            current += timedelta(days=1)
        return total

    # ── Public operations ─────────────────────────────────────────────────────

    def create(self, guest_id: int, data: ReservationCreate) -> Reservation:
        if data.check_in >= data.check_out:
            raise InvalidReservationDateError()

        acc = self._get_accommodation(data.accommodation_id)

        if data.guest_count > acc.max_guests:
            raise GuestCountExceededError()

        if self.avail_repo.get_blocked_in_range(data.accommodation_id, data.check_in, data.check_out):
            raise ReservationConflictError()

        if self.repo.get_overlapping(data.accommodation_id, data.check_in, data.check_out):
            raise ReservationConflictError()

        total_price = self._calculate_total_price(
            data.accommodation_id, data.check_in, data.check_out, acc.price_per_night
        )

        return self.repo.create({
            "accommodation_id": data.accommodation_id,
            "guest_id": guest_id,
            "check_in": data.check_in,
            "check_out": data.check_out,
            "guest_count": data.guest_count,
            "status": ReservationStatus.confirmed,
            "total_price": total_price,
            "notes": data.notes,
        })

    def get_by_id(
        self, reservation_id: int, requester_id: int, is_superuser: bool
    ) -> Reservation:
        reservation = self._get_reservation(reservation_id)

        if not is_superuser:
            if reservation.guest_id != requester_id:
                acc = self.acc_repo.get(reservation.accommodation_id)
                if not acc or acc.owner_id != requester_id:
                    raise ReservationForbiddenError()

        return reservation

    def my_reservations(
        self, guest_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Reservation]:
        return self.repo.get_by_guest(guest_id, skip=skip, limit=limit)

    def list_by_accommodation(
        self,
        accommodation_id: int,
        requester_id: int,
        is_superuser: bool,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Reservation]:
        acc = self._get_accommodation(accommodation_id)
        if not is_superuser and acc.owner_id != requester_id:
            raise ReservationForbiddenError()
        return self.repo.get_by_accommodation(accommodation_id, skip=skip, limit=limit)

    def cancel(
        self, reservation_id: int, requester_id: int, is_superuser: bool
    ) -> Reservation:
        reservation = self._get_reservation(reservation_id)
        self._check_guest_ownership(reservation, requester_id, is_superuser)

        if reservation.status == ReservationStatus.cancelled:
            raise ReservationAlreadyCancelledError()

        return self.repo.update(reservation, {"status": ReservationStatus.cancelled})
