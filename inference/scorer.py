"""
Production Scoring Engine Bridge (Pillar 1 & Pillar 2)
SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform

Executes inference on frozen production models and deterministic ESI calculation:
  Pillar 1: Platt-Calibrated RF_02, Cost Overrun RF Balanced, Schedule Revision LogReg, Candidate B synthesis
  Pillar 2: Deterministic 5-Dimension Operational Execution-Stress Index (ESI)
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def assign_risk_band(score: float) -> str:
    """Assigns predictive risk band based on Candidate B holdout calibration."""
    if score < 0.30:
        return 'LOW'
    elif score < 0.60:
        return 'MODERATE'
    elif score < 0.80:
        return 'HIGH'
    else:
        return 'VERY_HIGH'


def assign_esi_tier(score: float) -> str:
    """Assigns ESI operational early warning tier."""
    if score < 0.35:
        return 'NOMINAL'
    elif score < 0.55:
        return 'WATCH'
    elif score < 0.75:
        return 'ATTENTION'
    else:
        return 'HIGH_PRIORITY'


def compute_execution_stress_index(esi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes deterministic 5-dimension ESI directly from the exact 12 ESI input features.
    Matches formula in scripts/execution_risk/03_execution_stress_index.py.
    """
    # Dimension 1: S_stag (30% weight)
    months_stag = esi_df['months_since_last_progress_increase_t'].fillna(0).clip(lower=0)
    stag_duration_score = np.clip(months_stag / 4.0, 0.0, 1.0)
    rem_prog = esi_df['remaining_physical_progress_t'].fillna(50.0).clip(lower=0, upper=100) / 100.0
    s_stag = np.clip(0.7 * stag_duration_score + 0.3 * (stag_duration_score * rem_prog), 0.0, 1.0)
    flag_stag = ((months_stag >= 3) | (esi_df['stagnant_3m_t'] == 1.0)).astype(int)

    # Dimension 2: S_vel (25% weight)
    vel_3m = esi_df['progress_velocity_3m_t']
    vel_eff = vel_3m.combine_first(esi_df['progress_change_1m_t']).fillna(0.0)
    s_vel = np.where(
        vel_eff <= 0.0, 1.0,
        np.where(vel_eff < 1.0, 0.75 - 0.25 * (vel_eff / 1.0),
        np.where(vel_eff < 3.0, 0.50 - 0.50 * ((vel_eff - 1.0) / 2.0), 0.0))
    )
    s_vel = np.clip(s_vel, 0.0, 1.0)
    flag_vel = (vel_eff < 0.5).astype(int)

    # Dimension 3: S_sched (15% weight)
    slippage = esi_df['schedule_slippage_months_t'].fillna(0.0).clip(lower=0)
    slippage_score = np.clip(slippage / 36.0, 0.0, 1.0)
    months_to_orig = esi_df['months_to_original_doc_t'].fillna(12.0)
    is_overdue = (months_to_orig < 0).astype(float)
    overdue_magnitude = np.clip((-months_to_orig) / 24.0, 0.0, 1.0) * is_overdue
    s_sched = np.clip(0.6 * slippage_score + 0.4 * overdue_magnitude, 0.0, 1.0)
    flag_sched = ((slippage >= 12.0) | (months_to_orig < -6.0)).astype(int)

    # Dimension 4: S_div (20% weight)
    exp_ratio = esi_df['expenditure_ratio_pct_t'].fillna(0.0).clip(lower=0)
    phys_prog = esi_df['physical_progress_t'].fillna(0.0).clip(lower=0, upper=100)
    divergence_spread = exp_ratio - phys_prog
    s_div = np.where(
        divergence_spread <= 0.0, 0.0,
        np.clip(divergence_spread / 75.0, 0.0, 1.0)
    )
    flag_div = (divergence_spread > 25.0).astype(int)

    # Dimension 5: S_rep (10% weight)
    obs_gap = esi_df['observation_gap_flag_t'].fillna(0).astype(float)
    miss_prog = esi_df['missing_physical_progress_t'].fillna(0).astype(float)
    rev_count = esi_df['schedule_revision_count_to_date_t'].fillna(0).clip(lower=0)
    rev_stress = np.clip(rev_count / 3.0, 0.0, 1.0)
    s_rep = np.clip(0.4 * obs_gap + 0.3 * miss_prog + 0.3 * rev_stress, 0.0, 1.0)
    flag_rep = ((obs_gap == 1.0) | (miss_prog == 1.0) | (rev_count >= 2)).astype(int)

    # Total active stress flags
    total_stress_flags = flag_stag + flag_vel + flag_sched + flag_div + flag_rep

    # Composite Domain-Calibrated ESI (0.30/0.25/0.20/0.15/0.10)
    esi = (
        0.30 * s_stag +
        0.25 * s_vel +
        0.20 * s_div +
        0.15 * s_sched +
        0.10 * s_rep
    )

    esi_results = pd.DataFrame({
        's_stag': np.round(s_stag, 4),
        's_vel': np.round(s_vel, 4),
        's_sched': np.round(s_sched, 4),
        's_div': np.round(s_div, 4),
        's_rep': np.round(s_rep, 4),
        'flag_stag': flag_stag,
        'flag_vel': flag_vel,
        'flag_sched': flag_sched,
        'flag_div': flag_div,
        'flag_rep': flag_rep,
        'total_stress_flags': total_stress_flags,
        'execution_stress_index': np.round(esi, 4)
    })

    esi_results['esi_tier'] = esi_results['execution_stress_index'].apply(assign_esi_tier)

    # Dominant Stressor
    def get_dominant_stressor(row):
        contribs = {
            'Physical Progress Stagnation': 0.30 * row['s_stag'],
            'Progress Velocity Collapse': 0.25 * row['s_vel'],
            'Expenditure Divergence': 0.20 * row['s_div'],
            'Schedule Slippage Debt': 0.15 * row['s_sched'],
            'Reporting Friction': 0.10 * row['s_rep']
        }
        return max(contribs, key=contribs.get)

    esi_results['dominant_stressor'] = esi_results.apply(get_dominant_stressor, axis=1)

    # Prescriptive Suggested Action
    def get_suggested_action(row):
        if row['execution_stress_index'] >= 0.75 and row['total_stress_flags'] >= 3:
            return 'INTER_MINISTERIAL_COMMITTEE_ESCALATION'
        elif row['s_stag'] >= 0.75 or row['flag_stag'] == 1:
            return 'SITE_OBSTACLE_AUDIT'
        elif row['flag_div'] == 1:
            return 'FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT'
        elif row['flag_vel'] == 1:
            return 'RESOURCE_MOBILIZATION_DIRECTIVE'
        elif row['flag_sched'] == 1:
            return 'CRITICAL_PATH_RECALIBRATION'
        elif row['flag_rep'] == 1:
            return 'DATA_COMPLIANCE_DIRECTIVE'
        else:
            return 'RESOURCE_MOBILIZATION_DIRECTIVE'

    esi_results['suggested_action'] = esi_results.apply(get_suggested_action, axis=1)
    return esi_results


