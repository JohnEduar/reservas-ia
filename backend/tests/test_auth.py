"""Tests for Issue #14 — Auth module: token lifecycle, refresh, and token validation."""
from app.core.security import create_access_token, create_refresh_token
from tests.conftest import login, register


# ── Login response structure ──────────────────────────────────────────────────

def test_login_response_has_required_fields(client):
    register(client, "shape@test.com")
    resp = client.post("/api/v1/auth/token",
                       data={"username": "shape@test.com", "password": "password123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["expires_in"], int)
    assert data["expires_in"] > 0


def test_login_access_token_is_non_empty_string(client):
    register(client, "token@test.com")
    resp = client.post("/api/v1/auth/token",
                       data={"username": "token@test.com", "password": "password123"})
    assert isinstance(resp.json()["access_token"], str)
    assert len(resp.json()["access_token"]) > 20


def test_login_password_not_exposed_in_response(client):
    register(client, "nopw@test.com")
    resp = client.post("/api/v1/auth/token",
                       data={"username": "nopw@test.com", "password": "password123"})
    data = resp.json()
    assert "password" not in data
    assert "hashed_password" not in data


# ── Token refresh — happy path ────────────────────────────────────────────────

def test_refresh_returns_new_access_token(client, db):
    user = register(client, "refresh@test.com")
    refresh_token = create_refresh_token(user["id"])

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_refresh_new_token_grants_access(client, db):
    user = register(client, "reuse@test.com")
    refresh_token = create_refresh_token(user["id"])

    new_token = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    ).json()["access_token"]

    resp = client.get("/api/v1/users/me",
                      headers={"Authorization": f"Bearer {new_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "reuse@test.com"


# ── Token refresh — 401 cases ─────────────────────────────────────────────────

def test_refresh_with_garbage_token_returns_401(client):
    resp = client.post("/api/v1/auth/refresh",
                       json={"refresh_token": "not.a.valid.jwt"})
    assert resp.status_code == 401


def test_refresh_with_access_token_returns_401(client):
    """Access tokens must not be accepted as refresh tokens."""
    user = register(client, "wrongtype@test.com")
    access_token = create_access_token(user["id"])

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


def test_refresh_for_inactive_user_returns_401(client, db):
    user = register(client, "inact@test.com")
    refresh_token = create_refresh_token(user["id"])

    from app.repositories.user import UserRepository
    UserRepository(db).update(
        UserRepository(db).get_by_email("inact@test.com"), {"is_active": False}
    )

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


def test_refresh_for_nonexistent_user_returns_401(client):
    refresh_token = create_refresh_token(99999)
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


def test_refresh_missing_body_returns_422(client):
    resp = client.post("/api/v1/auth/refresh", json={})
    assert resp.status_code == 422


# ── Protected endpoint access patterns ────────────────────────────────────────

def test_access_with_valid_token(client, normal_user):
    resp = client.get("/api/v1/users/me", headers=normal_user["headers"])
    assert resp.status_code == 200


def test_access_without_token_returns_401(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_access_with_garbage_bearer_returns_401(client):
    resp = client.get("/api/v1/users/me",
                      headers={"Authorization": "Bearer garbage.token.here"})
    assert resp.status_code == 401


def test_access_with_malformed_header_returns_401(client):
    resp = client.get("/api/v1/users/me",
                      headers={"Authorization": "NotBearer sometoken"})
    assert resp.status_code == 401


def test_access_with_refresh_token_returns_401(client):
    """Refresh tokens must not be accepted as access tokens on protected endpoints."""
    user = register(client, "rfaccess@test.com")
    refresh_token = create_refresh_token(user["id"])

    resp = client.get("/api/v1/users/me",
                      headers={"Authorization": f"Bearer {refresh_token}"})
    assert resp.status_code == 401


def test_tokens_for_different_users_are_different(client):
    user_a = register(client, "usera@test.com")
    user_b = register(client, "userb@test.com")
    token_a = create_access_token(user_a["id"])
    token_b = create_access_token(user_b["id"])
    assert token_a != token_b
