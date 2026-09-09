"""
Point-in-Time Feature Engineering Engine (Production & Batch)
SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform

Implements strict point-in-time feature calculations strictly as of report_month (t).
Produces:
  1. Exact 75 production ML features (71 Numerical + 4 Categorical)
  2. Exact 12 ESI operational surveillance input features
"""

import os
import re
import numpy as np
import pandas as pd

# ==============================================================================
# EXACT PRODUCTION FEATURE UNIVERSE DEFINITIONS (SOURCE OF TRUTH)
# ==============================================================================

CATEGORICAL_FEATURE_NAMES = [
    'project_size_category',
    'current_schedule_status_as_of_t',
    'reporting_structure_version_t',
    'table_source_t'
]

NUMERICAL_FEATURE_NAMES = [
    # Static & Baseline (4)
    'original_cost_crore',
    'project_age_months_t',
    'planned_duration_months',
    'original_cost_log',
    
    # Current Snapshot (9)
    'physical_progress_t',
    'cumulative_expenditure_t',
    'revised_cost_t',
    'cost_escalation_pct_t',
    'expenditure_ratio_pct_t',
    'remaining_physical_progress_t',
    'schedule_slippage_months_t',
    'months_to_original_doc_t',
    'months_to_revised_doc_t',
    
    # Progress Dynamics (13)
    'physical_progress_lag1',
    'physical_progress_lag2',
    'physical_progress_lag3',
    'progress_change_1m_t',
    'progress_change_2m_t',
    'progress_change_3m_t',
    'progress_velocity_1m_t',
    'progress_velocity_3m_t',
    'progress_velocity_6m_t',
    'max_progress_to_date_t',
    'min_progress_to_date_t',
    'average_progress_to_date_t',
    'progress_std_to_date_t',
    
    # Expenditure Dynamics (10)
    'cumulative_expenditure_lag1',
    'cumulative_expenditure_lag3',
    'monthly_expenditure_delta_t',
    'expenditure_change_1m_t',
    'expenditure_change_3m_t',
    'expenditure_velocity_3m_t',
    'expenditure_velocity_6m_t',
    'avg_monthly_expenditure_to_date_t',
    'expenditure_growth_rate_t',
    'negative_expenditure_delta_flag_t',
    
    # Stagnation Dynamics (6)
    'stagnant_2m_t',
    'stagnant_3m_t',
    'stagnant_6m_t',
    'months_since_last_progress_increase_t',
    'longest_stagnation_to_date_t',
    'progress_change_last_3m_t',
    
    # Cost Evolution (5)
    'has_cost_revision_t',
    'cost_revision_count_to_date_t',
    'months_since_last_cost_revision_t',
    'largest_cost_revision_pct_to_date_t',
    'cost_reduction_pct_as_of_t',
    
    # Schedule Evolution (3)
    'has_revised_schedule_as_of_t',
    'schedule_revision_count_to_date_t',
    'months_since_last_schedule_revision_t',
    
    # Observation History (5)
    'months_observed_to_date_t',
    'months_since_first_observed_t',
    'observation_coverage_ratio_t',
    'consecutive_observation_count_t',
    'months_since_last_observation_t',
    
    # Data Health & Quality Flags (5)
    'missing_physical_progress_t',
    'missing_expenditure_t',
    'missing_revised_cost_t',
    'missing_revised_doc_t',
    'observation_gap_flag_t',
    
    # State & Agency Context Aggregates (10)
    'state_active_project_count_t',
    'state_mean_progress_t',
    'state_median_progress_t',
    'state_mean_cost_t',
    'state_mean_expenditure_ratio_t',
    'agency_active_project_count_t',
    'agency_mean_progress_t',
    'agency_median_progress_t',
    'agency_mean_cost_t',
    'agency_mean_expenditure_ratio_t',
    
    # Cohort Context (1)
    'focused_cohort_indicator_t'
]

# Exact 75 ML Features Contract (71 Numerical + 4 Categorical)
PRODUCTION_75_FEATURES = NUMERICAL_FEATURE_NAMES + CATEGORICAL_FEATURE_NAMES

# Excluded Date Strings (Non-features, strictly excluded from ML matrix X)
RAW_DATE_STRINGS = [
    'approval_start_date',
    'original_completion_date',
    'revised_doc_t',
    'first_observed_month'
]

