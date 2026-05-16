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

    def email_exists_for_other(self, email: str, exclude_id: int) -> bool:
        stmt = select(User).where(User.email == email, User.id != exclude_id)
        return self.db.scalar(stmt) is not None

    def soft_delete(self, id: int) -> User | None:
        user = self.get(id)
        if user:
            return self.update(user, {"is_active": False})
        return None
