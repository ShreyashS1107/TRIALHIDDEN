"""
Unit and Integration Tests for ML Batch Scoring Engine (Phase 5B-1).

Tests:
1. Lazy loading and model artifact existence.
2. Validation of required 75-feature contract.
3. Proper failure upon missing features (MissingFeatureError).
4. Proper failure upon invalid inputs (empty DataFrame, wrong type).
5. Proper failure upon missing artifact path (ModelArtifactNotFoundError).
6. Point-in-time safety: target columns in input are never fed to model matrix.
7. Shuffled feature columns still evaluate properly (order robustness).
8. Prediction outputs contain all required fields with expected types.
9. All probabilities and risk scores are bounded strictly in [0.0, 1.0].
10. Candidate B evidence-weighted synthesis formula is strictly verified.
11. Contribution calculations match synthesis weights exactly.
12. Risk band assignment matches defined intervals (<0.30, 0.30-0.60, 0.60-0.80, >=0.80).
13. Dominant component matches argmax across contributions.
14. Model version matches 'v1.0.0-rf02-calibrated'.
15. Metadata columns (project_id, report_month) are preserved.
16. Deterministic scoring across multiple repeated runs.
17. Numerical equivalence against reference integrated_risk_scores.csv.
"""

import sys
from pathlib import Path
ai_ml_root = Path(__file__).resolve().parent.parent.parent
if str(ai_ml_root) not in sys.path:
    sys.path.insert(0, str(ai_ml_root))
import numpy as np
import pandas as pd
import pytest

from ml.inference.batch_scorer import BatchScorer
from ml.inference.contracts import (
    ALL_MODEL_FEATURES,
    BAND_HIGH,
    BAND_LOW,
    BAND_MODERATE,
    BAND_VERY_HIGH,
    DOMINANT_COST_OVERRUN,
    DOMINANT_SCHEDULE_DELAY,
    DOMINANT_SCHEDULE_REVISION,
    KNOWN_TARGET_COLUMNS,
    MODEL_VERSION,
    REQUIRED_CATEGORICAL_FEATURES,
    REQUIRED_NUMERICAL_FEATURES,
    WEIGHT_COST_OVERRUN,
    WEIGHT_SCHEDULE_DELAY,
    WEIGHT_SCHEDULE_REVISION,
    InvalidInputError,
    MissingFeatureError,
    ModelArtifactNotFoundError,
)


