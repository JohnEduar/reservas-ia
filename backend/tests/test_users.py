"""Tests for Issue #7 — User module (CRUD, schemas, soft delete, email validation)."""
import pytest
from fastapi.testclient import TestClient

from tests.conftest import login, register, promote_superuser


# ── Registration ──────────────────────────────────────────────────────────────

def test_register_returns_user_data(client):
    resp = client.post("/api/v1/users/", json={
        "email": "new@test.com", "password": "password123", "full_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert data["full_name"] == "New User"
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_without_full_name(client):
    resp = client.post("/api/v1/users/", json={
        "email": "noname@test.com", "password": "password123",
    })
    assert resp.status_code == 201
    assert resp.json()["full_name"] is None


def test_register_duplicate_email_returns_409(client):
    client.post("/api/v1/users/", json={"email": "dup@test.com", "password": "password123"})
    resp = client.post("/api/v1/users/", json={"email": "dup@test.com", "password": "other1234"})
    assert resp.status_code == 409


def test_register_invalid_email_returns_422(client):
    resp = client.post("/api/v1/users/", json={"email": "not-an-email", "password": "password123"})
    assert resp.status_code == 422


def test_register_short_password_returns_422(client):
    resp = client.post("/api/v1/users/", json={"email": "short@test.com", "password": "abc"})
    assert resp.status_code == 422


# ── Authentication ────────────────────────────────────────────────────────────

def test_login_returns_access_token(client):
    register(client, "login@test.com")
    resp = client.post("/api/v1/auth/token",
                       data={"username": "login@test.com", "password": "password123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_wrong_password_returns_401(client):
    register(client, "wp@test.com")
    resp = client.post("/api/v1/auth/token",
                       data={"username": "wp@test.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_nonexistent_user_returns_401(client):
    resp = client.post("/api/v1/auth/token",
                       data={"username": "ghost@test.com", "password": "password123"})
    assert resp.status_code == 401


def test_login_inactive_user_returns_403(client, superuser, db):
    register(client, "inactive@test.com")
    from app.repositories.user import UserRepository
    UserRepository(db).update(
        UserRepository(db).get_by_email("inactive@test.com"), {"is_active": False}
    )
    resp = client.post("/api/v1/auth/token",
                       data={"username": "inactive@test.com", "password": "password123"})
    assert resp.status_code == 403


# ── Own profile ───────────────────────────────────────────────────────────────

def test_get_me_returns_own_data(client, normal_user):
    resp = client.get("/api/v1/users/me", headers=normal_user["headers"])
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"


def test_get_me_requires_auth(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_update_me_full_name(client, normal_user):
    resp = client.put("/api/v1/users/me", json={"full_name": "Updated"},
                      headers=normal_user["headers"])
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated"


def test_update_me_email(client, normal_user):
    resp = client.put("/api/v1/users/me", json={"email": "newemail@test.com"},
                      headers=normal_user["headers"])
    assert resp.status_code == 200
    assert resp.json()["email"] == "newemail@test.com"


def test_update_me_email_already_taken_returns_409(client, normal_user):
    register(client, "taken@test.com")
    resp = client.put("/api/v1/users/me", json={"email": "taken@test.com"},
                      headers=normal_user["headers"])
    assert resp.status_code == 409


# ── Superuser operations ──────────────────────────────────────────────────────

def test_list_users_requires_superuser(client, normal_user):
    resp = client.get("/api/v1/users/", headers=normal_user["headers"])
    assert resp.status_code == 403


def test_list_users_returns_all_active(client, superuser, normal_user):
    resp = client.get("/api/v1/users/", headers=superuser["headers"])
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "user@test.com" in emails
    assert "admin@test.com" in emails


def test_get_user_by_id_as_superuser(client, superuser, normal_user):
    user_id = normal_user["user"]["id"]
    resp = client.get(f"/api/v1/users/{user_id}", headers=superuser["headers"])
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"


def test_get_nonexistent_user_returns_404(client, superuser):
    resp = client.get("/api/v1/users/9999", headers=superuser["headers"])
    assert resp.status_code == 404


def test_update_user_as_superuser(client, superuser, normal_user):
    user_id = normal_user["user"]["id"]
    resp = client.put(f"/api/v1/users/{user_id}", json={"full_name": "Changed by Admin"},
                      headers=superuser["headers"])
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Changed by Admin"


# ── Soft delete ───────────────────────────────────────────────────────────────

def test_soft_delete_sets_inactive(client, superuser, normal_user):
    user_id = normal_user["user"]["id"]
    resp = client.delete(f"/api/v1/users/{user_id}", headers=superuser["headers"])
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_soft_deleted_user_cannot_login(client, superuser, normal_user):
    user_id = normal_user["user"]["id"]
    client.delete(f"/api/v1/users/{user_id}", headers=superuser["headers"])
    resp = client.post("/api/v1/auth/token",
                       data={"username": "user@test.com", "password": "password123"})
    assert resp.status_code == 403


def test_soft_deleted_user_excluded_from_list(client, superuser, normal_user):
    user_id = normal_user["user"]["id"]
    client.delete(f"/api/v1/users/{user_id}", headers=superuser["headers"])
    resp = client.get("/api/v1/users/", headers=superuser["headers"])
    emails = [u["email"] for u in resp.json()]
    assert "user@test.com" not in emails


def test_soft_delete_requires_superuser(client, normal_user):
    user_id = normal_user["user"]["id"]
    resp = client.delete(f"/api/v1/users/{user_id}", headers=normal_user["headers"])
    assert resp.status_code == 403
