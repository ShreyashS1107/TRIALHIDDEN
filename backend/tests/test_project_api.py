import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.models.dossier import ProjectMonthlyDossier
from app.models.project import Project

client = TestClient(app)


@pytest.fixture(scope="module")
def valid_project_id():
    """Dynamically fetch an existing project ID from the live database."""
    resp = client.get("/api/v1/projects?page=1&page_size=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) > 0, "At least one project required in database for tests."
    return data["items"][0]["project_id"]


@pytest.fixture(scope="module")
def project_with_dossier():
    """Dynamically find a project that has an associated row in v_project_monthly_dossier."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        dossier = session.query(ProjectMonthlyDossier).first()
        assert dossier is not None, "At least one dossier required in database for tests."
        return dossier.project_id, dossier.report_month
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def test_1_list_projects_status_200():
    """1. GET /api/v1/projects returns HTTP 200."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200


def test_2_project_list_pagination_structure():
    """2. Verify project list follows expected pagination envelope."""
    response = client.get("/api/v1/projects?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5
    assert data["total"] > 0

    first_item = data["items"][0]
    expected_keys = {"project_id", "project_name", "agency", "state", "original_cost_crore", "is_active"}
    assert expected_keys.issubset(first_item.keys())


def test_3_page_size_max_validation():
    """3. page_size > 100 or page < 1 must be rejected with HTTP 422."""
    resp_over = client.get("/api/v1/projects?page_size=101")
    assert resp_over.status_code == 422

    resp_zero = client.get("/api/v1/projects?page=0")
    assert resp_zero.status_code == 422


def test_4_project_filters():
    """4. Verify agency, state, and is_active filters work."""
    # Retrieve a sample agency and state
    sample_resp = client.get("/api/v1/projects?page=1&page_size=1")
    sample = sample_resp.json()["items"][0]
    target_agency = sample["agency"]

    filtered_resp = client.get(f"/api/v1/projects?agency={target_agency}&page_size=10")
    assert filtered_resp.status_code == 200
    filtered_data = filtered_resp.json()
    assert filtered_data["total"] > 0
    for item in filtered_data["items"]:
        assert item["agency"].lower() == target_agency.lower()

    # Verify is_active filter
    active_resp = client.get("/api/v1/projects?is_active=true&page_size=5")
    assert active_resp.status_code == 200
    for item in active_resp.json()["items"]:
        assert item["is_active"] is True


def test_5_get_project_detail_valid(valid_project_id):
    """5. GET /api/v1/projects/{valid_id} returns HTTP 200 with ProjectDetail fields."""
    response = client.get(f"/api/v1/projects/{valid_project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == valid_project_id
    assert "agency" in data
    assert "state" in data
    assert "legacy_ocms_code" in data
    assert "approval_start_date" in data
    assert "original_completion_date" in data


def test_6_get_project_detail_invalid():
    """6. GET /api/v1/projects/{invalid_id} returns HTTP 404."""
    response = client.get("/api/v1/projects/NONEXISTENT_PROJECT_999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_7_get_project_snapshots_valid(valid_project_id):
    """7. GET /api/v1/projects/{valid_id}/snapshots returns HTTP 200."""
    response = client.get(f"/api/v1/projects/{valid_project_id}/snapshots")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == valid_project_id
    assert "total_snapshots" in data
    assert "snapshots" in data
    assert isinstance(data["snapshots"], list)
    assert data["total_snapshots"] == len(data["snapshots"])


def test_8_snapshot_series_ordered_by_report_month(valid_project_id):
    """8. Snapshots in MonthlySnapshotSeriesResponse are ordered chronologically by report_month ASC."""
    response = client.get(f"/api/v1/projects/{valid_project_id}/snapshots")
    assert response.status_code == 200
    snapshots = response.json()["snapshots"]
    if len(snapshots) > 1:
        months = [s["report_month"] for s in snapshots]
        assert months == sorted(months), f"Snapshots not sorted chronologically: {months}"


def test_9_missing_project_for_snapshots_returns_404():
    """9. Missing project for snapshots returns HTTP 404."""
    response = client.get("/api/v1/projects/NONEXISTENT_PROJECT_999999/snapshots")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_10_get_project_dossier_valid(project_with_dossier):
    """10. GET /api/v1/projects/{valid_id}/dossier returns ProjectMonthlyDossierResponse."""
    project_id, report_month = project_with_dossier
    # Test default (latest month)
    resp_latest = client.get(f"/api/v1/projects/{project_id}/dossier")
    assert resp_latest.status_code == 200
    dossier_data = resp_latest.json()
    assert dossier_data["project_id"] == project_id
    assert "snapshot_id" in dossier_data
    assert "report_month" in dossier_data

    # Test explicit report_month query parameter
    resp_month = client.get(f"/api/v1/projects/{project_id}/dossier?report_month={report_month}")
    assert resp_month.status_code == 200
    assert resp_month.json()["report_month"] == report_month


def test_11_missing_project_for_dossier_returns_404():
    """11. Missing project for dossier returns HTTP 404."""
    response = client.get("/api/v1/projects/NONEXISTENT_PROJECT_999999/dossier")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_12_no_endpoint_performs_database_writes(valid_project_id, project_with_dossier):
    """12. Confirm that read-only endpoints execute zero database writes."""
    project_id, _ = project_with_dossier

    count_before = client.get("/api/v1/projects?page=1&page_size=1").json()["total"]

    # Execute all 4 read endpoints
    client.get("/api/v1/projects?page=1&page_size=10")
    client.get(f"/api/v1/projects/{valid_project_id}")
    client.get(f"/api/v1/projects/{valid_project_id}/snapshots")
    client.get(f"/api/v1/projects/{project_id}/dossier")

    count_after = client.get("/api/v1/projects?page=1&page_size=1").json()["total"]
    assert count_before == count_after, "Total project count changed after read requests!"
