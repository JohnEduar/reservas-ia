from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.accommodation import (
    Accommodation,
    AccommodationImage,
    Amenity,
    accommodation_amenities,
)
from app.repositories.base import BaseRepository


class AccommodationRepository(BaseRepository[Accommodation]):
    def __init__(self, db: Session) -> None:
        super().__init__(Accommodation, db)

    def get_public(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        location: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_guests: int | None = None,
        amenity_ids: list[int] | None = None,
    ) -> list[Accommodation]:
        stmt = select(Accommodation).where(Accommodation.is_active.is_(True))
        if location:
            stmt = stmt.where(Accommodation.location.ilike(f"%{location}%"))
        if min_price is not None:
            stmt = stmt.where(Accommodation.price_per_night >= min_price)
        if max_price is not None:
            stmt = stmt.where(Accommodation.price_per_night <= max_price)
        if min_guests is not None:
            stmt = stmt.where(Accommodation.max_guests >= min_guests)
        if amenity_ids:
            for amenity_id in amenity_ids:
                stmt = stmt.where(
                    Accommodation.id.in_(
                        select(accommodation_amenities.c.accommodation_id).where(
                            accommodation_amenities.c.amenity_id == amenity_id
                        )
                    )
                )
        return list(self.db.scalars(stmt.offset(skip).limit(limit)).unique().all())

    def get_by_owner(
        self, owner_id: int, *, skip: int = 0, limit: int = 100
    ) -> list[Accommodation]:
        stmt = (
            select(Accommodation)
            .where(Accommodation.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())


class AccommodationImageRepository(BaseRepository[AccommodationImage]):
    def __init__(self, db: Session) -> None:
        super().__init__(AccommodationImage, db)

    def get_by_accommodation(self, accommodation_id: int) -> list[AccommodationImage]:
        stmt = (
            select(AccommodationImage)
            .where(AccommodationImage.accommodation_id == accommodation_id)
            .order_by(AccommodationImage.sort_order)
        )
        return list(self.db.scalars(stmt).all())

    def clear_primary(self, accommodation_id: int) -> None:
        for img in self.get_by_accommodation(accommodation_id):
            img.is_primary = False
        self.db.commit()


class AmenityRepository(BaseRepository[Amenity]):
    def __init__(self, db: Session) -> None:
        super().__init__(Amenity, db)

    def get_by_ids(self, ids: list[int]) -> list[Amenity]:
        stmt = select(Amenity).where(Amenity.id.in_(ids))
        return list(self.db.scalars(stmt).all())

    def get_by_name(self, name: str) -> Amenity | None:
        stmt = select(Amenity).where(Amenity.name == name)
        return self.db.scalar(stmt)
