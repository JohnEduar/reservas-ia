from datetime import date as date_type, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.accommodation import AccommodationAvailability, SeasonalPrice
from app.repositories.accommodation import AccommodationRepository
from app.repositories.availability import AvailabilityRepository, SeasonalPriceRepository
from app.schemas.availability import (
    AvailabilityCalendarDayResponse,
    AvailabilityCheckResponse,
    SeasonalPriceCreate,
    SeasonalPriceUpdate,
)
from app.services.accommodation import AccommodationForbiddenError, AccommodationNotFoundError

_MAX_CALENDAR_DAYS = 365


class DateAlreadyBlockedError(Exception):
    pass


class DateNotBlockedError(Exception):
    pass


class AccommodationNotAvailableError(Exception):
    pass


class SeasonalPriceNotFoundError(Exception):
    pass


class SeasonalPriceConflictError(Exception):
    pass


class InvalidDateRangeError(Exception):
    pass


class AvailabilityService:
    def __init__(self, db: Session) -> None:
        self.acc_repo = AccommodationRepository(db)
        self.avail_repo = AvailabilityRepository(db)
        self.price_repo = SeasonalPriceRepository(db)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_accommodation(self, accommodation_id: int):
        acc = self.acc_repo.get(accommodation_id)
        if not acc:
            raise AccommodationNotFoundError(accommodation_id)
        return acc

    def _check_ownership(self, acc, requester_id: int, is_superuser: bool) -> None:
        if not is_superuser and acc.owner_id != requester_id:
            raise AccommodationForbiddenError()

    def _price_for_date(self, accommodation_id: int, d: date_type, base_price: Decimal) -> Decimal:
        seasonal = self.price_repo.get_price_for_date(accommodation_id, d)
        return seasonal.price_per_night if seasonal else base_price

    # ── Calendar ──────────────────────────────────────────────────────────────

    def get_calendar(
        self,
        accommodation_id: int,
        start_date: date_type,
        end_date: date_type,
    ) -> list[AvailabilityCalendarDayResponse]:
        if start_date > end_date:
            raise InvalidDateRangeError()
        if (end_date - start_date).days > _MAX_CALENDAR_DAYS:
            raise InvalidDateRangeError()

        acc = self._get_accommodation(accommodation_id)

        blocked_map = {
            b.date: b.reason
            for b in self.avail_repo.get_in_range_inclusive(accommodation_id, start_date, end_date)
        }

        result = []
        current = start_date
        while current <= end_date:
            price = self._price_for_date(accommodation_id, current, acc.price_per_night)
            is_blocked = current in blocked_map
            result.append(
                AvailabilityCalendarDayResponse(
                    date=current,
                    is_available=not is_blocked,
                    reason=blocked_map.get(current),
                    price_per_night=price,
                )
            )
            current += timedelta(days=1)

        return result

    # ── Availability check ────────────────────────────────────────────────────

    def check_availability(
        self,
        accommodation_id: int,
        check_in: date_type,
        check_out: date_type,
    ) -> AvailabilityCheckResponse:
        if check_in >= check_out:
            raise InvalidDateRangeError()

        acc = self._get_accommodation(accommodation_id)

        blocked = self.avail_repo.get_blocked_in_range(accommodation_id, check_in, check_out)
        is_available = len(blocked) == 0

        nights = (check_out - check_in).days
        total_price = Decimal("0")
        current = check_in
        while current < check_out:
            total_price += self._price_for_date(accommodation_id, current, acc.price_per_night)
            current += timedelta(days=1)

        return AvailabilityCheckResponse(
            accommodation_id=accommodation_id,
            check_in=check_in,
            check_out=check_out,
            is_available=is_available,
            nights=nights,
            total_price=total_price,
        )

    def assert_available(
        self, accommodation_id: int, check_in: date_type, check_out: date_type
    ) -> None:
        """Raises AccommodationNotAvailableError if any date in [check_in, check_out) is blocked.
        Intended for use by the future Reservation service."""
        if check_in >= check_out:
            raise InvalidDateRangeError()
        blocked = self.avail_repo.get_blocked_in_range(accommodation_id, check_in, check_out)
        if blocked:
            raise AccommodationNotAvailableError()

    # ── Blocked dates management ──────────────────────────────────────────────

    def block_dates(
        self,
        accommodation_id: int,
        dates: list[date_type],
        reason: str | None,
        requester_id: int,
        is_superuser: bool,
    ) -> list[AccommodationAvailability]:
        acc = self._get_accommodation(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        created = []
        for d in dates:
            if self.avail_repo.get_by_accommodation_and_date(accommodation_id, d):
                raise DateAlreadyBlockedError(str(d))
            created.append(
                self.avail_repo.create({"accommodation_id": accommodation_id, "date": d, "reason": reason})
            )
        return created

    def unblock_date(
        self,
        accommodation_id: int,
        date: date_type,
        requester_id: int,
        is_superuser: bool,
    ) -> AccommodationAvailability:
        acc = self._get_accommodation(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        record = self.avail_repo.get_by_accommodation_and_date(accommodation_id, date)
        if not record:
            raise DateNotBlockedError(str(date))

        self.avail_repo.db.delete(record)
        self.avail_repo.db.commit()
        return record

    # ── Seasonal prices ───────────────────────────────────────────────────────

    def list_seasonal_prices(self, accommodation_id: int) -> list[SeasonalPrice]:
        self._get_accommodation(accommodation_id)
        return self.price_repo.get_by_accommodation(accommodation_id)

    def create_seasonal_price(
        self,
        accommodation_id: int,
        data: SeasonalPriceCreate,
        requester_id: int,
        is_superuser: bool,
    ) -> SeasonalPrice:
        if data.start_date >= data.end_date:
            raise InvalidDateRangeError()

        acc = self._get_accommodation(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        if self.price_repo.get_overlapping(accommodation_id, data.start_date, data.end_date):
            raise SeasonalPriceConflictError()

        return self.price_repo.create({
            "accommodation_id": accommodation_id,
            "name": data.name,
            "start_date": data.start_date,
            "end_date": data.end_date,
            "price_per_night": data.price_per_night,
        })

    def update_seasonal_price(
        self,
        accommodation_id: int,
        price_id: int,
        data: SeasonalPriceUpdate,
        requester_id: int,
        is_superuser: bool,
    ) -> SeasonalPrice:
        acc = self._get_accommodation(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        record = self.price_repo.get(price_id)
        if not record or record.accommodation_id != accommodation_id:
            raise SeasonalPriceNotFoundError()

        new_start = data.start_date if data.start_date is not None else record.start_date
        new_end = data.end_date if data.end_date is not None else record.end_date

        if new_start >= new_end:
            raise InvalidDateRangeError()

        if data.start_date is not None or data.end_date is not None:
            if self.price_repo.get_overlapping(accommodation_id, new_start, new_end, exclude_id=price_id):
                raise SeasonalPriceConflictError()

        updates = {}
        if data.name is not None:
            updates["name"] = data.name
        if data.start_date is not None:
            updates["start_date"] = data.start_date
        if data.end_date is not None:
            updates["end_date"] = data.end_date
        if data.price_per_night is not None:
            updates["price_per_night"] = data.price_per_night

        return self.price_repo.update(record, updates)

    def delete_seasonal_price(
        self,
        accommodation_id: int,
        price_id: int,
        requester_id: int,
        is_superuser: bool,
    ) -> SeasonalPrice:
        acc = self._get_accommodation(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        record = self.price_repo.get(price_id)
        if not record or record.accommodation_id != accommodation_id:
            raise SeasonalPriceNotFoundError()

        self.price_repo.db.delete(record)
        self.price_repo.db.commit()
        return record
