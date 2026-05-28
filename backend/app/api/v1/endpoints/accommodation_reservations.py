from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.deps import get_db
from app.models.user import User
from app.schemas.reservation import ReservationResponse
from app.services.reservation import ReservationService

router = APIRouter()


@router.get(
    "/{accommodation_id}/reservations",
    response_model=list[ReservationResponse],
    summary="Listar reservas de un alojamiento",
    description=(
        "Retorna todas las reservas de un alojamiento, ordenadas por fecha de entrada. "
        "Solo el propietario del alojamiento o un superusuario pueden acceder."
    ),
)
def list_accommodation_reservations(
    accommodation_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ReservationResponse]:
    return ReservationService(db).list_by_accommodation(
        accommodation_id=accommodation_id,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
        skip=skip,
        limit=limit,
    )
