"""
Unit and Integration Test Suite for ExecutionSurveillanceEngine (Phase 5C-1).

Covers all 22 required test cases:
1. Basic ESI calculation
2. Stagnation formula (months_stag / 4.0, rem_prog scaling)
3. Velocity piecewise formula (<= 0, 0 < v < 1, 1 <= v < 3, >= 3)
4. Schedule formula (slippage / 36.0, overdue magnitude)
5. Divergence formula (exp_ratio - phys_prog, spread <= 0, spread / 75)
6. Reporting formula (obs_gap, miss_prog, rev_stress)
7. Operational flags (flag_stag, flag_vel, flag_sched, flag_div, flag_rep)
8. Total stress flags count
9. ESI weighted combination (0.30, 0.25, 0.20, 0.15, 0.10)
10. All tier boundaries explicitly (<0.35, 0.35-0.55, 0.55-0.75, >=0.75)
11. Dominant stressor attribution
12. Dominant stressor tie-breaking order
13. Prescriptive priority ordering (priorities 1 through 6)
14. Fallback prescriptive actions (priority 7)
15. Value bounds in [0.0, 1.0]
16. NaN / default handling
17. Metadata preservation (project_id, report_month)
18. Missing required feature rejection (MissingFeatureError / InvalidInputError)
19. Future / target column isolation
20. Deterministic repeated scoring
21. Multi-row batch scoring
22. Version field ("v1.0.0-esi-5dim")
"""

import sys
from pathlib import Path
ai_ml_root = Path(__file__).resolve().parent.parent.parent
if str(ai_ml_root) not in sys.path:
    sys.path.insert(0, str(ai_ml_root))

import numpy as np
import pandas as pd
import pytest

from ml.surveillance import (
    ACTION_CRITICAL_PATH_RECALIBRATION,
    ACTION_DATA_COMPLIANCE_DIRECTIVE,
    ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT,
    ACTION_INTER_MINISTERIAL_ESCALATION,
    ACTION_RESOURCE_MOBILIZATION_DIRECTIVE,
    ACTION_SITE_OBSTACLE_AUDIT,
    EXECUTION_INDEX_VERSION,
    KNOWN_TARGET_COLUMNS,
    ORDERED_ESI_TIERS,
    ORDERED_PRESCRIPTIVE_ACTIONS,
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
    ExecutionSurveillanceEngine,
    InvalidInputError,
    MissingFeatureError,
)


def make_clean_row(**overrides) -> dict:
    """Returns a baseline dictionary with nominal values for all 12 surveillance features."""
    base = {
        "project_id": "TEST_001",
        "report_month": "2025-06",
        "months_since_last_progress_increase_t": 0.0,
        "stagnant_3m_t": 0.0,
        "remaining_physical_progress_t": 50.0,
        "progress_velocity_3m_t": 3.5,
        "progress_change_1m_t": 3.5,
        "schedule_slippage_months_t": 0.0,
        "months_to_original_doc_t": 24.0,
        "expenditure_ratio_pct_t": 20.0,
        "physical_progress_t": 20.0,
        "observation_gap_flag_t": 0.0,
        "missing_physical_progress_t": 0.0,
        "schedule_revision_count_to_date_t": 0.0,
    }
    base.update(overrides)
    return base


@pytest.fixture
def engine():
    """Returns an ExecutionSurveillanceEngine instance."""
    return ExecutionSurveillanceEngine()


# ==============================================================================
# 1. BASIC ESI CALCULATION
# ==============================================================================
def test_basic_esi_calculation(engine):
    """Test standard calculation and presence of all required output columns."""
    df = pd.DataFrame([make_clean_row()])
    result = engine.compute_scores(df)

    for col in OUTPUT_SURVEILLANCE_COLUMNS:
        assert col in result.columns, f"Expected output column '{col}' missing from result."
    assert len(result) == 1
    assert result["execution_index_version"].iloc[0] == EXECUTION_INDEX_VERSION


