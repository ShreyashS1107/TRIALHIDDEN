"""
Surveillance Contracts and Constants for SIH26103 Execution Surveillance Engine.

Defines:
- 12-input point-in-time feature contract
- Domain-calibrated weighting parameters (30%, 25%, 20%, 15%, 10%)
- Canonical ESI tier thresholds (<0.35, 0.35-0.55, 0.55-0.75, >=0.75)
- Canonical dominant stressor names and deterministic tie-breaking order
- Canonical prescriptive action directives and priority hierarchy
- Output contract schemas
- Custom surveillance exceptions
"""

from typing import List

# ==============================================================================
# 1. VERSION IDENTIFIER
# ==============================================================================
EXECUTION_INDEX_VERSION: str = "v1.0.0-esi-5dim"

# ==============================================================================
# 2. REQUIRED INPUT FEATURE CONTRACT (12 Features)
# ==============================================================================
REQUIRED_SURVEILLANCE_FEATURES: List[str] = [
    "months_since_last_progress_increase_t",
    "stagnant_3m_t",
    "remaining_physical_progress_t",
    "progress_velocity_3m_t",
    "progress_change_1m_t",
    "schedule_slippage_months_t",
    "months_to_original_doc_t",
    "expenditure_ratio_pct_t",
    "physical_progress_t",
    "observation_gap_flag_t",
    "missing_physical_progress_t",
    "schedule_revision_count_to_date_t",
]

# Known target/future columns that MUST NEVER be used
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
# 3. COMPOSITE WEIGHTS
# ==============================================================================
WEIGHT_STAGNATION: float = 0.30   # S_stag
WEIGHT_VELOCITY: float = 0.25     # S_vel
WEIGHT_DIVERGENCE: float = 0.20   # S_div
WEIGHT_SCHEDULE: float = 0.15     # S_sched
WEIGHT_REPORTING: float = 0.10    # S_rep

# ==============================================================================
# 4. CANONICAL ESI TIERS
# ==============================================================================
TIER_NOMINAL: str = "NOMINAL"            # ESI < 0.35
TIER_WATCH: str = "WATCH"                # 0.35 <= ESI < 0.55
TIER_ATTENTION: str = "ATTENTION"        # 0.55 <= ESI < 0.75
TIER_HIGH_PRIORITY: str = "HIGH_PRIORITY" # ESI >= 0.75

ORDERED_ESI_TIERS: List[str] = [
    TIER_NOMINAL,
    TIER_WATCH,
    TIER_ATTENTION,
    TIER_HIGH_PRIORITY,
]

# ==============================================================================
# 5. CANONICAL DOMINANT STRESSORS (Database Enum Values)
# ==============================================================================
STRESSOR_PROGRESS_STAGNATION: str = "Physical Progress Stagnation"
STRESSOR_VELOCITY_COLLAPSE: str = "Progress Velocity Collapse"
STRESSOR_EXPENDITURE_DIVERGENCE: str = "Expenditure Divergence"
STRESSOR_SCHEDULE_SLIPPAGE: str = "Schedule Slippage Debt"
STRESSOR_REPORTING_FRICTION: str = "Reporting Friction"

# Authoritative deterministic tie-breaking order
ORDERED_STRESSOR_TIE_BREAK: List[str] = [
    STRESSOR_PROGRESS_STAGNATION,
    STRESSOR_VELOCITY_COLLAPSE,
    STRESSOR_EXPENDITURE_DIVERGENCE,
    STRESSOR_SCHEDULE_SLIPPAGE,
    STRESSOR_REPORTING_FRICTION,
]

# ==============================================================================
# 6. CANONICAL PRESCRIPTIVE ACTIONS (Database Enum Values)
# ==============================================================================
ACTION_INTER_MINISTERIAL_ESCALATION: str = "INTER_MINISTERIAL_COMMITTEE_ESCALATION"
ACTION_SITE_OBSTACLE_AUDIT: str = "SITE_OBSTACLE_AUDIT"
ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT: str = "FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT"
ACTION_RESOURCE_MOBILIZATION_DIRECTIVE: str = "RESOURCE_MOBILIZATION_DIRECTIVE"
ACTION_CRITICAL_PATH_RECALIBRATION: str = "CRITICAL_PATH_RECALIBRATION"
ACTION_DATA_COMPLIANCE_DIRECTIVE: str = "DATA_COMPLIANCE_DIRECTIVE"

ORDERED_PRESCRIPTIVE_ACTIONS: List[str] = [
    ACTION_INTER_MINISTERIAL_ESCALATION,
    ACTION_SITE_OBSTACLE_AUDIT,
    ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT,
    ACTION_RESOURCE_MOBILIZATION_DIRECTIVE,
    ACTION_CRITICAL_PATH_RECALIBRATION,
    ACTION_DATA_COMPLIANCE_DIRECTIVE,
]

# ==============================================================================
# 7. OUTPUT CONTRACT SCHEMA
# ==============================================================================
OUTPUT_SURVEILLANCE_COLUMNS: List[str] = [
    "project_id",
    "report_month",
    "s_stag",
    "s_vel",
    "s_div",
    "s_sched",
    "s_rep",
    "flag_stag",
    "flag_vel",
    "flag_div",
    "flag_sched",
    "flag_rep",
    "total_stress_flags",
    "execution_stress_index",
    "esi_tier",
    "dominant_stressor",
    "suggested_action",
    "execution_index_version",
]

# ==============================================================================
# 8. CUSTOM EXCEPTIONS
# ==============================================================================
class SurveillanceError(Exception):
    """Base exception for all surveillance engine operations."""
    pass

class MissingFeatureError(SurveillanceError):
    """Raised when required surveillance features are missing from input DataFrame."""
    pass

class InvalidInputError(SurveillanceError):
    """Raised when input data structure or content violates the surveillance contract."""
    pass
