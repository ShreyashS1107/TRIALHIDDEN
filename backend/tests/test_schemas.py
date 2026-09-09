from decimal import Decimal
import uuid
import pytest
from pydantic import ValidationError

from app.database.session import get_db
from app.models import (
    AlertSeverityEnum,
    AlertSourceEnum,
    AlertStatusEnum,
    DominantComponentEnum,
    DominantStressorEnum,
    EsiTierEnum,
    ExecutionStressScore,
    MLRiskScore,
    MonthlySnapshot,
    PrescriptiveActionEnum,
    Project,
    ProjectMonthlyDossier,
    RiskBandEnum,
)
from app.schemas import (
    BaseSchema,
    ExecutionStressScoreResponse,
    MLRiskScoreResponse,
    MonthlySnapshotResponse,
    MonthlySnapshotSeriesResponse,
    ProjectDetail,
    ProjectMonthlyDossierResponse,
    ProjectSummary,
    SystemAlertResponse,
)


@pytest.fixture(scope="module")
def db_session():
    """Yield a database session for read-only schema validation tests."""
    db_gen = get_db()
    session = next(db_gen)
    try:
        yield session
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


def test_1_schema_imports():
    """1. Verify all schema classes can be imported cleanly."""
    from app.schemas import (
        BaseSchema,
        ExecutionStressScoreResponse,
        MLRiskScoreResponse,
        MonthlySnapshotResponse,
        MonthlySnapshotSeriesResponse,
        ProjectDetail,
        ProjectMonthlyDossierResponse,
        ProjectSummary,
        SystemAlertResponse,
    )
    assert BaseSchema is not None
    assert ProjectSummary is not None
    assert ProjectDetail is not None
    assert MonthlySnapshotResponse is not None
    assert MonthlySnapshotSeriesResponse is not None
    assert MLRiskScoreResponse is not None
    assert ExecutionStressScoreResponse is not None
    assert SystemAlertResponse is not None
    assert ProjectMonthlyDossierResponse is not None


def test_2_project_summary_and_detail_from_live_orm(db_session):
    """2 & 7. Verify ProjectSummary and ProjectDetail validate from live ORM instances."""
    live_project = db_session.query(Project).first()
    assert live_project is not None, "Live project record required for validation test"

    summary = ProjectSummary.model_validate(live_project)
    assert summary.project_id == live_project.project_id
    assert summary.agency == live_project.agency
    assert summary.state == live_project.state
    assert summary.is_active == live_project.is_active
    if live_project.original_cost_crore is not None:
        assert isinstance(summary.original_cost_crore, Decimal)

    detail = ProjectDetail.model_validate(live_project)
    assert detail.project_id == live_project.project_id
    assert detail.legacy_ocms_code == live_project.legacy_ocms_code
    assert detail.approval_start_date == live_project.approval_start_date


def test_3_nullable_fields_accept_none():
    """3. Verify nullable database fields accept None without validation errors."""
    data = {
        "project_id": "TEST01",
        "project_name": None,
        "agency": "TEST_AGENCY",
        "state": "TEST_STATE",
        "original_cost_crore": None,
        "is_active": True,
        "legacy_ocms_code": None,
        "approval_start_date": None,
        "original_completion_date": None,
        "created_at": None,
        "updated_at": None,
    }
    detail = ProjectDetail.model_validate(data)
    assert detail.project_name is None
    assert detail.original_cost_crore is None
    assert detail.approval_start_date is None


def test_4_decimal_fields_remain_decimal(db_session):
    """4. Verify financial and score numeric fields remain Decimal."""
    live_snapshot = db_session.query(MonthlySnapshot).filter(MonthlySnapshot.revised_cost_crore.isnot(None)).first()
    if live_snapshot:
        resp = MonthlySnapshotResponse.model_validate(live_snapshot)
        assert isinstance(resp.revised_cost_crore, Decimal)
        if resp.cumulative_expenditure_crore is not None:
            assert isinstance(resp.cumulative_expenditure_crore, Decimal)

    live_risk = db_session.query(MLRiskScore).first()
    if live_risk:
        resp = MLRiskScoreResponse.model_validate(live_risk)
        assert isinstance(resp.schedule_delay_risk, Decimal)
        assert isinstance(resp.cost_overrun_risk, Decimal)
        assert isinstance(resp.selected_integrated_risk, Decimal)


def test_5_month_fields_remain_strings(db_session):
    """5. Verify YYYY-MM month fields serialize as 7-character strings."""
    live_snapshot = db_session.query(MonthlySnapshot).first()
    assert live_snapshot is not None
    resp = MonthlySnapshotResponse.model_validate(live_snapshot)
    assert isinstance(resp.report_month, str)
    assert len(resp.report_month) == 7
    assert resp.report_month[4] == "-"