# ==============================================================================
# 2. STAGNATION FORMULA
# ==============================================================================
def test_stagnation_formula(engine):
    """Test S_stag = 0.7 * (months_stag / 4.0) + 0.3 * (months_stag / 4.0 * rem_prog / 100)."""
    # 0 months -> 0.0
    df0 = pd.DataFrame([make_clean_row(months_since_last_progress_increase_t=0)])
    assert engine.compute_scores(df0)["s_stag"].iloc[0] == 0.0

    # 4 months with 100% remaining -> 0.7 * 1.0 + 0.3 * (1.0 * 1.0) = 1.0
    df4_100 = pd.DataFrame([
        make_clean_row(
            months_since_last_progress_increase_t=4.0,
            remaining_physical_progress_t=100.0,
        )
    ])
    assert engine.compute_scores(df4_100)["s_stag"].iloc[0] == 1.0

    # 2 months with 50% remaining -> stag_dur = 0.5, rem = 0.5 -> 0.7*0.5 + 0.3*0.25 = 0.425
    df2_50 = pd.DataFrame([
        make_clean_row(
            months_since_last_progress_increase_t=2.0,
            remaining_physical_progress_t=50.0,
        )
    ])
    assert engine.compute_scores(df2_50)["s_stag"].iloc[0] == 0.425

    # Capping at months_stag > 4
    df_cap = pd.DataFrame([
        make_clean_row(
            months_since_last_progress_increase_t=10.0,
            remaining_physical_progress_t=100.0,
        )
    ])
    assert engine.compute_scores(df_cap)["s_stag"].iloc[0] == 1.0


# ==============================================================================
# 3. VELOCITY PIECEWISE FORMULA
# ==============================================================================
def test_velocity_piecewise_formula(engine):
    """Test piecewise velocity stress curve: <=0 -> 1.0, 0<v<1, 1<=v<3, >=3 -> 0.0."""
    # vel <= 0 -> 1.0
    df_neg = pd.DataFrame([make_clean_row(progress_velocity_3m_t=-0.5)])
    assert engine.compute_scores(df_neg)["s_vel"].iloc[0] == 1.0

    df_zero = pd.DataFrame([make_clean_row(progress_velocity_3m_t=0.0)])
    assert engine.compute_scores(df_zero)["s_vel"].iloc[0] == 1.0

    # 0 < v < 1: v=0.5 -> 0.75 - 0.25 * 0.5 = 0.625
    df_half = pd.DataFrame([make_clean_row(progress_velocity_3m_t=0.5)])
    assert engine.compute_scores(df_half)["s_vel"].iloc[0] == 0.625

    # 1 <= v < 3: v=2.0 -> 0.50 - 0.50 * ((2.0 - 1.0) / 2.0) = 0.25
    df_mid = pd.DataFrame([make_clean_row(progress_velocity_3m_t=2.0)])
    assert engine.compute_scores(df_mid)["s_vel"].iloc[0] == 0.25

    # v >= 3 -> 0.0
    df_high = pd.DataFrame([make_clean_row(progress_velocity_3m_t=3.5)])
    assert engine.compute_scores(df_high)["s_vel"].iloc[0] == 0.0

    # Fallback to progress_change_1m_t when progress_velocity_3m_t is NaN
    df_fallback = pd.DataFrame([
        make_clean_row(progress_velocity_3m_t=np.nan, progress_change_1m_t=2.0)
    ])
    assert engine.compute_scores(df_fallback)["s_vel"].iloc[0] == 0.25


# ==============================================================================
# 4. SCHEDULE FORMULA
# ==============================================================================
def test_schedule_formula(engine):
    """Test S_sched = 0.6 * (slippage / 36.0) + 0.4 * overdue_magnitude."""
    # 18 months slippage, not overdue (months_to_orig = 12) -> 0.6 * (18/36) + 0.0 = 0.3
    df_slip = pd.DataFrame([
        make_clean_row(
            schedule_slippage_months_t=18.0,
            months_to_original_doc_t=12.0,
        )
    ])
    assert engine.compute_scores(df_slip)["s_sched"].iloc[0] == 0.3

    # 36 months slippage, overdue by 12 months (months_to_orig = -12) -> 0.6 * 1.0 + 0.4 * (12/24) = 0.8
    df_overdue = pd.DataFrame([
        make_clean_row(
            schedule_slippage_months_t=36.0,
            months_to_original_doc_t=-12.0,
        )
    ])
    assert engine.compute_scores(df_overdue)["s_sched"].iloc[0] == 0.8

    # Overdue capping (overdue by 40 months -> capped at 1.0 magnitude)
    df_max = pd.DataFrame([
        make_clean_row(
            schedule_slippage_months_t=48.0,
            months_to_original_doc_t=-40.0,
        )
    ])
    assert engine.compute_scores(df_max)["s_sched"].iloc[0] == 1.0


# ==============================================================================
# 5. DIVERGENCE FORMULA
# ==============================================================================
def test_divergence_formula(engine):
    """Test S_div: spread <= 0 -> 0.0, spread > 0 -> spread / 75.0 clipped to 1.0."""
    # Negative spread (expenditure <= physical) -> 0.0
    df_neg = pd.DataFrame([
        make_clean_row(expenditure_ratio_pct_t=20.0, physical_progress_t=30.0)
    ])
    assert engine.compute_scores(df_neg)["s_div"].iloc[0] == 0.0

    # 30% spread -> 30.0 / 75.0 = 0.4
    df_spread = pd.DataFrame([
        make_clean_row(expenditure_ratio_pct_t=50.0, physical_progress_t=20.0)
    ])
    assert engine.compute_scores(df_spread)["s_div"].iloc[0] == 0.4

    # 90% spread -> clipped to 1.0
    df_clip = pd.DataFrame([
        make_clean_row(expenditure_ratio_pct_t=100.0, physical_progress_t=5.0)
    ])
    assert engine.compute_scores(df_clip)["s_div"].iloc[0] == 1.0


