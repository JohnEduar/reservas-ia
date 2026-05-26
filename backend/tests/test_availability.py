"""Tests for availability engine — blocked dates, calendar, check, and seasonal prices."""
import pytest
from fastapi.testclient import TestClient

from tests.conftest import login, promote_superuser, register


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_accommodation(client, headers, **overrides):
    payload = {
        "title": "Glamping Disponibilidad",
        "location": "Cartagena",
        "price_per_night": "100.00",
        "max_guests": 4,
        "amenity_ids": [],
        **overrides,
    }
    resp = client.post("/api/v1/accommodations/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def block_dates(client, headers, acc_id, dates, reason=None):
    payload = {"dates": dates}
    if reason:
        payload["reason"] = reason
    resp = client.post(
        f"/api/v1/accommodations/{acc_id}/availability/blocked-dates",
        json=payload,
        headers=headers,
    )
    return resp


def create_seasonal_price(client, headers, acc_id, **overrides):
    payload = {
        "name": "Temporada Alta",
        "start_date": "2026-07-01",
        "end_date": "2026-07-31",
        "price_per_night": "200.00",
        **overrides,
    }
    resp = client.post(
        f"/api/v1/accommodations/{acc_id}/seasonal-prices",
        json=payload,
        headers=headers,
    )
    return resp


# ── Calendar ──────────────────────────────────────────────────────────────────

def test_calendar_is_public(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/availability/calendar",
        params={"start_date": "2026-07-01", "end_date": "2026-07-03"},
    )
    assert resp.status_code == 200
    days = resp.json()
    assert len(days) == 3
    assert all(d["is_available"] is True for d in days)
    assert all(d["price_per_night"] == "100.00" for d in days)


def test_calendar_shows_blocked_dates(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    block_dates(client, normal_user["headers"], acc["id"], ["2026-07-02"], reason="Mantenimiento")

    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/availability/calendar",
        params={"start_date": "2026-07-01", "end_date": "2026-07-03"},
    )
    assert resp.status_code == 200
    days = {d["date"]: d for d in resp.json()}
    assert days["2026-07-01"]["is_available"] is True
    assert days["2026-07-02"]["is_available"] is False
    assert days["2026-07-02"]["reason"] == "Mantenimiento"
    assert days["2026-07-03"]["is_available"] is True


def test_calendar_uses_seasonal_price(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    create_seasonal_price(
        client, normal_user["headers"], acc["id"],
        start_date="2026-07-01", end_date="2026-07-31", price_per_night="250.00",
    )

    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/availability/calendar",
        params={"start_date": "2026-07-01", "end_date": "2026-07-01"},
    )
    assert resp.status_code == 200
    assert resp.json()[0]["price_per_night"] == "250.00"


def test_calendar_invalid_range_returns_422(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/availability/calendar",
        params={"start_date": "2026-07-10", "end_date": "2026-07-01"},
    )
    assert resp.status_code == 422


def test_calendar_unknown_accommodation_returns_404(client):
    resp = client.get(
        "/api/v1/accommodations/99999/availability/calendar",
        params={"start_date": "2026-07-01", "end_date": "2026-07-03"},
    )
    assert resp.status_code == 404


# ── Availability check ────────────────────────────────────────────────────────

def test_check_availability_available(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/availability/check",
        params={"check_in": "2026-08-01", "check_out": "2026-08-05"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_available"] is True
    assert data["nights"] == 4
    assert float(data["total_price"]) == 400.0


def test_check_availability_with_blocked_dates(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    block_dates(client, normal_user["headers"], acc["id"], ["2026-08-03"])

    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/availability/check",
        params={"check_in": "2026-08-01", "check_out": "2026-08-05"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_available"] is False


def test_check_availability_uses_seasonal_price(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    create_seasonal_price(
        client, normal_user["headers"], acc["id"],
        start_date="2026-08-01", end_date="2026-08-05", price_per_night="300.00",
    )

    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/availability/check",
        params={"check_in": "2026-08-01", "check_out": "2026-08-03"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["total_price"]) == 600.0


def test_check_same_check_in_out_returns_422(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/availability/check",
        params={"check_in": "2026-08-01", "check_out": "2026-08-01"},
    )
    assert resp.status_code == 422


def test_check_unknown_accommodation_returns_404(client):
    resp = client.get(
        "/api/v1/accommodations/99999/availability/check",
        params={"check_in": "2026-08-01", "check_out": "2026-08-05"},
    )
    assert resp.status_code == 404


# ── Block dates ───────────────────────────────────────────────────────────────

def test_block_dates_as_owner_returns_201(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = block_dates(client, normal_user["headers"], acc["id"], ["2026-09-10", "2026-09-11"])
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 2
    assert data[0]["date"] == "2026-09-10"
    assert data[1]["date"] == "2026-09-11"


def test_block_dates_as_superuser_returns_201(client, normal_user, superuser):
    acc = create_accommodation(client, normal_user["headers"])
    resp = block_dates(client, superuser["headers"], acc["id"], ["2026-09-15"])
    assert resp.status_code == 201


def test_block_dates_as_other_user_returns_403(client, normal_user, db):
    acc = create_accommodation(client, normal_user["headers"])

    other = register(client, "other@test.com")
    other_token = login(client, "other@test.com")
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp = block_dates(client, other_headers, acc["id"], ["2026-09-20"])
    assert resp.status_code == 403


def test_block_dates_unauthenticated_returns_401(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = block_dates(client, {}, acc["id"], ["2026-09-20"])
    assert resp.status_code == 401


def test_block_duplicate_date_returns_409(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    block_dates(client, normal_user["headers"], acc["id"], ["2026-09-25"])
    resp = block_dates(client, normal_user["headers"], acc["id"], ["2026-09-25"])
    assert resp.status_code == 409


def test_block_unknown_accommodation_returns_404(client, normal_user):
    resp = block_dates(client, normal_user["headers"], 99999, ["2026-09-25"])
    assert resp.status_code == 404


# ── Unblock dates ─────────────────────────────────────────────────────────────

def test_unblock_date_as_owner(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    block_dates(client, normal_user["headers"], acc["id"], ["2026-10-05"])

    resp = client.delete(
        f"/api/v1/accommodations/{acc['id']}/availability/blocked-dates/2026-10-05",
        headers=normal_user["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-10-05"


def test_unblock_non_blocked_date_returns_404(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.delete(
        f"/api/v1/accommodations/{acc['id']}/availability/blocked-dates/2026-10-05",
        headers=normal_user["headers"],
    )
    assert resp.status_code == 404


def test_unblock_as_other_user_returns_403(client, normal_user, db):
    acc = create_accommodation(client, normal_user["headers"])
    block_dates(client, normal_user["headers"], acc["id"], ["2026-10-10"])

    other_token = login(client, register(client, "other2@test.com")["email"])
    resp = client.delete(
        f"/api/v1/accommodations/{acc['id']}/availability/blocked-dates/2026-10-10",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


# ── Seasonal prices ───────────────────────────────────────────────────────────

def test_list_seasonal_prices_is_public(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.get(f"/api/v1/accommodations/{acc['id']}/seasonal-prices")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_seasonal_price_as_owner(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = create_seasonal_price(client, normal_user["headers"], acc["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Temporada Alta"
    assert data["price_per_night"] == "200.00"
    assert data["start_date"] == "2026-07-01"
    assert data["end_date"] == "2026-07-31"


def test_create_seasonal_price_unauthenticated_returns_401(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = create_seasonal_price(client, {}, acc["id"])
    assert resp.status_code == 401


def test_create_seasonal_price_as_other_user_returns_403(client, normal_user, db):
    acc = create_accommodation(client, normal_user["headers"])
    other_token = login(client, register(client, "other3@test.com")["email"])
    resp = create_seasonal_price(client, {"Authorization": f"Bearer {other_token}"}, acc["id"])
    assert resp.status_code == 403


def test_create_overlapping_seasonal_price_returns_409(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    create_seasonal_price(
        client, normal_user["headers"], acc["id"],
        start_date="2026-07-01", end_date="2026-07-31",
    )
    resp = create_seasonal_price(
        client, normal_user["headers"], acc["id"],
        start_date="2026-07-15", end_date="2026-08-15",
    )
    assert resp.status_code == 409


def test_create_seasonal_price_invalid_range_returns_422(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = create_seasonal_price(
        client, normal_user["headers"], acc["id"],
        start_date="2026-07-31", end_date="2026-07-01",
    )
    assert resp.status_code == 422


def test_update_seasonal_price(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    price = create_seasonal_price(client, normal_user["headers"], acc["id"]).json()

    resp = client.put(
        f"/api/v1/accommodations/{acc['id']}/seasonal-prices/{price['id']}",
        json={"price_per_night": "350.00"},
        headers=normal_user["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["price_per_night"] == "350.00"


def test_update_seasonal_price_not_found_returns_404(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.put(
        f"/api/v1/accommodations/{acc['id']}/seasonal-prices/99999",
        json={"price_per_night": "350.00"},
        headers=normal_user["headers"],
    )
    assert resp.status_code == 404


def test_delete_seasonal_price(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    price = create_seasonal_price(client, normal_user["headers"], acc["id"]).json()

    resp = client.delete(
        f"/api/v1/accommodations/{acc['id']}/seasonal-prices/{price['id']}",
        headers=normal_user["headers"],
    )
    assert resp.status_code == 200

    prices = client.get(f"/api/v1/accommodations/{acc['id']}/seasonal-prices").json()
    assert prices == []


def test_delete_seasonal_price_not_found_returns_404(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.delete(
        f"/api/v1/accommodations/{acc['id']}/seasonal-prices/99999",
        headers=normal_user["headers"],
    )
    assert resp.status_code == 404
