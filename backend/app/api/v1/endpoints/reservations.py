from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.deps import get_db
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.services.reservation import ReservationService

router = APIRouter()


@router.post(
    "/",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reserva",
    description=(
        "Crea una nueva reserva para el alojamiento indicado. Valida disponibilidad de fechas "
        "y calcula el precio total considerando tarifas de temporada. Requiere autenticación."
    ),
)
def create_reservation(
    data: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReservationResponse:
    return ReservationService(db).create(guest_id=current_user.id, data=data)


@router.get(
    "/me",
    response_model=list[ReservationResponse],
    summary="Mis reservas",
    description="Retorna el historial de reservas del usuario autenticado, ordenadas por fecha de creación.",
)
def my_reservations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ReservationResponse]:
    return ReservationService(db).my_reservations(
        guest_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponse,
    summary="Obtener reserva",
    description=(
        "Retorna el detalle de una reserva. Accesible por el huésped, el propietario del "
        "alojamiento o un superusuario."
    ),
)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReservationResponse:
    return ReservationService(db).get_by_id(
        reservation_id=reservation_id,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )


@router.post(
    "/{reservation_id}/cancel",
    response_model=ReservationResponse,
    summary="Cancelar reserva",
    description=(
        "Cancela una reserva activa. Solo el huésped propietario de la reserva o un "
        "superusuario pueden cancelar. No se puede cancelar una reserva ya cancelada."
    ),
)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReservationResponse:
    return ReservationService(db).cancel(
        reservation_id=reservation_id,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