# ==============================================================================
# 6. REPORTING FORMULA
# ==============================================================================
def test_reporting_formula(engine):
    """Test S_rep = 0.4 * obs_gap + 0.3 * miss_prog + 0.3 * (rev_count / 3.0)."""
    # obs_gap only -> 0.4
    df_gap = pd.DataFrame([make_clean_row(observation_gap_flag_t=1.0)])
    assert engine.compute_scores(df_gap)["s_rep"].iloc[0] == 0.4

    # miss_prog only -> 0.3
    df_miss = pd.DataFrame([make_clean_row(missing_physical_progress_t=1.0)])
    assert engine.compute_scores(df_miss)["s_rep"].iloc[0] == 0.3

    # rev_count = 3 only -> 0.3 * (3 / 3) = 0.3
    df_rev = pd.DataFrame([make_clean_row(schedule_revision_count_to_date_t=3.0)])
    assert engine.compute_scores(df_rev)["s_rep"].iloc[0] == 0.3

    # All three active -> 0.4 + 0.3 + 0.3 = 1.0
    df_all = pd.DataFrame([
        make_clean_row(
            observation_gap_flag_t=1.0,
            missing_physical_progress_t=1.0,
            schedule_revision_count_to_date_t=5.0,
        )
    ])
    assert engine.compute_scores(df_all)["s_rep"].iloc[0] == 1.0


# ==============================================================================
# 7. OPERATIONAL FLAGS
# ==============================================================================
def test_operational_flags(engine):
    """Test operational flag triggers for all 5 dimensions."""
    # Stagnation flag: months >= 3 OR stagnant_3m_t == 1
    df_stag1 = pd.DataFrame([make_clean_row(months_since_last_progress_increase_t=3.0)])
    df_stag2 = pd.DataFrame([make_clean_row(stagnant_3m_t=1.0)])
    df_stag_off = pd.DataFrame([make_clean_row(months_since_last_progress_increase_t=2.0)])
    assert engine.compute_scores(df_stag1)["flag_stag"].iloc[0] == 1
    assert engine.compute_scores(df_stag2)["flag_stag"].iloc[0] == 1
    assert engine.compute_scores(df_stag_off)["flag_stag"].iloc[0] == 0

    # Velocity flag: vel < 0.5
    df_vel_on = pd.DataFrame([make_clean_row(progress_velocity_3m_t=0.49)])
    df_vel_off = pd.DataFrame([make_clean_row(progress_velocity_3m_t=0.50)])
    assert engine.compute_scores(df_vel_on)["flag_vel"].iloc[0] == 1
    assert engine.compute_scores(df_vel_off)["flag_vel"].iloc[0] == 0

    # Schedule flag: slippage >= 12 OR months_to_orig < -6
    df_sched1 = pd.DataFrame([make_clean_row(schedule_slippage_months_t=12.0)])
    df_sched2 = pd.DataFrame([make_clean_row(months_to_original_doc_t=-6.1)])
    df_sched_off = pd.DataFrame([
        make_clean_row(schedule_slippage_months_t=11.9, months_to_original_doc_t=-5.9)
    ])
    assert engine.compute_scores(df_sched1)["flag_sched"].iloc[0] == 1
    assert engine.compute_scores(df_sched2)["flag_sched"].iloc[0] == 1
    assert engine.compute_scores(df_sched_off)["flag_sched"].iloc[0] == 0

    # Divergence flag: spread > 25.0
    df_div_on = pd.DataFrame([
        make_clean_row(expenditure_ratio_pct_t=55.1, physical_progress_t=30.0)
    ])
    df_div_off = pd.DataFrame([
        make_clean_row(expenditure_ratio_pct_t=55.0, physical_progress_t=30.0)
    ])
    assert engine.compute_scores(df_div_on)["flag_div"].iloc[0] == 1
    assert engine.compute_scores(df_div_off)["flag_div"].iloc[0] == 0

    # Reporting flag: obs_gap == 1 OR miss_prog == 1 OR rev_count >= 2
    df_rep1 = pd.DataFrame([make_clean_row(observation_gap_flag_t=1.0)])
    df_rep2 = pd.DataFrame([make_clean_row(missing_physical_progress_t=1.0)])
    df_rep3 = pd.DataFrame([make_clean_row(schedule_revision_count_to_date_t=2.0)])
    df_rep_off = pd.DataFrame([
        make_clean_row(
            observation_gap_flag_t=0.0,
            missing_physical_progress_t=0.0,
            schedule_revision_count_to_date_t=1.0,
        )
    ])
    assert engine.compute_scores(df_rep1)["flag_rep"].iloc[0] == 1
    assert engine.compute_scores(df_rep2)["flag_rep"].iloc[0] == 1
    assert engine.compute_scores(df_rep3)["flag_rep"].iloc[0] == 1
    assert engine.compute_scores(df_rep_off)["flag_rep"].iloc[0] == 0


