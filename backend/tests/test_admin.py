"""Tests for the admin dashboard and analytics endpoints."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import login, promote_superuser, register


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def superuser_headers(client: TestClient, db: Session) -> dict:
    register(client, "super@test.com", password="Admin1234!", full_name="Super Admin")
    promote_superuser(db, "super@test.com")
    token = login(client, "super@test.com", password="Admin1234!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers(client: TestClient) -> dict:
    register(client, "user@test.com")
    token = login(client, "user@test.com")
    return {"Authorization": f"Bearer {token}"}


def _make_accommodation(client: TestClient, headers: dict) -> int:
    resp = client.post(
        "/api/v1/accommodations/",
        json={
            "title": "Test Glamping",
            "location": "Forest",
            "price_per_night": "100.00",
            "max_guests": 4,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _make_reservation(
    client: TestClient,
    headers: dict,
    accommodation_id: int,
    check_in: date,
    check_out: date,
) -> int:
    resp = client.post(
        "/api/v1/reservations/",
        json={
            "accommodation_id": accommodation_id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guest_count": 2,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── GET /admin/kpis ───────────────────────────────────────────────────────────

class TestGetKPIs:
    def test_happy_path_empty_db(self, client: TestClient, superuser_headers: dict):
        resp = client.get("/api/v1/admin/kpis", headers=superuser_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Superuser itself was registered, so at least 1 user
        assert data["total_users"] >= 1
        assert data["active_users"] >= 1
        assert data["total_accommodations"] == 0
        assert data["total_reservations"] == 0
        assert data["total_revenue"] == "0"
        assert data["confirmed_reservations"] == 0
        assert data["cancelled_reservations"] == 0

    def test_happy_path_with_data(
        self, client: TestClient, db: Session, superuser_headers: dict, user_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        check_in = date.today() + timedelta(days=10)
        check_out = check_in + timedelta(days=3)
        _make_reservation(client, user_headers, acc_id, check_in, check_out)

        resp = client.get("/api/v1/admin/kpis", headers=superuser_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_accommodations"] == 1
        assert data["active_accommodations"] == 1
        assert data["total_reservations"] == 1
        assert data["confirmed_reservations"] == 1
        assert data["cancelled_reservations"] == 0
        assert float(data["total_revenue"]) == 300.0

    def test_401_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/admin/kpis")
        assert resp.status_code == 401

    def test_403_non_superuser(self, client: TestClient, user_headers: dict):
        resp = client.get("/api/v1/admin/kpis", headers=user_headers)
        assert resp.status_code == 403


# ── GET /admin/stats/occupancy ────────────────────────────────────────────────

class TestOccupancyStats:
    def test_happy_path(
        self, client: TestClient, db: Session, superuser_headers: dict, user_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        check_in = date.today() + timedelta(days=5)
        check_out = check_in + timedelta(days=2)
        _make_reservation(client, user_headers, acc_id, check_in, check_out)

        period_start = date.today()
        period_end = date.today() + timedelta(days=30)
        resp = client.get(
            "/api/v1/admin/stats/occupancy",
            params={"start_date": period_start.isoformat(), "end_date": period_end.isoformat()},
            headers=superuser_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["accommodation_id"] == acc_id
        assert data[0]["total_nights_booked"] == 2
        assert data[0]["total_reservations"] == 1
        assert data[0]["occupancy_rate"] > 0

    def test_empty_when_no_reservations(
        self, client: TestClient, superuser_headers: dict
    ):
        resp = client.get(
            "/api/v1/admin/stats/occupancy",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=30)).isoformat(),
            },
            headers=superuser_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_401_unauthenticated(self, client: TestClient):
        resp = client.get(
            "/api/v1/admin/stats/occupancy",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )
        assert resp.status_code == 401

    def test_403_non_superuser(self, client: TestClient, user_headers: dict):
        resp = client.get(
            "/api/v1/admin/stats/occupancy",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat(),
            },
            headers=user_headers,
        )
        assert resp.status_code == 403

    def test_422_missing_params(self, client: TestClient, superuser_headers: dict):
        resp = client.get("/api/v1/admin/stats/occupancy", headers=superuser_headers)
        assert resp.status_code == 422


# ── GET /admin/stats/revenue/period ──────────────────────────────────────────

class TestRevenueByPeriod:
    def test_happy_path_returns_list(self, client: TestClient, superuser_headers: dict):
        resp = client.get("/api/v1/admin/stats/revenue/period", headers=superuser_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_with_data(
        self, client: TestClient, db: Session, superuser_headers: dict, user_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        check_in = date.today() + timedelta(days=10)
        check_out = check_in + timedelta(days=2)
        _make_reservation(client, user_headers, acc_id, check_in, check_out)

        resp = client.get("/api/v1/admin/stats/revenue/period", headers=superuser_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        entry = data[0]
        assert "period" in entry
        assert "revenue" in entry
        assert "reservations_count" in entry
        assert entry["reservations_count"] >= 1

    def test_year_filter(self, client: TestClient, superuser_headers: dict):
        resp = client.get(
            "/api/v1/admin/stats/revenue/period",
            params={"year": 2026},
            headers=superuser_headers,
        )
        assert resp.status_code == 200

    def test_401_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/admin/stats/revenue/period")
        assert resp.status_code == 401

    def test_403_non_superuser(self, client: TestClient, user_headers: dict):
        resp = client.get("/api/v1/admin/stats/revenue/period", headers=user_headers)
        assert resp.status_code == 403


# ── GET /admin/stats/revenue/accommodation ────────────────────────────────────

class TestRevenueByAccommodation:
    def test_happy_path_empty(self, client: TestClient, superuser_headers: dict):
        resp = client.get(
            "/api/v1/admin/stats/revenue/accommodation", headers=superuser_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_data(
        self, client: TestClient, db: Session, superuser_headers: dict, user_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        check_in = date.today() + timedelta(days=10)
        check_out = check_in + timedelta(days=5)
        _make_reservation(client, user_headers, acc_id, check_in, check_out)

        resp = client.get(
            "/api/v1/admin/stats/revenue/accommodation", headers=superuser_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["accommodation_id"] == acc_id
        assert float(data[0]["total_revenue"]) == 500.0
        assert data[0]["reservations_count"] == 1

    def test_limit_param(self, client: TestClient, superuser_headers: dict):
        resp = client.get(
            "/api/v1/admin/stats/revenue/accommodation",
            params={"limit": 5},
            headers=superuser_headers,
        )
        assert resp.status_code == 200

    def test_401_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/admin/stats/revenue/accommodation")
        assert resp.status_code == 401

    def test_403_non_superuser(self, client: TestClient, user_headers: dict):
        resp = client.get(
            "/api/v1/admin/stats/revenue/accommodation", headers=user_headers
        )
        assert resp.status_code == 403


# ── GET /admin/reservations ───────────────────────────────────────────────────

class TestListReservations:
    def test_happy_path_empty(self, client: TestClient, superuser_headers: dict):
        resp = client.get("/api/v1/admin/reservations", headers=superuser_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_reservations(
        self, client: TestClient, db: Session, superuser_headers: dict, user_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        check_in = date.today() + timedelta(days=10)
        check_out = check_in + timedelta(days=2)
        res_id = _make_reservation(client, user_headers, acc_id, check_in, check_out)

        resp = client.get("/api/v1/admin/reservations", headers=superuser_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        item = data[0]
        assert item["id"] == res_id
        assert item["accommodation_id"] == acc_id
        assert "accommodation_title" in item
        assert "guest_email" in item
        assert item["status"] == "confirmed"

    def test_status_filter_confirmed(
        self, client: TestClient, db: Session, superuser_headers: dict, user_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        check_in = date.today() + timedelta(days=10)
        check_out = check_in + timedelta(days=2)
        res_id = _make_reservation(client, user_headers, acc_id, check_in, check_out)
        # Cancel it
        client.post(
            f"/api/v1/reservations/{res_id}/cancel",
            headers=user_headers,
        )

        resp = client.get(
            "/api/v1/admin/reservations",
            params={"status": "confirmed"},
            headers=superuser_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

        resp = client.get(
            "/api/v1/admin/reservations",
            params={"status": "cancelled"},
            headers=superuser_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_pagination(
        self, client: TestClient, db: Session, superuser_headers: dict, user_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        for i in range(3):
            check_in = date.today() + timedelta(days=10 + i * 5)
            check_out = check_in + timedelta(days=2)
            _make_reservation(client, user_headers, acc_id, check_in, check_out)

        resp = client.get(
            "/api/v1/admin/reservations",
            params={"skip": 0, "limit": 2},
            headers=superuser_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_invalid_status_422(self, client: TestClient, superuser_headers: dict):
        resp = client.get(
            "/api/v1/admin/reservations",
            params={"status": "pending"},
            headers=superuser_headers,
        )
        assert resp.status_code == 422

    def test_401_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/admin/reservations")
        assert resp.status_code == 401

    def test_403_non_superuser(self, client: TestClient, user_headers: dict):
        resp = client.get("/api/v1/admin/reservations", headers=user_headers)
        assert resp.status_code == 403


# ── GET /admin/accommodations ─────────────────────────────────────────────────

class TestListAccommodations:
    def test_happy_path_empty(self, client: TestClient, superuser_headers: dict):
        resp = client.get("/api/v1/admin/accommodations", headers=superuser_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_including_inactive(
        self, client: TestClient, superuser_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        # Soft-delete it
        client.delete(f"/api/v1/accommodations/{acc_id}", headers=superuser_headers)

        resp = client.get(
            "/api/v1/admin/accommodations",
            params={"include_inactive": True},
            headers=superuser_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["is_active"] is False

    def test_exclude_inactive(self, client: TestClient, superuser_headers: dict):
        acc_id = _make_accommodation(client, superuser_headers)
        client.delete(f"/api/v1/accommodations/{acc_id}", headers=superuser_headers)

        resp = client.get(
            "/api/v1/admin/accommodations",
            params={"include_inactive": False},
            headers=superuser_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_response_shape(self, client: TestClient, superuser_headers: dict):
        _make_accommodation(client, superuser_headers)
        resp = client.get("/api/v1/admin/accommodations", headers=superuser_headers)
        assert resp.status_code == 200
        item = resp.json()[0]
        assert "id" in item
        assert "title" in item
        assert "is_active" in item
        assert "owner_id" in item

    def test_401_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/admin/accommodations")
        assert resp.status_code == 401

    def test_403_non_superuser(self, client: TestClient, user_headers: dict):
        resp = client.get("/api/v1/admin/accommodations", headers=user_headers)
        assert resp.status_code == 403


# ── GET /admin/reports/activity ───────────────────────────────────────────────

class TestActivityReport:
    def test_happy_path_empty(self, client: TestClient, superuser_headers: dict):
        resp = client.get("/api/v1/admin/reports/activity", headers=superuser_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "recent_reservations" in data
        assert "recent_cancellations" in data
        assert "recent_registrations" in data
        # The superuser itself appears in recent_registrations
        assert len(data["recent_registrations"]) >= 1

    def test_with_data(
        self, client: TestClient, db: Session, superuser_headers: dict, user_headers: dict
    ):
        acc_id = _make_accommodation(client, superuser_headers)
        check_in = date.today() + timedelta(days=10)
        check_out = check_in + timedelta(days=2)
        res_id = _make_reservation(client, user_headers, acc_id, check_in, check_out)
        client.post(f"/api/v1/reservations/{res_id}/cancel", headers=user_headers)

        resp = client.get("/api/v1/admin/reports/activity", headers=superuser_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recent_reservations"]) == 1  # all (cancelled is included)
        assert len(data["recent_cancellations"]) == 1
        assert len(data["recent_registrations"]) >= 2  # superuser + user

    def test_limit_param(self, client: TestClient, superuser_headers: dict):
        resp = client.get(
            "/api/v1/admin/reports/activity",
            params={"limit": 5},
            headers=superuser_headers,
        )
        assert resp.status_code == 200

    def test_401_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/admin/reports/activity")
        assert resp.status_code == 401

    def test_403_non_superuser(self, client: TestClient, user_headers: dict):
        resp = client.get("/api/v1/admin/reports/activity", headers=user_headers)
        assert resp.status_code == 403
