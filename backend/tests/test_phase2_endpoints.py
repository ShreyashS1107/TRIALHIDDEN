from fastapi.testclient import TestClient
from app.main import app


from app.core.security import get_current_user
from app.models.user import User
from app.models.enums import UserRoleEnum
import uuid

def override_get_current_user():
    return User(
        user_id=uuid.uuid4(),
        email="test@mospi.gov.in",
        full_name="Test User",
        role=UserRoleEnum.MOSPI_ADMIN,
        is_active=True
    )


import pytest
@pytest.fixture(autouse=True, scope="module")
def mock_auth_for_module():
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


client = TestClient(app)

def test_portfolio_summary():
    response = client.get("/api/v1/portfolio/summary")
    assert response.status_code == 200

def test_portfolio_breakdown_agency():
    response = client.get("/api/v1/portfolio/breakdown/agency?report_month=2026-03")
    assert response.status_code == 200

def test_portfolio_breakdown_state():
    response = client.get("/api/v1/portfolio/breakdown/state?report_month=2026-03")
    assert response.status_code == 200

def test_meta_epochs():
    response = client.get("/api/v1/meta/epochs")
    assert response.status_code == 200
    assert "total_epochs" in response.json()

def test_export_csv():
    response = client.get("/api/v1/export/projects/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

def test_projects_compare():
    # Comparing 2 arbitrary IDs
    response = client.get("/api/v1/projects/compare?project_ids=1,2")
    assert response.status_code == 200
    # Could be empty list if projects not found
    assert isinstance(response.json(), list)

def test_projects_compare_invalid():
    # < 2 IDs should fail
    response = client.get("/api/v1/projects/compare?project_ids=1")
    assert response.status_code == 400