class ProductionScorer:
    """
    Loads frozen production models and executes scoring for Pillar 1 (ML) and Pillar 2 (ESI).
    """

    def __init__(self, models_base_dir: str = None):
        if models_base_dir is None:
            models_base_dir = os.path.join(BASE_DIR, "ml")

        primary_path = os.path.join(models_base_dir, "calibration_final", "models", "rf02_calibrated.pkl")
        cost_path = os.path.join(models_base_dir, "secondary_targets", "selected_models", "cost_overrun_state_3m", "model.pkl")
        srev_path = os.path.join(models_base_dir, "secondary_targets", "selected_models", "schedule_revision_3m", "model.pkl")

        if not os.path.exists(primary_path):
            raise FileNotFoundError(f"Primary model not found at {primary_path}")
        if not os.path.exists(cost_path):
            raise FileNotFoundError(f"Cost overrun model not found at {cost_path}")
        if not os.path.exists(srev_path):
            raise FileNotFoundError(f"Schedule revision model not found at {srev_path}")

        self.primary_pipe = joblib.load(primary_path)
        self.cost_pipe = joblib.load(cost_path)
        self.srev_pipe = joblib.load(srev_path)

    def score(
        self,
        features_df: pd.DataFrame,
        esi_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Runs dual-pillar inference across extracted features.

        Returns:
            tuple (ml_scores_df, esi_scores_df)
        """
        # 1. Pillar 1: Predictive ML Risk Scoring
        all_cols = list(features_df.columns)

        # Primary Schedule Delay (Sigmoid calibrated RF_02)
        X_sched = self.primary_pipe['preprocessor'].transform(features_df[all_cols])
        p_raw = self.primary_pipe['classifier'].predict_proba(X_sched)[:, 1]
        eps = 1e-6
        sched_logits = np.log(np.clip(p_raw, eps, 1 - eps) / np.clip(1 - p_raw, eps, 1 - eps)).reshape(-1, 1)
        schedule_delay_risk = self.primary_pipe['calibrator'].predict_proba(sched_logits)[:, 1]

        # Secondary Cost Overrun (Balanced Random Forest)
        X_cost = self.cost_pipe['preprocessor'].transform(features_df[all_cols])
        cost_overrun_risk = self.cost_pipe['classifier'].predict_proba(X_cost)[:, 1]

        # Secondary Schedule Revision (Logistic Regression)
        X_srev = self.srev_pipe['preprocessor'].transform(features_df[all_cols])
        schedule_revision_risk = self.srev_pipe['classifier'].predict_proba(X_srev)[:, 1]

        # Candidate B Evidence-Weighted Integrated Risk Index (0.50/0.35/0.15)
        sched_contrib = 0.50 * schedule_delay_risk
        cost_contrib = 0.35 * cost_overrun_risk
        srev_contrib = 0.15 * schedule_revision_risk
        integrated_risk = sched_contrib + cost_contrib + srev_contrib

        ml_scores = pd.DataFrame({
            'schedule_delay_risk': np.round(schedule_delay_risk, 4),
            'cost_overrun_risk': np.round(cost_overrun_risk, 4),
            'schedule_revision_risk': np.round(schedule_revision_risk, 4),
            'selected_integrated_risk': np.round(integrated_risk, 4),
            'schedule_contribution': np.round(sched_contrib, 4),
            'cost_contribution': np.round(cost_contrib, 4),
            'schedule_revision_contribution': np.round(srev_contrib, 4)
        })

        ml_scores['risk_band'] = ml_scores['selected_integrated_risk'].apply(assign_risk_band)

        def get_dominant_component(row):
            contribs = {
                'Schedule Delay': row['schedule_contribution'],
                'Cost Overrun': row['cost_contribution'],
                'Schedule Revision': row['schedule_revision_contribution']
            }
            return max(contribs, key=contribs.get)

        ml_scores['dominant_component'] = ml_scores.apply(get_dominant_component, axis=1)

        total_contrib = ml_scores['selected_integrated_risk']
        ml_scores['schedule_contrib_pct'] = np.where(total_contrib > 0, np.round(ml_scores['schedule_contribution'] / total_contrib * 100, 2), 0.0)
        ml_scores['cost_contrib_pct'] = np.where(total_contrib > 0, np.round(ml_scores['cost_contribution'] / total_contrib * 100, 2), 0.0)
        ml_scores['schedule_rev_contrib_pct'] = np.where(total_contrib > 0, np.round(ml_scores['schedule_revision_contribution'] / total_contrib * 100, 2), 0.0)

        # 2. Pillar 2: Operational Execution-Stress Index (ESI) Scoring
        esi_scores = compute_execution_stress_index(esi_df)

        return ml_scores, esi_scores
