from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

from sqlalchemy import text
# from app.core.database import engine


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # verifica la conexión antes de usarla del pool
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,    # recicla conexiones cada hora (evita timeout de MySQL)
)


with engine.connect() as connection:
    result = connection.execute(text(""))
    print("Database connection successful!")


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass
