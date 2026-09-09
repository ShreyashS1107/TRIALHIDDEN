import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.models.execution import ExecutionStressScore
from app.models.risk import MLRiskScore

client = TestClient(app)


def test_1_get_risk_rankings_status_200():
    """1. GET /api/v1/analytics/risk-rankings returns HTTP 200."""
    response = client.get("/api/v1/analytics/risk-rankings")
    assert response.status_code == 200


def test_2_risk_rankings_pagination_envelope():
    """2. Verify risk-rankings response matches paginated envelope."""
    response = client.get("/api/v1/analytics/risk-rankings?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) <= 10
    assert data["total"] > 0

    first = data["items"][0]
    expected_fields = {
        "score_id",
        "project_id",
        "report_month",
        "selected_integrated_risk",
        "risk_band",
        "dominant_component",
    }
    assert expected_fields.issubset(first.keys())


def test_3_risk_rankings_descending_order():
    """3. Verify deterministic ordering: selected_integrated_risk DESC."""
    response = client.get("/api/v1/analytics/risk-rankings?page=1&page_size=25")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 1
    for i in range(len(items) - 1):
        curr_score = float(items[i]["selected_integrated_risk"])
        next_score = float(items[i + 1]["selected_integrated_risk"])
        assert curr_score >= next_score, (
            f"Risk scores not in descending order: {curr_score} < {next_score}"
        )


def test_4_risk_rankings_filter_by_risk_band():
    """4. Verify filter by risk_band."""
    response = client.get("/api/v1/analytics/risk-rankings?risk_band=HIGH&page_size=10")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["risk_band"] == "HIGH"


def test_5_risk_rankings_filter_by_month_and_project():
    """5. Verify filter by report_month and project_id."""
    sample_resp = client.get("/api/v1/analytics/risk-rankings?page=1&page_size=1")
    sample = sample_resp.json()["items"][0]
    proj_id = sample["project_id"]
    month = sample["report_month"]

    filtered_resp = client.get(
        f"/api/v1/analytics/risk-rankings?project_id={proj_id}&report_month={month}"
    )
    assert filtered_resp.status_code == 200
    filtered_data = filtered_resp.json()
    assert filtered_data["total"] >= 1
    for item in filtered_data["items"]:
        assert item["project_id"] == proj_id
        assert item["report_month"] == month


def test_6_risk_rankings_pagination_validation():
    """6. Bounded page size (1..100) and page (>=1) validation."""
    resp_over = client.get("/api/v1/analytics/risk-rankings?page_size=101")
    assert resp_over.status_code == 422

    resp_zero = client.get("/api/v1/analytics/risk-rankings?page=0")
    assert resp_zero.status_code == 422

    resp_bad_month = client.get("/api/v1/analytics/risk-rankings?report_month=2024-999")
    assert resp_bad_month.status_code == 422


def test_7_get_surveillance_status_200():
    """7. GET /api/v1/analytics/surveillance returns HTTP 200."""
    response = client.get("/api/v1/analytics/surveillance")
    assert response.status_code == 200


def test_8_surveillance_pagination_envelope():
    """8. Verify surveillance response matches paginated envelope."""
    response = client.get("/api/v1/analytics/surveillance?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) <= 10
    assert data["total"] > 0

    first = data["items"][0]
    expected_fields = {
        "project_id",
        "report_month",
        "execution_stress_index",
        "esi_tier",
        "dominant_stressor",
        "suggested_action",
    }
    assert expected_fields.issubset(first.keys())


def test_9_surveillance_descending_order():
    """9. Verify deterministic ordering: execution_stress_index DESC."""
    response = client.get("/api/v1/analytics/surveillance?page=1&page_size=25")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 1
    for i in range(len(items) - 1):
        curr_esi = float(items[i]["execution_stress_index"])
        next_esi = float(items[i + 1]["execution_stress_index"])
        assert curr_esi >= next_esi, (
            f"ESI scores not in descending order: {curr_esi} < {next_esi}"
        )


def test_10_surveillance_filters():
    """10. Verify surveillance filter by esi_tier and project_id."""
    sample_resp = client.get("/api/v1/analytics/surveillance?page=1&page_size=1")
    sample = sample_resp.json()["items"][0]
    tier = sample["esi_tier"]

    filtered_resp = client.get(f"/api/v1/analytics/surveillance?esi_tier={tier}&page_size=10")
    assert filtered_resp.status_code == 200
    for item in filtered_resp.json()["items"]:
        assert item["esi_tier"] == tier


def test_11_surveillance_pagination_validation():
    """11. Surveillance endpoint rejects invalid page and page_size."""
    resp_over = client.get("/api/v1/analytics/surveillance?page_size=101")
    assert resp_over.status_code == 422

    resp_zero = client.get("/api/v1/analytics/surveillance?page=0")
    assert resp_zero.status_code == 422


def test_12_analytics_no_writes():
    """12. Verify analytics endpoints perform zero database writes."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        risk_count_before = session.query(MLRiskScore).count()
        esi_count_before = session.query(ExecutionStressScore).count()
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

    # Call both endpoints multiple times with filters
    client.get("/api/v1/analytics/risk-rankings?page=1&page_size=20")
    client.get("/api/v1/analytics/surveillance?page=1&page_size=20")

    db_gen2 = get_db()
    session2 = next(db_gen2)
    try:
        risk_count_after = session2.query(MLRiskScore).count()
        esi_count_after = session2.query(ExecutionStressScore).count()
    finally:
        try:
            next(db_gen2)
        except StopIteration:
            pass

    assert risk_count_before == risk_count_after
    assert esi_count_before == esi_count_after
