from sqlalchemy.orm import Session

from app.models.review import Review
from app.repositories.accommodation import AccommodationRepository
from app.repositories.review import ReviewRepository
from app.schemas.review import ReviewCreate
from app.services.accommodation import AccommodationNotFoundError


class ReviewNotFoundError(Exception):
    pass


class ReviewForbiddenError(Exception):
    pass


class DuplicateReviewError(Exception):
    pass


class SelfReviewError(Exception):
    pass


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.repo = ReviewRepository(db)
        self.accommodation_repo = AccommodationRepository(db)

    def get_by_id(self, review_id: int) -> Review:
        review = self.repo.get(review_id)
        if not review:
            raise ReviewNotFoundError(review_id)
        return review

    def list_by_accommodation(
        self, accommodation_id: int, *, skip: int = 0, limit: int = 50
    ) -> list[Review]:
        if not self.accommodation_repo.get(accommodation_id):
            raise AccommodationNotFoundError(accommodation_id)
        return self.repo.get_by_accommodation(accommodation_id, skip=skip, limit=limit)

    def get_summary(self, accommodation_id: int) -> dict:
        if not self.accommodation_repo.get(accommodation_id):
            raise AccommodationNotFoundError(accommodation_id)
        reviews = self.repo.get_by_accommodation(accommodation_id, limit=1000)
        return {
            "reviews": reviews,
            "average_rating": self.repo.get_average_rating(accommodation_id),
            "total_reviews": self.repo.count_by_accommodation(accommodation_id),
        }

    def create(self, reviewer_id: int, data: ReviewCreate) -> Review:
        acc = self.accommodation_repo.get(data.accommodation_id)
        if not acc:
            raise AccommodationNotFoundError(data.accommodation_id)

        if acc.owner_id == reviewer_id:
            raise SelfReviewError()

        if self.repo.get_user_review(reviewer_id, data.accommodation_id):
            raise DuplicateReviewError()

        return self.repo.create({
            "accommodation_id": data.accommodation_id,
            "reviewer_id": reviewer_id,
            "rating": data.rating,
            "comment": data.comment,
        })

    def delete(self, review_id: int, requester_id: int, is_superuser: bool) -> Review:
        review = self.get_by_id(review_id)
        if not is_superuser and review.reviewer_id != requester_id:
            raise ReviewForbiddenError()
        self.repo.db.delete(review)
        self.repo.db.commit()
        return review