# Exact 12 ESI Input Features Contract (Required by ExecutionSurveillanceEngine)
ESI_12_INPUT_FEATURES = [
    'months_since_last_progress_increase_t',
    'stagnant_3m_t',
    'remaining_physical_progress_t',
    'progress_velocity_3m_t',
    'progress_change_1m_t',
    'schedule_slippage_months_t',
    'months_to_original_doc_t',
    'expenditure_ratio_pct_t',
    'physical_progress_t',
    'observation_gap_flag_t',
    'missing_physical_progress_t',
    'schedule_revision_count_to_date_t'
]

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def clean_str_date(val):
    """Normalizes date string to YYYY-MM prefix or None."""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if s == '' or s.lower() in ['nan', 'nat', 'none', 'null', '-', '--', 'nil']:
        return None
    return s[:7]


def month_diff(ym1, ym2):
    """Computes (ym1 - ym2) in calendar months. Returns NaN if invalid."""
    s1 = clean_str_date(ym1)
    s2 = clean_str_date(ym2)
    if s1 is None or s2 is None:
        return np.nan
    try:
        y1, m1 = map(int, s1.split('-'))
        y2, m2 = map(int, s2.split('-'))
        return (y1 - y2) * 12 + (m1 - m2)
    except Exception:
        return np.nan


def clean_state(st):
    """Standardizes state name strings."""
    if pd.isna(st) or st is None or str(st).strip() == '':
        return 'UNKNOWN'
    s = str(st).strip().upper()
    tokens = s.split()
    clean_tokens = [t for t in tokens if not any(c.isdigit() for c in t) and t not in [',', '.']]
    cleaned = ' '.join(clean_tokens)
    return cleaned if cleaned else s


# ==============================================================================
# CORE POINT-IN-TIME FEATURE GENERATION
# ==============================================================================

