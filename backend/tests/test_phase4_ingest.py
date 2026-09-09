import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user
from app.models.user import User
from app.models.enums import UserRoleEnum
import uuid

# --- AUTH MOCK ---
def override_get_current_user():
    return User(
        user_id=uuid.uuid4(),
        email="admin@mospi.gov.in",
        full_name="Admin",
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

# --- TESTS ---

def test_upload_invalid_file_type():
    response = client.post(
        "/api/v1/ingest/flash-report",
        data={"report_month": "2026-07"},
        files={"file": ("test.txt", b"dummy content", "text/plain")}
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]

def test_upload_invalid_month():
    response = client.post(
        "/api/v1/ingest/flash-report",
        data={"report_month": "July 2026"},
        files={"file": ("test.pdf", b"dummy pdf content", "application/pdf")}
    )
    assert response.status_code == 400
    assert "YYYY-MM" in response.json()["detail"]

@patch("app.api.v1.ingest.process_flash_report_task")
def test_upload_valid_pdf_queues_task(mock_task):
    mock_task.delay.return_value = MagicMock(id="fake-uuid-1234")
    
    response = client.post(
        "/api/v1/ingest/flash-report",
        data={"report_month": "2026-07"},
        files={"file": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "QUEUED"
    assert data["task_id"] == "fake-uuid-1234"
    assert data["report_month"] == "2026-07"
    mock_task.delay.assert_called_once()

def test_worker_fails_at_missing_boundary():
    from app.worker.tasks import process_flash_report_task
    with pytest.raises(NotImplementedError) as exc_info:
        # Pass None for self because bind=True
        process_flash_report_task(None, "fake/path.pdf", "2026-07")
    
    assert "external/ML-side dependency and is not implemented" in str(exc_info.value)

@patch("app.services.ingestion.insert")
def test_valid_ml_output_mapping(mock_insert):
    from app.services.ingestion import IngestionPersistenceService
    
    mock_db = MagicMock()
    service = IngestionPersistenceService(mock_db)
    
    df = pd.DataFrame({
        "project_id": ["P1"],
        "report_month": ["2026-07"],
        "schedule_delay_risk": [0.5],
        "cost_overrun_risk": [0.1],
        "schedule_revision_risk": [0.2],
        "selected_integrated_risk": [0.4],
        "risk_band": ["MODERATE"],
        "dominant_component": ["Schedule Delay"],
        "schedule_contribution": [0.8],
        "cost_contribution": [0.1],
        "schedule_revision_contribution": [0.1],
        "model_version": ["v1.0.0-rf02-calibrated"]
    })
    
    mock_stmt = MagicMock()
    mock_insert.return_value = mock_stmt
    mock_stmt.on_conflict_do_update.return_value = "upsert_stmt"
    
    count = service.persist_ml_risk_scores(df)
    assert count == 1
    mock_db.execute.assert_called_once()
