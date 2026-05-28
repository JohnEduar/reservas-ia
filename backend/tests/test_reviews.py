"""Tests for Issue #13 — Reviews and ratings module."""
import pytest
from fastapi.testclient import TestClient

from tests.conftest import login, register, promote_superuser


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_accommodation(client, headers, **overrides):
    payload = {
        "title": "Cabaña en el Lago",
        "location": "Medellin",
        "price_per_night": "200.00",
        "max_guests": 5,
        "amenity_ids": [],
        **overrides,
    }
    resp = client.post("/api/v1/accommodations/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_review(client, headers, accommodation_id: int, rating: int = 5, comment: str | None = "Great place"):
    resp = client.post(
        "/api/v1/reviews/",
        json={"accommodation_id": accommodation_id, "rating": rating, "comment": comment},
        headers=headers,
    )
    return resp


# ── Happy path ────────────────────────────────────────────────────────────────

def test_create_review_happy_path(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    resp = create_review(client, normal_user["headers"], acc["id"], rating=4, comment="Muy bueno")
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 4
    assert data["comment"] == "Muy bueno"
    assert data["accommodation_id"] == acc["id"]
    assert data["reviewer_id"] == normal_user["user"]["id"]


def test_create_review_without_comment(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    resp = create_review(client, normal_user["headers"], acc["id"], rating=3, comment=None)
    assert resp.status_code == 201
    assert resp.json()["comment"] is None


def test_list_reviews_is_public(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    create_review(client, normal_user["headers"], acc["id"], rating=5)
    resp = client.get(f"/api/v1/reviews/accommodations/{acc['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_reviews"] == 1
    assert data["average_rating"] == 5.0
    assert len(data["reviews"]) == 1


def test_average_rating_multiple_reviews(client, superuser, db):
    acc = create_accommodation(client, superuser["headers"])
    # Create two additional users
    user_a = register(client, "a@test.com")
    token_a = login(client, "a@test.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    user_b = register(client, "b@test.com")
    token_b = login(client, "b@test.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    create_review(client, headers_a, acc["id"], rating=4)
    create_review(client, headers_b, acc["id"], rating=2)

    resp = client.get(f"/api/v1/reviews/accommodations/{acc['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_reviews"] == 2
    assert data["average_rating"] == pytest.approx(3.0)


def test_delete_own_review(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    review = create_review(client, normal_user["headers"], acc["id"]).json()
    resp = client.delete(f"/api/v1/reviews/{review['id']}", headers=normal_user["headers"])
    assert resp.status_code == 200
    # Verify removed
    summary = client.get(f"/api/v1/reviews/accommodations/{acc['id']}").json()
    assert summary["total_reviews"] == 0


def test_superuser_can_delete_any_review(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    review = create_review(client, normal_user["headers"], acc["id"]).json()
    resp = client.delete(f"/api/v1/reviews/{review['id']}", headers=superuser["headers"])
    assert resp.status_code == 200


# ── 401 Unauthorized ─────────────────────────────────────────────────────────

def test_create_review_requires_auth(client, superuser):
    acc = create_accommodation(client, superuser["headers"])
    resp = client.post(
        "/api/v1/reviews/",
        json={"accommodation_id": acc["id"], "rating": 5},
    )
    assert resp.status_code == 401


def test_delete_review_requires_auth(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    review = create_review(client, normal_user["headers"], acc["id"]).json()
    resp = client.delete(f"/api/v1/reviews/{review['id']}")
    assert resp.status_code == 401


# ── 403 Forbidden ────────────────────────────────────────────────────────────

def test_cannot_delete_other_users_review(client, normal_user, superuser, db):
    acc = create_accommodation(client, superuser["headers"])
    review = create_review(client, normal_user["headers"], acc["id"]).json()

    other = register(client, "other@test.com")
    token = login(client, "other@test.com")
    other_headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete(f"/api/v1/reviews/{review['id']}", headers=other_headers)
    assert resp.status_code == 403


# ── 404 Not Found ─────────────────────────────────────────────────────────────

def test_list_reviews_accommodation_not_found(client):
    resp = client.get("/api/v1/reviews/accommodations/99999")
    assert resp.status_code == 404


def test_delete_review_not_found(client, normal_user):
    resp = client.delete("/api/v1/reviews/99999", headers=normal_user["headers"])
    assert resp.status_code == 404


# ── 409 Conflict ─────────────────────────────────────────────────────────────

def test_duplicate_review_returns_409(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    create_review(client, normal_user["headers"], acc["id"], rating=5)
    resp = create_review(client, normal_user["headers"], acc["id"], rating=3)
    assert resp.status_code == 409


# ── 422 Unprocessable ────────────────────────────────────────────────────────

def test_rating_out_of_range_returns_422(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    resp = client.post(
        "/api/v1/reviews/",
        json={"accommodation_id": acc["id"], "rating": 6},
        headers=normal_user["headers"],
    )
    assert resp.status_code == 422


def test_rating_zero_returns_422(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    resp = client.post(
        "/api/v1/reviews/",
        json={"accommodation_id": acc["id"], "rating": 0},
        headers=normal_user["headers"],
    )
    assert resp.status_code == 422


def test_owner_cannot_review_own_accommodation(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = create_review(client, normal_user["headers"], acc["id"], rating=5)
    assert resp.status_code == 422


def test_accommodation_not_found_on_create(client, normal_user):
    resp = client.post(
        "/api/v1/reviews/",
        json={"accommodation_id": 99999, "rating": 5},
        headers=normal_user["headers"],
    )
    assert resp.status_code == 404
