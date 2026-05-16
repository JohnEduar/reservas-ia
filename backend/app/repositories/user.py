from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def get_active(self, *, skip: int = 0, limit: int = 100) -> list[User]:
        stmt = select(User).where(User.is_active.is_(True)).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())
