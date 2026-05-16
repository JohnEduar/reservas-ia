from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user
from app.db.deps import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthService, EmailAlreadyRegisteredError

router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de usuario",
    description="Crea un nuevo usuario. El email debe ser único.",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    try:
        return AuthService(db).register(user_in)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Perfil del usuario autenticado",
    description="Retorna los datos del usuario dueño del access token.",
)
def get_me(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    return current_user
