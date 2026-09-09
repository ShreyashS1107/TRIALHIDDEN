"""
Modular Execution Surveillance Engine for SIH26103.

Implements Pillar 2 (Operational Surveillance & Early Warning) directly from
point-in-time project metrics (<= t):
- 5 Core Stress Dimensions: S_stag, S_vel, S_sched, S_div, S_rep
- Operational Stress Flags and Total Stress Flag Count
- Domain-Calibrated Operational Execution-Stress Index (ESI)
- 4-Tier Early Warning Alert Hierarchy (NOMINAL, WATCH, ATTENTION, HIGH_PRIORITY)
- Dominant Stressor Attribution (Deterministic Argmax with tie-breaking)
- Prescriptive Monitoring Action Logic Matrix
"""

from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd

from .contracts import (
    ACTION_CRITICAL_PATH_RECALIBRATION,
    ACTION_DATA_COMPLIANCE_DIRECTIVE,
    ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT,
    ACTION_INTER_MINISTERIAL_ESCALATION,
    ACTION_RESOURCE_MOBILIZATION_DIRECTIVE,
    ACTION_SITE_OBSTACLE_AUDIT,
    EXECUTION_INDEX_VERSION,
    KNOWN_TARGET_COLUMNS,
    ORDERED_STRESSOR_TIE_BREAK,
    OUTPUT_SURVEILLANCE_COLUMNS,
    REQUIRED_SURVEILLANCE_FEATURES,
    STRESSOR_EXPENDITURE_DIVERGENCE,
    STRESSOR_PROGRESS_STAGNATION,
    STRESSOR_REPORTING_FRICTION,
    STRESSOR_SCHEDULE_SLIPPAGE,
    STRESSOR_VELOCITY_COLLAPSE,
    TIER_ATTENTION,
    TIER_HIGH_PRIORITY,
    TIER_NOMINAL,
    TIER_WATCH,
    WEIGHT_DIVERGENCE,
    WEIGHT_REPORTING,
    WEIGHT_SCHEDULE,
    WEIGHT_STAGNATION,
    WEIGHT_VELOCITY,
    InvalidInputError,
    MissingFeatureError,
    SurveillanceError,
)


