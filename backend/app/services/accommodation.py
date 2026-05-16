import shutil
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.accommodation import Accommodation, AccommodationImage, Amenity
from app.repositories.accommodation import (
    AccommodationImageRepository,
    AccommodationRepository,
    AmenityRepository,
)
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate

UPLOAD_DIR = Path("uploads/accommodations")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class AccommodationNotFoundError(Exception):
    pass


class AccommodationForbiddenError(Exception):
    pass


class ImageNotFoundError(Exception):
    pass


class InvalidImageError(Exception):
    pass


class AmenityNotFoundError(Exception):
    def __init__(self, amenity_id: int) -> None:
        self.amenity_id = amenity_id
        super().__init__(f"Amenity {amenity_id} not found")


class AmenityAlreadyExistsError(Exception):
    pass


class AccommodationService:
    def __init__(self, db: Session) -> None:
        self.repo = AccommodationRepository(db)
        self.image_repo = AccommodationImageRepository(db)
        self.amenity_repo = AmenityRepository(db)

    def get_by_id(self, accommodation_id: int) -> Accommodation:
        acc = self.repo.get(accommodation_id)
        if not acc:
            raise AccommodationNotFoundError(accommodation_id)
        return acc

    def list_public(
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
        return self.repo.get_public(
            skip=skip,
            limit=limit,
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_guests=min_guests,
            amenity_ids=amenity_ids,
        )

    def create(self, owner_id: int, data: AccommodationCreate) -> Accommodation:
        amenities = self._resolve_amenities(data.amenity_ids)
        acc = self.repo.create({
            "title": data.title,
            "description": data.description,
            "location": data.location,
            "price_per_night": data.price_per_night,
            "max_guests": data.max_guests,
            "owner_id": owner_id,
        })
        acc.amenities = amenities
        self.repo.db.commit()
        self.repo.db.refresh(acc)
        return acc

    def update(
        self,
        accommodation_id: int,
        requester_id: int,
        is_superuser: bool,
        data: AccommodationUpdate,
    ) -> Accommodation:
        acc = self.get_by_id(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        updates: dict = {}
        if data.title is not None:
            updates["title"] = data.title
        if data.description is not None:
            updates["description"] = data.description
        if data.location is not None:
            updates["location"] = data.location
        if data.price_per_night is not None:
            updates["price_per_night"] = data.price_per_night
        if data.max_guests is not None:
            updates["max_guests"] = data.max_guests
        if data.is_active is not None:
            updates["is_active"] = data.is_active

        if updates:
            acc = self.repo.update(acc, updates)

        if data.amenity_ids is not None:
            acc.amenities = self._resolve_amenities(data.amenity_ids)
            self.repo.db.commit()
            self.repo.db.refresh(acc)

        return acc

    def soft_delete(
        self, accommodation_id: int, requester_id: int, is_superuser: bool
    ) -> Accommodation:
        acc = self.get_by_id(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)
        return self.repo.update(acc, {"is_active": False})

    def upload_image(
        self,
        accommodation_id: int,
        requester_id: int,
        is_superuser: bool,
        file: UploadFile,
    ) -> AccommodationImage:
        acc = self.get_by_id(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise InvalidImageError(file.content_type)

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        ext = (
            file.filename.rsplit(".", 1)[-1]
            if file.filename and "." in file.filename
            else "jpg"
        )
        filename = f"{uuid.uuid4().hex}.{ext}"
        dest = UPLOAD_DIR / filename

        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        existing = self.image_repo.get_by_accommodation(accommodation_id)
        return self.image_repo.create({
            "accommodation_id": accommodation_id,
            "url": f"/uploads/accommodations/{filename}",
            "is_primary": len(existing) == 0,
            "sort_order": len(existing),
        })

    def delete_image(
        self,
        accommodation_id: int,
        image_id: int,
        requester_id: int,
        is_superuser: bool,
    ) -> AccommodationImage:
        acc = self.get_by_id(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        image = self.image_repo.get(image_id)
        if not image or image.accommodation_id != accommodation_id:
            raise ImageNotFoundError(image_id)

        was_primary = image.is_primary
        file_path = Path(image.url.lstrip("/"))
        if file_path.exists():
            file_path.unlink()

        self.image_repo.db.delete(image)
        self.image_repo.db.commit()

        if was_primary:
            remaining = self.image_repo.get_by_accommodation(accommodation_id)
            if remaining:
                remaining[0].is_primary = True
                self.image_repo.db.commit()

        return image

    def set_primary_image(
        self,
        accommodation_id: int,
        image_id: int,
        requester_id: int,
        is_superuser: bool,
    ) -> AccommodationImage:
        acc = self.get_by_id(accommodation_id)
        self._check_ownership(acc, requester_id, is_superuser)

        image = self.image_repo.get(image_id)
        if not image or image.accommodation_id != accommodation_id:
            raise ImageNotFoundError(image_id)

        self.image_repo.clear_primary(accommodation_id)
        return self.image_repo.update(image, {"is_primary": True})

    # ── Amenity helpers ──────────────────────────────────────────────────────

    def list_amenities(self) -> list[Amenity]:
        return self.amenity_repo.get_multi(limit=200)

    def create_amenity(self, name: str, icon: str | None) -> Amenity:
        if self.amenity_repo.get_by_name(name):
            raise AmenityAlreadyExistsError(name)
        return self.amenity_repo.create({"name": name, "icon": icon})

    # ── Private helpers ──────────────────────────────────────────────────────

    def _resolve_amenities(self, amenity_ids: list[int]) -> list[Amenity]:
        if not amenity_ids:
            return []
        amenities = self.amenity_repo.get_by_ids(amenity_ids)
        found_ids = {a.id for a in amenities}
        for aid in amenity_ids:
            if aid not in found_ids:
                raise AmenityNotFoundError(aid)
        return amenities

    def _check_ownership(
        self, acc: Accommodation, requester_id: int, is_superuser: bool
    ) -> None:
        if not is_superuser and acc.owner_id != requester_id:
            raise AccommodationForbiddenError()
