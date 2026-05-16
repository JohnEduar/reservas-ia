from typing import Any, Generic, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session) -> None:
        self.model = model
        self.db = db

    def get(self, id: int) -> ModelType | None:
        return self.db.get(self.model, id)

    def get_multi(self, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> ModelType | None:
        db_obj = self.get(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
        return db_obj

    def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        return self.db.scalar(stmt) or 0

    def exists(self, id: int) -> bool:
        return self.get(id) is not None
