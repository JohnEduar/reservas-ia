from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_superuser
from app.db.deps import get_db
from app.models.user import User
from app.schemas.accommodation import AmenityCreate, AmenityResponse
from app.services.accommodation import AccommodationService

router = APIRouter()


@router.get(
    "/",
    response_model=list[AmenityResponse],
    summary="Listar amenidades (público)",
    description="Retorna todas las amenidades disponibles.",
)
def list_amenities(db: Session = Depends(get_db)) -> list[AmenityResponse]:
    return AccommodationService(db).list_amenities()


@router.post(
    "/",
    response_model=AmenityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear amenidad",
    description="Crea una nueva amenidad. Solo superusuarios.",
)
def create_amenity(
    data: AmenityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AmenityResponse:
    return AccommodationService(db).create_amenity(name=data.name, icon=data.icon)