class ExecutionSurveillanceEngine:
    """
    Modular, deterministic Operational Execution Surveillance Engine (Pillar 2).

    Consumes point-in-time project time-series features (<= t) and produces
    continuous stress scores, operational flags, alert tiers, dominant stressors,
    and prescriptive action directives.
    """

    def __init__(self):
        """Initializes the ExecutionSurveillanceEngine."""
        self.version = EXECUTION_INDEX_VERSION

    def validate_input(self, df: pd.DataFrame) -> None:
        """
        Validates that the input satisfies the 12-feature surveillance contract.

        Raises:
            InvalidInputError: If df is not a non-empty pandas DataFrame.
            MissingFeatureError: If any of the 12 required features are absent.
        """
        if not isinstance(df, pd.DataFrame):
            raise InvalidInputError(
                f"Expected pandas DataFrame as input, got {type(df).__name__}."
            )
        if len(df) == 0:
            raise InvalidInputError("Input DataFrame contains 0 rows.")

        missing = [col for col in REQUIRED_SURVEILLANCE_FEATURES if col not in df.columns]
        if missing:
            raise MissingFeatureError(
                f"Missing required surveillance features ({len(missing)}): {sorted(missing)}"
            )

    def compute_scores(
        self,
        df: pd.DataFrame,
        preserve_metadata: bool = True,
    ) -> pd.DataFrame:
        """
        Computes the complete Execution Surveillance Suite across an input DataFrame.

        Steps:
        1. Validates input schema against the 12-feature surveillance contract.
        2. Strictly isolates input features (ignoring target/future columns).
        3. Computes S_stag and flag_stag (Physical Progress Stagnation).
        4. Computes S_vel and flag_vel (Progress Velocity Deterioration).
        5. Computes S_sched and flag_sched (Schedule Slippage & Overdue).
        6. Computes S_div and flag_div (Expenditure / Progress Divergence).
        7. Computes S_rep and flag_rep (Observation & Reporting Quality).
        8. Aggregates total_stress_flags.
        9. Computes Domain-Calibrated ESI (0.30/0.25/0.20/0.15/0.10).
        10. Maps ESI tier (NOMINAL, WATCH, ATTENTION, HIGH_PRIORITY).
        11. Determines dominant_stressor via deterministic argmax with tie-breaking.
        12. Determines suggested_action via authoritative priority hierarchy.

        Returns:
            pd.DataFrame: Complete surveillance scores and directives.
        """
        self.validate_input(df)

        # ----------------------------------------------------------------------
        # Dimension 1: Physical Progress Stagnation Stress (S_stag in [0, 1])
        # ----------------------------------------------------------------------
        months_stag = df["months_since_last_progress_increase_t"].fillna(0).clip(lower=0)
        stag_duration_score = np.clip(months_stag / 4.0, 0.0, 1.0)
        rem_prog = df["remaining_physical_progress_t"].fillna(50.0).clip(lower=0.0, upper=100.0) / 100.0
        s_stag = np.clip(0.7 * stag_duration_score + 0.3 * (stag_duration_score * rem_prog), 0.0, 1.0)
        flag_stag = ((months_stag >= 3) | (df["stagnant_3m_t"] == 1.0)).astype(int)

        # ----------------------------------------------------------------------
        # Dimension 2: Progress Velocity Deterioration Stress (S_vel in [0, 1])
        # ----------------------------------------------------------------------
        vel_3m = df["progress_velocity_3m_t"]
        vel_eff = vel_3m.combine_first(df["progress_change_1m_t"]).fillna(0.0)
        s_vel = np.where(
            vel_eff <= 0.0,
            1.0,
            np.where(
                vel_eff < 1.0,
                0.75 - 0.25 * (vel_eff / 1.0),
                np.where(
                    vel_eff < 3.0,
                    0.50 - 0.50 * ((vel_eff - 1.0) / 2.0),
                    0.0,
                ),
            ),
        )
        s_vel = np.clip(s_vel, 0.0, 1.0)
        flag_vel = (vel_eff < 0.5).astype(int)

        # ----------------------------------------------------------------------
        # Dimension 3: Schedule Slippage & Proximity Stress (S_sched in [0, 1])
        # ----------------------------------------------------------------------
        slippage = df["schedule_slippage_months_t"].fillna(0.0).clip(lower=0.0)
        slippage_score = np.clip(slippage / 36.0, 0.0, 1.0)
        months_to_orig = df["months_to_original_doc_t"].fillna(12.0)
        is_overdue = (months_to_orig < 0.0).astype(float)
        overdue_magnitude = np.clip((-months_to_orig) / 24.0, 0.0, 1.0) * is_overdue
        s_sched = np.clip(0.6 * slippage_score + 0.4 * overdue_magnitude, 0.0, 1.0)
        flag_sched = ((slippage >= 12.0) | (months_to_orig < -6.0)).astype(int)

        # ----------------------------------------------------------------------
        # Dimension 4: Expenditure / Progress Divergence Stress (S_div in [0, 1])
        # ----------------------------------------------------------------------
        exp_ratio = df["expenditure_ratio_pct_t"].fillna(0.0).clip(lower=0.0)
        phys_prog = df["physical_progress_t"].fillna(0.0).clip(lower=0.0, upper=100.0)
        divergence_spread = exp_ratio - phys_prog
        s_div = np.where(
            divergence_spread <= 0.0,
            0.0,
            np.clip(divergence_spread / 75.0, 0.0, 1.0),
        )
        s_div = np.clip(s_div, 0.0, 1.0)
        flag_div = (divergence_spread > 25.0).astype(int)

        # ----------------------------------------------------------------------
        # Dimension 5: Observation & Reporting Quality Stress (S_rep in [0, 1])
        # ----------------------------------------------------------------------
        obs_gap = df["observation_gap_flag_t"].fillna(0).astype(float)
        miss_prog = df["missing_physical_progress_t"].fillna(0).astype(float)
        rev_count = df["schedule_revision_count_to_date_t"].fillna(0).clip(lower=0.0)
        rev_stress = np.clip(rev_count / 3.0, 0.0, 1.0)
        s_rep = np.clip(0.4 * obs_gap + 0.3 * miss_prog + 0.3 * rev_stress, 0.0, 1.0)
        flag_rep = ((obs_gap == 1.0) | (miss_prog == 1.0) | (rev_count >= 2.0)).astype(int)

        # ----------------------------------------------------------------------
        # Total Stress Flags
        # ----------------------------------------------------------------------
        total_stress_flags = flag_stag + flag_vel + flag_sched + flag_div + flag_rep

        # ----------------------------------------------------------------------
        # Composite Execution-Stress Index (ESI)
        # ----------------------------------------------------------------------
        esi_raw = (
            WEIGHT_STAGNATION * s_stag
            + WEIGHT_VELOCITY * s_vel
            + WEIGHT_DIVERGENCE * s_div
            + WEIGHT_SCHEDULE * s_sched
            + WEIGHT_REPORTING * s_rep
        )
        execution_stress_index = np.round(esi_raw, 4)

        # ----------------------------------------------------------------------
        # ESI Tiers (Boundaries: < 0.35, 0.35 - 0.55, 0.55 - 0.75, >= 0.75)
        # ----------------------------------------------------------------------
        esi_tier = np.select(
            [
                execution_stress_index < 0.35,
                execution_stress_index < 0.55,
                execution_stress_index < 0.75,
            ],
            [TIER_NOMINAL, TIER_WATCH, TIER_ATTENTION],
            default=TIER_HIGH_PRIORITY,
        )

        # ----------------------------------------------------------------------
        # Dominant Stressor Attribution (Deterministic Argmax with tie-breaking)
        # Order: 1. Stagnation, 2. Velocity, 3. Divergence, 4. Schedule, 5. Reporting
        # ----------------------------------------------------------------------
        w_stag = np.round(WEIGHT_STAGNATION * s_stag, 6)
        w_vel = np.round(WEIGHT_VELOCITY * s_vel, 6)
        w_div = np.round(WEIGHT_DIVERGENCE * s_div, 6)
        w_sched = np.round(WEIGHT_SCHEDULE * s_sched, 6)
        w_rep = np.round(WEIGHT_REPORTING * s_rep, 6)

        stacked_weights = np.column_stack([w_stag, w_vel, w_div, w_sched, w_rep])
        # np.argmax returns the lowest index on ties, strictly matching ORDERED_STRESSOR_TIE_BREAK
        dominant_indices = np.argmax(stacked_weights, axis=1)
        stressor_labels = np.array(ORDERED_STRESSOR_TIE_BREAK)
        dominant_stressor = stressor_labels[dominant_indices]

        # ----------------------------------------------------------------------
        # Prescriptive Monitoring Action Logic Matrix
        # Evaluated in strict priority hierarchy
        # ----------------------------------------------------------------------
        cond_escalation = (execution_stress_index >= 0.75) & (total_stress_flags >= 3)
        cond_stagnation = (s_stag >= 0.75) | (flag_stag == 1)
        cond_divergence = (s_div >= 0.75) | (flag_div == 1)
        cond_velocity = (s_vel >= 0.75) | (flag_vel == 1)
        cond_schedule = (s_sched >= 0.75) | (flag_sched == 1)
        cond_reporting = (s_rep >= 0.75) | (flag_rep == 1)

        # Fallback conditions using dominant_stressor
        fb_divergence = dominant_stressor == STRESSOR_EXPENDITURE_DIVERGENCE
        fb_velocity = dominant_stressor == STRESSOR_VELOCITY_COLLAPSE
        fb_schedule = dominant_stressor == STRESSOR_SCHEDULE_SLIPPAGE
        fb_reporting = dominant_stressor == STRESSOR_REPORTING_FRICTION
        # Otherwise -> SITE_OBSTACLE_AUDIT (Stagnation)

        suggested_action = np.select(
            [
                cond_escalation,
                cond_stagnation,
                cond_divergence,
                cond_velocity,
                cond_schedule,
                cond_reporting,
                fb_divergence,
                fb_velocity,
                fb_schedule,
                fb_reporting,
            ],
            [
                ACTION_INTER_MINISTERIAL_ESCALATION,
                ACTION_SITE_OBSTACLE_AUDIT,
                ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT,
                ACTION_RESOURCE_MOBILIZATION_DIRECTIVE,
                ACTION_CRITICAL_PATH_RECALIBRATION,
                ACTION_DATA_COMPLIANCE_DIRECTIVE,
                ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT,
                ACTION_RESOURCE_MOBILIZATION_DIRECTIVE,
                ACTION_CRITICAL_PATH_RECALIBRATION,
                ACTION_DATA_COMPLIANCE_DIRECTIVE,
            ],
            default=ACTION_SITE_OBSTACLE_AUDIT,
        )

        # ----------------------------------------------------------------------
        # Assemble Output DataFrame
        # ----------------------------------------------------------------------
        output_dict = {}

        if preserve_metadata:
            if "project_id" in df.columns:
                output_dict["project_id"] = df["project_id"].values
            if "report_month" in df.columns:
                output_dict["report_month"] = df["report_month"].values
            elif "prediction_month" in df.columns:
                output_dict["report_month"] = df["prediction_month"].values

        output_dict["s_stag"] = np.round(s_stag, 4)
        output_dict["s_vel"] = np.round(s_vel, 4)
        output_dict["s_div"] = np.round(s_div, 4)
        output_dict["s_sched"] = np.round(s_sched, 4)
        output_dict["s_rep"] = np.round(s_rep, 4)

        output_dict["flag_stag"] = flag_stag.values if isinstance(flag_stag, pd.Series) else flag_stag
        output_dict["flag_vel"] = flag_vel.values if isinstance(flag_vel, pd.Series) else flag_vel
        output_dict["flag_div"] = flag_div.values if isinstance(flag_div, pd.Series) else flag_div
        output_dict["flag_sched"] = flag_sched.values if isinstance(flag_sched, pd.Series) else flag_sched
        output_dict["flag_rep"] = flag_rep.values if isinstance(flag_rep, pd.Series) else flag_rep

        output_dict["total_stress_flags"] = (
            total_stress_flags.values if isinstance(total_stress_flags, pd.Series) else total_stress_flags
        )
        output_dict["execution_stress_index"] = execution_stress_index
        output_dict["esi_tier"] = esi_tier
        output_dict["dominant_stressor"] = dominant_stressor
        output_dict["suggested_action"] = suggested_action
        output_dict["execution_index_version"] = self.version

        return pd.DataFrame(output_dict, index=df.index)
