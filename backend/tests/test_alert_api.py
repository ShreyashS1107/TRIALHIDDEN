import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.models.alert import SystemAlert

client = TestClient(app)


def test_1_get_alerts_status_200():
    """1. GET /api/v1/alerts returns HTTP 200."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200


def test_2_alerts_pagination_envelope():
    """2. Verify alerts response conforms to PaginatedAlertsResponse schema."""
    response = client.get("/api/v1/alerts?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)


def test_3_alerts_filter_parameters():
    """3. Verify query parameter filters are accepted and handled."""
    response = client.get(
        "/api/v1/alerts?status=ACTIVE&severity=HIGH&alert_source=ML_ENGINE&page_size=5"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)


def test_4_alerts_pagination_and_enum_validation():
    """4. Reject invalid page, page_size, and non-existent enums with HTTP 422."""
    resp_over = client.get("/api/v1/alerts?page_size=101")
    assert resp_over.status_code == 422

    resp_zero = client.get("/api/v1/alerts?page=0")
    assert resp_zero.status_code == 422

    resp_bad_status = client.get("/api/v1/alerts?status=NON_EXISTENT_STATUS")
    assert resp_bad_status.status_code == 422

    resp_bad_severity = client.get("/api/v1/alerts?severity=INVALID_SEVERITY")
    assert resp_bad_severity.status_code == 422

    resp_bad_source = client.get("/api/v1/alerts?alert_source=INVALID_SOURCE")
    assert resp_bad_source.status_code == 422

    resp_bad_month = client.get("/api/v1/alerts?report_month=INVALID_MONTH")
    assert resp_bad_month.status_code == 422


def test_5_alerts_read_only_safety():
    """5. Confirm that GET /api/v1/alerts executes zero database mutations."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        count_before = session.query(SystemAlert).count()
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

    client.get("/api/v1/alerts")
    client.get("/api/v1/alerts?page=1&page_size=10")
    client.get("/api/v1/alerts?status=ACTIVE")

    db_gen2 = get_db()
    session2 = next(db_gen2)
    try:
        count_after = session2.query(SystemAlert).count()
    finally:
        try:
            next(db_gen2)
        except StopIteration:
            pass

    assert count_before == count_after, "Alerts count changed after read operations!"
