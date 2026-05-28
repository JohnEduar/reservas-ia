from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import Review
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, db: Session) -> None:
        super().__init__(Review, db)

    def get_by_accommodation(
        self, accommodation_id: int, *, skip: int = 0, limit: int = 50
    ) -> list[Review]:
        stmt = (
            select(Review)
            .where(Review.accommodation_id == accommodation_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_user_review(self, user_id: int, accommodation_id: int) -> Review | None:
        stmt = select(Review).where(
            Review.reviewer_id == user_id,
            Review.accommodation_id == accommodation_id,
        )
        return self.db.scalars(stmt).first()

    def get_average_rating(self, accommodation_id: int) -> float | None:
        stmt = select(func.avg(Review.rating)).where(
            Review.accommodation_id == accommodation_id
        )
        result = self.db.scalar(stmt)
        return float(result) if result is not None else None

    def count_by_accommodation(self, accommodation_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Review)
            .where(Review.accommodation_id == accommodation_id)
        )
        return self.db.scalar(stmt) or 0
