from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate


class UserNotFoundError(Exception):
    pass


class EmailAlreadyInUseError(Exception):
    pass


class UserService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def get_by_id(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    def get_all(self, *, skip: int = 0, limit: int = 100) -> list[User]:
        return self.repo.get_active(skip=skip, limit=limit)

    def update(self, user_id: int, user_in: UserUpdate) -> User:
        user = self.get_by_id(user_id)
        updates: dict = {}
        if user_in.email is not None:
            if self.repo.email_exists_for_other(user_in.email, user_id):
                raise EmailAlreadyInUseError(user_in.email)
            updates["email"] = user_in.email
        if user_in.full_name is not None:
            updates["full_name"] = user_in.full_name
        if user_in.password is not None:
            updates["hashed_password"] = hash_password(user_in.password)
        return self.repo.update(user, updates)

    def soft_delete(self, user_id: int) -> User:
        user = self.get_by_id(user_id)
        return self.repo.update(user, {"is_active": False})
