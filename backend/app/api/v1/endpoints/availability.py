from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.deps import get_db
from app.models.user import User
from app.schemas.availability import (
    AvailabilityBlockCreate,
    AvailabilityBlockResponse,
    AvailabilityCalendarDayResponse,
    AvailabilityCheckResponse,
    SeasonalPriceCreate,
    SeasonalPriceResponse,
    SeasonalPriceUpdate,
)
from app.services.availability import AvailabilityService

router = APIRouter()


# ── Public endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/{accommodation_id}/availability/calendar",
    response_model=list[AvailabilityCalendarDayResponse],
    summary="Calendario de disponibilidad",
    description=(
        "Retorna el estado de disponibilidad y precio por día para el rango indicado. "
        "Máximo 365 días. No requiere autenticación."
    ),
)
def get_calendar(
    accommodation_id: int,
    start_date: date = Query(..., description="Fecha de inicio (inclusive)"),
    end_date: date = Query(..., description="Fecha de fin (inclusive)"),
    db: Session = Depends(get_db),
) -> list[AvailabilityCalendarDayResponse]:
    return AvailabilityService(db).get_calendar(
        accommodation_id=accommodation_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{accommodation_id}/availability/check",
    response_model=AvailabilityCheckResponse,
    summary="Verificar disponibilidad para un período",
    description=(
        "Comprueba si el alojamiento está disponible para el período solicitado y calcula "
        "el precio total considerando tarifas de temporada. No requiere autenticación."
    ),
)
def check_availability(
    accommodation_id: int,
    check_in: date = Query(..., description="Fecha de entrada"),
    check_out: date = Query(..., description="Fecha de salida (exclusiva — última noche es check_out - 1)"),
    db: Session = Depends(get_db),
) -> AvailabilityCheckResponse:
    return AvailabilityService(db).check_availability(
        accommodation_id=accommodation_id,
        check_in=check_in,
        check_out=check_out,
    )


@router.get(
    "/{accommodation_id}/seasonal-prices",
    response_model=list[SeasonalPriceResponse],
    summary="Listar precios de temporada",
    description="Retorna las tarifas especiales configuradas para el alojamiento. No requiere autenticación.",
)
def list_seasonal_prices(
    accommodation_id: int,
    db: Session = Depends(get_db),
) -> list[SeasonalPriceResponse]:
    return AvailabilityService(db).list_seasonal_prices(accommodation_id)


# ── Authenticated endpoints ──────────────────────────────────────────────────

@router.post(
    "/{accommodation_id}/availability/blocked-dates",
    response_model=list[AvailabilityBlockResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bloquear fechas",
    description="Bloquea una o más fechas para el alojamiento. Solo el propietario o superusuario.",
)
def block_dates(
    accommodation_id: int,
    data: AvailabilityBlockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[AvailabilityBlockResponse]:
    return AvailabilityService(db).block_dates(
        accommodation_id=accommodation_id,
        dates=data.dates,
        reason=data.reason,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )


@router.delete(
    "/{accommodation_id}/availability/blocked-dates/{blocked_date}",
    response_model=AvailabilityBlockResponse,
    summary="Desbloquear fecha",
    description="Elimina el bloqueo de una fecha específica. Solo el propietario o superusuario.",
)
def unblock_date(
    accommodation_id: int,
    blocked_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AvailabilityBlockResponse:
    return AvailabilityService(db).unblock_date(
        accommodation_id=accommodation_id,
        date=blocked_date,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )


@router.post(
    "/{accommodation_id}/seasonal-prices",
    response_model=SeasonalPriceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear precio de temporada",
    description=(
        "Crea una tarifa especial para un rango de fechas. Los rangos no pueden solaparse. "
        "Solo el propietario o superusuario."
    ),
)
def create_seasonal_price(
    accommodation_id: int,
    data: SeasonalPriceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SeasonalPriceResponse:
    return AvailabilityService(db).create_seasonal_price(
        accommodation_id=accommodation_id,
        data=data,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )


@router.put(
    "/{accommodation_id}/seasonal-prices/{price_id}",
    response_model=SeasonalPriceResponse,
    summary="Actualizar precio de temporada",
    description="Actualiza una tarifa de temporada existente. Solo el propietario o superusuario.",
)
def update_seasonal_price(
    accommodation_id: int,
    price_id: int,
    data: SeasonalPriceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SeasonalPriceResponse:
    return AvailabilityService(db).update_seasonal_price(
        accommodation_id=accommodation_id,
        price_id=price_id,
        data=data,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )


@router.delete(
    "/{accommodation_id}/seasonal-prices/{price_id}",
    response_model=SeasonalPriceResponse,
    summary="Eliminar precio de temporada",
    description="Elimina una tarifa de temporada. Solo el propietario o superusuario.",
)
def delete_seasonal_price(
    accommodation_id: int,
    price_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SeasonalPriceResponse:
    return AvailabilityService(db).delete_seasonal_price(
        accommodation_id=accommodation_id,
        price_id=price_id,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