def compute_point_in_time_features_for_month(
    current_records_df: pd.DataFrame,
    historical_records_df: pd.DataFrame = None,
    as_of_month: str = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Computes exact 75 ML features and exact 12 ESI inputs for all projects present in current_records_df.

    Parameters:
        current_records_df: DataFrame of project records observed at report_month (as_of_month).
        historical_records_df: Optional DataFrame of prior project snapshots (report_month < as_of_month).
        as_of_month: The target reporting month epoch in 'YYYY-MM' format.

    Returns:
        tuple (features_df, esi_df, metadata_df):
            - features_df: DataFrame with exactly 75 production ML features
            - esi_df: DataFrame with exactly 12 ESI inputs
            - metadata_df: DataFrame with project identity and timing columns
    """
    if current_records_df is None or len(current_records_df) == 0:
        raise ValueError("current_records_df cannot be empty.")

    curr_df = current_records_df.copy()

    # Determine or validate as_of_month
    if as_of_month is None:
        if 'report_month' in curr_df.columns:
            months = curr_df['report_month'].dropna().unique()
            if len(months) == 1:
                as_of_month = str(months[0])
            else:
                raise ValueError(f"Multiple report months found in current records: {months}. Please specify as_of_month.")
        else:
            raise ValueError("as_of_month must be specified.")

    as_of_month = clean_str_date(as_of_month)
    if as_of_month is None or not re.match(r'^\d{4}-\d{2}$', as_of_month):
        raise ValueError(f"Invalid as_of_month format: {as_of_month}. Expected 'YYYY-MM'.")

    # Enforce report_month on current records
    curr_df['report_month'] = as_of_month

    # Normalize numeric and text columns in current records
    curr_df['original_cost_crore'] = pd.to_numeric(curr_df.get('original_cost_crore'), errors='coerce')
    curr_df['revised_cost_crore'] = pd.to_numeric(curr_df.get('revised_cost_crore'), errors='coerce')
    curr_df['cumulative_expenditure_crore'] = pd.to_numeric(curr_df.get('cumulative_expenditure_crore'), errors='coerce')
    curr_df['physical_progress_percent'] = pd.to_numeric(curr_df.get('physical_progress_percent'), errors='coerce')
    curr_df['clean_state'] = curr_df.get('state', 'UNKNOWN').apply(clean_state)
    curr_df['project_id'] = curr_df['project_id'].astype(str).str.strip()

    # Process historical records
    if historical_records_df is not None and len(historical_records_df) > 0:
        hist_df = historical_records_df.copy()
        hist_df['project_id'] = hist_df['project_id'].astype(str).str.strip()
        hist_df['original_cost_crore'] = pd.to_numeric(hist_df.get('original_cost_crore'), errors='coerce')
        hist_df['revised_cost_crore'] = pd.to_numeric(hist_df.get('revised_cost_crore'), errors='coerce')
        hist_df['cumulative_expenditure_crore'] = pd.to_numeric(hist_df.get('cumulative_expenditure_crore'), errors='coerce')
        hist_df['physical_progress_percent'] = pd.to_numeric(hist_df.get('physical_progress_percent'), errors='coerce')
        hist_df['clean_state'] = hist_df.get('state', 'UNKNOWN').apply(clean_state)

        # STRICT POINT-IN-TIME ENFORCEMENT: Exclude any historical records with report_month >= as_of_month
        # (Current month facts come strictly from curr_df)
        hist_df = hist_df[hist_df['report_month'] < as_of_month].copy()
        
        # Combine historical records and current month snapshot
        combined_panel = pd.concat([hist_df, curr_df], ignore_index=True)
    else:
        combined_panel = curr_df.copy()

    # Sort chronologically
    combined_panel = combined_panel.sort_values(by=['project_id', 'report_month']).reset_index(drop=True)

    # Precompute Context Aggregates for as_of_month (strictly across projects active at as_of_month)
    curr_sub = curr_df.copy()
    curr_sub['exp_ratio'] = curr_sub['cumulative_expenditure_crore'] / curr_sub['revised_cost_crore']

    state_aggs = curr_sub.groupby('clean_state').agg(
        count=('project_id', 'count'),
        mean_prog=('physical_progress_percent', 'mean'),
        median_prog=('physical_progress_percent', 'median'),
        mean_cost=('original_cost_crore', 'mean'),
        mean_exp_ratio=('exp_ratio', 'mean')
    ).to_dict(orient='index')

    agency_aggs = curr_sub.groupby('agency').agg(
        count=('project_id', 'count'),
        mean_prog=('physical_progress_percent', 'mean'),
        median_prog=('physical_progress_percent', 'median'),
        mean_cost=('original_cost_crore', 'mean'),
        mean_exp_ratio=('exp_ratio', 'mean')
    ).to_dict(orient='index')

    # Index project histories by project_id
    panel_by_proj = {}
    for pid, grp in combined_panel.groupby('project_id'):
        panel_by_proj[pid] = grp.sort_values('report_month').reset_index(drop=True)

    # Reporting Structure Cohort Context
    if as_of_month in ['2025-04', '2025-05', '2025-06']:
        struct_ver = 'v1_initial'
        focused_cohort = 0
    elif as_of_month in ['2025-07', '2025-08', '2025-09', '2025-10', '2025-11']:
        struct_ver = 'v2_focused_cohort'
        focused_cohort = 1
    else:
        struct_ver = 'v3_expanded'
        focused_cohort = 0

    feature_rows = []
    metadata_rows = []

    # Iterate through current month projects
    for idx, curr_row in curr_df.iterrows():
        pid = curr_row['project_id']
        t = as_of_month

        proj_hist = panel_by_proj.get(pid)
        if proj_hist is None:
            hist = pd.DataFrame([curr_row])
        else:
            # Enforce strictly <= t
            hist = proj_hist[proj_hist['report_month'] <= t].copy()
            if hist.empty:
                hist = pd.DataFrame([curr_row])

        # -------------------------------------------------------------
        # A. STATIC / BASELINE FEATURES
        # -------------------------------------------------------------
        pname = curr_row.get('project_name', '')
        agency = curr_row.get('agency', 'UNKNOWN')
        state = curr_row.get('clean_state', 'UNKNOWN')
        start_date = clean_str_date(curr_row.get('approval_start_date'))
        orig_doc = clean_str_date(curr_row.get('original_completion_date'))
        orig_cost = curr_row.get('original_cost_crore')

        project_age_months = month_diff(t, start_date)
        planned_duration = month_diff(orig_doc, start_date)
        orig_cost_log = np.log1p(orig_cost) if pd.notnull(orig_cost) and orig_cost >= 0 else np.nan

        if pd.notnull(orig_cost):
            if orig_cost < 150:
                size_cat = 'Small (<150Cr)'
            elif orig_cost < 500:
                size_cat = 'Medium (150-500Cr)'
            elif orig_cost < 1000:
                size_cat = 'Large (500-1000Cr)'
            else:
                size_cat = 'Mega (>1000Cr)'
        else:
            size_cat = 'Unknown'

        # -------------------------------------------------------------
        # B. CURRENT SNAPSHOT FEATURES (As of t)
        # -------------------------------------------------------------
        prog_t = curr_row.get('physical_progress_percent')
        exp_t = curr_row.get('cumulative_expenditure_crore')
        rev_cost_t = curr_row.get('revised_cost_crore')
        rev_doc_t = clean_str_date(curr_row.get('revised_completion_date'))

        cost_escalation_pct_t = ((rev_cost_t - orig_cost) / orig_cost) * 100.0 if pd.notnull(rev_cost_t) and pd.notnull(orig_cost) and orig_cost > 0 else np.nan
        exp_ratio_pct_t = (exp_t / rev_cost_t) * 100.0 if pd.notnull(exp_t) and pd.notnull(rev_cost_t) and rev_cost_t > 0 else np.nan
        remaining_prog_t = (100.0 - prog_t) if pd.notnull(prog_t) else np.nan

        schedule_slippage_t = month_diff(rev_doc_t, orig_doc) if rev_doc_t is not None and orig_doc is not None else np.nan
        months_to_orig_doc_t = month_diff(orig_doc, t)
        months_to_rev_doc_t = month_diff(rev_doc_t, t) if rev_doc_t is not None else np.nan

        # -------------------------------------------------------------
        # C. PROGRESS DYNAMICS (Strictly <= t)
        # -------------------------------------------------------------
        hist_progs = hist['physical_progress_percent'].dropna().values
        hist_months = hist['report_month'].values
        n_hist = len(hist_progs)

        prog_lag1 = hist_progs[-2] if n_hist >= 2 else np.nan
        prog_lag2 = hist_progs[-3] if n_hist >= 3 else np.nan
        prog_lag3 = hist_progs[-4] if n_hist >= 4 else np.nan

        prog_change_1m = (prog_t - prog_lag1) if pd.notnull(prog_t) and pd.notnull(prog_lag1) else np.nan
        prog_change_2m = (prog_t - prog_lag2) if pd.notnull(prog_t) and pd.notnull(prog_lag2) else np.nan
        prog_change_3m = (prog_t - prog_lag3) if pd.notnull(prog_t) and pd.notnull(prog_lag3) else np.nan

        prog_velocity_1m = prog_change_1m
        prog_velocity_3m = (prog_t - prog_lag3) / 3.0 if pd.notnull(prog_t) and pd.notnull(prog_lag3) else np.nan

        prog_lag6 = hist_progs[-7] if n_hist >= 7 else np.nan
        prog_velocity_6m = (prog_t - prog_lag6) / 6.0 if pd.notnull(prog_t) and pd.notnull(prog_lag6) else np.nan

        max_prog_to_date = np.max(hist_progs) if n_hist > 0 else np.nan
        min_prog_to_date = np.min(hist_progs) if n_hist > 0 else np.nan
        avg_prog_to_date = np.mean(hist_progs) if n_hist > 0 else np.nan
        prog_std_to_date = np.std(hist_progs) if n_hist >= 2 else 0.0

        # -------------------------------------------------------------
        # D. EXPENDITURE DYNAMICS (Strictly <= t)
        # -------------------------------------------------------------
        hist_exps = hist['cumulative_expenditure_crore'].dropna().values
        n_exp = len(hist_exps)

        exp_lag1 = hist_exps[-2] if n_exp >= 2 else np.nan
        exp_lag3 = hist_exps[-4] if n_exp >= 4 else np.nan

        monthly_exp_delta = (exp_t - exp_lag1) if pd.notnull(exp_t) and pd.notnull(exp_lag1) else np.nan
        exp_change_1m = monthly_exp_delta
        exp_change_3m = (exp_t - exp_lag3) if pd.notnull(exp_t) and pd.notnull(exp_lag3) else np.nan

        exp_velocity_3m = exp_change_3m / 3.0 if pd.notnull(exp_change_3m) else np.nan
        exp_lag6 = hist_exps[-7] if n_exp >= 7 else np.nan
        exp_velocity_6m = (exp_t - exp_lag6) / 6.0 if pd.notnull(exp_t) and pd.notnull(exp_lag6) else np.nan

        if n_exp >= 2:
            deltas = np.diff(hist_exps)
            avg_monthly_exp_to_date = np.mean(deltas) if len(deltas) > 0 else np.nan
        else:
            avg_monthly_exp_to_date = np.nan

        exp_growth_rate = (monthly_exp_delta / exp_lag1) if pd.notnull(monthly_exp_delta) and pd.notnull(exp_lag1) and exp_lag1 > 0 else np.nan
        neg_exp_delta_flag = 1 if pd.notnull(monthly_exp_delta) and monthly_exp_delta < -0.01 else 0

        # -------------------------------------------------------------
        # E. STAGNATION FEATURES (Strictly <= t)
        # -------------------------------------------------------------
        stagnant_2m = 1 if n_hist >= 2 and pd.notnull(prog_t) and pd.notnull(prog_lag1) and abs(prog_t - prog_lag1) <= 0.001 else (0 if n_hist >= 2 else np.nan)
        stagnant_3m = 1 if n_hist >= 3 and pd.notnull(prog_t) and pd.notnull(prog_lag2) and abs(prog_t - prog_lag2) <= 0.001 else (0 if n_hist >= 3 else np.nan)
        stagnant_6m = 1 if n_hist >= 6 and pd.notnull(prog_t) and pd.notnull(hist_progs[-6]) and abs(prog_t - hist_progs[-6]) <= 0.001 else (0 if n_hist >= 6 else np.nan)

        months_since_prog_inc = 0
        if n_hist >= 2:
            for j in range(len(hist_progs) - 1, 0, -1):
                if hist_progs[j] > hist_progs[j-1] + 0.001:
                    break
                months_since_prog_inc += 1
        else:
            months_since_prog_inc = 0

        longest_stag = 0
        current_stag = 0
        if n_hist >= 2:
            for j in range(1, len(hist_progs)):
                if abs(hist_progs[j] - hist_progs[j-1]) <= 0.001:
                    current_stag += 1
                    if current_stag > longest_stag:
                        longest_stag = current_stag
                else:
                    current_stag = 0
        longest_stagnation_to_date = longest_stag
        progress_change_last_3m = prog_change_3m

        # -------------------------------------------------------------
        # F. COST EVOLUTION FEATURES (Strictly <= t)
        # -------------------------------------------------------------
        has_cost_rev = 1 if pd.notnull(rev_cost_t) and pd.notnull(orig_cost) and abs(rev_cost_t - orig_cost) > 0.01 else 0

        hist_rev_costs = hist['revised_cost_crore'].dropna().unique()
        cost_rev_count_to_date = len(hist_rev_costs) - 1 if len(hist_rev_costs) > 1 else 0

        months_since_cost_rev = 0
        if len(hist) >= 2 and pd.notnull(rev_cost_t):
            for j in range(len(hist) - 1, 0, -1):
                prev_c = hist.iloc[j-1]['revised_cost_crore']
                if pd.notnull(prev_c) and abs(rev_cost_t - prev_c) > 0.01:
                    break
                months_since_cost_rev += 1
        else:
            months_since_cost_rev = 0

        if pd.notnull(orig_cost) and orig_cost > 0:
            hist_escalations = [((rc - orig_cost) / orig_cost) * 100.0 for rc in hist_rev_costs if pd.notnull(rc)]
            largest_cost_rev_pct = max(hist_escalations) if hist_escalations else 0.0
            cost_reduction_pct_t = ((orig_cost - rev_cost_t) / orig_cost) * 100.0 if pd.notnull(rev_cost_t) and rev_cost_t < orig_cost else 0.0
        else:
            largest_cost_rev_pct = np.nan
            cost_reduction_pct_t = np.nan

        # -------------------------------------------------------------
        # G. SCHEDULE EVOLUTION FEATURES (Strictly <= t)
        # -------------------------------------------------------------
        has_rev_schedule = 1 if rev_doc_t is not None else 0
        hist_rev_docs = hist['revised_completion_date'].dropna().unique()
        schedule_rev_count_to_date = len(hist_rev_docs)

        months_since_sched_rev = 0
        if len(hist) >= 2 and rev_doc_t is not None:
            for j in range(len(hist) - 1, 0, -1):
                prev_d = clean_str_date(hist.iloc[j-1]['revised_completion_date'])
                if prev_d is not None and prev_d != rev_doc_t:
                    break
                months_since_sched_rev += 1
        else:
            months_since_sched_rev = 0

        if orig_doc is None:
            sched_status = 'missing_doc'
        elif rev_doc_t is not None and rev_doc_t > orig_doc:
            sched_status = 'delayed_rescheduled'
        elif t > orig_doc and (pd.isna(prog_t) or prog_t < 99.9):
            sched_status = 'past_due_breached'
        else:
            sched_status = 'on_schedule'

        # -------------------------------------------------------------
        # H. OBSERVATION HISTORY & CONTINUITY (Strictly <= t)
        # -------------------------------------------------------------
        months_observed_to_date = len(hist)
        first_observed_m = hist_months[0] if len(hist_months) > 0 else t
        months_since_first_obs = month_diff(t, first_observed_m)
        obs_coverage_ratio = months_observed_to_date / (months_since_first_obs + 1) if pd.notnull(months_since_first_obs) and months_since_first_obs >= 0 else 1.0

        streak = 1
        for j in range(len(hist) - 1, 0, -1):
            m_curr = hist.iloc[j]['report_month']
            m_prev = hist.iloc[j-1]['report_month']
            if month_diff(m_curr, m_prev) == 1:
                streak += 1
            else:
                break
        consecutive_obs_count = streak

        prev_obs_m = hist.iloc[-2]['report_month'] if len(hist) >= 2 else t
        months_since_last_obs = month_diff(t, prev_obs_m)

        # -------------------------------------------------------------
        # I. REPORTING QUALITY & DATA HEALTH (Strictly <= t)
        # -------------------------------------------------------------
        missing_prog_flag = 1 if pd.isna(prog_t) else 0
        missing_exp_flag = 1 if pd.isna(exp_t) else 0
        missing_rev_cost_flag = 1 if pd.isna(rev_cost_t) else 0
        missing_rev_doc_flag = 1 if rev_doc_t is None else 0
        obs_gap_flag = 1 if obs_coverage_ratio < 0.999 else 0

        # -------------------------------------------------------------
        # J. STATE & AGENCY CONTEXT AGGREGATES (As of Month t)
        # -------------------------------------------------------------
        st_data = state_aggs.get(state, {})
        state_active_count = st_data.get('count', np.nan)
        state_mean_prog = st_data.get('mean_prog', np.nan)
        state_median_prog = st_data.get('median_prog', np.nan)
        state_mean_cost = st_data.get('mean_cost', np.nan)
        state_mean_exp_ratio = st_data.get('mean_exp_ratio', np.nan)

        ag_data = agency_aggs.get(agency, {})
        agency_active_count = ag_data.get('count', np.nan)
        agency_mean_prog = ag_data.get('mean_prog', np.nan)
        agency_median_prog = ag_data.get('median_prog', np.nan)
        agency_mean_cost = ag_data.get('mean_cost', np.nan)
        agency_mean_exp_ratio = ag_data.get('mean_exp_ratio', np.nan)

        table_src = curr_row.get('source_table', 'Table 6: All Ongoing Projects')

        # Assemble full point-in-time feature dictionary
        row_feat = {
            # Static & Baseline (4 numeric + 1 categorical)
            'original_cost_crore': orig_cost if pd.notnull(orig_cost) else np.nan,
            'project_age_months_t': project_age_months,
            'planned_duration_months': planned_duration,
            'original_cost_log': orig_cost_log,
            'project_size_category': size_cat,

            # Current Snapshot (9 numeric)
            'physical_progress_t': prog_t,
            'cumulative_expenditure_t': exp_t,
            'revised_cost_t': rev_cost_t,
            'cost_escalation_pct_t': cost_escalation_pct_t,
            'expenditure_ratio_pct_t': exp_ratio_pct_t,
            'remaining_physical_progress_t': remaining_prog_t,
            'schedule_slippage_months_t': schedule_slippage_t,
            'months_to_original_doc_t': months_to_orig_doc_t,
            'months_to_revised_doc_t': months_to_rev_doc_t,

            # Progress Dynamics (13 numeric)
            'physical_progress_lag1': prog_lag1,
            'physical_progress_lag2': prog_lag2,
            'physical_progress_lag3': prog_lag3,
            'progress_change_1m_t': prog_change_1m,
            'progress_change_2m_t': prog_change_2m,
            'progress_change_3m_t': prog_change_3m,
            'progress_velocity_1m_t': prog_velocity_1m,
            'progress_velocity_3m_t': prog_velocity_3m,
            'progress_velocity_6m_t': prog_velocity_6m,
            'max_progress_to_date_t': max_prog_to_date,
            'min_progress_to_date_t': min_prog_to_date,
            'average_progress_to_date_t': avg_prog_to_date,
            'progress_std_to_date_t': prog_std_to_date,

            # Expenditure Dynamics (10 numeric)
            'cumulative_expenditure_lag1': exp_lag1,
            'cumulative_expenditure_lag3': exp_lag3,
            'monthly_expenditure_delta_t': monthly_exp_delta,
            'expenditure_change_1m_t': exp_change_1m,
            'expenditure_change_3m_t': exp_change_3m,
            'expenditure_velocity_3m_t': exp_velocity_3m,
            'expenditure_velocity_6m_t': exp_velocity_6m,
            'avg_monthly_expenditure_to_date_t': avg_monthly_exp_to_date,
            'expenditure_growth_rate_t': exp_growth_rate,
            'negative_expenditure_delta_flag_t': neg_exp_delta_flag,

            # Stagnation Features (6 numeric)
            'stagnant_2m_t': stagnant_2m,
            'stagnant_3m_t': stagnant_3m,
            'stagnant_6m_t': stagnant_6m,
            'months_since_last_progress_increase_t': months_since_prog_inc,
            'longest_stagnation_to_date_t': longest_stagnation_to_date,
            'progress_change_last_3m_t': progress_change_last_3m,

            # Cost Evolution (5 numeric)
            'has_cost_revision_t': has_cost_rev,
            'cost_revision_count_to_date_t': cost_rev_count_to_date,
            'months_since_last_cost_revision_t': months_since_cost_rev,
            'largest_cost_revision_pct_to_date_t': largest_cost_rev_pct,
            'cost_reduction_pct_as_of_t': cost_reduction_pct_t,

            # Schedule Evolution (3 numeric + 1 categorical)
            'has_revised_schedule_as_of_t': has_rev_schedule,
            'schedule_revision_count_to_date_t': schedule_rev_count_to_date,
            'months_since_last_schedule_revision_t': months_since_sched_rev,
            'current_schedule_status_as_of_t': sched_status,

            # Observation History (5 numeric)
            'months_observed_to_date_t': months_observed_to_date,
            'months_since_first_observed_t': months_since_first_obs,
            'observation_coverage_ratio_t': obs_coverage_ratio,
            'consecutive_observation_count_t': consecutive_obs_count,
            'months_since_last_observation_t': months_since_last_obs,

            # Reporting Quality & Data Health (5 numeric)
            'missing_physical_progress_t': missing_prog_flag,
            'missing_expenditure_t': missing_exp_flag,
            'missing_revised_cost_t': missing_rev_cost_flag,
            'missing_revised_doc_t': missing_rev_doc_flag,
            'observation_gap_flag_t': obs_gap_flag,

            # State & Agency Context Aggregates (10 numeric)
            'state_active_project_count_t': state_active_count,
            'state_mean_progress_t': state_mean_prog,
            'state_median_progress_t': state_median_prog,
            'state_mean_cost_t': state_mean_cost,
            'state_mean_expenditure_ratio_t': state_mean_exp_ratio,
            'agency_active_project_count_t': agency_active_count,
            'agency_mean_progress_t': agency_mean_prog,
            'agency_median_progress_t': agency_median_prog,
            'agency_mean_cost_t': agency_mean_cost,
            'agency_mean_expenditure_ratio_t': agency_mean_exp_ratio,

            # Reporting Cohort Context (1 numeric + 2 categorical)
            'reporting_structure_version_t': struct_ver,
            'focused_cohort_indicator_t': focused_cohort,
            'table_source_t': table_src
        }

        row_meta = {
            'project_id': pid,
            'project_name': pname,
            'agency': agency,
            'state': state,
            'report_month': t,
            'approval_start_date': start_date if start_date is not None else '',
            'original_completion_date': orig_doc if orig_doc is not None else '',
            'revised_completion_date': rev_doc_t if rev_doc_t is not None else '',
            'legacy_ocms_code': curr_row.get('legacy_ocms_code')
        }

        feature_rows.append(row_feat)
        metadata_rows.append(row_meta)

    raw_features_df = pd.DataFrame(feature_rows)
    metadata_df = pd.DataFrame(metadata_rows)

    # 1. Exact 75 ML Features DataFrame (Order-locked & Type-enforced)
    features_df = raw_features_df[PRODUCTION_75_FEATURES].copy()

    # 2. Exact 12 ESI Input Features DataFrame
    esi_df = raw_features_df[ESI_12_INPUT_FEATURES].copy()

    return features_df, esi_df, metadata_df
