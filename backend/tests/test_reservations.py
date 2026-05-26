"""Tests for the reservation flow — create, list, get, cancel."""
import pytest
from fastapi.testclient import TestClient

from tests.conftest import login, promote_superuser, register


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_accommodation(client, headers, **overrides):
    payload = {
        "title": "Glamping Reservas",
        "location": "Santa Marta",
        "price_per_night": "100.00",
        "max_guests": 4,
        "amenity_ids": [],
        **overrides,
    }
    resp = client.post("/api/v1/accommodations/", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_reservation(client, headers, accommodation_id, **overrides):
    payload = {
        "accommodation_id": accommodation_id,
        "check_in": "2026-09-01",
        "check_out": "2026-09-05",
        "guest_count": 2,
        **overrides,
    }
    return client.post("/api/v1/reservations/", json=payload, headers=headers)


def block_dates(client, headers, acc_id, dates):
    return client.post(
        f"/api/v1/accommodations/{acc_id}/availability/blocked-dates",
        json={"dates": dates},
        headers=headers,
    )


def create_seasonal_price(client, headers, acc_id, **overrides):
    payload = {
        "name": "Temporada Alta",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
        "price_per_night": "200.00",
        **overrides,
    }
    return client.post(
        f"/api/v1/accommodations/{acc_id}/seasonal-prices",
        json=payload,
        headers=headers,
    )


# ── Create reservation ────────────────────────────────────────────────────────

def test_create_reservation_happy_path(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = create_reservation(client, normal_user["headers"], acc["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["accommodation_id"] == acc["id"]
    assert data["guest_id"] == normal_user["user"]["id"]
    assert data["check_in"] == "2026-09-01"
    assert data["check_out"] == "2026-09-05"
    assert data["guest_count"] == 2
    assert data["status"] == "confirmed"
    assert float(data["total_price"]) == 400.0


def test_create_reservation_with_seasonal_price(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    create_seasonal_price(client, normal_user["headers"], acc["id"])
    resp = create_reservation(client, normal_user["headers"], acc["id"])
    assert resp.status_code == 201
    # 4 nights × 200 = 800
    assert float(resp.json()["total_price"]) == 800.0


def test_create_reservation_unauthenticated_returns_401(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = create_reservation(client, {}, acc["id"])
    assert resp.status_code == 401


def test_create_reservation_unknown_accommodation_returns_404(client, normal_user):
    resp = create_reservation(client, normal_user["headers"], 99999)
    assert resp.status_code == 404


def test_create_reservation_same_check_in_out_returns_422(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = create_reservation(
        client, normal_user["headers"], acc["id"],
        check_in="2026-09-01", check_out="2026-09-01",
    )
    assert resp.status_code == 422


def test_create_reservation_check_out_before_check_in_returns_422(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = create_reservation(
        client, normal_user["headers"], acc["id"],
        check_in="2026-09-05", check_out="2026-09-01",
    )
    assert resp.status_code == 422


def test_create_reservation_exceeds_max_guests_returns_422(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"], max_guests=2)
    resp = create_reservation(
        client, normal_user["headers"], acc["id"],
        guest_count=5,
    )
    assert resp.status_code == 422


def test_create_reservation_on_blocked_dates_returns_409(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    block_dates(client, normal_user["headers"], acc["id"], ["2026-09-03"])
    resp = create_reservation(client, normal_user["headers"], acc["id"])
    assert resp.status_code == 409


def test_create_overlapping_reservation_returns_409(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    create_reservation(client, normal_user["headers"], acc["id"])
    resp = create_reservation(
        client, normal_user["headers"], acc["id"],
        check_in="2026-09-03", check_out="2026-09-07",
    )
    assert resp.status_code == 409


def test_adjacent_reservations_do_not_conflict(client, normal_user):
    """check_out of first == check_in of second: no conflict."""
    acc = create_accommodation(client, normal_user["headers"])
    r1 = create_reservation(
        client, normal_user["headers"], acc["id"],
        check_in="2026-09-01", check_out="2026-09-05",
    )
    assert r1.status_code == 201
    r2 = create_reservation(
        client, normal_user["headers"], acc["id"],
        check_in="2026-09-05", check_out="2026-09-09",
    )
    assert r2.status_code == 201


# ── My reservations (history) ─────────────────────────────────────────────────

def test_my_reservations_returns_own_reservations(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    create_reservation(client, normal_user["headers"], acc["id"])

    resp = client.get("/api/v1/reservations/me", headers=normal_user["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["guest_id"] == normal_user["user"]["id"]


def test_my_reservations_unauthenticated_returns_401(client):
    resp = client.get("/api/v1/reservations/me")
    assert resp.status_code == 401


def test_my_reservations_does_not_return_other_users_reservations(client, normal_user, db):
    acc = create_accommodation(client, normal_user["headers"])
    create_reservation(client, normal_user["headers"], acc["id"])

    other = register(client, "other@test.com")
    other_token = login(client, "other@test.com")
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp = client.get("/api/v1/reservations/me", headers=other_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ── Get reservation by ID ─────────────────────────────────────────────────────

def test_get_reservation_as_guest(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()
    resp = client.get(f"/api/v1/reservations/{res['id']}", headers=normal_user["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == res["id"]


def test_get_reservation_as_accommodation_owner(client, normal_user, db):
    owner = register(client, "owner@test.com")
    owner_token = login(client, "owner@test.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    acc = create_accommodation(client, owner_headers)
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()

    resp = client.get(f"/api/v1/reservations/{res['id']}", headers=owner_headers)
    assert resp.status_code == 200


def test_get_reservation_as_other_user_returns_403(client, normal_user, db):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()

    other_token = login(client, register(client, "stranger@test.com")["email"])
    resp = client.get(
        f"/api/v1/reservations/{res['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


def test_get_reservation_as_superuser(client, normal_user, superuser):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()
    resp = client.get(f"/api/v1/reservations/{res['id']}", headers=superuser["headers"])
    assert resp.status_code == 200


def test_get_reservation_not_found_returns_404(client, normal_user):
    resp = client.get("/api/v1/reservations/99999", headers=normal_user["headers"])
    assert resp.status_code == 404


def test_get_reservation_unauthenticated_returns_401(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()
    resp = client.get(f"/api/v1/reservations/{res['id']}")
    assert resp.status_code == 401


# ── Cancel reservation ────────────────────────────────────────────────────────

def test_cancel_reservation_as_guest(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()

    resp = client.post(
        f"/api/v1/reservations/{res['id']}/cancel", headers=normal_user["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_reservation_as_superuser(client, normal_user, superuser):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()

    resp = client.post(
        f"/api/v1/reservations/{res['id']}/cancel", headers=superuser["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_cancel_reservation_as_other_user_returns_403(client, normal_user, db):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()

    other_token = login(client, register(client, "cancel_stranger@test.com")["email"])
    resp = client.post(
        f"/api/v1/reservations/{res['id']}/cancel",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


def test_cancel_already_cancelled_returns_409(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()

    client.post(f"/api/v1/reservations/{res['id']}/cancel", headers=normal_user["headers"])
    resp = client.post(
        f"/api/v1/reservations/{res['id']}/cancel", headers=normal_user["headers"]
    )
    assert resp.status_code == 409


def test_cancel_allows_rebooking(client, normal_user, db):
    """After cancellation, the same dates should become available again."""
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()
    client.post(f"/api/v1/reservations/{res['id']}/cancel", headers=normal_user["headers"])

    other = register(client, "rebooker@test.com")
    other_token = login(client, "rebooker@test.com")
    resp = create_reservation(
        client, {"Authorization": f"Bearer {other_token}"}, acc["id"]
    )
    assert resp.status_code == 201


def test_cancel_not_found_returns_404(client, normal_user):
    resp = client.post("/api/v1/reservations/99999/cancel", headers=normal_user["headers"])
    assert resp.status_code == 404


def test_cancel_unauthenticated_returns_401(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    res = create_reservation(client, normal_user["headers"], acc["id"]).json()
    resp = client.post(f"/api/v1/reservations/{res['id']}/cancel")
    assert resp.status_code == 401


# ── Accommodation reservation listing (host view) ────────────────────────────

def test_list_accommodation_reservations_as_owner(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    create_reservation(client, normal_user["headers"], acc["id"])

    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/reservations",
        headers=normal_user["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["accommodation_id"] == acc["id"]


def test_list_accommodation_reservations_as_superuser(client, normal_user, superuser):
    acc = create_accommodation(client, normal_user["headers"])
    create_reservation(client, normal_user["headers"], acc["id"])

    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/reservations",
        headers=superuser["headers"],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_accommodation_reservations_as_other_user_returns_403(client, normal_user, db):
    acc = create_accommodation(client, normal_user["headers"])

    other_token = login(client, register(client, "noowner@test.com")["email"])
    resp = client.get(
        f"/api/v1/accommodations/{acc['id']}/reservations",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


def test_list_accommodation_reservations_unauthenticated_returns_401(client, normal_user):
    acc = create_accommodation(client, normal_user["headers"])
    resp = client.get(f"/api/v1/accommodations/{acc['id']}/reservations")
    assert resp.status_code == 401


def test_list_accommodation_reservations_not_found_returns_404(client, normal_user):
    resp = client.get(
        "/api/v1/accommodations/99999/reservations", headers=normal_user["headers"]
    )
    assert resp.status_code == 404