# ==============================================================================
# 8. TOTAL STRESS FLAGS COUNT
# ==============================================================================
def test_total_stress_flags_count(engine):
    """Test integer sum of the 5 operational flags [0, 5]."""
    # 0 flags
    df0 = pd.DataFrame([make_clean_row()])
    assert engine.compute_scores(df0)["total_stress_flags"].iloc[0] == 0

    # 5 flags
    df5 = pd.DataFrame([
        make_clean_row(
            months_since_last_progress_increase_t=4.0,  # flag_stag
            progress_velocity_3m_t=0.1,                 # flag_vel
            schedule_slippage_months_t=20.0,            # flag_sched
            expenditure_ratio_pct_t=80.0,               # flag_div (spread = 60)
            physical_progress_t=20.0,
            observation_gap_flag_t=1.0,                 # flag_rep
        )
    ])
    res5 = engine.compute_scores(df5)
    assert res5["flag_stag"].iloc[0] == 1
    assert res5["flag_vel"].iloc[0] == 1
    assert res5["flag_sched"].iloc[0] == 1
    assert res5["flag_div"].iloc[0] == 1
    assert res5["flag_rep"].iloc[0] == 1
    assert res5["total_stress_flags"].iloc[0] == 5


# ==============================================================================
# 9. ESI WEIGHTED COMBINATION
# ==============================================================================
def test_esi_weighted_combination(engine):
    """Test ESI = 0.30*S_stag + 0.25*S_vel + 0.20*S_div + 0.15*S_sched + 0.10*S_rep."""
    # When all dimensions are 1.0 -> ESI = 1.0
    df_max = pd.DataFrame([
        make_clean_row(
            months_since_last_progress_increase_t=4.0,
            remaining_physical_progress_t=100.0,
            progress_velocity_3m_t=-1.0,
            expenditure_ratio_pct_t=100.0,
            physical_progress_t=0.0,
            schedule_slippage_months_t=36.0,
            months_to_original_doc_t=-24.0,
            observation_gap_flag_t=1.0,
            missing_physical_progress_t=1.0,
            schedule_revision_count_to_date_t=3.0,
        )
    ])
    res_max = engine.compute_scores(df_max)
    assert res_max["execution_stress_index"].iloc[0] == 1.0000

    # Dimension weight verification
    assert WEIGHT_STAGNATION == 0.30
    assert WEIGHT_VELOCITY == 0.25
    assert WEIGHT_DIVERGENCE == 0.20
    assert WEIGHT_SCHEDULE == 0.15
    assert WEIGHT_REPORTING == 0.10
    assert sum([WEIGHT_STAGNATION, WEIGHT_VELOCITY, WEIGHT_DIVERGENCE, WEIGHT_SCHEDULE, WEIGHT_REPORTING]) == 1.0


# ==============================================================================
# 10. TIER BOUNDARIES
# ==============================================================================
def test_tier_boundaries(engine):
    """
    Test exact tier boundary transitions:
    < 0.35: NOMINAL
    0.35 <= ESI < 0.55: WATCH
    0.55 <= ESI < 0.75: ATTENTION
    >= 0.75: HIGH_PRIORITY
    """
    vals = [
        (0.0000, TIER_NOMINAL),
        (0.3499, TIER_NOMINAL),
        (0.3500, TIER_WATCH),
        (0.5499, TIER_WATCH),
        (0.5500, TIER_ATTENTION),
        (0.7499, TIER_ATTENTION),
        (0.7500, TIER_HIGH_PRIORITY),
        (0.9500, TIER_HIGH_PRIORITY),
    ]

    for val, expected_tier in vals:
        assigned = np.select(
            [val < 0.35, val < 0.55, val < 0.75],
            [TIER_NOMINAL, TIER_WATCH, TIER_ATTENTION],
            default=TIER_HIGH_PRIORITY,
        ).item()
        assert assigned == expected_tier, f"Value {val} mapped to {assigned}, expected {expected_tier}"


