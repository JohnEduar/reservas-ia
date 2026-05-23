"""Tests for Issue #8 — Accommodations module (amenities, CRUD, filters, ownership, images)."""
import io

import pytest
from fastapi.testclient import TestClient

from tests.conftest import login, register, promote_superuser


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_accommodation(client, headers, **overrides):
    payload = {
        "title": "Glamping Test",
        "location": "Bogota",
        "price_per_night": "150.00",
        "max_guests": 4,
        "amenity_ids": [],
        **overrides,
    }
    resp = client.post("/api/v1/accommodations/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_amenity(client, headers, name="WiFi", icon=None):
    resp = client.post("/api/v1/amenities/", json={"name": name, "icon": icon},
                       headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def fake_image(filename="photo.jpg", content_type="image/jpeg"):
    return ("file", (filename, io.BytesIO(b"fake-image-bytes"), content_type))


# ── Amenities ─────────────────────────────────────────────────────────────────

def test_list_amenities_is_public(client):
    resp = client.get("/api/v1/amenities/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_amenity_as_superuser(client, superuser):
    resp = client.post("/api/v1/amenities/", json={"name": "Pool", "icon": "pool"},
                       headers=superuser["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Pool"
    assert data["icon"] == "pool"
    assert "id" in data


def test_create_amenity_duplicate_returns_409(client, superuser):
    create_amenity(client, superuser["headers"], name="Jacuzzi")
    resp = client.post("/api/v1/amenities/", json={"name": "Jacuzzi"},
                       headers=superuser["headers"])
    assert resp.status_code == 409


def test_create_amenity_as_normal_user_returns_403(client, normal_user):
    resp = client.post("/api/v1/amenities/", json={"name": "BBQ"},
                       headers=normal_user["headers"])
    assert resp.status_code == 403


def test_create_amenity_unauthenticated_returns_401(client):
    resp = client.post("/api/v1/amenities/", json={"name": "Parking"})
    assert resp.status_code == 401


# ── Accommodation creation ────────────────────────────────────────────────────

def test_create_accommodation_returns_201(client, normal_user):
    resp = client.post("/api/v1/accommodations/", json={
        "title": "Forest Dome",
        "location": "Medellin",
        "price_per_night": "200.00",
        "max_guests": 2,
        "amenity_ids": [],
    }, headers=normal_user["headers"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Forest Dome"
    assert data["location"] == "Medellin"
    assert float(data["price_per_night"]) == 200.0
    assert data["max_guests"] == 2
    assert data["is_active"] is True
    assert data["owner_id"] == normal_user["user"]["id"]
    assert "id" in data
    assert "created_at" in data


def test_create_accommodation_requires_auth(client):
    resp = client.post("/api/v1/accommodations/", json={
        "title": "Forest Dome",
        "location": "Medellin",
        "price_per_night": "200.00",
        "max_guests": 2,
    })
    assert resp.status_code == 401


def test_create_accommodation_with_amenities(client, normal_user, superuser):
    amenity = create_amenity(client, superuser["headers"], name="Sauna")
    resp = client.post("/api/v1/accommodations/", json={
        "title": "Sauna Cabin",
        "location": "Cali",
        "price_per_night": "99.99",
        "max_guests": 3,
        "amenity_ids": [amenity["id"]],
    }, headers=normal_user["headers"])
    assert resp.status_code == 201
    amenity_ids = [a["id"] for a in resp.json()["amenities"]]
    assert amenity["id"] in amenity_ids


def test_create_accommodation_invalid_amenity_returns_422(client, normal_user):
    resp = client.post("/api/v1/accommodations/", json={
        "title": "Bad Amenity",
        "location": "Bogota",
        "price_per_night": "50.00",
        "max_guests": 1,
        "amenity_ids": [9999],
    }, headers=normal_user["headers"])
    assert resp.status_code == 422


def test_create_accommodation_short_title_returns_422(client, normal_user):
    resp = client.post("/api/v1/accommodations/", json={
        "title": "Hi",
        "location": "Bogota",
        "price_per_night": "50.00",
        "max_guests": 1,
    }, headers=normal_user["headers"])
    assert resp.status_code == 422


def test_create_accommodation_zero_price_returns_422(client, normal_user):
    resp = client.post("/api/v1/accommodations/", json={
        "title": "Zero Price",
        "location": "Bogota",
        "price_per_night": "0.00",
        "max_guests": 1,
    }, headers=normal_user["headers"])
    assert resp.status_code == 422


def test_create_accommodation_guests_out_of_range_returns_422(client, normal_user):
    resp = client.post("/api/v1/accommodations/", json={
        "title": "Too Many",
        "location": "Bogota",
        "price_per_night": "100.00",
        "max_guests": 51,
    }, headers=normal_user["headers"])
    assert resp.status_code == 422


# ── Public listing & filters ──────────────────────────────────────────────────

def test_list_accommodations_is_public(client, normal_user):
    create_accommodation(client, normal_user["headers"])
    resp = client.get("/api/v1/accommodations/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_excludes_inactive(client, normal_user, superuser):
    acc = create_accommodation(client, normal_user["headers"])
    client.delete(f"/api/v1/accommodations/{acc['id']}", headers=normal_user["headers"])
    resp = client.get("/api/v1/accommodations/")
    ids = [a["id"] for a in resp.json()]
    assert acc["id"] not in ids


def test_filter_by_location(client, normal_user):
    create_accommodation(client, normal_user["headers"], title="Jungle Hut", location="Amazon")
    create_accommodation(client, normal_user["headers"], title="City Loft", location="Bogota")
    resp = client.get("/api/v1/accommodations/", params={"location": "Amazon"})
    assert resp.status_code == 200
    titles = [a["title"] for a in resp.json()]
    assert "Jungle Hut" in titles
    assert "City Loft" not in titles


def test_filter_by_min_price(client, normal_user):
    create_accommodation(client, normal_user["headers"], title="Cheap Stay", price_per_night="50.00")
    create_accommodation(client, normal_user["headers"], title="Luxury Tent", price_per_night="500.00")
    resp = client.get("/api/v1/accommodations/", params={"min_price": "200"})
    titles = [a["title"] for a in resp.json()]
    assert "Luxury Tent" in titles
    assert "Cheap Stay" not in titles


def test_filter_by_max_price(client, normal_user):
    create_accommodation(client, normal_user["headers"], title="Budget Dome", price_per_night="80.00")
    create_accommodation(client, normal_user["headers"], title="Premium Cabin", price_per_night="800.00")
    resp = client.get("/api/v1/accommodations/", params={"max_price": "100"})
    titles = [a["title"] for a in resp.json()]
    assert "Budget Dome" in titles
    assert "Premium Cabin" not in titles


def test_filter_by_min_guests(client, normal_user):
    create_accommodation(client, normal_user["headers"], title="Solo Nook", max_guests=1)
    create_accommodation(client, normal_user["headers"], title="Family Tent", max_guests=8)
    resp = client.get("/api/v1/accommodations/", params={"min_guests": 5})
    titles = [a["title"] for a in resp.json()]
    assert "Family Tent" in titles
    assert "Solo Nook" not in titles


def test_pagination_skip_limit(client, normal_user):
    for i in range(5):
        create_accommodation(client, normal_user["headers"], title=f"Place {i}")
    resp_all = client.get("/api/v1/accommodations/", params={"limit": 100})
    resp_page = client.get("/api/v1/accommodations/", params={"skip": 2, "limit": 2})
    assert resp_page.status_code == 200
    assert len(resp_page.json()) == 2


# ── Get single accommodation ──────────────────────────────────────────────────

def test_get_accommodation_by_id(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.get(f"/api/v1/accommodations/{acc['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == acc["id"]


def test_get_nonexistent_accommodation_returns_404(client):
    resp = client.get("/api/v1/accommodations/9999")
    assert resp.status_code == 404


# ── Update accommodation ──────────────────────────────────────────────────────

def test_owner_can_update_accommodation(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.put(f"/api/v1/accommodations/{acc['id']}",
                      json={"title": "Updated Title"},
                      headers=normal_user["headers"])
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


def test_non_owner_update_returns_403(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    resp = client.put(f"/api/v1/accommodations/{acc['id']}",
                      json={"title": "Hacked"},
                      headers=normal_user["headers"])
    assert resp.status_code == 403


def test_superuser_can_update_any_accommodation(client, normal_user, superuser):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.put(f"/api/v1/accommodations/{acc['id']}",
                      json={"title": "Admin Changed"},
                      headers=superuser["headers"])
    assert resp.status_code == 200
    assert resp.json()["title"] == "Admin Changed"


def test_update_nonexistent_accommodation_returns_404(client, normal_user):
    resp = client.put("/api/v1/accommodations/9999",
                      json={"title": "Ghost Update"},
                      headers=normal_user["headers"])
    assert resp.status_code == 404


# ── Soft delete ───────────────────────────────────────────────────────────────

def test_owner_can_soft_delete(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.delete(f"/api/v1/accommodations/{acc['id']}",
                         headers=normal_user["headers"])
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_non_owner_delete_returns_403(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    resp = client.delete(f"/api/v1/accommodations/{acc['id']}",
                         headers=normal_user["headers"])
    assert resp.status_code == 403


def test_superuser_can_delete_any(client, normal_user, superuser):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.delete(f"/api/v1/accommodations/{acc['id']}",
                         headers=superuser["headers"])
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_delete_requires_auth(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.delete(f"/api/v1/accommodations/{acc['id']}")
    assert resp.status_code == 401


# ── Image management ──────────────────────────────────────────────────────────

def test_upload_image_jpeg(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.post(
        f"/api/v1/accommodations/{acc['id']}/images",
        files=[fake_image("photo.jpg", "image/jpeg")],
        headers=normal_user["headers"],
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_primary"] is True
    assert data["url"].startswith("/uploads/")


def test_upload_image_png(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.post(
        f"/api/v1/accommodations/{acc['id']}/images",
        files=[fake_image("photo.png", "image/png")],
        headers=normal_user["headers"],
    )
    assert resp.status_code == 201


def test_upload_invalid_image_type_returns_415(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.post(
        f"/api/v1/accommodations/{acc['id']}/images",
        files=[fake_image("document.pdf", "application/pdf")],
        headers=normal_user["headers"],
    )
    assert resp.status_code == 415


def test_second_image_is_not_primary(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    client.post(f"/api/v1/accommodations/{acc['id']}/images",
                files=[fake_image()], headers=normal_user["headers"])
    resp = client.post(f"/api/v1/accommodations/{acc['id']}/images",
                       files=[fake_image()], headers=normal_user["headers"])
    assert resp.status_code == 201
    assert resp.json()["is_primary"] is False


def test_non_owner_upload_returns_403(client, normal_user, superuser):
    acc = create_accommodation(client, superuser["headers"])
    resp = client.post(
        f"/api/v1/accommodations/{acc['id']}/images",
        files=[fake_image()],
        headers=normal_user["headers"],
    )
    assert resp.status_code == 403


def test_delete_image(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    img = client.post(f"/api/v1/accommodations/{acc['id']}/images",
                      files=[fake_image()], headers=normal_user["headers"]).json()
    resp = client.delete(f"/api/v1/accommodations/{acc['id']}/images/{img['id']}",
                         headers=normal_user["headers"])
    assert resp.status_code == 200


def test_delete_primary_image_promotes_next(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    img1 = client.post(f"/api/v1/accommodations/{acc['id']}/images",
                       files=[fake_image()], headers=normal_user["headers"]).json()
    img2 = client.post(f"/api/v1/accommodations/{acc['id']}/images",
                       files=[fake_image()], headers=normal_user["headers"]).json()
    assert img1["is_primary"] is True
    assert img2["is_primary"] is False

    client.delete(f"/api/v1/accommodations/{acc['id']}/images/{img1['id']}",
                  headers=normal_user["headers"])

    detail = client.get(f"/api/v1/accommodations/{acc['id']}").json()
    remaining = detail["images"]
    assert len(remaining) == 1
    assert remaining[0]["is_primary"] is True


def test_set_primary_image(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    img1 = client.post(f"/api/v1/accommodations/{acc['id']}/images",
                       files=[fake_image()], headers=normal_user["headers"]).json()
    img2 = client.post(f"/api/v1/accommodations/{acc['id']}/images",
                       files=[fake_image()], headers=normal_user["headers"]).json()

    resp = client.patch(
        f"/api/v1/accommodations/{acc['id']}/images/{img2['id']}/primary",
        headers=normal_user["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["is_primary"] is True

    detail = client.get(f"/api/v1/accommodations/{acc['id']}").json()
    primaries = [i for i in detail["images"] if i["is_primary"]]
    assert len(primaries) == 1
    assert primaries[0]["id"] == img2["id"]


def test_delete_nonexistent_image_returns_404(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.delete(f"/api/v1/accommodations/{acc['id']}/images/9999",
                         headers=normal_user["headers"])
    assert resp.status_code == 404