def test_6_enum_fields_serialize_exact_database_values(db_session):
    """6. Verify PostgreSQL enums serialize using their exact database values, including spaces."""
    live_risk = db_session.query(MLRiskScore).first()
    assert live_risk is not None
    resp = MLRiskScoreResponse.model_validate(live_risk)
    dumped = resp.model_dump()
    assert dumped["dominant_component"] in ["Schedule Delay", "Cost Overrun", "Schedule Revision"]
    assert dumped["risk_band"] in ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]

    live_esi = db_session.query(ExecutionStressScore).first()
    assert live_esi is not None
    esi_resp = ExecutionStressScoreResponse.model_validate(live_esi)
    esi_dumped = esi_resp.model_dump()
    assert esi_dumped["dominant_stressor"] in [
        "Progress Velocity Collapse",
        "Physical Progress Stagnation",
        "Expenditure Divergence",
        "Schedule Slippage Debt",
        "Reporting Friction",
    ]
    assert esi_dumped["esi_tier"] in ["NOMINAL", "WATCH", "ATTENTION", "HIGH_PRIORITY"]


def test_8_monthly_snapshot_series_schema(db_session):
    """8. Verify MonthlySnapshotSeriesResponse represents an ordered collection."""
    snapshots = db_session.query(MonthlySnapshot).limit(5).all()
    assert len(snapshots) > 0
    project_id = snapshots[0].project_id

    series = MonthlySnapshotSeriesResponse(
        project_id=project_id,
        total_snapshots=len(snapshots),
        snapshots=[MonthlySnapshotResponse.model_validate(s) for s in snapshots],
    )
    assert series.project_id == project_id
    assert series.total_snapshots == len(snapshots)
    assert len(series.snapshots) == len(snapshots)
    assert isinstance(series.snapshots[0].snapshot_id, uuid.UUID)


def test_9_ml_risk_score_schema(db_session):
    """9. Verify MLRiskScoreResponse validates from live prediction records."""
    live_risk = db_session.query(MLRiskScore).first()
    assert live_risk is not None
    resp = MLRiskScoreResponse.model_validate(live_risk)
    assert resp.score_id == live_risk.score_id
    assert resp.project_id == live_risk.project_id
    assert resp.report_month == live_risk.report_month
    assert resp.model_version == live_risk.model_version


def test_10_execution_stress_score_schema(db_session):
    """10. Verify ExecutionStressScoreResponse validates from live surveillance records."""
    live_esi = db_session.query(ExecutionStressScore).first()
    assert live_esi is not None
    resp = ExecutionStressScoreResponse.model_validate(live_esi)
    assert resp.project_id == live_esi.project_id
    assert resp.report_month == live_esi.report_month
    assert 0 <= resp.total_stress_flags <= 5
    assert resp.execution_index_version == live_esi.execution_index_version


def test_11_alert_schema():
    """11. Verify SystemAlertResponse schema with exact enums."""
    sample_id = uuid.uuid4()
    alert_data = {
        "alert_id": sample_id,
        "project_id": "105236",
        "report_month": "2025-04",
        "alert_code": "ML_CRITICAL_RISK",
        "severity": AlertSeverityEnum.HIGH,
        "alert_source": AlertSourceEnum.ML_ENGINE,
        "message": "Integrated risk exceeded critical threshold",
        "status": AlertStatusEnum.ACTIVE,
        "acknowledged_by": None,
        "acknowledged_at": None,
        "created_at": None,
    }
    alert_resp = SystemAlertResponse.model_validate(alert_data)
    assert alert_resp.alert_id == sample_id
    assert alert_resp.severity == AlertSeverityEnum.HIGH
    assert alert_resp.alert_source == AlertSourceEnum.ML_ENGINE
    assert alert_resp.status == AlertStatusEnum.ACTIVE
    assert alert_resp.model_dump()["severity"] == "HIGH"


def test_12_dossier_schema(db_session):
    """12. Verify ProjectMonthlyDossierResponse validates from live analytical view."""
    live_dossier = db_session.query(ProjectMonthlyDossier).first()
    assert live_dossier is not None
    resp = ProjectMonthlyDossierResponse.model_validate(live_dossier)
    assert resp.snapshot_id == live_dossier.snapshot_id
    assert resp.project_id == live_dossier.project_id
    assert resp.report_month == live_dossier.report_month
    # Check that derived fields validate without error
    if resp.cost_escalation_crore is not None:
        assert isinstance(resp.cost_escalation_crore, Decimal)


def test_13_missing_required_fields_rejected():
    """13. Verify that omitting required fields raises a ValidationError."""
    with pytest.raises(ValidationError):
        # Missing project_id, agency, state, is_active
        ProjectSummary.model_validate({"project_name": "Incomplete Project"})

    with pytest.raises(ValidationError):
        # Missing score_id, risks, bands
        MLRiskScoreResponse.model_validate({"project_id": "105236", "report_month": "2025-04"})

    with pytest.raises(ValidationError):
        # Missing snapshot_id
        MonthlySnapshotResponse.model_validate({"project_id": "105236", "report_month": "2025-04"})