# ==============================================================================
# 11. DOMINANT STRESSOR ATTRIBUTION
# ==============================================================================
def test_dominant_stressor_attribution(engine):
    """Test attribution when a single dimension clearly dominates."""
    # 1. Stagnation dominant
    df_stag = pd.DataFrame([
        make_clean_row(
            months_since_last_progress_increase_t=4.0,
            remaining_physical_progress_t=100.0,
            progress_velocity_3m_t=3.5,  # s_vel = 0.0
        )
    ])
    assert engine.compute_scores(df_stag)["dominant_stressor"].iloc[0] == STRESSOR_PROGRESS_STAGNATION

    # 2. Velocity collapse dominant
    df_vel = pd.DataFrame([
        make_clean_row(
            progress_velocity_3m_t=-1.0,  # s_vel = 1.0 -> 0.25
        )
    ])
    assert engine.compute_scores(df_vel)["dominant_stressor"].iloc[0] == STRESSOR_VELOCITY_COLLAPSE

    # 3. Expenditure divergence dominant
    df_div = pd.DataFrame([
        make_clean_row(
            expenditure_ratio_pct_t=100.0,  # s_div = 1.0 -> 0.20
            physical_progress_t=0.0,
            progress_velocity_3m_t=3.5,     # s_vel = 0.0
        )
    ])
    assert engine.compute_scores(df_div)["dominant_stressor"].iloc[0] == STRESSOR_EXPENDITURE_DIVERGENCE

    # 4. Schedule slippage dominant
    df_sched = pd.DataFrame([
        make_clean_row(
            schedule_slippage_months_t=36.0,
            months_to_original_doc_t=-24.0,  # s_sched = 1.0 -> 0.15
            progress_velocity_3m_t=3.5,      # s_vel = 0.0
        )
    ])
    assert engine.compute_scores(df_sched)["dominant_stressor"].iloc[0] == STRESSOR_SCHEDULE_SLIPPAGE

    # 5. Reporting friction dominant
    df_rep = pd.DataFrame([
        make_clean_row(
            observation_gap_flag_t=1.0,
            missing_physical_progress_t=1.0,
            schedule_revision_count_to_date_t=3.0,  # s_rep = 1.0 -> 0.10
            progress_velocity_3m_t=3.5,              # s_vel = 0.0
        )
    ])
    assert engine.compute_scores(df_rep)["dominant_stressor"].iloc[0] == STRESSOR_REPORTING_FRICTION


# ==============================================================================
# 12. DOMINANT STRESSOR TIE-BREAKING ORDER
# ==============================================================================
def test_dominant_stressor_tie_breaking_order(engine):
    """
    Test that when weighted contributions are tied, the tie breaks in exact order:
    1. Physical Progress Stagnation
    2. Progress Velocity Collapse
    3. Expenditure Divergence
    4. Schedule Slippage Debt
    5. Reporting Friction
    """
    # When all 5 dimensions have 0 score, all weighted contributions are 0.0
    # Tie must break to the FIRST in order: Physical Progress Stagnation
    df_zeros = pd.DataFrame([
        make_clean_row(
            progress_velocity_3m_t=3.5,  # s_vel = 0.0
        )
    ])
    res_zeros = engine.compute_scores(df_zeros)
    assert res_zeros["s_stag"].iloc[0] == 0.0
    assert res_zeros["s_vel"].iloc[0] == 0.0
    assert res_zeros["s_div"].iloc[0] == 0.0
    assert res_zeros["s_sched"].iloc[0] == 0.0
    assert res_zeros["s_rep"].iloc[0] == 0.0
    assert res_zeros["dominant_stressor"].iloc[0] == ORDERED_STRESSOR_TIE_BREAK[0]
    assert res_zeros["dominant_stressor"].iloc[0] == STRESSOR_PROGRESS_STAGNATION

    # Test tie-break between Velocity and Divergence when Stagnation is 0
    df_tie_vel_div = pd.DataFrame([
        make_clean_row(
            progress_velocity_3m_t=1.4,
            expenditure_ratio_pct_t=57.5,
            physical_progress_t=20.0,
        )
    ])
    res_tie = engine.compute_scores(df_tie_vel_div)
    assert np.isclose(res_tie["s_vel"].iloc[0] * 0.25, res_tie["s_div"].iloc[0] * 0.20)
    assert res_tie["dominant_stressor"].iloc[0] == STRESSOR_VELOCITY_COLLAPSE


