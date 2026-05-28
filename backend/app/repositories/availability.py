from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accommodation import AccommodationAvailability, SeasonalPrice
from app.repositories.base import BaseRepository


class AvailabilityRepository(BaseRepository[AccommodationAvailability]):
    def __init__(self, db: Session) -> None:
        super().__init__(AccommodationAvailability, db)

    def get_by_accommodation_and_date(
        self, accommodation_id: int, date: date_type
    ) -> AccommodationAvailability | None:
        stmt = select(AccommodationAvailability).where(
            AccommodationAvailability.accommodation_id == accommodation_id,
            AccommodationAvailability.date == date,
        )
        return self.db.scalar(stmt)

    def get_blocked_in_range(
        self, accommodation_id: int, start_date: date_type, end_date: date_type
    ) -> list[AccommodationAvailability]:
        """Return blocked dates in [start_date, end_date), exclusive end — for reservation checks."""
        stmt = (
            select(AccommodationAvailability)
            .where(
                AccommodationAvailability.accommodation_id == accommodation_id,
                AccommodationAvailability.date >= start_date,
                AccommodationAvailability.date < end_date,
            )
            .order_by(AccommodationAvailability.date)
        )
        return list(self.db.scalars(stmt).all())

    def get_in_range_inclusive(
        self, accommodation_id: int, start_date: date_type, end_date: date_type
    ) -> list[AccommodationAvailability]:
        """Return blocked dates in [start_date, end_date] inclusive — for calendar display."""
        stmt = (
            select(AccommodationAvailability)
            .where(
                AccommodationAvailability.accommodation_id == accommodation_id,
                AccommodationAvailability.date >= start_date,
                AccommodationAvailability.date <= end_date,
            )
            .order_by(AccommodationAvailability.date)
        )
        return list(self.db.scalars(stmt).all())


class SeasonalPriceRepository(BaseRepository[SeasonalPrice]):
    def __init__(self, db: Session) -> None:
        super().__init__(SeasonalPrice, db)

    def get_by_accommodation(self, accommodation_id: int) -> list[SeasonalPrice]:
        stmt = (
            select(SeasonalPrice)
            .where(SeasonalPrice.accommodation_id == accommodation_id)
            .order_by(SeasonalPrice.start_date)
        )
        return list(self.db.scalars(stmt).all())

    def get_overlapping(
        self,
        accommodation_id: int,
        start_date: date_type,
        end_date: date_type,
        exclude_id: int | None = None,
    ) -> list[SeasonalPrice]:
        """Return seasonal prices whose date range overlaps [start_date, end_date]."""
        stmt = select(SeasonalPrice).where(
            SeasonalPrice.accommodation_id == accommodation_id,
            SeasonalPrice.start_date <= end_date,
            SeasonalPrice.end_date >= start_date,
        )
        if exclude_id is not None:
            stmt = stmt.where(SeasonalPrice.id != exclude_id)
        return list(self.db.scalars(stmt).all())

    def get_price_for_date(
        self, accommodation_id: int, date: date_type
    ) -> SeasonalPrice | None:
        stmt = (
            select(SeasonalPrice)
            .where(
                SeasonalPrice.accommodation_id == accommodation_id,
                SeasonalPrice.start_date <= date,
                SeasonalPrice.end_date >= date,
            )
            .limit(1)
        )
        return self.db.scalar(stmt)
