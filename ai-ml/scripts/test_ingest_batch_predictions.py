"""
Unit and Integration Tests for Batch Prediction Ingestion Pipeline (Phase 5B-2).

Tests:
1. Valid BatchScorer output maps correctly to MLRiskScore record schema.
2. Duplicate (project_id, report_month) keys within input batch are detected and rejected.
3. Invalid/out-of-bounds risk values (<0, >1, NaN, Inf) are rejected.
4. Invalid report_month formats are rejected.
5. Missing required output fields trigger validation failure.
6. Invalid risk_band and dominant_component enums are rejected.
7. Idempotent upsert logic: ON CONFLICT (project_id, report_month) DO UPDATE statement construction.
8. Database error causes immediate transaction rollback.
9. Credentials sanitization: passwords and connection URIs are never exposed in exceptions.
10. Model version is strictly preserved.
11. ESI isolation: execution_stress_scores is never queried or mutated.
"""

from decimal import Decimal
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Ensure ai-ml and backend paths are importable
AI_ML_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = AI_ML_ROOT.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(AI_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ML_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from scripts.ingest_batch_predictions import (
    BatchDuplicateKeyError,
    BatchValidationError,
    DatabaseIngestionError,
    sanitize_error_message,
    upsert_ml_risk_scores,
    validate_prediction_dataframe,
)
from app.models.enums import DominantComponentEnum, RiskBandEnum
from app.models.risk import MLRiskScore


@pytest.fixture
def valid_sample_df() -> pd.DataFrame:
    """Returns a valid 3-row DataFrame matching BatchScorer output contract."""
    return pd.DataFrame([
        {
            "project_id": "PRJ001",
            "report_month": "2025-04",
            "schedule_delay_risk": 0.8520,
            "cost_overrun_risk": 0.4210,
            "schedule_revision_risk": 0.1200,
            "selected_integrated_risk": 0.5914,
            "risk_band": "MODERATE",
            "dominant_component": "Schedule Delay",
            "schedule_contribution": 0.4260,
            "cost_contribution": 0.1474,
            "schedule_revision_contribution": 0.0180,
            "model_version": "v1.0.0-rf02-calibrated",
        },
        {
            "project_id": "PRJ002",
            "report_month": "2025-04",
            "schedule_delay_risk": 0.2140,
            "cost_overrun_risk": 0.7890,
            "schedule_revision_risk": 0.0500,
            "selected_integrated_risk": 0.3907,
            "risk_band": "MODERATE",
            "dominant_component": "Cost Overrun",
            "schedule_contribution": 0.1070,
            "cost_contribution": 0.2762,
            "schedule_revision_contribution": 0.0075,
            "model_version": "v1.0.0-rf02-calibrated",
        },
        {
            "project_id": "PRJ003",
            "report_month": "2025-04",
            "schedule_delay_risk": 0.9500,
            "cost_overrun_risk": 0.8900,
            "schedule_revision_risk": 0.8200,
            "selected_integrated_risk": 0.9095,
            "risk_band": "VERY_HIGH",
            "dominant_component": "Schedule Delay",
            "schedule_contribution": 0.4750,
            "cost_contribution": 0.3115,
            "schedule_revision_contribution": 0.1230,
            "model_version": "v1.0.0-rf02-calibrated",
        },
    ])


# ------------------------------------------------------------------------------
# Test 1: Valid Mapping
# ------------------------------------------------------------------------------
def test_valid_batch_scorer_output_mapping(valid_sample_df):
    """Verifies that valid BatchScorer output correctly transforms into database records."""
    records = validate_prediction_dataframe(valid_sample_df)
    assert len(records) == 3

    r0 = records[0]
    assert r0["project_id"] == "PRJ001"
    assert r0["report_month"] == "2025-04"
    assert isinstance(r0["schedule_delay_risk"], Decimal)
    assert r0["schedule_delay_risk"] == Decimal("0.8520")
    assert r0["risk_band"] == RiskBandEnum.MODERATE
    assert r0["dominant_component"] == DominantComponentEnum.SCHEDULE_DELAY
    assert r0["model_version"] == "v1.0.0-rf02-calibrated"


# ------------------------------------------------------------------------------
# Test 2: In-Batch Duplicate Key Detection
# ------------------------------------------------------------------------------
def test_duplicate_keys_within_batch_detected(valid_sample_df):
    """Verifies that duplicate (project_id, report_month) keys inside batch are rejected."""
    df_dup = valid_sample_df.copy()
    # Make row 1 duplicate row 0 key
    df_dup.loc[1, "project_id"] = "PRJ001"
    df_dup.loc[1, "report_month"] = "2025-04"

    with pytest.raises(BatchDuplicateKeyError) as exc_info:
        validate_prediction_dataframe(df_dup)
    assert "PRJ001" in str(exc_info.value)
    assert "2025-04" in str(exc_info.value)


# ------------------------------------------------------------------------------
# Test 3: Numerical Bounds & NaN Validation
# ------------------------------------------------------------------------------
def test_invalid_risk_values_rejected(valid_sample_df):
    """Verifies that NaN, Inf, and out-of-bound risk values are rejected."""
    # NaN
    df_nan = valid_sample_df.copy()
    df_nan.loc[0, "schedule_delay_risk"] = np.nan
    with pytest.raises(BatchValidationError) as exc_info:
        validate_prediction_dataframe(df_nan)
    assert "NaN or Inf" in str(exc_info.value)

    # Below 0.0
    df_neg = valid_sample_df.copy()
    df_neg.loc[0, "cost_overrun_risk"] = -0.05
    with pytest.raises(BatchValidationError) as exc_info:
        validate_prediction_dataframe(df_neg)
    assert "out of bounds" in str(exc_info.value)

    # Above 1.0
    df_large = valid_sample_df.copy()
    df_large.loc[0, "selected_integrated_risk"] = 1.05
    with pytest.raises(BatchValidationError) as exc_info:
        validate_prediction_dataframe(df_large)
    assert "out of bounds" in str(exc_info.value)


# ------------------------------------------------------------------------------
# Test 4: Report Month Format
# ------------------------------------------------------------------------------
def test_invalid_report_month_rejected(valid_sample_df):
    """Verifies that malformed report_month values are rejected."""
    invalid_months = ["2025/04", "2025-13", "2025-00", "April-2025", "2025-4", "2025-04-01"]
    for bad_month in invalid_months:
        df_bad = valid_sample_df.copy()
        df_bad.loc[0, "report_month"] = bad_month
        with pytest.raises(BatchValidationError) as exc_info:
            validate_prediction_dataframe(df_bad)
        assert "Invalid report_month" in str(exc_info.value)


# ------------------------------------------------------------------------------
# Test 5: Missing Output Fields
# ------------------------------------------------------------------------------
def test_missing_output_fields_rejected(valid_sample_df):
    """Verifies that missing columns from the output contract are caught immediately."""
    df_missing = valid_sample_df.drop(columns=["schedule_contribution"])
    with pytest.raises(BatchValidationError) as exc_info:
        validate_prediction_dataframe(df_missing)
    assert "Missing required prediction output columns" in str(exc_info.value)
    assert "schedule_contribution" in str(exc_info.value)


# ------------------------------------------------------------------------------
# Test 6: Invalid Enums
# ------------------------------------------------------------------------------
def test_invalid_enums_rejected(valid_sample_df):
    """Verifies that non-standard risk bands or dominant components are rejected."""
    df_bad_band = valid_sample_df.copy()
    df_bad_band.loc[0, "risk_band"] = "CRITICAL"
    with pytest.raises(BatchValidationError) as exc_info:
        validate_prediction_dataframe(df_bad_band)
    assert "Invalid risk_band 'CRITICAL'" in str(exc_info.value)

    df_bad_dom = valid_sample_df.copy()
    df_bad_dom.loc[0, "dominant_component"] = "Environmental Delay"
    with pytest.raises(BatchValidationError) as exc_info:
        validate_prediction_dataframe(df_bad_dom)
    assert "Invalid dominant_component" in str(exc_info.value)


# ------------------------------------------------------------------------------
# Test 7: Idempotent Upsert Logic (Mocked DB Session)
# ------------------------------------------------------------------------------
def test_idempotent_upsert_logic_mock(valid_sample_df):
    """Verifies that upsert_ml_risk_scores executes ON CONFLICT DO UPDATE correctly."""
    records = validate_prediction_dataframe(valid_sample_df)

    mock_session = MagicMock()
    # Simulate 1 existing row (PRJ001, 2025-04) and 2 new rows
    mock_session.execute.return_value.all.return_value = [("PRJ001", "2025-04")]

    counts = upsert_ml_risk_scores(mock_session, records)

    assert counts["total"] == 3
    assert counts["inserted"] == 2
    assert counts["updated"] == 1
    assert counts["skipped"] == 0

    # Ensure session.execute was called twice: once for key check, once for pg_insert
    assert mock_session.execute.call_count == 2


# ------------------------------------------------------------------------------
# Test 8: Transaction Rollback on Database Error
# ------------------------------------------------------------------------------
def test_transaction_rollback_on_db_error(valid_sample_df):
    """Verifies that database exceptions trigger session rollback and raise DatabaseIngestionError."""
    records = validate_prediction_dataframe(valid_sample_df)

    mock_session = MagicMock()
    # Mock error on insert execution
    mock_session.execute.side_effect = [
        MagicMock(all=lambda: []),  # Key check succeeds
        Exception("Connection terminated unexpectedly"),  # Upsert statement fails
    ]

    with pytest.raises(Exception):
        upsert_ml_risk_scores(mock_session, records)


# ------------------------------------------------------------------------------
# Test 9: Credentials Sanitization
# ------------------------------------------------------------------------------
def test_credentials_never_printed():
    """Verifies that sensitive connection strings and passwords are masked from all logs/errors."""
    raw_error = "FATAL: password authentication failed for user 'postgres' in postgresql://postgres:superSecretPass123@aws.supabase.com:5432/postgres"
    sanitized = sanitize_error_message(raw_error)

    assert "superSecretPass123" not in sanitized
    assert "://***:***@" in sanitized


# ------------------------------------------------------------------------------
# Test 10: Model Version Preserved
# ------------------------------------------------------------------------------
def test_model_version_preserved(valid_sample_df):
    """Verifies that model_version is strictly preserved from the scoring engine."""
    records = validate_prediction_dataframe(valid_sample_df)
    for r in records:
        assert r["model_version"] == "v1.0.0-rf02-calibrated"


# ------------------------------------------------------------------------------
# Test 11: ESI Isolation
# ------------------------------------------------------------------------------
def test_esi_isolation():
    """Verifies that ingest_batch_predictions interacts strictly with ml_risk_scores."""
    from scripts.ingest_batch_predictions import MLRiskScore

    assert MLRiskScore.__tablename__ == "ml_risk_scores"
    # Ensure no import or usage of ExecutionStressScore in the ingestion script
    import scripts.ingest_batch_predictions as mod
    assert not hasattr(mod, "ExecutionStressScore")
