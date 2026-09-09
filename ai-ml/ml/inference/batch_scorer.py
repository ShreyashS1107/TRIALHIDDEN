"""
Modular Offline Batch Scoring Engine for SIH26103.

This module provides a deterministic, offline batch scoring engine that loads
the three certified frozen ML model artifacts:
  1. Primary Calibrated Random Forest (schedule_delay_3m)
  2. Secondary Random Forest Balanced (cost_overrun_state_3m)
  3. Secondary Logistic Regression Unweighted (schedule_revision_3m)

POINT-IN-TIME SAFETY ASSUMPTIONS:
The batch scorer assumes its input DataFrame has already been constructed
using the certified point-in-time feature engineering pipeline. Target
columns, future revision dates, or future expenditure indicators are
strictly isolated and NEVER passed into the model matrix.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd

from .contracts import (
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
    OUTPUT_COLUMNS,
    REQUIRED_CATEGORICAL_FEATURES,
    REQUIRED_NUMERICAL_FEATURES,
    WEIGHT_COST_OVERRUN,
    WEIGHT_SCHEDULE_DELAY,
    WEIGHT_SCHEDULE_REVISION,
    InferenceError,
    InvalidInputError,
    MissingFeatureError,
    ModelArtifactNotFoundError,
)


class BatchScorer:
    """
    Offline Batch Scoring Engine for Multi-Target Infrastructure Risk Inference.

    Loads frozen scikit-learn pipeline artifacts lazily and executes deterministic
    prediction, calibration, Candidate B evidence-weighted synthesis, contribution
    decomposition, and risk band assignment.
    """

    def __init__(
        self,
        primary_model_path: Optional[Union[str, Path]] = None,
        cost_model_path: Optional[Union[str, Path]] = None,
        schedule_rev_model_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initializes the BatchScorer with paths to frozen model artifacts.
        Artifacts are NOT loaded at initialization time (lazy loading).
        """
        base_dir = Path(__file__).resolve().parent.parent

        self.primary_model_path = (
            Path(primary_model_path)
            if primary_model_path is not None
            else base_dir / "calibration_final" / "models" / "rf02_calibrated.pkl"
        )
        self.cost_model_path = (
            Path(cost_model_path)
            if cost_model_path is not None
            else base_dir / "secondary_targets" / "selected_models" / "cost_overrun_state_3m" / "model.pkl"
        )
        self.schedule_rev_model_path = (
            Path(schedule_rev_model_path)
            if schedule_rev_model_path is not None
            else base_dir / "secondary_targets" / "selected_models" / "schedule_revision_3m" / "model.pkl"
        )

        self._primary_pipe: Optional[Dict] = None
        self._cost_pipe: Optional[Dict] = None
        self._srev_pipe: Optional[Dict] = None

    @property
    def is_loaded(self) -> bool:
        """Returns True if all three model artifacts are loaded in memory."""
        return (
            self._primary_pipe is not None
            and self._cost_pipe is not None
            and self._srev_pipe is not None
        )

    def load_models(self) -> None:
        """
        Safely loads all three frozen model artifacts into memory and verifies
        their feature signatures against the canonical 75-feature contract.

        Raises:
            ModelArtifactNotFoundError: If any artifact file does not exist.
            InferenceError: If artifact loading or signature verification fails.
        """
        artifacts = [
            (self.primary_model_path, "Primary calibrated model (schedule_delay_3m)"),
            (self.cost_model_path, "Secondary model (cost_overrun_state_3m)"),
            (self.schedule_rev_model_path, "Secondary model (schedule_revision_3m)"),
        ]

        for path, name in artifacts:
            if not path.exists():
                raise ModelArtifactNotFoundError(
                    f"{name} artifact not found at expected path: {path}"
                )

        try:
            self._primary_pipe = joblib.load(self.primary_model_path)
            self._cost_pipe = joblib.load(self.cost_model_path)
            self._srev_pipe = joblib.load(self.schedule_rev_model_path)
        except Exception as exc:
            raise InferenceError(f"Failed to deserialize model artifacts: {exc}") from exc

        # Verify contracts in loaded artifacts
        loaded_pipes = [
            (self._primary_pipe, "Primary calibrated"),
            (self._cost_pipe, "Cost overrun"),
            (self._srev_pipe, "Schedule revision"),
        ]
        for pipe, pipe_name in loaded_pipes:
            if not isinstance(pipe, dict):
                raise InferenceError(f"Artifact {pipe_name} is corrupted: expected dictionary.")
            if pipe.get("feature_names_numeric") != REQUIRED_NUMERICAL_FEATURES:
                raise InferenceError(
                    f"Artifact {pipe_name} numerical feature contract mismatch."
                )
            if pipe.get("feature_names_categorical") != REQUIRED_CATEGORICAL_FEATURES:
                raise InferenceError(
                    f"Artifact {pipe_name} categorical feature contract mismatch."
                )

    def validate_input(self, df: pd.DataFrame) -> None:
        """
        Validates that input DataFrame satisfies the 75-feature inference contract.

        Raises:
            InvalidInputError: If df is not a non-empty pandas DataFrame.
            MissingFeatureError: If any of the 75 required features are absent.
        """
        if not isinstance(df, pd.DataFrame):
            raise InvalidInputError(
                f"Expected pandas DataFrame as input, got {type(df).__name__}."
            )
        if len(df) == 0:
            raise InvalidInputError("Input DataFrame contains 0 rows.")

        missing_features = [col for col in ALL_MODEL_FEATURES if col not in df.columns]
        if missing_features:
            raise MissingFeatureError(
                f"Missing required model features ({len(missing_features)}): {sorted(missing_features)}"
            )

    def score_batch(
        self,
        df: pd.DataFrame,
        preserve_metadata: bool = True,
    ) -> pd.DataFrame:
        """
        Executes deterministic batch inference across an input DataFrame.

        Steps:
        1. Validates input schema against the 75-feature contract.
        2. Lazily loads model artifacts if not already loaded.
        3. Extracts the 75-feature matrix X in exact canonical order.
        4. Predicts calibrated schedule delay risk via RF02 + isotonic/sigmoid calibrator.
        5. Predicts cost overrun state risk via secondary Random Forest.
        6. Predicts schedule revision risk via secondary Logistic Regression.
        7. Computes Candidate B Evidence-Weighted synthesis:
           0.50 * schedule_delay + 0.35 * cost_overrun + 0.15 * schedule_revision.
        8. Computes component contributions and normalized dominant component.
        9. Maps risk bands: LOW (<0.30), MODERATE (0.30-0.60), HIGH (0.60-0.80), VERY_HIGH (>=0.80).
        10. Attaches model version 'v1.0.0-rf02-calibrated' and preserves metadata.

        Returns:
            pd.DataFrame: Deterministic prediction dataframe.
        """
        self.validate_input(df)

        if not self.is_loaded:
            self.load_models()

        # Strict isolation: extract ONLY the 75 canonical features in exact order.
        # This guarantees point-in-time safety by preventing target or future leakage columns
        # from entering the preprocessors or model matrices.
        X_df = df[ALL_MODEL_FEATURES]

        # ----------------------------------------------------------------------
        # 1. Primary Schedule Delay (Calibrated RF_02)
        # ----------------------------------------------------------------------
        X_sched = self._primary_pipe["preprocessor"].transform(X_df)
        p_sched_raw = self._primary_pipe["classifier"].predict_proba(X_sched)[:, 1]
        eps = 1e-6
        p_clipped = np.clip(p_sched_raw, eps, 1.0 - eps)
        sched_logits = np.log(p_clipped / (1.0 - p_clipped)).reshape(-1, 1)
        schedule_delay_risk = np.round(
            self._primary_pipe["calibrator"].predict_proba(sched_logits)[:, 1], 4
        )

        # ----------------------------------------------------------------------
        # 2. Secondary Cost Overrun State (RF Balanced)
        # ----------------------------------------------------------------------
        X_cost = self._cost_pipe["preprocessor"].transform(X_df)
        cost_overrun_risk = np.round(
            self._cost_pipe["classifier"].predict_proba(X_cost)[:, 1], 4
        )

        # ----------------------------------------------------------------------
        # 3. Secondary Schedule Revision (Logistic Regression Unweighted)
        # ----------------------------------------------------------------------
        X_srev = self._srev_pipe["preprocessor"].transform(X_df)
        schedule_revision_risk = np.round(
            self._srev_pipe["classifier"].predict_proba(X_srev)[:, 1], 4
        )

        # ----------------------------------------------------------------------
        # 4. Candidate B Evidence-Weighted Synthesis (0.50 / 0.35 / 0.15)
        # ----------------------------------------------------------------------
        selected_integrated_risk = np.round(
            WEIGHT_SCHEDULE_DELAY * schedule_delay_risk
            + WEIGHT_COST_OVERRUN * cost_overrun_risk
            + WEIGHT_SCHEDULE_REVISION * schedule_revision_risk,
            4,
        )

        # ----------------------------------------------------------------------
        # 5. Component Contributions
        # ----------------------------------------------------------------------
        schedule_contribution = np.round(WEIGHT_SCHEDULE_DELAY * schedule_delay_risk, 4)
        cost_contribution = np.round(WEIGHT_COST_OVERRUN * cost_overrun_risk, 4)
        schedule_revision_contribution = np.round(
            WEIGHT_SCHEDULE_REVISION * schedule_revision_risk, 4
        )

        # ----------------------------------------------------------------------
        # 6. Risk Band Assignment
        # Boundaries: < 0.30 (LOW), 0.30 - 0.60 (MODERATE), 0.60 - 0.80 (HIGH), >= 0.80 (VERY_HIGH)
        # ----------------------------------------------------------------------
        risk_bands = np.select(
            [
                selected_integrated_risk < 0.30,
                selected_integrated_risk < 0.60,
                selected_integrated_risk < 0.80,
            ],
            [BAND_LOW, BAND_MODERATE, BAND_HIGH],
            default=BAND_VERY_HIGH,
        )

        # ----------------------------------------------------------------------
        # 7. Dominant Component Assignment
        # Argmax across contributions with deterministic tie-breaking order:
        # Schedule Delay -> Cost Overrun -> Schedule Revision
        # ----------------------------------------------------------------------
        contrib_matrix = np.column_stack(
            [schedule_contribution, cost_contribution, schedule_revision_contribution]
        )
        dominant_indices = np.argmax(contrib_matrix, axis=1)
        component_names = np.array(
            [DOMINANT_SCHEDULE_DELAY, DOMINANT_COST_OVERRUN, DOMINANT_SCHEDULE_REVISION]
        )
        dominant_component = component_names[dominant_indices]

        # ----------------------------------------------------------------------
        # 8. Output Assembly
        # ----------------------------------------------------------------------
        output_dict = {}

        if preserve_metadata:
            if "project_id" in df.columns:
                output_dict["project_id"] = df["project_id"].values
            if "report_month" in df.columns:
                output_dict["report_month"] = df["report_month"].values
            elif "prediction_month" in df.columns:
                output_dict["report_month"] = df["prediction_month"].values

        output_dict["schedule_delay_risk"] = schedule_delay_risk
        output_dict["cost_overrun_risk"] = cost_overrun_risk
        output_dict["schedule_revision_risk"] = schedule_revision_risk
        output_dict["selected_integrated_risk"] = selected_integrated_risk
        output_dict["risk_band"] = risk_bands
        output_dict["dominant_component"] = dominant_component
        output_dict["schedule_contribution"] = schedule_contribution
        output_dict["cost_contribution"] = cost_contribution
        output_dict["schedule_revision_contribution"] = schedule_revision_contribution
        output_dict["model_version"] = MODEL_VERSION

        return pd.DataFrame(output_dict, index=df.index)