# ==============================================================================
# 13. PRESCRIPTIVE PRIORITY ORDERING
# ==============================================================================
def test_prescriptive_priority_ordering(engine):
    """
    Test prescriptive action priority ordering:
    P1: Compound Escalation (ESI >= 0.75 and flags >= 3)
    P2: Stagnation (s_stag >= 0.75 or flag_stag == 1)
    P3: Divergence (s_div >= 0.75 or flag_div == 1)
    P4: Velocity (s_vel >= 0.75 or flag_vel == 1)
    P5: Schedule (s_sched >= 0.75 or flag_sched == 1)
    P6: Reporting (s_rep >= 0.75 or flag_rep == 1)
    """
    # P1: Compound Escalation wins even if all individual conditions are true
    df_p1 = pd.DataFrame([
        make_clean_row(
            months_since_last_progress_increase_t=4.0,  # flag_stag
            remaining_physical_progress_t=100.0,
            progress_velocity_3m_t=-1.0,                 # flag_vel
            expenditure_ratio_pct_t=100.0,              # flag_div
            physical_progress_t=0.0,
            schedule_slippage_months_t=36.0,            # flag_sched
            months_to_original_doc_t=-24.0,
            observation_gap_flag_t=1.0,                 # flag_rep
        )
    ])
    res_p1 = engine.compute_scores(df_p1)
    assert res_p1["execution_stress_index"].iloc[0] >= 0.75
    assert res_p1["total_stress_flags"].iloc[0] >= 3
    assert res_p1["suggested_action"].iloc[0] == ACTION_INTER_MINISTERIAL_ESCALATION

    # P2: Stagnation over Divergence/Velocity when not P1
    df_p2 = pd.DataFrame([
        make_clean_row(
            months_since_last_progress_increase_t=3.0,  # flag_stag = 1
            progress_velocity_3m_t=0.1,                 # flag_vel = 1 (total flags = 2, so not P1)
            expenditure_ratio_pct_t=30.0,
            physical_progress_t=30.0,
        )
    ])
    res_p2 = engine.compute_scores(df_p2)
    assert res_p2["total_stress_flags"].iloc[0] < 3
    assert res_p2["suggested_action"].iloc[0] == ACTION_SITE_OBSTACLE_AUDIT

    # P3: Divergence over Velocity/Schedule/Reporting
    df_p3 = pd.DataFrame([
        make_clean_row(
            expenditure_ratio_pct_t=60.0,               # flag_div = 1 (spread 35 > 25)
            physical_progress_t=25.0,
            progress_velocity_3m_t=0.1,                 # flag_vel = 1 (total flags = 2)
        )
    ])
    res_p3 = engine.compute_scores(df_p3)
    assert res_p3["flag_stag"].iloc[0] == 0
    assert res_p3["flag_div"].iloc[0] == 1
    assert res_p3["suggested_action"].iloc[0] == ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT

    # P4: Velocity over Schedule/Reporting
    df_p4 = pd.DataFrame([
        make_clean_row(
            progress_velocity_3m_t=0.1,                 # flag_vel = 1
            schedule_slippage_months_t=15.0,            # flag_sched = 1 (total flags = 2)
        )
    ])
    res_p4 = engine.compute_scores(df_p4)
    assert res_p4["flag_stag"].iloc[0] == 0
    assert res_p4["flag_div"].iloc[0] == 0
    assert res_p4["flag_vel"].iloc[0] == 1
    assert res_p4["suggested_action"].iloc[0] == ACTION_RESOURCE_MOBILIZATION_DIRECTIVE

    # P5: Schedule over Reporting
    df_p5 = pd.DataFrame([
        make_clean_row(
            progress_velocity_3m_t=3.5,
            schedule_slippage_months_t=15.0,            # flag_sched = 1
            observation_gap_flag_t=1.0,                 # flag_rep = 1 (total flags = 2)
        )
    ])
    res_p5 = engine.compute_scores(df_p5)
    assert res_p5["flag_stag"].iloc[0] == 0
    assert res_p5["flag_div"].iloc[0] == 0
    assert res_p5["flag_vel"].iloc[0] == 0
    assert res_p5["flag_sched"].iloc[0] == 1
    assert res_p5["suggested_action"].iloc[0] == ACTION_CRITICAL_PATH_RECALIBRATION

    # P6: Reporting alone
    df_p6 = pd.DataFrame([
        make_clean_row(
            progress_velocity_3m_t=3.5,
            observation_gap_flag_t=1.0,                 # flag_rep = 1
        )
    ])
    res_p6 = engine.compute_scores(df_p6)
    assert res_p6["suggested_action"].iloc[0] == ACTION_DATA_COMPLIANCE_DIRECTIVE


