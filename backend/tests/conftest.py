from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure uploads dir exists before StaticFiles mount (triggered at app import)
Path("uploads/accommodations").mkdir(parents=True, exist_ok=True)

from app.db.database import Base  # noqa: E402
from app.db.deps import get_db    # noqa: E402
from app.main import app          # noqa: E402

# ── SQLite in-memory test database ──────────────────────────────────────────
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


# ── Per-test DB reset ────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


# ── Core fixtures ─────────────────────────────────────────────────────────────
@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db():
    session = _TestingSession()
    try:
        yield session
    finally:
        session.close()


# ── Auth helpers ──────────────────────────────────────────────────────────────
def register(client: TestClient, email: str, password: str = "password123",
             full_name: str = "Test User") -> dict:
    resp = client.post("/api/v1/users/", json={
        "email": email, "password": password, "full_name": full_name,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def login(client: TestClient, email: str, password: str = "password123") -> str:
    resp = client.post("/api/v1/auth/token",
                       data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def promote_superuser(db, email: str) -> None:
    from app.repositories.user import UserRepository
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    repo.update(user, {"is_superuser": True})


# ── Reusable user fixtures ────────────────────────────────────────────────────
@pytest.fixture
def normal_user(client, db):
    user = register(client, "user@test.com")
    token = login(client, "user@test.com")
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def superuser(client, db):
    user = register(client, "admin@test.com", password="Admin1234!", full_name="Admin")
    promote_superuser(db, "admin@test.com")
    token = login(client, "admin@test.com", password="Admin1234!")
    return {"user": user, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
