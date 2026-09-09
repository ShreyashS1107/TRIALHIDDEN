from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """
    Test GET /api/v1/health endpoint with active database.
    Verifies HTTP 200, status == 'ok', service == 'SIH26103 Backend',
    and database == 'connected'.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "SIH26103 Backend"
    assert data["database"] == "connected"


def test_health_check_degraded_when_db_fails():
    """
    Test GET /api/v1/health endpoint when database connection fails.
    Verifies degraded status without exposing error details or crashing.
    """
    with patch("app.api.v1.health.engine") as mock_engine:
        mock_engine.connect.side_effect = Exception("Simulated connection error")
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["service"] == "SIH26103 Backend"
        assert data["database"] == "unavailable"
        assert "Simulated" not in response.text


def test_docs_and_openapi_available():
    """
    Verify /docs and /openapi.json are exposed properly.
    """
    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "SIH26103 Backend"

    docs_response = client.get("/docs")
    assert docs_response.status_code == 200
