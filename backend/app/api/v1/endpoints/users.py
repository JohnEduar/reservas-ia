from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_active_user, get_current_superuser
from app.db.deps import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de usuario",
    description="Crea un nuevo usuario. El email debe ser único.",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    return AuthService(db).register(user_in)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Listar usuarios activos",
    description="Retorna la lista paginada de usuarios activos. Solo superusuarios.",
)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[UserResponse]:
    return UserService(db).get_all(skip=skip, limit=limit)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Perfil del usuario autenticado",
    description="Retorna los datos del usuario dueño del access token.",
)
def get_me(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Actualizar perfil propio",
    description="Actualiza los datos del usuario autenticado.",
)
def update_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return UserService(db).update(current_user.id, user_in)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obtener usuario por ID",
    description="Retorna un usuario específico. Solo superusuarios.",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> UserResponse:
    return UserService(db).get_by_id(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario",
    description="Actualiza los datos de un usuario. Solo superusuarios.",
)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> UserResponse:
    return UserService(db).update(user_id, user_in)


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="Eliminación lógica de usuario",
    description="Desactiva un usuario (soft delete). Solo superusuarios.",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> UserResponse:
    return UserService(db).soft_delete(user_id)
