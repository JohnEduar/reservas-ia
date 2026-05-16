from decimal import Decimal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_current_superuser
from app.db.deps import get_db
from app.models.user import User
from app.schemas.accommodation import AccommodationCreate, AccommodationResponse, AccommodationUpdate, AccommodationImageResponse
from app.services.accommodation import (
    AccommodationForbiddenError,
    AccommodationNotFoundError,
    AccommodationService,
    AmenityNotFoundError,
    ImageNotFoundError,
    InvalidImageError,
)

router = APIRouter()


# ── Public endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[AccommodationResponse],
    summary="Listar alojamientos (público)",
    description="Retorna alojamientos activos con filtros opcionales. No requiere autenticación.",
)
def list_accommodations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    location: str | None = Query(default=None, description="Filtrar por ubicación (búsqueda parcial)"),
    min_price: Decimal | None = Query(default=None, ge=0, description="Precio mínimo por noche"),
    max_price: Decimal | None = Query(default=None, ge=0, description="Precio máximo por noche"),
    min_guests: int | None = Query(default=None, ge=1, description="Capacidad mínima requerida"),
    amenity_ids: list[int] | None = Query(default=None, description="IDs de amenidades requeridas"),
    db: Session = Depends(get_db),
) -> list[AccommodationResponse]:
    return AccommodationService(db).list_public(
        skip=skip,
        limit=limit,
        location=location,
        min_price=min_price,
        max_price=max_price,
        min_guests=min_guests,
        amenity_ids=amenity_ids,
    )


@router.get(
    "/{accommodation_id}",
    response_model=AccommodationResponse,
    summary="Obtener alojamiento por ID (público)",
)
def get_accommodation(
    accommodation_id: int,
    db: Session = Depends(get_db),
) -> AccommodationResponse:
    try:
        return AccommodationService(db).get_by_id(accommodation_id)
    except AccommodationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")


# ── Authenticated endpoints ──────────────────────────────────────────────────

@router.post(
    "/",
    response_model=AccommodationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear alojamiento",
    description="Crea un nuevo alojamiento. El usuario autenticado queda como propietario.",
)
def create_accommodation(
    data: AccommodationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AccommodationResponse:
    try:
        return AccommodationService(db).create(owner_id=current_user.id, data=data)
    except AmenityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Amenity {e.amenity_id} not found",
        )


@router.put(
    "/{accommodation_id}",
    response_model=AccommodationResponse,
    summary="Actualizar alojamiento",
    description="Actualiza un alojamiento. Solo el propietario o superusuario.",
)
def update_accommodation(
    accommodation_id: int,
    data: AccommodationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AccommodationResponse:
    try:
        return AccommodationService(db).update(
            accommodation_id=accommodation_id,
            requester_id=current_user.id,
            is_superuser=current_user.is_superuser,
            data=data,
        )
    except AccommodationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    except AccommodationForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    except AmenityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Amenity {e.amenity_id} not found",
        )


@router.delete(
    "/{accommodation_id}",
    response_model=AccommodationResponse,
    summary="Eliminación lógica de alojamiento",
    description="Desactiva un alojamiento (soft delete). Solo el propietario o superusuario.",
)
def delete_accommodation(
    accommodation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AccommodationResponse:
    try:
        return AccommodationService(db).soft_delete(
            accommodation_id=accommodation_id,
            requester_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    except AccommodationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    except AccommodationForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")


# ── Image management ─────────────────────────────────────────────────────────

@router.post(
    "/{accommodation_id}/images",
    response_model=AccommodationImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir imagen",
    description="Sube una imagen al alojamiento (JPEG, PNG o WebP). La primera imagen se marca como primaria.",
)
def upload_image(
    accommodation_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AccommodationImageResponse:
    try:
        return AccommodationService(db).upload_image(
            accommodation_id=accommodation_id,
            requester_id=current_user.id,
            is_superuser=current_user.is_superuser,
            file=file,
        )
    except AccommodationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    except AccommodationForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    except InvalidImageError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image type: {e}. Allowed: JPEG, PNG, WebP",
        )


@router.delete(
    "/{accommodation_id}/images/{image_id}",
    response_model=AccommodationImageResponse,
    summary="Eliminar imagen",
)
def delete_image(
    accommodation_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AccommodationImageResponse:
    try:
        return AccommodationService(db).delete_image(
            accommodation_id=accommodation_id,
            image_id=image_id,
            requester_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    except AccommodationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    except AccommodationForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    except ImageNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@router.patch(
    "/{accommodation_id}/images/{image_id}/primary",
    response_model=AccommodationImageResponse,
    summary="Establecer imagen primaria",
)
def set_primary_image(
    accommodation_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AccommodationImageResponse:
    try:
        return AccommodationService(db).set_primary_image(
            accommodation_id=accommodation_id,
            image_id=image_id,
            requester_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    except AccommodationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")
    except AccommodationForbiddenError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    except ImageNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
