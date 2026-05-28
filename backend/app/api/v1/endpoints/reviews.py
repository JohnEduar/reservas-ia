from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.deps import get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewSummary
from app.services.review import ReviewService

router = APIRouter()


@router.get(
    "/accommodations/{accommodation_id}",
    response_model=ReviewSummary,
    summary="Listar reseñas de un alojamiento (público)",
)
def list_reviews(
    accommodation_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ReviewSummary:
    svc = ReviewService(db)
    summary = svc.get_summary(accommodation_id)
    return ReviewSummary(
        reviews=summary["reviews"][skip : skip + limit],
        average_rating=summary["average_rating"],
        total_reviews=summary["total_reviews"],
    )


@router.post(
    "/",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reseña",
    description="El usuario autenticado crea una reseña para un alojamiento. No puede ser el propietario ni dejar reseña duplicada.",
)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReviewResponse:
    return ReviewService(db).create(reviewer_id=current_user.id, data=data)


@router.delete(
    "/{review_id}",
    response_model=ReviewResponse,
    summary="Eliminar reseña",
    description="El autor de la reseña o un superusuario puede eliminarla.",
)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReviewResponse:
    return ReviewService(db).delete(
        review_id=review_id,
        requester_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