@pytest.fixture(scope="session")
def base_dir():
    """Returns the base ai-ml directory."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="session")
def feature_sample_df(base_dir):
    """Loads a 25-row sample from feature_dataset_v1.csv for test execution."""
    data_path = base_dir / "features" / "feature_dataset_v1.csv"
    assert data_path.exists(), f"Feature dataset not found at {data_path}"
    df = pd.read_csv(data_path, nrows=25, low_memory=False)
    return df


@pytest.fixture(scope="session")
def reference_scores_df(base_dir):
    """Loads reference scores from integrated_risk_scores.csv."""
    ref_path = base_dir / "ml" / "risk_engine" / "integrated_risk_scores.csv"
    assert ref_path.exists(), f"Reference scores not found at {ref_path}"
    df = pd.read_csv(ref_path, nrows=25, low_memory=False)
    return df


@pytest.fixture
def scorer():
    """Returns an instance of BatchScorer."""
    return BatchScorer()


# ------------------------------------------------------------------------------
# Test 1: Lazy Loading and Artifact Integrity
# ------------------------------------------------------------------------------
def test_lazy_loading(scorer):
    """Verifies that model artifacts are not loaded at instantiation time."""
    assert not scorer.is_loaded
    scorer.load_models()
    assert scorer.is_loaded


def test_missing_artifact_error(tmp_path):
    """Verifies that ModelArtifactNotFoundError is raised if an artifact path is missing."""
    fake_path = tmp_path / "non_existent_model.pkl"
    scorer = BatchScorer(primary_model_path=fake_path)
    with pytest.raises(ModelArtifactNotFoundError) as exc_info:
        scorer.load_models()
    assert "artifact not found" in str(exc_info.value).lower()


# ------------------------------------------------------------------------------
# Test 2: Input Contract Validation
# ------------------------------------------------------------------------------
def test_missing_feature_error(scorer, feature_sample_df):
    """Verifies that MissingFeatureError is raised when any required feature is absent."""
    df_missing = feature_sample_df.drop(columns=["original_cost_crore"])
    with pytest.raises(MissingFeatureError) as exc_info:
        scorer.score_batch(df_missing)
    assert "original_cost_crore" in str(exc_info.value)


def test_multiple_missing_features_error(scorer, feature_sample_df):
    """Verifies that MissingFeatureError reports all missing features."""
    drop_cols = ["original_cost_crore", "project_size_category", "physical_progress_t"]
    df_missing = feature_sample_df.drop(columns=drop_cols)
    with pytest.raises(MissingFeatureError) as exc_info:
        scorer.score_batch(df_missing)
    for col in drop_cols:
        assert col in str(exc_info.value)


def test_invalid_input_type(scorer):
    """Verifies that InvalidInputError is raised if input is not a DataFrame."""
    with pytest.raises(InvalidInputError):
        scorer.score_batch({"a": [1, 2, 3]})


def test_empty_dataframe(scorer):
    """Verifies that InvalidInputError is raised if input DataFrame is empty."""
    with pytest.raises(InvalidInputError):
        scorer.score_batch(pd.DataFrame())


# ------------------------------------------------------------------------------
# Test 3: Point-in-Time Safety & Target Isolation
# ------------------------------------------------------------------------------
def test_target_columns_isolation(scorer, feature_sample_df):
    """
    Verifies that presence of target columns in the input DataFrame does NOT
    leak into or affect feature processing.
    """
    # Verify input has target columns
    assert "schedule_delay_3m" in feature_sample_df.columns
    assert "cost_overrun_state_3m" in feature_sample_df.columns

    # Score with target columns present
    preds1 = scorer.score_batch(feature_sample_df)

    # Score with target columns completely removed
    cols_to_drop = [c for c in KNOWN_TARGET_COLUMNS if c in feature_sample_df.columns]
    df_clean = feature_sample_df.drop(columns=cols_to_drop)
    preds2 = scorer.score_batch(df_clean)

    # Results must be 100% bitwise identical
    pd.testing.assert_frame_equal(preds1, preds2)


# ------------------------------------------------------------------------------
# Test 4: Column Order Robustness
# ------------------------------------------------------------------------------
def test_feature_column_order_robustness(scorer, feature_sample_df):
    """Verifies that reordering columns in input DataFrame yields identical predictions."""
    cols_shuffled = list(feature_sample_df.columns)
    np.random.seed(42)
    np.random.shuffle(cols_shuffled)
    df_shuffled = feature_sample_df[cols_shuffled]

    preds_orig = scorer.score_batch(feature_sample_df)
    preds_shuffled = scorer.score_batch(df_shuffled)

    pd.testing.assert_frame_equal(preds_orig, preds_shuffled)


# ------------------------------------------------------------------------------
# Test 5: Output Schema and Value Bounds
# ------------------------------------------------------------------------------
def test_output_contract_fields_and_bounds(scorer, feature_sample_df):
    """Verifies output columns, data types, and value boundaries."""
    preds = scorer.score_batch(feature_sample_df)

    expected_cols = [
        "project_id",
        "report_month",
        "schedule_delay_risk",
        "cost_overrun_risk",
        "schedule_revision_risk",
        "selected_integrated_risk",
        "risk_band",
        "dominant_component",
        "schedule_contribution",
        "cost_contribution",
        "schedule_revision_contribution",
        "model_version",
    ]
    for col in expected_cols:
        assert col in preds.columns, f"Expected output column missing: {col}"

    assert len(preds) == len(feature_sample_df)

    # Check bounds [0.0, 1.0]
    for col in [
        "schedule_delay_risk",
        "cost_overrun_risk",
        "schedule_revision_risk",
        "selected_integrated_risk",
        "schedule_contribution",
        "cost_contribution",
        "schedule_revision_contribution",
    ]:
        assert (preds[col] >= 0.0).all(), f"Values below 0 in {col}"
        assert (preds[col] <= 1.0).all(), f"Values above 1 in {col}"

    # Check valid risk bands
    valid_bands = {BAND_LOW, BAND_MODERATE, BAND_HIGH, BAND_VERY_HIGH}
    assert set(preds["risk_band"].unique()).issubset(valid_bands)

    # Check valid dominant components
    valid_dom = {DOMINANT_SCHEDULE_DELAY, DOMINANT_COST_OVERRUN, DOMINANT_SCHEDULE_REVISION}
    assert set(preds["dominant_component"].unique()).issubset(valid_dom)

    # Check model version
    assert (preds["model_version"] == MODEL_VERSION).all()


# ------------------------------------------------------------------------------
# Test 6: Synthesis and Contribution Mathematics
# ------------------------------------------------------------------------------
def test_synthesis_and_contributions(scorer, feature_sample_df):
    """Verifies exact synthesis and contribution mathematics."""
    preds = scorer.score_batch(feature_sample_df)

    expected_sched_contrib = np.round(WEIGHT_SCHEDULE_DELAY * preds["schedule_delay_risk"], 4)
    expected_cost_contrib = np.round(WEIGHT_COST_OVERRUN * preds["cost_overrun_risk"], 4)
    expected_srev_contrib = np.round(WEIGHT_SCHEDULE_REVISION * preds["schedule_revision_risk"], 4)

    np.testing.assert_allclose(preds["schedule_contribution"], expected_sched_contrib)
    np.testing.assert_allclose(preds["cost_contribution"], expected_cost_contrib)
    np.testing.assert_allclose(preds["schedule_revision_contribution"], expected_srev_contrib)

    # Candidate B computes integrated risk directly from component probabilities
    expected_integrated = np.round(
        WEIGHT_SCHEDULE_DELAY * preds["schedule_delay_risk"]
        + WEIGHT_COST_OVERRUN * preds["cost_overrun_risk"]
        + WEIGHT_SCHEDULE_REVISION * preds["schedule_revision_risk"],
        4,
    )
    np.testing.assert_allclose(preds["selected_integrated_risk"], expected_integrated)

    # Sum of rounded contributions matches integrated risk within floating rounding tolerance
    contrib_sum = (
        preds["schedule_contribution"]
        + preds["cost_contribution"]
        + preds["schedule_revision_contribution"]
    )
    np.testing.assert_allclose(preds["selected_integrated_risk"], contrib_sum, atol=2e-4)



# ------------------------------------------------------------------------------
# Test 7: Risk Band Boundaries
# ------------------------------------------------------------------------------
def test_risk_band_mapping(scorer, feature_sample_df):
    """Verifies risk band assignment logic against defined thresholds."""
    preds = scorer.score_batch(feature_sample_df)
    for _, row in preds.iterrows():
        score = row["selected_integrated_risk"]
        band = row["risk_band"]
        if score < 0.30:
            assert band == BAND_LOW
        elif score < 0.60:
            assert band == BAND_MODERATE
        elif score < 0.80:
            assert band == BAND_HIGH
        else:
            assert band == BAND_VERY_HIGH


# ------------------------------------------------------------------------------
# Test 8: Dominant Component Assignment
# ------------------------------------------------------------------------------
def test_dominant_component_logic(scorer, feature_sample_df):
    """Verifies dominant component assignment logic matches max contribution."""
    preds = scorer.score_batch(feature_sample_df)
    for _, row in preds.iterrows():
        contribs = {
            DOMINANT_SCHEDULE_DELAY: row["schedule_contribution"],
            DOMINANT_COST_OVERRUN: row["cost_contribution"],
            DOMINANT_SCHEDULE_REVISION: row["schedule_revision_contribution"],
        }
        expected_dom = max(contribs, key=contribs.get)
        assert row["dominant_component"] == expected_dom


# ------------------------------------------------------------------------------
# Test 9: Metadata Preservation
# ------------------------------------------------------------------------------
def test_metadata_preservation(scorer, feature_sample_df):
    """Verifies that project_id and report_month are correctly preserved in the output."""
    preds = scorer.score_batch(feature_sample_df)
    np.testing.assert_array_equal(preds["project_id"].values, feature_sample_df["project_id"].values)
    np.testing.assert_array_equal(preds["report_month"].values, feature_sample_df["prediction_month"].values)


# ------------------------------------------------------------------------------
# Test 10: Determinism
# ------------------------------------------------------------------------------
def test_deterministic_scoring(scorer, feature_sample_df):
    """Verifies that repeated scoring of identical input produces bitwise identical results."""
    run1 = scorer.score_batch(feature_sample_df)
    run2 = scorer.score_batch(feature_sample_df)
    pd.testing.assert_frame_equal(run1, run2)


# ------------------------------------------------------------------------------
# Test 11: Exact Equivalence to Reference Artifacts
# ------------------------------------------------------------------------------
def test_reference_numerical_equivalence(scorer, feature_sample_df, reference_scores_df):
    """
    Verifies that the new BatchScorer reproduces exact predictions from
    the reference integrated_risk_scores.csv.
    """
    preds = scorer.score_batch(feature_sample_df)

    # Compare first 25 rows
    np.testing.assert_allclose(
        preds["schedule_delay_risk"].values,
        reference_scores_df["schedule_delay_risk"].values,
        atol=1e-4,
    )
    np.testing.assert_allclose(
        preds["cost_overrun_risk"].values,
        reference_scores_df["cost_overrun_risk"].values,
        atol=1e-4,
    )
    np.testing.assert_allclose(
        preds["schedule_revision_risk"].values,
        reference_scores_df["schedule_revision_risk"].values,
        atol=1e-4,
    )
    np.testing.assert_allclose(
        preds["selected_integrated_risk"].values,
        reference_scores_df["selected_integrated_risk"].values,
        atol=1e-4,
    )
    np.testing.assert_array_equal(
        preds["risk_band"].values,
        reference_scores_df["risk_band"].values,
    )
    np.testing.assert_array_equal(
        preds["dominant_component"].values,
        reference_scores_df["dominant_component"].values,
    )
