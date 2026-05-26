from fastapi import APIRouter

from app.api.v1.endpoints import (
    accommodation_reservations,
    accommodations,
    amenities,
    auth,
    availability,
    health,
    reservations,
    users,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(accommodations.router, prefix="/accommodations", tags=["Accommodations"])
api_router.include_router(amenities.router, prefix="/amenities", tags=["Amenities"])
api_router.include_router(availability.router, prefix="/accommodations", tags=["Availability"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])
api_router.include_router(
    accommodation_reservations.router, prefix="/accommodations", tags=["Reservations"]
)
