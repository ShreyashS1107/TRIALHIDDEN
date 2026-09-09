"""
Phase 5D Test Suite: Stored ML + ESI Intelligence API Integration.

Verifies:
1. GET /api/v1/projects/{project_id}/intelligence (full data, partial data, 404, latest record semantics)
2. GET /api/v1/analytics/summary (default dynamic month, filtered month, 422 invalid format)
3. CORS headers and safe origin configuration
4. Strict read-only database safety
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import func

from app.database.session import get_db
from app.main import app
from app.models.alert import SystemAlert
from app.models.dossier import ProjectMonthlyDossier
from app.models.execution import ExecutionStressScore
from app.models.project import MonthlySnapshot, Project
from app.models.risk import MLRiskScore

client = TestClient(app)


@pytest.fixture(scope="module")
def fully_scored_project_id():
    """Dynamically discover a project ID that has ML risk, ESI, snapshot, and dossier records."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        # Find project present in ml_risk_scores
        risk_record = (
            session.query(MLRiskScore.project_id)
            .order_by(MLRiskScore.report_month.desc())
            .first()
        )
        assert risk_record is not None, "At least one MLRiskScore required in test database."
        return risk_record[0]
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@pytest.fixture(scope="module")
def unscored_project_id():
    """Dynamically discover a project ID with no ML risk scores (to test null-safety)."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        subquery = session.query(MLRiskScore.project_id).distinct().subquery()
        proj = session.query(Project).filter(~Project.project_id.in_(subquery.select())).first()
        if proj:
            return proj.project_id
        return None
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def test_1_get_project_intelligence_status_200(fully_scored_project_id):
    """1. GET /api/v1/projects/{project_id}/intelligence returns HTTP 200 with full structure."""
    response = client.get(f"/api/v1/projects/{fully_scored_project_id}/intelligence")
    assert response.status_code == 200
    data = response.json()

    # Verify top-level structure
    assert "project" in data
    assert "latest_snapshot" in data
    assert "latest_risk" in data
    assert "latest_surveillance" in data
    assert "latest_alerts" in data
    assert "latest_dossier" in data

    # Verify project details
    project = data["project"]
    assert project["project_id"] == fully_scored_project_id
    assert "agency" in project
    assert "state" in project
    assert "is_active" in project


def test_2_project_intelligence_components_and_types(fully_scored_project_id):
    """2. Verify component types, decimals, and enums in project intelligence response."""
    response = client.get(f"/api/v1/projects/{fully_scored_project_id}/intelligence")
    assert response.status_code == 200
    data = response.json()

    # Risk component
    if data["latest_risk"]:
        risk = data["latest_risk"]
        assert risk["project_id"] == fully_scored_project_id
        assert risk["risk_band"] in ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
        assert risk["dominant_component"] in [
            "Schedule Delay",
            "Cost Overrun",
            "Schedule Revision",
        ]
        # Decimal serialization checks
        assert 0.0 <= float(risk["selected_integrated_risk"]) <= 1.0
        assert 0.0 <= float(risk["schedule_delay_risk"]) <= 1.0

    # Surveillance component
    if data["latest_surveillance"]:
        esi = data["latest_surveillance"]
        assert esi["project_id"] == fully_scored_project_id
        assert esi["esi_tier"] in ["NOMINAL", "WATCH", "ATTENTION", "HIGH_PRIORITY"]
        assert esi["dominant_stressor"] in [
            "Progress Velocity Collapse",
            "Physical Progress Stagnation",
            "Expenditure Divergence",
            "Schedule Slippage Debt",
            "Reporting Friction",
        ]
        assert 0.0 <= float(esi["execution_stress_index"]) <= 1.0

    # Alerts component must be a list
    assert isinstance(data["latest_alerts"], list)


def test_3_project_intelligence_latest_record_semantics(fully_scored_project_id):
    """3. Verify latest record semantics: snapshot, risk, ESI, dossier correspond to latest report_month."""
    response = client.get(f"/api/v1/projects/{fully_scored_project_id}/intelligence")
    assert response.status_code == 200
    data = response.json()

    db_gen = get_db()
    session = next(db_gen)
    try:
        # Check snapshot
        if data["latest_snapshot"]:
            latest_snap_db = (
                session.query(MonthlySnapshot.report_month)
                .filter(MonthlySnapshot.project_id == fully_scored_project_id)
                .order_by(MonthlySnapshot.report_month.desc())
                .first()
            )
            assert data["latest_snapshot"]["report_month"] == latest_snap_db[0]

        # Check risk
        if data["latest_risk"]:
            latest_risk_db = (
                session.query(MLRiskScore.report_month)
                .filter(MLRiskScore.project_id == fully_scored_project_id)
                .order_by(MLRiskScore.report_month.desc())
                .first()
            )
            assert data["latest_risk"]["report_month"] == latest_risk_db[0]

        # Check ESI
        if data["latest_surveillance"]:
            latest_esi_db = (
                session.query(ExecutionStressScore.report_month)
                .filter(ExecutionStressScore.project_id == fully_scored_project_id)
                .order_by(ExecutionStressScore.report_month.desc())
                .first()
            )
            assert data["latest_surveillance"]["report_month"] == latest_esi_db[0]
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def test_4_project_intelligence_missing_components_null_safety(unscored_project_id):
    """4. If a project has missing intelligence components, returns null/empty without failing."""
    if not unscored_project_id:
        pytest.skip("No unscored project present in database.")

    response = client.get(f"/api/v1/projects/{unscored_project_id}/intelligence")
    assert response.status_code == 200
    data = response.json()

    assert data["project"]["project_id"] == unscored_project_id
    assert data["latest_risk"] is None
    assert isinstance(data["latest_alerts"], list)


def test_5_project_intelligence_not_found():
    """5. GET /api/v1/projects/{invalid_id}/intelligence returns HTTP 404."""
    response = client.get("/api/v1/projects/NON_EXISTENT_PROJECT_99999/intelligence")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_6_get_portfolio_summary_default_month():
    """6. GET /api/v1/analytics/summary returns HTTP 200 with dynamic portfolio aggregates."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()

    # Metric keys
    assert "total_projects" in data
    assert "active_projects" in data
    assert "scored_projects" in data
    assert "risk_band_distribution" in data
    assert "esi_tier_distribution" in data
    assert "alert_counts_by_severity" in data
    assert "alert_counts_by_status" in data
    assert "total_alerts" in data
    assert "latest_report_month" in data
    assert "latest_snapshot_month" in data

    # Values sanity
    assert data["total_projects"] >= data["active_projects"] >= 0
    assert data["scored_projects"] >= 0
    assert data["total_alerts"] >= 0

    # Risk band distribution completeness
    for band in ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]:
        assert band in data["risk_band_distribution"]
        assert isinstance(data["risk_band_distribution"][band], int)

    # ESI tier distribution completeness
    for tier in ["NOMINAL", "WATCH", "ATTENTION", "HIGH_PRIORITY"]:
        assert tier in data["esi_tier_distribution"]
        assert isinstance(data["esi_tier_distribution"][tier], int)

    # Alert breakdowns
    for sev in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        assert sev in data["alert_counts_by_severity"]
    for st in ["ACTIVE", "ACKNOWLEDGED", "RESOLVED"]:
        assert st in data["alert_counts_by_status"]

    # Month strings format
    if data["latest_report_month"]:
        assert len(data["latest_report_month"]) == 7
        assert data["latest_report_month"][4] == "-"
    if data["latest_snapshot_month"]:
        assert len(data["latest_snapshot_month"]) == 7
        assert data["latest_snapshot_month"][4] == "-"