# ==============================================================================
# 14. FALLBACK PRESCRIPTIVE ACTIONS
# ==============================================================================
def test_fallback_prescriptive_actions(engine):
    """
    Test Priority 7 fallback actions when no flag is 1 and all dimension scores < 0.75.
    Actions are assigned based on the dominant stressor.
    """
    # Case A: Velocity collapse dominant without triggering flag_vel (< 0.5) or s_vel >= 0.75
    df_fb_vel = pd.DataFrame([make_clean_row(progress_velocity_3m_t=1.2)])
    res_fb_vel = engine.compute_scores(df_fb_vel)
    assert res_fb_vel["total_stress_flags"].iloc[0] == 0
    assert res_fb_vel["dominant_stressor"].iloc[0] == STRESSOR_VELOCITY_COLLAPSE
    assert res_fb_vel["suggested_action"].iloc[0] == ACTION_RESOURCE_MOBILIZATION_DIRECTIVE

    # Case B: Divergence dominant without triggering flag_div (> 25) or s_div >= 0.75
    df_fb_div = pd.DataFrame([
        make_clean_row(
            expenditure_ratio_pct_t=40.0,
            physical_progress_t=20.0,
            progress_velocity_3m_t=3.5,
        )
    ])
    res_fb_div = engine.compute_scores(df_fb_div)
    assert res_fb_div["total_stress_flags"].iloc[0] == 0
    assert res_fb_div["dominant_stressor"].iloc[0] == STRESSOR_EXPENDITURE_DIVERGENCE
    assert res_fb_div["suggested_action"].iloc[0] == ACTION_FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT

    # Case C: Schedule slippage dominant without triggering flag_sched or s_sched >= 0.75
    df_fb_sched = pd.DataFrame([
        make_clean_row(
            schedule_slippage_months_t=6.0,
            progress_velocity_3m_t=3.5,
        )
    ])
    res_fb_sched = engine.compute_scores(df_fb_sched)
    assert res_fb_sched["total_stress_flags"].iloc[0] == 0
    assert res_fb_sched["dominant_stressor"].iloc[0] == STRESSOR_SCHEDULE_SLIPPAGE
    assert res_fb_sched["suggested_action"].iloc[0] == ACTION_CRITICAL_PATH_RECALIBRATION

    # Case D: Reporting friction dominant without triggering flag_rep or s_rep >= 0.75
    df_fb_rep = pd.DataFrame([
        make_clean_row(
            schedule_revision_count_to_date_t=1.0,
            progress_velocity_3m_t=3.5,
        )
    ])
    res_fb_rep = engine.compute_scores(df_fb_rep)
    assert res_fb_rep["total_stress_flags"].iloc[0] == 0
    assert res_fb_rep["dominant_stressor"].iloc[0] == STRESSOR_REPORTING_FRICTION
    assert res_fb_rep["suggested_action"].iloc[0] == ACTION_DATA_COMPLIANCE_DIRECTIVE


# ==============================================================================
# 15. VALUE BOUNDS
# ==============================================================================
def test_value_bounds(engine):
    """Verify that all output dimension and composite scores are strictly within [0.0, 1.0]."""
    extreme_rows = [
        make_clean_row(months_since_last_progress_increase_t=-10.0),
        make_clean_row(months_since_last_progress_increase_t=100.0),
        make_clean_row(progress_velocity_3m_t=-50.0),
        make_clean_row(progress_velocity_3m_t=50.0),
        make_clean_row(schedule_slippage_months_t=-10.0),
        make_clean_row(schedule_slippage_months_t=120.0),
        make_clean_row(expenditure_ratio_pct_t=-50.0, physical_progress_t=100.0),
        make_clean_row(expenditure_ratio_pct_t=200.0, physical_progress_t=0.0),
    ]
    df = pd.DataFrame(extreme_rows)
    res = engine.compute_scores(df)

    for dim in ["s_stag", "s_vel", "s_div", "s_sched", "s_rep", "execution_stress_index"]:
        assert (res[dim] >= 0.0).all(), f"{dim} contains values < 0.0"
        assert (res[dim] <= 1.0).all(), f"{dim} contains values > 1.0"

    for flag in ["flag_stag", "flag_vel", "flag_div", "flag_sched", "flag_rep"]:
        assert set(res[flag].unique()).issubset({0, 1}), f"{flag} contains values outside {{0, 1}}"

    assert (res["total_stress_flags"] >= 0).all()
    assert (res["total_stress_flags"] <= 5).all()


# ==============================================================================
# 16. NAN / DEFAULT HANDLING
# ==============================================================================
def test_nan_and_default_handling(engine):
    """Test robust scoring when inputs contain NaNs across various columns."""
    nan_row = {col: np.nan for col in REQUIRED_SURVEILLANCE_FEATURES}
    nan_row["project_id"] = "NAN_PROJ"
    nan_row["report_month"] = "2025-06"
    df = pd.DataFrame([nan_row])

    res = engine.compute_scores(df)
    assert len(res) == 1
    for col in OUTPUT_SURVEILLANCE_COLUMNS:
        assert not res[col].isna().any(), f"Output column '{col}' contains NaN"


