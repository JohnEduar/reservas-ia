from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.accommodation import (
    AccommodationForbiddenError,
    AccommodationNotFoundError,
    AmenityAlreadyExistsError,
    AmenityNotFoundError,
    ImageNotFoundError,
    InvalidImageError,
)
from app.services.auth import EmailAlreadyRegisteredError
from app.services.availability import (
    AccommodationNotAvailableError,
    DateAlreadyBlockedError,
    DateNotBlockedError,
    InvalidDateRangeError,
    SeasonalPriceConflictError,
    SeasonalPriceNotFoundError,
)
from app.services.reservation import (
    GuestCountExceededError,
    InvalidReservationDateError,
    ReservationAlreadyCancelledError,
    ReservationConflictError,
    ReservationForbiddenError,
    ReservationNotFoundError,
)
from app.services.review import (
    DuplicateReviewError,
    ReviewForbiddenError,
    ReviewNotFoundError,
    SelfReviewError,
)
from app.services.user import EmailAlreadyInUseError, UserNotFoundError

_EXCEPTION_STATUS_MAP: dict[type[Exception], tuple[int, str]] = {
    UserNotFoundError:                (404, "User not found"),
    EmailAlreadyInUseError:           (409, "Email already in use"),
    EmailAlreadyRegisteredError:      (409, "Email already registered"),
    AccommodationNotFoundError:       (404, "Accommodation not found"),
    AccommodationForbiddenError:      (403, "Not enough permissions"),
    ImageNotFoundError:               (404, "Image not found"),
    InvalidImageError:                (415, "Unsupported media type"),
    AmenityNotFoundError:             (422, "Amenity not found"),
    AmenityAlreadyExistsError:        (409, "Amenity already exists"),
    DateAlreadyBlockedError:          (409, "Date is already blocked"),
    DateNotBlockedError:              (404, "Blocked date not found"),
    AccommodationNotAvailableError:   (409, "Accommodation not available for the requested dates"),
    SeasonalPriceNotFoundError:       (404, "Seasonal price not found"),
    SeasonalPriceConflictError:       (409, "Seasonal price range overlaps an existing one"),
    InvalidDateRangeError:            (422, "Invalid date range"),
    ReservationNotFoundError:         (404, "Reservation not found"),
    ReservationForbiddenError:        (403, "Not enough permissions"),
    ReservationConflictError:         (409, "Requested dates are not available"),
    ReservationAlreadyCancelledError: (409, "Reservation is already cancelled"),
    GuestCountExceededError:          (422, "Guest count exceeds accommodation capacity"),
    InvalidReservationDateError:      (422, "check_in must be before check_out"),
    ReviewNotFoundError:              (404, "Review not found"),
    ReviewForbiddenError:             (403, "Not enough permissions"),
    DuplicateReviewError:             (409, "You have already reviewed this accommodation"),
    SelfReviewError:                  (422, "Owners cannot review their own accommodation"),
}


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code, detail = _EXCEPTION_STATUS_MAP.get(type(exc), (500, "Internal server error"))
    return JSONResponse(status_code=status_code, content={"detail": detail})


def register_exception_handlers(app) -> None:
    for exc_class in _EXCEPTION_STATUS_MAP:
        app.add_exception_handler(exc_class, domain_exception_handler)