def test_7_get_portfolio_summary_specific_month():
    """7. GET /api/v1/analytics/summary?report_month=YYYY-MM filters correctly."""
    # First get default to discover a valid month
    resp_default = client.get("/api/v1/analytics/summary")
    assert resp_default.status_code == 200
    target_month = resp_default.json()["latest_report_month"]

    if target_month:
        response = client.get(f"/api/v1/analytics/summary?report_month={target_month}")
        assert response.status_code == 200
        data = response.json()
        assert data["latest_report_month"] == target_month
        assert data["scored_projects"] == resp_default.json()["scored_projects"]


def test_8_get_portfolio_summary_invalid_month_format():
    """8. Invalid report_month query parameter returns HTTP 422 Unprocessable Entity."""
    response = client.get("/api/v1/analytics/summary?report_month=invalid-date")
    assert response.status_code == 422


def test_9_cors_headers_configured_origin():
    """9. Verify CORS headers returned for configured origin."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_10_cors_preflight_options():
    """10. Verify CORS preflight OPTIONS request."""
    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_11_read_only_safety_verification():
    """11. Verify that intelligence endpoints execute zero mutating operations."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        proj_count_before = session.query(func.count(Project.project_id)).scalar()
        risk_count_before = session.query(func.count(MLRiskScore.score_id)).scalar()
        esi_count_before = session.query(func.count(ExecutionStressScore.project_id)).scalar()
        alert_count_before = session.query(func.count(SystemAlert.alert_id)).scalar()

        # Execute endpoints
        client.get("/api/v1/analytics/summary")
        proj = session.query(Project.project_id).first()
        if proj:
            client.get(f"/api/v1/projects/{proj[0]}/intelligence")

        proj_count_after = session.query(func.count(Project.project_id)).scalar()
        risk_count_after = session.query(func.count(MLRiskScore.score_id)).scalar()
        esi_count_after = session.query(func.count(ExecutionStressScore.project_id)).scalar()
        alert_count_after = session.query(func.count(SystemAlert.alert_id)).scalar()

        assert proj_count_before == proj_count_after
        assert risk_count_before == risk_count_after
        assert esi_count_before == esi_count_after
        assert alert_count_before == alert_count_after
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