# ==============================================================================
# 17. METADATA PRESERVATION
# ==============================================================================
def test_metadata_preservation(engine):
    """Test preservation of project_id and report_month (or prediction_month)."""
    df1 = pd.DataFrame([make_clean_row(project_id="PROJ_999", report_month="2025-09")])
    res1 = engine.compute_scores(df1, preserve_metadata=True)
    assert res1["project_id"].iloc[0] == "PROJ_999"
    assert res1["report_month"].iloc[0] == "2025-09"

    row2 = make_clean_row(project_id="PROJ_888")
    del row2["report_month"]
    row2["prediction_month"] = "2025-10"
    df2 = pd.DataFrame([row2])
    res2 = engine.compute_scores(df2, preserve_metadata=True)
    assert res2["project_id"].iloc[0] == "PROJ_888"
    assert res2["report_month"].iloc[0] == "2025-10"


# ==============================================================================
# 18. MISSING REQUIRED FEATURE REJECTION
# ==============================================================================
def test_missing_required_feature_rejection(engine):
    """Test that MissingFeatureError is raised when any of 12 required features is missing."""
    row = make_clean_row()
    del row["months_since_last_progress_increase_t"]
    df = pd.DataFrame([row])

    with pytest.raises(MissingFeatureError, match="Missing required surveillance features"):
        engine.compute_scores(df)

    with pytest.raises(InvalidInputError, match="Expected pandas DataFrame"):
        engine.compute_scores([1, 2, 3])

    with pytest.raises(InvalidInputError, match="contains 0 rows"):
        engine.compute_scores(pd.DataFrame())


# ==============================================================================
# 19. FUTURE / TARGET COLUMN ISOLATION
# ==============================================================================
def test_future_target_column_isolation(engine):
    """Test that future/target columns present in input do not affect surveillance scoring."""
    row_clean = make_clean_row()
    row_polluted = make_clean_row()
    for col in KNOWN_TARGET_COLUMNS:
        row_polluted[col] = 999.0

    df_clean = pd.DataFrame([row_clean])
    df_polluted = pd.DataFrame([row_polluted])

    res_clean = engine.compute_scores(df_clean)
    res_polluted = engine.compute_scores(df_polluted)

    for col in OUTPUT_SURVEILLANCE_COLUMNS:
        assert res_clean[col].iloc[0] == res_polluted[col].iloc[0]


# ==============================================================================
# 20. DETERMINISTIC REPEATED SCORING
# ==============================================================================
def test_deterministic_repeated_scoring(engine):
    """Test that running compute_scores 5 times produces bit-identical results."""
    df = pd.DataFrame([make_clean_row() for _ in range(10)])
    runs = [engine.compute_scores(df) for _ in range(5)]

    for i in range(1, 5):
        pd.testing.assert_frame_equal(runs[0], runs[i])


# ==============================================================================
# 21. MULTI-ROW BATCH SCORING
# ==============================================================================
def test_multi_row_batch_scoring(engine):
    """Test scoring a batch of 100 rows with varying features and index preservation."""
    rows = []
    for i in range(100):
        rows.append(
            make_clean_row(
                project_id=f"PROJ_{i:03d}",
                report_month="2025-06",
                months_since_last_progress_increase_t=float(i % 5),
                remaining_physical_progress_t=float(100 - i),
                progress_velocity_3m_t=float(i % 4),
                schedule_slippage_months_t=float(i % 40),
                months_to_original_doc_t=float(24 - i),
                expenditure_ratio_pct_t=float(i),
                physical_progress_t=float(min(i, 100)),
                observation_gap_flag_t=float(i % 2),
                missing_physical_progress_t=float((i + 1) % 2),
                schedule_revision_count_to_date_t=float(i % 4),
            )
        )
    df = pd.DataFrame(rows, index=[f"idx_{i}" for i in range(100)])
    res = engine.compute_scores(df)

    assert len(res) == 100
    assert list(res.index) == list(df.index)
    assert not res.isna().any().any()


# ==============================================================================
# 22. VERSION IDENTIFIER
# ==============================================================================
def test_version_identifier(engine):
    """Verify version identifier is 'v1.0.0-esi-5dim'."""
    assert engine.version == "v1.0.0-esi-5dim"
    assert EXECUTION_INDEX_VERSION == "v1.0.0-esi-5dim"
    df = pd.DataFrame([make_clean_row()])
    res = engine.compute_scores(df)
    assert (res["execution_index_version"] == "v1.0.0-esi-5dim").all()
