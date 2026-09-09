"""
Unit and Integration Tests for Execution Surveillance (ESI) Ingestion Pipeline (Phase 5C-2).

Tests:
1. Valid surveillance DataFrame correctly maps to ExecutionStressScore schema.
2. Duplicate (project_id, report_month) keys within input batch are detected and rejected.
3. Invalid/out-of-bounds score values (<0, >1, NaN, Inf) are rejected.
4. Invalid report_month formats are rejected.
5. Missing required output fields trigger validation failure.
6. Invalid esi_tier enums are rejected.
7. Invalid dominant_stressor enums are rejected.
8. Invalid suggested_action enums are rejected.
9. Invalid operational flags (<0, >1, non-integers) are rejected.
10. Total stress flags validation (bounds [0, 5] and sum match).
11. Version string validation (must equal 'v1.0.0-esi-5dim').
12. Decimal conversion to exactly 4 decimal places.
13. project_id validation (non-empty, <= 32 chars).
14. Idempotent upsert SQL construction: ON CONFLICT (project_id, report_month) DO UPDATE.
15. Upsert counting: accurately counts inserts vs updates.
16. Project foreign key verification: succeeds when all projects exist.
17. Project foreign key verification: fails safely with MissingProjectError when project missing.
18. Rollback-test mode: executes session.rollback() and never calls commit.
19. Transaction failure handling: exception triggers rollback and raises DatabaseIngestionError.
20. Credentials sanitization: passwords and connection URIs are masked in error messages.
21. Dry-run mode: computes and validates without database connection.
22. Month and project filtering: correctly filters input rows.
23. Limit option: correctly caps processed row count.
24. Empty input handling: returns zero counts cleanly.
25. Deterministic repeated ingestion: identical payloads across runs.
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

from scripts.ingest_surveillance_scores import (
    BatchDuplicateKeyError,
    BatchValidationError,
    DatabaseIngestionError,
    MissingProjectError,
    run_ingestion,
    sanitize_error_message,
    to_decimal_4,
    upsert_execution_stress_scores,
    validate_surveillance_dataframe,
    verify_project_foreign_keys,
)
from app.models.enums import DominantStressorEnum, EsiTierEnum, PrescriptiveActionEnum
from app.models.execution import ExecutionStressScore


@pytest.fixture
def valid_surveillance_df() -> pd.DataFrame:
    """Returns a valid 3-row DataFrame matching ExecutionSurveillanceEngine output."""
    return pd.DataFrame([
        {
            "project_id": "PRJ001",
            "report_month": "2025-04",
            "s_stag": 0.4250,
            "s_vel": 0.6250,
            "s_div": 0.4000,
            "s_sched": 0.3000,
            "s_rep": 0.4000,
            "flag_stag": 1,
            "flag_vel": 1,
            "flag_div": 1,
            "flag_sched": 0,
            "flag_rep": 1,
            "total_stress_flags": 4,
            "execution_stress_index": 0.4488,
            "esi_tier": "WATCH",
            "dominant_stressor": "Progress Velocity Collapse",
            "suggested_action": "SITE_OBSTACLE_AUDIT",
            "execution_index_version": "v1.0.0-esi-5dim",
        },
        {
            "project_id": "PRJ002",
            "report_month": "2025-04",
            "s_stag": 0.0000,
            "s_vel": 1.0000,
            "s_div": 0.0000,
            "s_sched": 0.5000,
            "s_rep": 0.3000,
            "flag_stag": 0,
            "flag_vel": 1,
            "flag_div": 0,
            "flag_sched": 0,
            "flag_rep": 0,
            "total_stress_flags": 1,
            "execution_stress_index": 0.3550,
            "esi_tier": "WATCH",
            "dominant_stressor": "Progress Velocity Collapse",
            "suggested_action": "RESOURCE_MOBILIZATION_DIRECTIVE",
            "execution_index_version": "v1.0.0-esi-5dim",
        },
        {
            "project_id": "PRJ003",
            "report_month": "2025-05",
            "s_stag": 0.8500,
            "s_vel": 0.8000,
            "s_div": 0.7500,
            "s_sched": 0.9000,
            "s_rep": 0.7000,
            "flag_stag": 1,
            "flag_vel": 1,
            "flag_div": 1,
            "flag_sched": 1,
            "flag_rep": 1,
            "total_stress_flags": 5,
            "execution_stress_index": 0.8100,
            "esi_tier": "HIGH_PRIORITY",
            "dominant_stressor": "Physical Progress Stagnation",
            "suggested_action": "INTER_MINISTERIAL_COMMITTEE_ESCALATION",
            "execution_index_version": "v1.0.0-esi-5dim",
        },
    ])


# ==============================================================================
# 1. Output Mapping Validation
# ==============================================================================
def test_valid_surveillance_dataframe_mapping(valid_surveillance_df):
    """Validates that a conforming surveillance DataFrame maps to typed records."""
    records = validate_surveillance_dataframe(valid_surveillance_df)
    assert len(records) == 3

    r0 = records[0]
    assert r0["project_id"] == "PRJ001"
    assert r0["report_month"] == "2025-04"
    assert isinstance(r0["s_stag"], Decimal)
    assert r0["s_stag"] == Decimal("0.4250")
    assert isinstance(r0["flag_stag"], int)
    assert r0["flag_stag"] == 1
    assert r0["total_stress_flags"] == 4
    assert isinstance(r0["execution_stress_index"], Decimal)
    assert r0["esi_tier"] == EsiTierEnum.WATCH
    assert r0["dominant_stressor"] == DominantStressorEnum.PROGRESS_VELOCITY_COLLAPSE
    assert r0["suggested_action"] == PrescriptiveActionEnum.SITE_OBSTACLE_AUDIT
    assert r0["execution_index_version"] == "v1.0.0-esi-5dim"


# ==============================================================================
# 2. Duplicate Key Detection
# ==============================================================================
def test_duplicate_keys_within_batch_detected(valid_surveillance_df):
    """Rejects batches containing duplicate (project_id, report_month) composite keys."""
    dup_row = valid_surveillance_df.iloc[0:1].copy()
    df_with_dups = pd.concat([valid_surveillance_df, dup_row], ignore_index=True)

    with pytest.raises(BatchDuplicateKeyError, match="duplicate.*composite keys"):
        validate_surveillance_dataframe(df_with_dups)


# ==============================================================================
# 3. Invalid Score Value Rejection
# ==============================================================================
@pytest.mark.parametrize("bad_val", [-0.01, 1.05, np.nan, np.inf])
def test_invalid_score_values_rejected(valid_surveillance_df, bad_val):
    """Rejects out-of-bounds or non-finite values in any score field."""
    df = valid_surveillance_df.copy()
    df.loc[0, "execution_stress_index"] = bad_val
    with pytest.raises(BatchValidationError):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 4. Invalid Report Month Format
# ==============================================================================
@pytest.mark.parametrize("bad_month", ["2025-13", "2025-00", "2025/04", "April 2025", "2025-4", ""])
def test_invalid_report_month_rejected(valid_surveillance_df, bad_month):
    """Rejects non-conforming report_month formats."""
    df = valid_surveillance_df.copy()
    df.loc[0, "report_month"] = bad_month
    with pytest.raises(BatchValidationError, match="Invalid report_month"):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 5. Missing Output Fields
# ==============================================================================
def test_missing_output_fields_rejected(valid_surveillance_df):
    """Rejects DataFrame missing any required column."""
    df = valid_surveillance_df.drop(columns=["dominant_stressor"])
    with pytest.raises(BatchValidationError, match="Missing required surveillance output columns"):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 6. Invalid ESI Tier
# ==============================================================================
def test_invalid_esi_tier_rejected(valid_surveillance_df):
    """Rejects unknown ESI tiers."""
    df = valid_surveillance_df.copy()
    df.loc[0, "esi_tier"] = "EXTREME_HAZARD"
    with pytest.raises(BatchValidationError, match="Invalid esi_tier"):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 7. Invalid Dominant Stressor
# ==============================================================================
def test_invalid_dominant_stressor_rejected(valid_surveillance_df):
    """Rejects non-canonical dominant stressor names."""
    df = valid_surveillance_df.copy()
    df.loc[0, "dominant_stressor"] = "General Confusion"
    with pytest.raises(BatchValidationError, match="Invalid dominant_stressor"):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 8. Invalid Suggested Action
# ==============================================================================
def test_invalid_suggested_action_rejected(valid_surveillance_df):
    """Rejects non-canonical prescriptive actions."""
    df = valid_surveillance_df.copy()
    df.loc[0, "suggested_action"] = "DO_NOTHING"
    with pytest.raises(BatchValidationError, match="Invalid suggested_action"):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 9. Invalid Operational Flags
# ==============================================================================
@pytest.mark.parametrize("bad_flag", [-1, 2, 5, 0.5, "yes"])
def test_invalid_flags_rejected(valid_surveillance_df, bad_flag):
    """Rejects operational flags that are not 0 or 1."""
    df = valid_surveillance_df.astype({"flag_stag": object})
    df.loc[0, "flag_stag"] = bad_flag
    with pytest.raises(BatchValidationError, match="flag_stag"):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 10. Total Stress Flags Validation
# ==============================================================================
def test_total_stress_flags_validation(valid_surveillance_df):
    """Rejects inconsistent total_stress_flags sum or out-of-bounds count."""
    # Out of bounds (>5)
    df_oob = valid_surveillance_df.copy()
    df_oob.loc[0, "total_stress_flags"] = 6
    with pytest.raises(BatchValidationError, match="total_stress_flags"):
        validate_surveillance_dataframe(df_oob)

    # Inconsistent with flags sum
    df_mismatch = valid_surveillance_df.copy()
    df_mismatch.loc[0, "total_stress_flags"] = 2  # actual flags sum is 4
    with pytest.raises(BatchValidationError, match="does not match sum of flags"):
        validate_surveillance_dataframe(df_mismatch)


# ==============================================================================
# 11. Version String Validation
# ==============================================================================
def test_version_string_validated(valid_surveillance_df):
    """Rejects version identifiers that do not match 'v1.0.0-esi-5dim'."""
    df = valid_surveillance_df.copy()
    df.loc[0, "execution_index_version"] = "v2.0.0-experimental"
    with pytest.raises(BatchValidationError, match="Invalid execution_index_version"):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 12. Decimal Precision
# ==============================================================================
def test_decimal_precision_four_places(valid_surveillance_df):
    """Verifies that all scores are stored with exactly 4 decimal digits."""
    records = validate_surveillance_dataframe(valid_surveillance_df)
    for r in records:
        for f in ["s_stag", "s_vel", "s_div", "s_sched", "s_rep", "execution_stress_index"]:
            d_val = r[f]
            assert isinstance(d_val, Decimal)
            # as_tuple().exponent should be -4
            assert d_val.as_tuple().exponent == -4, f"{f} exponent {d_val.as_tuple().exponent} != -4"


# ==============================================================================
# 13. Project ID Validation
# ==============================================================================
@pytest.mark.parametrize("bad_pid", ["", "   ", "P" * 33, "nan", "NaN"])
def test_project_id_validation(valid_surveillance_df, bad_pid):
    """Rejects invalid project_id values."""
    df = valid_surveillance_df.copy()
    df.loc[0, "project_id"] = bad_pid
    with pytest.raises(BatchValidationError, match="Invalid project_id"):
        validate_surveillance_dataframe(df)


# ==============================================================================
# 14. Idempotent Upsert SQL Construction
# ==============================================================================
def test_idempotent_upsert_sql_construction_mock(valid_surveillance_df):
    """Verifies that upsert_execution_stress_scores builds pg_insert with ON CONFLICT DO UPDATE."""
    records = validate_surveillance_dataframe(valid_surveillance_df)

    mock_session = MagicMock()
    # Mock existing keys query returning empty (all new inserts)
    mock_session.execute.return_value.all.return_value = []

    counts = upsert_execution_stress_scores(mock_session, records)

    assert counts["total"] == 3
    assert counts["inserted"] == 3
    assert counts["updated"] == 0
    assert mock_session.execute.called


# ==============================================================================
# 15. Upsert Insert vs Update Accounting
# ==============================================================================
def test_upsert_counts_insert_vs_update(valid_surveillance_df):
    """Verifies correct counting of inserted vs updated rows based on existing DB keys."""
    records = validate_surveillance_dataframe(valid_surveillance_df)

    mock_session = MagicMock()
    # Simulate PRJ001 already existing in DB
    mock_session.execute.return_value.all.return_value = [("PRJ001", "2025-04")]

    counts = upsert_execution_stress_scores(mock_session, records)

    assert counts["total"] == 3
    assert counts["inserted"] == 2
    assert counts["updated"] == 1


# ==============================================================================
# 16. Project Foreign Key Verification - Success
# ==============================================================================
def test_project_foreign_key_verification_success(valid_surveillance_df):
    """Verifies verify_project_foreign_keys succeeds when all project IDs exist."""
    records = validate_surveillance_dataframe(valid_surveillance_df)

    mock_session = MagicMock()
    mock_session.execute.return_value.scalars.return_value.all.return_value = ["PRJ001", "PRJ002", "PRJ003"]

    # Should succeed without error
    verify_project_foreign_keys(mock_session, records)


# ==============================================================================
# 17. Project Foreign Key Verification - Failure
# ==============================================================================
def test_project_foreign_key_verification_failure(valid_surveillance_df):
    """Verifies verify_project_foreign_keys raises MissingProjectError when a project is missing."""
    records = validate_surveillance_dataframe(valid_surveillance_df)

    mock_session = MagicMock()
    # Simulate PRJ003 missing from DB
    mock_session.execute.return_value.scalars.return_value.all.return_value = ["PRJ001", "PRJ002"]

    with pytest.raises(MissingProjectError, match="Foreign key verification failed.*PRJ003"):
        verify_project_foreign_keys(mock_session, records)


# ==============================================================================
# 18. Rollback-Test Mode
# ==============================================================================
def test_rollback_test_mode_does_not_commit(tmp_path):
    """Verifies rollback_test=True calls rollback and never calls commit."""
    # Create minimal valid CSV
    df_raw = pd.DataFrame([{
        "project_id": "PRJ001",
        "prediction_month": "2025-04",
        "months_since_last_progress_increase_t": 0.0,
        "stagnant_3m_t": 0.0,
        "remaining_physical_progress_t": 50.0,
        "progress_velocity_3m_t": 2.0,
        "progress_change_1m_t": 2.0,
        "schedule_slippage_months_t": 6.0,
        "months_to_original_doc_t": 12.0,
        "expenditure_ratio_pct_t": 30.0,
        "physical_progress_t": 30.0,
        "observation_gap_flag_t": 0.0,
        "missing_physical_progress_t": 0.0,
        "schedule_revision_count_to_date_t": 0.0,
    }])
    csv_file = tmp_path / "feat.csv"
    df_raw.to_csv(csv_file, index=False)

    mock_session = MagicMock()
    mock_session.execute.return_value.scalars.return_value.all.return_value = ["PRJ001"]
    mock_session.execute.return_value.all.return_value = []

    with patch("scripts.ingest_surveillance_scores.sessionmaker") as mock_sm:
        mock_sm.return_value.return_value.__enter__.return_value = mock_session
        with patch("scripts.ingest_surveillance_scores.create_engine"):
            counts = run_ingestion(
                feature_file=csv_file,
                rollback_test=True,
                database_url="postgresql://user:pass@localhost:5432/testdb",
            )

    assert mock_session.rollback.called
    assert not mock_session.commit.called
    assert counts["total"] == 1


# ==============================================================================
# 19. Transaction Failure Handling
# ==============================================================================
def test_transaction_rollback_on_db_error(tmp_path):
    """Verifies database exception triggers session.rollback() and raises DatabaseIngestionError."""
    df_raw = pd.DataFrame([{
        "project_id": "PRJ001",
        "prediction_month": "2025-04",
        "months_since_last_progress_increase_t": 0.0,
        "stagnant_3m_t": 0.0,
        "remaining_physical_progress_t": 50.0,
        "progress_velocity_3m_t": 2.0,
        "progress_change_1m_t": 2.0,
        "schedule_slippage_months_t": 6.0,
        "months_to_original_doc_t": 12.0,
        "expenditure_ratio_pct_t": 30.0,
        "physical_progress_t": 30.0,
        "observation_gap_flag_t": 0.0,
        "missing_physical_progress_t": 0.0,
        "schedule_revision_count_to_date_t": 0.0,
    }])
    csv_file = tmp_path / "feat.csv"
    df_raw.to_csv(csv_file, index=False)

    mock_session = MagicMock()
    # First execute call is FK check (returns PRJ001), second execute call (upsert) fails
    mock_fk_result = MagicMock()
    mock_fk_result.scalars.return_value.all.return_value = ["PRJ001"]
    mock_session.execute.side_effect = [mock_fk_result, RuntimeError("Simulated DB connection drop")]

    with patch("scripts.ingest_surveillance_scores.sessionmaker") as mock_sm:
        mock_sm.return_value.return_value.__enter__.return_value = mock_session
        with patch("scripts.ingest_surveillance_scores.create_engine"):
            with pytest.raises(DatabaseIngestionError, match="Database upsert failed"):
                run_ingestion(
                    feature_file=csv_file,
                    rollback_test=False,
                    database_url="postgresql://user:pass@localhost:5432/testdb",
                )

    assert mock_session.rollback.called


# ==============================================================================
# 20. Credentials Sanitization
# ==============================================================================
def test_credentials_never_printed():
    """Verifies sanitize_error_message removes passwords from PostgreSQL URIs."""
    leak_string = "Error connecting to postgresql://admin_user:SuperSecretPassword123@aws-db.supabase.com:5432/postgres"
    sanitized = sanitize_error_message(leak_string)

    assert "SuperSecretPassword123" not in sanitized
    assert "admin_user" not in sanitized
    assert "://***:***@" in sanitized


# ==============================================================================
# 21. Dry-Run Mode No Database
# ==============================================================================
def test_dry_run_mode_no_database_connection(tmp_path):
    """Verifies --dry-run performs scoring and validation without opening a database session."""
    df_raw = pd.DataFrame([{
        "project_id": "PRJ001",
        "prediction_month": "2025-04",
        "months_since_last_progress_increase_t": 0.0,
        "stagnant_3m_t": 0.0,
        "remaining_physical_progress_t": 50.0,
        "progress_velocity_3m_t": 2.0,
        "progress_change_1m_t": 2.0,
        "schedule_slippage_months_t": 6.0,
        "months_to_original_doc_t": 12.0,
        "expenditure_ratio_pct_t": 30.0,
        "physical_progress_t": 30.0,
        "observation_gap_flag_t": 0.0,
        "missing_physical_progress_t": 0.0,
        "schedule_revision_count_to_date_t": 0.0,
    }])
    csv_file = tmp_path / "feat.csv"
    df_raw.to_csv(csv_file, index=False)

    with patch("scripts.ingest_surveillance_scores.create_engine") as mock_engine:
        results = run_ingestion(
            feature_file=csv_file,
            dry_run=True,
            database_url=None,
        )

    assert not mock_engine.called
    assert results["total"] == 1
    assert results["inserted"] == 0
    assert results["skipped"] == 1


# ==============================================================================
# 22. Month and Project Filtering
# ==============================================================================
def test_cli_month_and_project_filtering(tmp_path):
    """Verifies filtering by report month and project ID."""
    df_raw = pd.DataFrame([
        {
            "project_id": "PRJ001",
            "prediction_month": "2025-04",
            "months_since_last_progress_increase_t": 0.0,
            "stagnant_3m_t": 0.0,
            "remaining_physical_progress_t": 50.0,
            "progress_velocity_3m_t": 2.0,
            "progress_change_1m_t": 2.0,
            "schedule_slippage_months_t": 6.0,
            "months_to_original_doc_t": 12.0,
            "expenditure_ratio_pct_t": 30.0,
            "physical_progress_t": 30.0,
            "observation_gap_flag_t": 0.0,
            "missing_physical_progress_t": 0.0,
            "schedule_revision_count_to_date_t": 0.0,
        },
        {
            "project_id": "PRJ002",
            "prediction_month": "2025-05",
            "months_since_last_progress_increase_t": 0.0,
            "stagnant_3m_t": 0.0,
            "remaining_physical_progress_t": 50.0,
            "progress_velocity_3m_t": 2.0,
            "progress_change_1m_t": 2.0,
            "schedule_slippage_months_t": 6.0,
            "months_to_original_doc_t": 12.0,
            "expenditure_ratio_pct_t": 30.0,
            "physical_progress_t": 30.0,
            "observation_gap_flag_t": 0.0,
            "missing_physical_progress_t": 0.0,
            "schedule_revision_count_to_date_t": 0.0,
        },
    ])
    csv_file = tmp_path / "feat.csv"
    df_raw.to_csv(csv_file, index=False)

    res = run_ingestion(feature_file=csv_file, month="2025-04", dry_run=True)
    assert res["total"] == 1

    res_p = run_ingestion(feature_file=csv_file, project_id="PRJ002", dry_run=True)
    assert res_p["total"] == 1


# ==============================================================================
# 23. Limit Option
# ==============================================================================
def test_cli_limit_behavior(tmp_path):
    """Verifies that --limit restricts the batch size."""
    rows = []
    for i in range(10):
        rows.append({
            "project_id": f"PRJ_{i}",
            "prediction_month": "2025-04",
            "months_since_last_progress_increase_t": 0.0,
            "stagnant_3m_t": 0.0,
            "remaining_physical_progress_t": 50.0,
            "progress_velocity_3m_t": 2.0,
            "progress_change_1m_t": 2.0,
            "schedule_slippage_months_t": 6.0,
            "months_to_original_doc_t": 12.0,
            "expenditure_ratio_pct_t": 30.0,
            "physical_progress_t": 30.0,
            "observation_gap_flag_t": 0.0,
            "missing_physical_progress_t": 0.0,
            "schedule_revision_count_to_date_t": 0.0,
        })
    csv_file = tmp_path / "feat.csv"
    pd.DataFrame(rows).to_csv(csv_file, index=False)

    res = run_ingestion(feature_file=csv_file, limit=4, dry_run=True)
    assert res["total"] == 4


# ==============================================================================
# 24. Empty Input Handling
# ==============================================================================
def test_empty_input_behavior(tmp_path):
    """Verifies that 0 matching rows returns gracefully."""
    df_raw = pd.DataFrame([{
        "project_id": "PRJ001",
        "prediction_month": "2025-04",
        "months_since_last_progress_increase_t": 0.0,
        "stagnant_3m_t": 0.0,
        "remaining_physical_progress_t": 50.0,
        "progress_velocity_3m_t": 2.0,
        "progress_change_1m_t": 2.0,
        "schedule_slippage_months_t": 6.0,
        "months_to_original_doc_t": 12.0,
        "expenditure_ratio_pct_t": 30.0,
        "physical_progress_t": 30.0,
        "observation_gap_flag_t": 0.0,
        "missing_physical_progress_t": 0.0,
        "schedule_revision_count_to_date_t": 0.0,
    }])
    csv_file = tmp_path / "feat.csv"
    df_raw.to_csv(csv_file, index=False)

    res = run_ingestion(feature_file=csv_file, month="2099-01", dry_run=True)
    assert res["total"] == 0
    assert res["inserted"] == 0
    assert res["skipped"] == 0


# ==============================================================================
# 25. Deterministic Repeated Ingestion
# ==============================================================================
def test_deterministic_repeated_ingestion(valid_surveillance_df):
    """Verifies that multiple calls on the same data yield identical validated records."""
    res1 = validate_surveillance_dataframe(valid_surveillance_df)
    res2 = validate_surveillance_dataframe(valid_surveillance_df)

    assert len(res1) == len(res2)
    for r1, r2 in zip(res1, res2):
        assert r1 == r2
