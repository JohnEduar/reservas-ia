from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import InvalidTokenError, decode_token
from app.db.deps import get_db
from app.models.user import User

# Tells FastAPI (and Swagger) that endpoints use Bearer token auth.
# tokenUrl points to the login endpoint that will issue the token.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/token"
)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},  # required by RFC 6750
)

_FORBIDDEN = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not enough permissions",
)

_INACTIVE = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Inactive user",
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        raise _UNAUTHORIZED

    if payload.type != "access":
        raise _UNAUTHORIZED

    user = db.get(User, int(payload.sub))
    if user is None:
        raise _UNAUTHORIZED

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise _INACTIVE
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise _FORBIDDEN
    return current_user
