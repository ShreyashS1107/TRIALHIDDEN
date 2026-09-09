from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_benchmarks_endpoint():
    """
    Test GET /api/v1/benchmarks/ocms endpoint.
    Verifies that the endpoint exists and returns a paginated response.
    """
    response = client.get("/api/v1/benchmarks/ocms")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data

def test_list_benchmarks_with_filters():
    """
    Test GET /api/v1/benchmarks/ocms endpoint with filters.
    """
    response = client.get("/api/v1/benchmarks/ocms?benchmark_level=Agency x Year&entity_name=NHAI&year=2023")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
