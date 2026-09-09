"""
Inference Contracts and Constants for SIH26103 Batch Risk Scoring Engine.

This module defines:
- Strict 75-feature input contract (71 numeric + 4 categorical)
- Model version identifier ('v1.0.0-rf02-calibrated')
- Candidate B Evidence-Weighted synthesis weights (0.50 / 0.35 / 0.15)
- Risk-band boundaries and dominant-component definitions
- Point-in-time safety assumptions and target column guards
- Custom inference exception classes
"""

from typing import List, Tuple

# ==============================================================================
# 1. MODEL VERSION IDENTIFIER
# ==============================================================================
MODEL_VERSION: str = "v1.0.0-rf02-calibrated"

# ==============================================================================
# 2. FEATURE CONTRACT DEFINITIONS (75 Features: 71 Numeric + 4 Categorical)
# ==============================================================================
REQUIRED_NUMERICAL_FEATURES: List[str] = ['original_cost_crore', 'project_age_months_t', 'planned_duration_months', 'original_cost_log', 'physical_progress_t', 'cumulative_expenditure_t', 'revised_cost_t', 'cost_escalation_pct_t', 'expenditure_ratio_pct_t', 'remaining_physical_progress_t', 'schedule_slippage_months_t', 'months_to_original_doc_t', 'months_to_revised_doc_t', 'physical_progress_lag1', 'physical_progress_lag2', 'physical_progress_lag3', 'progress_change_1m_t', 'progress_change_2m_t', 'progress_change_3m_t', 'progress_velocity_1m_t', 'progress_velocity_3m_t', 'progress_velocity_6m_t', 'max_progress_to_date_t', 'min_progress_to_date_t', 'average_progress_to_date_t', 'progress_std_to_date_t', 'cumulative_expenditure_lag1', 'cumulative_expenditure_lag3', 'monthly_expenditure_delta_t', 'expenditure_change_1m_t', 'expenditure_change_3m_t', 'expenditure_velocity_3m_t', 'expenditure_velocity_6m_t', 'avg_monthly_expenditure_to_date_t', 'expenditure_growth_rate_t', 'negative_expenditure_delta_flag_t', 'stagnant_2m_t', 'stagnant_3m_t', 'stagnant_6m_t', 'months_since_last_progress_increase_t', 'longest_stagnation_to_date_t', 'progress_change_last_3m_t', 'has_cost_revision_t', 'cost_revision_count_to_date_t', 'months_since_last_cost_revision_t', 'largest_cost_revision_pct_to_date_t', 'cost_reduction_pct_as_of_t', 'has_revised_schedule_as_of_t', 'schedule_revision_count_to_date_t', 'months_since_last_schedule_revision_t', 'months_observed_to_date_t', 'months_since_first_observed_t', 'observation_coverage_ratio_t', 'consecutive_observation_count_t', 'months_since_last_observation_t', 'missing_physical_progress_t', 'missing_expenditure_t', 'missing_revised_cost_t', 'missing_revised_doc_t', 'observation_gap_flag_t', 'state_active_project_count_t', 'state_mean_progress_t', 'state_median_progress_t', 'state_mean_cost_t', 'state_mean_expenditure_ratio_t', 'agency_active_project_count_t', 'agency_mean_progress_t', 'agency_median_progress_t', 'agency_mean_cost_t', 'agency_mean_expenditure_ratio_t', 'focused_cohort_indicator_t']

REQUIRED_CATEGORICAL_FEATURES: List[str] = ['project_size_category', 'current_schedule_status_as_of_t', 'reporting_structure_version_t', 'table_source_t']

ALL_MODEL_FEATURES: List[str] = REQUIRED_NUMERICAL_FEATURES + REQUIRED_CATEGORICAL_FEATURES

# ==============================================================================
# 3. POINT-IN-TIME SAFETY GUARDS
# Target and future-looking columns that MUST NEVER enter the model matrix X
# ==============================================================================
KNOWN_TARGET_COLUMNS: List[str] = [
    "schedule_delay_3m",
    "cost_overrun_state_3m",
    "schedule_revision_3m",
    "cost_revision_event_3m",
    "evaluation_month",
    "final_completion_delay_months",
    "final_cost_overrun_pct",
]

# ==============================================================================
# 4. SYNTHESIS WEIGHTS (Candidate B: Evidence-Weighted Architecture)
# ==============================================================================
WEIGHT_SCHEDULE_DELAY: float = 0.50
WEIGHT_COST_OVERRUN: float = 0.35
WEIGHT_SCHEDULE_REVISION: float = 0.15

# ==============================================================================
# 5. RISK BANDS & DOMINANT COMPONENTS
# ==============================================================================
BAND_LOW: str = "LOW"            # score < 0.30
BAND_MODERATE: str = "MODERATE"    # 0.30 <= score < 0.60
BAND_HIGH: str = "HIGH"            # 0.60 <= score < 0.80
BAND_VERY_HIGH: str = "VERY_HIGH"  # score >= 0.80

DOMINANT_SCHEDULE_DELAY: str = "Schedule Delay"
DOMINANT_COST_OVERRUN: str = "Cost Overrun"
DOMINANT_SCHEDULE_REVISION: str = "Schedule Revision"

ORDERED_DOMINANT_COMPONENTS: Tuple[str, str, str] = (
    DOMINANT_SCHEDULE_DELAY,
    DOMINANT_COST_OVERRUN,
    DOMINANT_SCHEDULE_REVISION,
)

# Standard output column list
OUTPUT_COLUMNS: List[str] = [
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

# ==============================================================================
# 6. CUSTOM EXCEPTION CLASSES
# ==============================================================================
class InferenceError(Exception):
    """Base exception for all ML inference operations."""
    pass

class MissingFeatureError(InferenceError):
    """Raised when required model features are missing from input DataFrame."""
    pass

class ModelArtifactNotFoundError(InferenceError):
    """Raised when a required frozen model artifact (.pkl) is not found."""
    pass

class InvalidInputError(InferenceError):
    """Raised when input data structure or content violates the inference contract."""
    pass
