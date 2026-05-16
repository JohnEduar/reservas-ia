from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    def register(self, user_in: UserCreate) -> User:
        if self.repo.get_by_email(user_in.email):
            raise EmailAlreadyRegisteredError(user_in.email)
        return self.repo.create({
            "email": user_in.email,
            "hashed_password": hash_password(user_in.password),
            "full_name": user_in.full_name,
        })
