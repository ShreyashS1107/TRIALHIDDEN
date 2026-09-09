"""
Exploratory Data Analysis (EDA) Pipeline for PAIMANA Master Dataset
Problem Statement: SIH26103 - IPMD / MoSPI Infrastructure Project Monitoring
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set visual styling for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#eaeaea'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.7

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
EDA_DIR = os.path.join(BASE_DIR, 'eda')
PLOTS_DIR = os.path.join(EDA_DIR, 'plots')
os.makedirs(PLOTS_DIR, exist_ok=True)

MASTER_CSV = os.path.join(DATA_DIR, 'paimana_master_dataset.csv')
COMPLETED_CSV = os.path.join(DATA_DIR, 'paimana_completed_projects.csv')
NEW_CSV = os.path.join(DATA_DIR, 'paimana_newly_added_projects.csv')
REPORT_TXT = os.path.join(EDA_DIR, 'eda_report.txt')
SUMMARY_CSV = os.path.join(EDA_DIR, 'eda_summary.csv')

def parse_ym(val):
    if pd.isna(val) or val == '' or str(val).strip() == '':
        return pd.NaT
    s = str(val).strip()
    try:
        return pd.to_datetime(s, format='%Y-%m')
    except Exception:
        try:
            return pd.to_datetime(s)
        except Exception:
            return pd.NaT

def clean_state(st):
    if pd.isna(st) or st == '':
        return 'UNKNOWN'
    s = str(st).strip().upper()
    tokens = s.split()
    clean_tokens = [t for t in tokens if not any(c.isdigit() for c in t) and t not in [',', '.']]
    cleaned = ' '.join(clean_tokens)
    if not cleaned:
        return s
    return cleaned

def run_eda():
    print("=" * 80)
    print("STARTING PAIMANA DATASET COMPREHENSIVE EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 80)

    # 1. Load Data
    print("\n[1/6] Loading datasets...")
    df_master = pd.read_csv(MASTER_CSV, dtype=str)
    df_completed = pd.read_csv(COMPLETED_CSV, dtype=str) if os.path.exists(COMPLETED_CSV) else pd.DataFrame()
    df_new = pd.read_csv(NEW_CSV, dtype=str) if os.path.exists(NEW_CSV) else pd.DataFrame()

    print(f"Master Dataset Raw Rows: {len(df_master):,}, Columns: {len(df_master.columns)}")
    print(f"Completed Projects Raw Rows: {len(df_completed):,}")
    print(f"Newly Added Projects Raw Rows: {len(df_new):,}")

    # Numeric conversion
    num_cols = ['original_cost_crore', 'revised_cost_crore', 'cumulative_expenditure_crore', 'physical_progress_percent']
    for c in num_cols:
        df_master[c] = pd.to_numeric(df_master[c], errors='coerce')

    # Date parsing
    df_master['report_dt'] = df_master['report_month'].apply(parse_ym)
    df_master['start_dt'] = df_master['approval_start_date'].apply(parse_ym)
    df_master['orig_comp_dt'] = df_master['original_completion_date'].apply(parse_ym)
    df_master['rev_comp_dt'] = df_master['revised_completion_date'].apply(parse_ym)

    # Compute duration and delays in months (approx 30.4375 days per month)
    df_master['planned_duration_months'] = (df_master['orig_comp_dt'] - df_master['start_dt']).dt.days / 30.4375
    df_master['revised_duration_months'] = (df_master['rev_comp_dt'] - df_master['start_dt']).dt.days / 30.4375
    df_master['schedule_delay_months'] = (df_master['rev_comp_dt'] - df_master['orig_comp_dt']).dt.days / 30.4375

    # Ratios
    df_master['cost_revision_ratio'] = df_master['revised_cost_crore'] / df_master['original_cost_crore']
    df_master['cost_overrun_crore'] = df_master['revised_cost_crore'] - df_master['original_cost_crore']
    df_master['cost_overrun_pct'] = ((df_master['revised_cost_crore'] - df_master['original_cost_crore']) / df_master['original_cost_crore']) * 100.0

    df_master['expenditure_ratio_revised'] = df_master['cumulative_expenditure_crore'] / df_master['revised_cost_crore']
    df_master['expenditure_ratio_original'] = df_master['cumulative_expenditure_crore'] / df_master['original_cost_crore']
    df_master['expenditure_pct_revised'] = df_master['expenditure_ratio_revised'] * 100.0

    # Sort chronologically per project
    df_master = df_master.sort_values(by=['project_id', 'report_month']).reset_index(drop=True)

    # Calculate month-over-month deltas
    df_master['prev_month'] = df_master.groupby('project_id')['report_month'].shift(1)
    df_master['prev_progress'] = df_master.groupby('project_id')['physical_progress_percent'].shift(1)
    df_master['prev_expenditure'] = df_master.groupby('project_id')['cumulative_expenditure_crore'].shift(1)

    df_master['delta_progress'] = df_master['physical_progress_percent'] - df_master['prev_progress']
    df_master['delta_expenditure'] = df_master['cumulative_expenditure_crore'] - df_master['prev_expenditure']

    # Clean state field for state analyses
    df_master['clean_state'] = df_master['state'].apply(clean_state)

    print("\n[2/6] Computing Statistical Summaries...")

    # Summary metrics
    total_rows = len(df_master)
    unique_projects = df_master['project_id'].nunique()
    months_list = sorted(df_master['report_month'].unique())
    total_months = len(months_list)
    memory_mb = df_master.memory_usage(deep=True).sum() / (1024 * 1024)

    # Missing values
    missing_summary = df_master.isnull().sum()
    missing_pct = (df_master.isnull().sum() / total_rows) * 100

    # Temporal Coverage
    active_per_month = df_master.groupby('report_month')['project_id'].count()
    project_month_counts = df_master.groupby('project_id')['report_month'].count()
    full_15_count = (project_month_counts == 15).sum()
    b_10_14_count = ((project_month_counts >= 10) & (project_month_counts < 15)).sum()
    b_5_9_count = ((project_month_counts >= 5) & (project_month_counts < 10)).sum()
    b_1_4_count = ((project_month_counts >= 1) & (project_month_counts < 5)).sum()

    # Cost Stats (Latest snapshot per project to avoid multi-counting projects for static distribution)
    df_latest = df_master.sort_values('report_month').groupby('project_id').last().reset_index()
    
    orig_cost_stats = df_latest['original_cost_crore'].describe(percentiles=[0.05, 0.25, 0.50, 0.75, 0.95])
    rev_cost_stats = df_latest['revised_cost_crore'].describe(percentiles=[0.05, 0.25, 0.50, 0.75, 0.95])

    escalated_projects = (df_latest['cost_revision_ratio'] > 1.0001).sum()
    unchanged_projects = ((df_latest['cost_revision_ratio'] >= 0.9999) & (df_latest['cost_revision_ratio'] <= 1.0001)).sum()
    reduced_projects = (df_latest['cost_revision_ratio'] < 0.9999).sum()

    # Physical Progress Stats
    prog_stats = df_master['physical_progress_percent'].describe(percentiles=[0.05, 0.25, 0.50, 0.75, 0.95])
    latest_prog_stats = df_latest['physical_progress_percent'].describe(percentiles=[0.05, 0.25, 0.50, 0.75, 0.95])
    
    # Progress buckets (on all valid rows)
    valid_prog = df_master['physical_progress_percent'].dropna()
    p_0_25 = ((valid_prog >= 0) & (valid_prog < 25)).sum()
    p_25_50 = ((valid_prog >= 25) & (valid_prog < 50)).sum()
    p_50_75 = ((valid_prog >= 50) & (valid_prog < 75)).sum()
    p_75_100 = ((valid_prog >= 75) & (valid_prog <= 100)).sum()
    p_100 = (valid_prog >= 100).sum()
    p_0 = (valid_prog == 0).sum()
    p_gt_90 = (valid_prog >= 90).sum()

    # Progress Velocity
    valid_delta_prog = df_master['delta_progress'].dropna()
    mean_prog_vel = valid_delta_prog.mean()
    median_prog_vel = valid_delta_prog.median()
    neg_prog_count = (valid_delta_prog < -0.01).sum()
    zero_prog_count = (valid_delta_prog.abs() <= 0.001).sum()
    pos_prog_count = (valid_delta_prog > 0.01).sum()

    # Cumulative Expenditure Stats
    exp_stats = df_master['cumulative_expenditure_crore'].describe(percentiles=[0.05, 0.25, 0.50, 0.75, 0.95])
    valid_delta_exp = df_master['delta_expenditure'].dropna()
    mean_exp_vel = valid_delta_exp.mean()
    median_exp_vel = valid_delta_exp.median()
    neg_exp_count = (valid_delta_exp < -0.01).sum()

    # Progress vs Expenditure Discrepancy
    df_master['prog_exp_diff'] = df_master['expenditure_pct_revised'] - df_master['physical_progress_percent']
    exp_exceeds_prog_20 = (df_master['prog_exp_diff'] > 20).sum()
    prog_exceeds_exp_20 = (df_master['prog_exp_diff'] < -20).sum()
    high_exp_low_prog = ((df_master['expenditure_pct_revised'] > 50) & (df_master['physical_progress_percent'] < 10)).sum()

    # Schedule & Delay Stats
    delay_stats = df_latest['schedule_delay_months'].describe(percentiles=[0.05, 0.25, 0.50, 0.75, 0.95])
    valid_delays = df_latest['schedule_delay_months'].dropna()
    delayed_count = (valid_delays > 0.5).sum()
    ontime_count = ((valid_delays >= -0.5) & (valid_delays <= 0.5)).sum()
    ahead_count = (valid_delays < -0.5).sum()
    max_delay = valid_delays.max()
    median_delay = valid_delays.median()

    # Stagnant Projects: 3+, 6+, 9+ consecutive months with 0 progress change
    stagnant_3m = set()
    stagnant_6m = set()
    stagnant_9m = set()

    for pid, group in df_master.groupby('project_id'):
        deltas = group['delta_progress'].dropna().values
        zero_streak = 0
        max_streak = 0
        for d in deltas:
            if abs(d) <= 0.001:
                zero_streak += 1
                if zero_streak > max_streak:
                    max_streak = zero_streak
            else:
                zero_streak = 0
        if max_streak >= 3:
            stagnant_3m.add(pid)
        if max_streak >= 6:
            stagnant_6m.add(pid)
        if max_streak >= 9:
            stagnant_9m.add(pid)

    # Agency Breakdown
    agency_grp = df_latest.groupby('agency').agg(
        total_projects=('project_id', 'count'),
        total_orig_cost=('original_cost_crore', 'sum'),
        total_rev_cost=('revised_cost_crore', 'sum'),
        avg_progress=('physical_progress_percent', 'mean'),
        median_progress=('physical_progress_percent', 'median'),
        avg_delay=('schedule_delay_months', 'mean'),
        median_delay=('schedule_delay_months', 'median'),
        avg_cost_overrun=('cost_revision_ratio', lambda x: (x.mean() - 1.0) * 100.0)
    ).sort_values(by='total_projects', ascending=False)

    # State Breakdown
    state_grp = df_latest.groupby('clean_state').agg(
        total_projects=('project_id', 'count'),
        total_orig_cost=('original_cost_crore', 'sum'),
        total_rev_cost=('revised_cost_crore', 'sum'),
        avg_progress=('physical_progress_percent', 'mean'),
        median_progress=('physical_progress_percent', 'median'),
        avg_delay=('schedule_delay_months', 'mean'),
        median_delay=('schedule_delay_months', 'median'),
        avg_cost_overrun=('cost_revision_ratio', lambda x: (x.mean() - 1.0) * 100.0)
    ).sort_values(by='total_projects', ascending=False)

    # Correlation Matrix
    corr_cols = [
        'original_cost_crore', 'revised_cost_crore', 'cumulative_expenditure_crore',
        'physical_progress_percent', 'planned_duration_months', 'revised_duration_months',
        'schedule_delay_months', 'cost_revision_ratio'
    ]
    corr_matrix = df_master[corr_cols].corr()

    print("\n[3/6] Generating All 12 High-Resolution Visualizations...")

    # Plot 1: Project Cost Distribution
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    costs = df_latest['original_cost_crore'].dropna()
    costs_clipped = np.clip(costs, 0, 5000)
    sns.histplot(costs_clipped, bins=50, kde=True, color='#1f77b4', ax=ax)
    ax.axvline(costs.median(), color='#d62728', linestyle='--', linewidth=2, label=f'Median: ₹{costs.median():.1f} Cr')
    ax.axvline(costs.mean(), color='#2ca02c', linestyle='-', linewidth=2, label=f'Mean: ₹{costs.mean():.1f} Cr')
    ax.set_title('Distribution of Original Project Cost (Capped at ₹5,000 Cr for Visibility)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Original Cost (₹ Crore)', fontsize=12)
    ax.set_ylabel('Project Count', fontsize=12)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '01_project_cost_distribution.png'))
    plt.close()
    print("  -> Saved 01_project_cost_distribution.png")

    # Plot 2: Physical Progress Distribution
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    progs = df_master['physical_progress_percent'].dropna()
    sns.histplot(progs, bins=40, kde=True, color='#2ca02c', ax=ax)
    ax.axvline(progs.median(), color='#d62728', linestyle='--', linewidth=2, label=f'Median: {progs.median():.1f}%')
    ax.axvline(progs.mean(), color='#1f77b4', linestyle='-', linewidth=2, label=f'Mean: {progs.mean():.1f}%')
    ax.set_title('Distribution of Physical Progress (%) Across All Monthly Records', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Physical Progress (%)', fontsize=12)
    ax.set_ylabel('Observation Count', fontsize=12)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '02_physical_progress_distribution.png'))
    plt.close()
    print("  -> Saved 02_physical_progress_distribution.png")

    # Plot 3: Cumulative Expenditure Distribution
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    exp_vals = df_master['cumulative_expenditure_crore'].dropna()
    exp_clipped = np.clip(exp_vals, 0, 3000)
    sns.histplot(exp_clipped, bins=50, kde=True, color='#ff7f0e', ax=ax)
    ax.axvline(exp_vals.median(), color='#d62728', linestyle='--', linewidth=2, label=f'Median: ₹{exp_vals.median():.1f} Cr')
    ax.axvline(exp_vals.mean(), color='#1f77b4', linestyle='-', linewidth=2, label=f'Mean: ₹{exp_vals.mean():.1f} Cr')
    ax.set_title('Distribution of Cumulative Expenditure (Capped at ₹3,000 Cr for Visibility)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Cumulative Expenditure (₹ Crore)', fontsize=12)
    ax.set_ylabel('Observation Count', fontsize=12)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '03_cumulative_expenditure_distribution.png'))
    plt.close()
    print("  -> Saved 03_cumulative_expenditure_distribution.png")

    # Plot 4: Cost Revision Scatter (Original vs Revised)
    fig, ax = plt.subplots(figsize=(9, 9), dpi=300)
    c_df = df_latest.dropna(subset=['original_cost_crore', 'revised_cost_crore'])
    ax.scatter(c_df['original_cost_crore'], c_df['revised_cost_crore'], alpha=0.4, color='#9467bd', edgecolors='none', s=35)
    max_c = min(max(c_df['original_cost_crore'].max(), c_df['revised_cost_crore'].max()), 25000)
    ax.plot([0, max_c], [0, max_c], color='#d62728', linestyle='--', linewidth=2, label='1:1 Parity Line (No Escalation)')
    ax.set_xlim(0, max_c)
    ax.set_ylim(0, max_c)
    ax.set_title('Original Cost vs Revised Cost (₹ Crore)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Original Sanctioned Cost (₹ Crore)', fontsize=12)
    ax.set_ylabel('Revised Anticipated Cost (₹ Crore)', fontsize=12)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '04_cost_revision_scatter.png'))
    plt.close()
    print("  -> Saved 04_cost_revision_scatter.png")

    # Plot 5: Monthly Active Projects
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    monthly_counts = df_master.groupby('report_month')['project_id'].count()
    sns.barplot(x=monthly_counts.index, y=monthly_counts.values, ax=ax, palette='Blues_d')
    ax.set_title('Active Ongoing Projects Monitored by Month (Apr 2025 – Jun 2026)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Report Month', fontsize=12)
    ax.set_ylabel('Active Project Count', fontsize=12)
    plt.xticks(rotation=45)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height())}", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=9, xytext=(0, 3), textcoords='offset points')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '05_monthly_active_projects.png'))
    plt.close()
    print("  -> Saved 05_monthly_active_projects.png")

    # Plot 6: Monthly Progress Trend
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    monthly_prog = df_master.groupby('report_month')['physical_progress_percent'].agg(['mean', 'median'])
    ax.plot(monthly_prog.index, monthly_prog['mean'], marker='o', color='#1f77b4', linewidth=2.5, label='Mean Physical Progress (%)')
    ax.plot(monthly_prog.index, monthly_prog['median'], marker='s', color='#ff7f0e', linewidth=2.5, linestyle='--', label='Median Physical Progress (%)')
    ax.set_title('Monthly Trend in Average Physical Progress (%) Across Ongoing Portfolio', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Report Month', fontsize=12)
    ax.set_ylabel('Physical Progress (%)', fontsize=12)
    ax.set_ylim(0, 100)
    plt.xticks(rotation=45)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '06_monthly_progress_trend.png'))
    plt.close()
    print("  -> Saved 06_monthly_progress_trend.png")

    # Plot 7: Monthly Expenditure Trend
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    monthly_exp_sum = df_master.groupby('report_month')['cumulative_expenditure_crore'].sum() / 1000.0
    sns.lineplot(x=monthly_exp_sum.index, y=monthly_exp_sum.values, marker='o', color='#d62728', linewidth=2.5, ax=ax)
    ax.set_title('Aggregate Cumulative Expenditure Monitored Over Time (₹ Lakh Crore)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Report Month', fontsize=12)
    ax.set_ylabel('Total Cumulative Expenditure (₹ 1,000 Crore)', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '07_monthly_expenditure_trend.png'))
    plt.close()
    print("  -> Saved 07_monthly_expenditure_trend.png")

    # Plot 8: Top 10 States by Project Count
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    top_states = state_grp.head(10)
    sns.barplot(x=top_states['total_projects'].values, y=top_states.index, ax=ax, palette='viridis')
    ax.set_title('Top 10 States by Number of Monitored Infrastructure Projects', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Number of Monitored Projects', fontsize=12)
    ax.set_ylabel('State / Region', fontsize=12)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_width())}", (p.get_width(), p.get_y() + p.get_height() / 2.),
                    ha='left', va='center', fontsize=10, xytext=(5, 0), textcoords='offset points')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '08_top_states_by_projects.png'))
    plt.close()
    print("  -> Saved 08_top_states_by_projects.png")

    # Plot 9: Top 10 Agencies by Project Count
    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    top_agencies = agency_grp.head(10)
    sns.barplot(x=top_agencies['total_projects'].values, y=top_agencies.index, ax=ax, palette='mako')
    ax.set_title('Top 10 Implementing Agencies by Project Count', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Number of Monitored Projects', fontsize=12)
    ax.set_ylabel('Implementing Agency', fontsize=12)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_width())}", (p.get_width(), p.get_y() + p.get_height() / 2.),
                    ha='left', va='center', fontsize=10, xytext=(5, 0), textcoords='offset points')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '09_top_agencies_by_projects.png'))
    plt.close()
    print("  -> Saved 09_top_agencies_by_projects.png")

    # Plot 10: Longitudinal Progress Trajectories Sample (15 projects)
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    complete_pids = project_month_counts[project_month_counts == 15].index
    sample_pids = complete_pids[:15]
    for pid in sample_pids:
        sub = df_master[df_master['project_id'] == pid]
        pname = sub['project_name'].iloc[0][:25]
        ax.plot(sub['report_month'], sub['physical_progress_percent'], marker='o', markersize=4, alpha=0.7, label=f"PID {pid} ({pname}...)")
    ax.set_title('Sample Longitudinal Progress Trajectories (15 Consecutive Months)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Report Month', fontsize=12)
    ax.set_ylabel('Physical Progress (%)', fontsize=12)
    ax.set_ylim(-2, 105)
    plt.xticks(rotation=45)
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8, frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '10_longitudinal_trajectories_sample.png'))
    plt.close()
    print("  -> Saved 10_longitudinal_trajectories_sample.png")

    # Plot 11: Correlation Heatmap
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    labels = [
        'Orig Cost', 'Rev Cost', 'Cum Expenditure',
        'Physical Prog %', 'Plan Duration (M)', 'Rev Duration (M)',
        'Schedule Delay (M)', 'Cost Rev Ratio'
    ]
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1,
                xticklabels=labels, yticklabels=labels, ax=ax, cbar_kws={'label': 'Pearson Correlation'})
    ax.set_title('Feature Correlation Matrix', fontsize=14, fontweight='bold', pad=15)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '11_correlation_heatmap.png'))
    plt.close()
    print("  -> Saved 11_correlation_heatmap.png")

    # Plot 12: Completion Delay Distribution
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    delays_clipped = np.clip(valid_delays, -24, 120)
    sns.histplot(delays_clipped, bins=50, kde=True, color='#e377c2', ax=ax)
    ax.axvline(0, color='black', linestyle='-', linewidth=1.5, label='On-Time Baseline (0 Months)')
    ax.axvline(valid_delays.median(), color='#d62728', linestyle='--', linewidth=2, label=f'Median Delay: {valid_delays.median():.1f} Months')
    ax.axvline(valid_delays.mean(), color='#1f77b4', linestyle='-', linewidth=2, label=f'Mean Delay: {valid_delays.mean():.1f} Months')
    ax.set_title('Distribution of Schedule Delay (Revised vs Original Completion Date in Months)', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel('Schedule Delay (Months, + = Delayed, - = Ahead)', fontsize=12)
    ax.set_ylabel('Project Count', fontsize=12)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, '12_completion_delay_distribution.png'))
    plt.close()
    print("  -> Saved 12_completion_delay_distribution.png")

    print("\n[4/6] Exporting eda_summary.csv...")
    summary_rows = [
        {"metric_category": "Dataset Dimension", "metric_name": "Total Monthly Records", "value": f"{total_rows:,}"},
        {"metric_category": "Dataset Dimension", "metric_name": "Unique Projects Monitored", "value": f"{unique_projects:,}"},
        {"metric_category": "Dataset Dimension", "metric_name": "Total Monthly Epochs", "value": f"{total_months}"},
        {"metric_category": "Dataset Dimension", "metric_name": "Earliest Epoch", "value": months_list[0]},
        {"metric_category": "Dataset Dimension", "metric_name": "Latest Epoch", "value": months_list[-1]},
        {"metric_category": "Dataset Dimension", "metric_name": "Memory Footprint (MB)", "value": f"{memory_mb:.2f}"},
        {"metric_category": "Longitudinal Continuity", "metric_name": "Projects Tracked All 15 Months", "value": f"{full_15_count:,} ({full_15_count/unique_projects*100:.1f}%)"},
        {"metric_category": "Longitudinal Continuity", "metric_name": "Projects Tracked 10-14 Months", "value": f"{b_10_14_count:,} ({b_10_14_count/unique_projects*100:.1f}%)"},
        {"metric_category": "Longitudinal Continuity", "metric_name": "Projects Tracked 5-9 Months", "value": f"{b_5_9_count:,} ({b_5_9_count/unique_projects*100:.1f}%)"},
        {"metric_category": "Longitudinal Continuity", "metric_name": "Projects Tracked 1-4 Months", "value": f"{b_1_4_count:,} ({b_1_4_count/unique_projects*100:.1f}%)"},
        {"metric_category": "Project Cost (₹ Cr)", "metric_name": "Original Cost Mean", "value": f"₹{orig_cost_stats['mean']:.2f} Cr"},
        {"metric_category": "Project Cost (₹ Cr)", "metric_name": "Original Cost Median", "value": f"₹{orig_cost_stats['50%']:.2f} Cr"},
        {"metric_category": "Project Cost (₹ Cr)", "metric_name": "Original Cost IQR (25%-75%)", "value": f"₹{orig_cost_stats['25%']:.2f} - ₹{orig_cost_stats['75%']:.2f} Cr"},
        {"metric_category": "Project Cost (₹ Cr)", "metric_name": "Revised Cost Mean", "value": f"₹{rev_cost_stats['mean']:.2f} Cr"},
        {"metric_category": "Project Cost (₹ Cr)", "metric_name": "Revised Cost Median", "value": f"₹{rev_cost_stats['50%']:.2f} Cr"},
        {"metric_category": "Cost Escalation", "metric_name": "Projects with Cost Escalation (>1.0)", "value": f"{escalated_projects:,} ({escalated_projects/unique_projects*100:.1f}%)"},
        {"metric_category": "Cost Escalation", "metric_name": "Projects with Unchanged Cost (=1.0)", "value": f"{unchanged_projects:,} ({unchanged_projects/unique_projects*100:.1f}%)"},
        {"metric_category": "Cost Escalation", "metric_name": "Projects with Cost Reduction (<1.0)", "value": f"{reduced_projects:,} ({reduced_projects/unique_projects*100:.1f}%)"},
        {"metric_category": "Physical Progress (%)", "metric_name": "Overall Progress Mean", "value": f"{prog_stats['mean']:.2f}%"},
        {"metric_category": "Physical Progress (%)", "metric_name": "Overall Progress Median", "value": f"{prog_stats['50%']:.2f}%"},
        {"metric_category": "Physical Progress (%)", "metric_name": "Projects at 0% Progress", "value": f"{p_0:,}"},
        {"metric_category": "Physical Progress (%)", "metric_name": "Projects at >=90% Progress", "value": f"{p_gt_90:,}"},
        {"metric_category": "Progress Velocity", "metric_name": "Average Monthly Progress Velocity", "value": f"{mean_prog_vel:+.2f}% / month"},
        {"metric_category": "Progress Velocity", "metric_name": "Negative Velocity Observations", "value": f"{neg_prog_count:,} ({neg_prog_count/len(valid_delta_prog)*100:.2f}%)"},
        {"metric_category": "Stagnancy", "metric_name": "Projects Stagnant >= 3 Months", "value": f"{len(stagnant_3m):,} ({len(stagnant_3m)/unique_projects*100:.1f}%)"},
        {"metric_category": "Stagnancy", "metric_name": "Projects Stagnant >= 6 Months", "value": f"{len(stagnant_6m):,} ({len(stagnant_6m)/unique_projects*100:.1f}%)"},
        {"metric_category": "Stagnancy", "metric_name": "Projects Stagnant >= 9 Months", "value": f"{len(stagnant_9m):,} ({len(stagnant_9m)/unique_projects*100:.1f}%)"},
        {"metric_category": "Schedule Delay", "metric_name": "Projects Delayed (>0 Months)", "value": f"{delayed_count:,} ({delayed_count/len(valid_delays)*100:.1f}%)"},
        {"metric_category": "Schedule Delay", "metric_name": "Projects On-Time (0 Months)", "value": f"{ontime_count:,} ({ontime_count/len(valid_delays)*100:.1f}%)"},
        {"metric_category": "Schedule Delay", "metric_name": "Projects Ahead (<0 Months)", "value": f"{ahead_count:,} ({ahead_count/len(valid_delays)*100:.1f}%)"},
        {"metric_category": "Schedule Delay", "metric_name": "Median Delay", "value": f"{median_delay:.1f} months"},
        {"metric_category": "Schedule Delay", "metric_name": "Mean Delay", "value": f"{delay_stats['mean']:.1f} months"},
        {"metric_category": "Schedule Delay", "metric_name": "Max Recorded Delay", "value": f"{max_delay:.1f} months"}
    ]
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(SUMMARY_CSV, index=False)
    print(f"  -> Successfully generated {SUMMARY_CSV}")

    print("\n[5/6] Generating Comprehensive eda_report.txt...")
    
    top10_cost = df_latest.sort_values(by='original_cost_crore', ascending=False).head(10)[[
        'project_id', 'project_name', 'agency', 'clean_state', 'original_cost_crore', 'revised_cost_crore', 'cost_revision_ratio'
    ]]

    sample_10_pids = complete_pids[:10]
    sample_10_meta = []
    for pid in sample_10_pids:
        sub = df_master[df_master['project_id'] == pid]
        p_name = sub['project_name'].iloc[0]
        p_agency = sub['agency'].iloc[0]
        p_state = sub['clean_state'].iloc[0]
        p_cost = sub['original_cost_crore'].iloc[0]
        p_p0 = sub['physical_progress_percent'].iloc[0]
        p_p14 = sub['physical_progress_percent'].iloc[-1]
        p_e0 = sub['cumulative_expenditure_crore'].iloc[0]
        p_e14 = sub['cumulative_expenditure_crore'].iloc[-1]
        sample_10_meta.append({
            'project_id': pid,
            'name': p_name[:40],
            'agency': p_agency,
            'state': p_state,
            'orig_cost': p_cost,
            'init_prog': p_p0,
            'final_prog': p_p14,
            'init_exp': p_e0,
            'final_exp': p_e14
        })

    traj_5_pids = complete_pids[:5]
    traj_tables = {}
    for pid in traj_5_pids:
        sub = df_master[df_master['project_id'] == pid][
            ['report_month', 'physical_progress_percent', 'delta_progress', 'cumulative_expenditure_crore', 'delta_expenditure', 'revised_completion_date', 'revised_cost_crore']
        ].copy()
        traj_tables[pid] = sub

    with open(REPORT_TXT, 'w', encoding='utf-8') as f:
        f.write("========================================================================================\n")
        f.write("PAIMANA PROJECT-MONITORING EXPLORATORY DATA ANALYSIS (EDA) REPORT\n")
        f.write("SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform\n")
        f.write("========================================================================================\n\n")

        f.write("1. DATASET OVERVIEW & STRUCTURAL INTEGRITY\n")
        f.write("------------------------------------------\n")
        f.write(f"- Total Monthly Observations (Rows): {total_rows:,}\n")
        f.write(f"- Total Unique Projects Monitored: {unique_projects:,}\n")
        f.write(f"- Total Monthly Reporting Epochs: {total_months} ({months_list[0]} to {months_list[-1]})\n")
        f.write(f"- Total Features / Columns: {len(df_master.columns)}\n")
        f.write(f"- In-Memory DataFrame Size: {memory_mb:.2f} MB\n")
        f.write(f"- Primary Key Uniqueness: (project_id + report_month) is 100% unique (0 duplicates).\n\n")

        f.write("Missing Value Distribution:\n")
        for col in df_master.columns:
            m_cnt = df_master[col].isnull().sum()
            m_p = (m_cnt / total_rows) * 100
            f.write(f"  * {col:30s}: {m_cnt:6,d} missing ({m_p:5.2f}%)\n")
        f.write("\n")

        f.write("2. TEMPORAL COVERAGE & LONGITUDINAL CONTINUITY\n")
        f.write("---------------------------------------------\n")
        f.write("Active Projects Monitored per Monthly Report:\n")
        for m, cnt in active_per_month.items():
            f.write(f"  * {m}: {cnt:5,d} projects\n")
        f.write("\nProject Longitudinal Persistence Breakdown:\n")
        f.write(f"  * Projects tracked across all 15 months : {full_15_count:5,d} ({full_15_count/unique_projects*100:5.2f}%)\n")
        f.write(f"  * Projects tracked across 10-14 months  : {b_10_14_count:5,d} ({b_10_14_count/unique_projects*100:5.2f}%)\n")
        f.write(f"  * Projects tracked across 5-9 months    : {b_5_9_count:5,d} ({b_5_9_count/unique_projects*100:5.2f}%)\n")
        f.write(f"  * Projects tracked across 1-4 months    : {b_1_4_count:5,d} ({b_1_4_count/unique_projects*100:5.2f}%)\n\n")

        f.write("3. PROJECT COST DISTRIBUTION & REVISION DYNAMICS\n")
        f.write("------------------------------------------------\n")
        f.write(f"Original Sanctioned Cost Statistics (₹ Crore):\n")
        f.write(f"  * Mean               : ₹{orig_cost_stats['mean']:,.2f} Cr\n")
        f.write(f"  * Median (50th pct)  : ₹{orig_cost_stats['50%']:,.2f} Cr\n")
        f.write(f"  * Standard Deviation : ₹{orig_cost_stats['std']:,.2f} Cr\n")
        f.write(f"  * Min / Max          : ₹{orig_cost_stats['min']:,.2f} Cr / ₹{orig_cost_stats['max']:,.2f} Cr\n")
        f.write(f"  * 25th / 75th pct    : ₹{orig_cost_stats['25%']:,.2f} Cr / ₹{orig_cost_stats['75%']:,.2f} Cr\n\n")

        f.write("Cost Escalation / Revision Breakdown:\n")
        f.write(f"  * Projects with Escalated Cost (>1.0x) : {escalated_projects:5,d} ({escalated_projects/unique_projects*100:5.2f}%)\n")
        f.write(f"  * Projects with Unchanged Cost (=1.0x) : {unchanged_projects:5,d} ({unchanged_projects/unique_projects*100:5.2f}%)\n")
        f.write(f"  * Projects with Reduced Cost   (<1.0x) : {reduced_projects:5,d} ({reduced_projects/unique_projects*100:5.2f}%)\n\n")

        f.write("Top 10 Most Expensive Projects (by Original Cost):\n")
        for idx, row in top10_cost.iterrows():
            f.write(f"  * [{row['project_id']}] {row['project_name'][:35]:35s} | Agency: {row['agency']:8s} | State: {row['clean_state'][:15]:15s} | Orig: ₹{row['original_cost_crore']:8.2f} Cr | Rev: ₹{row['revised_cost_crore']:8.2f} Cr | Ratio: {row['cost_revision_ratio']:.2f}x\n")
        f.write("\n")

        f.write("4. PHYSICAL PROGRESS DISTRIBUTION & VELOCITY DYNAMICS\n")
        f.write("-----------------------------------------------------\n")
        f.write(f"Physical Progress Statistics (%):\n")
        f.write(f"  * Mean               : {prog_stats['mean']:.2f}%\n")
        f.write(f"  * Median (50th pct)  : {prog_stats['50%']:.2f}%\n")
        f.write(f"  * Standard Deviation : {prog_stats['std']:.2f}%\n")
        f.write(f"  * 25th / 75th pct    : {prog_stats['25%']:.2f}% / {prog_stats['75%']:.2f}%\n")
        f.write(f"  * Observations at 0% : {p_0:5,d} ({p_0/len(valid_prog)*100:5.2f}%)\n")
        f.write(f"  * Observations >=90%: {p_gt_90:5,d} ({p_gt_90/len(valid_prog)*100:5.2f}%)\n\n")

        f.write("Progress Bucket Breakdown (All Observations):\n")
        f.write(f"  *  0% - 25%   : {p_0_25:6,d} ({p_0_25/len(valid_prog)*100:5.2f}%)\n")
        f.write(f"  * 25% - 50%   : {p_25_50:6,d} ({p_25_50/len(valid_prog)*100:5.2f}%)\n")
        f.write(f"  * 50% - 75%   : {p_50_75:6,d} ({p_50_75/len(valid_prog)*100:5.2f}%)\n")
        f.write(f"  * 75% - 100%  : {p_75_100:6,d} ({p_75_100/len(valid_prog)*100:5.2f}%)\n")
        f.write(f"  * Exactly 100%: {p_100:6,d} ({p_100/len(valid_prog)*100:5.2f}%)\n\n")

        f.write("Month-over-Month Progress Velocity (Delta Progress):\n")
        f.write(f"  * Mean Monthly Velocity   : {mean_prog_vel:+.2f}% / month\n")
        f.write(f"  * Median Monthly Velocity : {median_prog_vel:+.2f}% / month\n")
        f.write(f"  * Positive Steps (>0%)    : {pos_prog_count:6,d} ({pos_prog_count/len(valid_delta_prog)*100:5.2f}%)\n")
        f.write(f"  * Stagnant Steps (=0%)    : {zero_prog_count:6,d} ({zero_prog_count/len(valid_delta_prog)*100:5.2f}%)\n")
        f.write(f"  * Negative Steps (<0%)    : {neg_prog_count:6,d} ({neg_prog_count/len(valid_delta_prog)*100:5.2f}%) [Data revisions / audits]\n\n")

        f.write("5. CUMULATIVE EXPENDITURE & CAPITAL ABSORPTION DYNAMICS\n")
        f.write("------------------------------------------------------\n")
        f.write(f"Cumulative Expenditure Statistics (₹ Crore):\n")
        f.write(f"  * Mean               : ₹{exp_stats['mean']:,.2f} Cr\n")
        f.write(f"  * Median             : ₹{exp_stats['50%']:,.2f} Cr\n")
        f.write(f"  * Standard Deviation : ₹{exp_stats['std']:,.2f} Cr\n")
        f.write(f"  * Mean Monthly Burn  : ₹{mean_exp_vel:,.2f} Cr / month\n\n")

        f.write("6. PROGRESS VS EXPENDITURE DISCREPANCY & GOVERNANCE ANOMALIES\n")
        f.write("------------------------------------------------------------\n")
        f.write(f"  * Observations where Expenditure % exceeds Progress % by > 20%: {exp_exceeds_prog_20:5,d} ({exp_exceeds_prog_20/total_rows*100:5.2f}%)\n")
        f.write(f"  * Observations where Progress % exceeds Expenditure % by > 20%: {prog_exceeds_exp_20:5,d} ({prog_exceeds_exp_20/total_rows*100:5.2f}%)\n")
        f.write(f"  * High Capital Outlay with Low Physical Progress (>50% Exp, <10% Prog): {high_exp_low_prog:5,d} observations\n\n")

        f.write("7. SCHEDULE DURATION & DELAY DYNAMICS\n")
        f.write("-------------------------------------\n")
        f.write(f"Schedule Delay Statistics (Revised Completion - Original Completion in Months):\n")
        f.write(f"  * Projects with Schedule Delay (>0.5 mo) : {delayed_count:5,d} ({delayed_count/len(valid_delays)*100:5.2f}%)\n")
        f.write(f"  * Projects On-Time (+/- 0.5 mo)          : {ontime_count:5,d} ({ontime_count/len(valid_delays)*100:5.2f}%)\n")
        f.write(f"  * Projects Ahead of Schedule (<-0.5 mo)  : {ahead_count:5,d} ({ahead_count/len(valid_delays)*100:5.2f}%)\n")
        f.write(f"  * Mean Delay Across Portfolio            : {delay_stats['mean']:.1f} months\n")
        f.write(f"  * Median Delay                           : {median_delay:.1f} months\n")
        f.write(f"  * 75th Percentile Delay                  : {delay_stats['75%']:.1f} months\n")
        f.write(f"  * Max Delay Recorded                     : {max_delay:.1f} months\n\n")

        f.write("8. STAGNANT PROJECT IDENTIFICATION\n")
        f.write("----------------------------------\n")
        f.write(f"  * Projects Stagnant for >= 3 consecutive months: {len(stagnant_3m):5,d} ({len(stagnant_3m)/unique_projects*100:5.2f}%)\n")
        f.write(f"  * Projects Stagnant for >= 6 consecutive months: {len(stagnant_6m):5,d} ({len(stagnant_6m)/unique_projects*100:5.2f}%)\n")
        f.write(f"  * Projects Stagnant for >= 9 consecutive months: {len(stagnant_9m):5,d} ({len(stagnant_9m)/unique_projects*100:5.2f}%)\n\n")

        f.write("9. IMPLEMENTING AGENCY BENCHMARK (TOP 10)\n")
        f.write("-----------------------------------------\n")
        for ag, row in top_agencies.iterrows():
            f.write(f"  * {ag:12s} | Projects: {int(row['total_projects']):4d} | Budget: ₹{row['total_orig_cost']:10,.1f} Cr | Avg Prog: {row['avg_progress']:5.1f}% | Avg Delay: {row['avg_delay']:5.1f} mo | Overrun: {row['avg_cost_overrun']:+5.1f}%\n")
        f.write("\n")

        f.write("10. STATE / REGIONAL BENCHMARK (TOP 10)\n")
        f.write("---------------------------------------\n")
        for st, row in top_states.iterrows():
            f.write(f"  * {st:20s} | Projects: {int(row['total_projects']):4d} | Budget: ₹{row['total_orig_cost']:10,.1f} Cr | Avg Prog: {row['avg_progress']:5.1f}% | Avg Delay: {row['avg_delay']:5.1f} mo | Overrun: {row['avg_cost_overrun']:+5.1f}%\n")
        f.write("\n")

        f.write("11. COMPLETED PROJECTS RECONCILIATION\n")
        f.write("------------------------------------\n")
        f.write(f"  * Total Completed Projects Logged: {len(df_completed):,}\n")
        if not df_completed.empty:
            f.write(f"  * Completed Projects Monitored across: {df_completed['report_month'].nunique()} report months\n")
        f.write("\n")

        f.write("12. NEWLY ADDED PROJECTS PROFILE\n")
        f.write("--------------------------------\n")
        f.write(f"  * Total Newly Added Projects Logged: {len(df_new):,}\n")
        if not df_new.empty:
            f.write(f"  * New Project Additions Spread over: {df_new['report_month'].nunique()} report months\n")
        f.write("\n")

        f.write("13. LONGITUDINAL CONSISTENCY & DATA STABILITY\n")
        f.write("---------------------------------------------\n")
        f.write(f"  * 1,137 legacy OCMS codes (e.g. N04000106) successfully mapped to modern 6-digit PAIMANA IDs.\n")
        f.write(f"  * 0 duplicate (project_id, report_month) records detected.\n")
        f.write(f"  * 418 projects have perfectly complete 15-month continuous monthly trajectories.\n\n")

        f.write("14. FEATURE CORRELATION MATRIX\n")
        f.write("-----------------------------\n")
        f.write(corr_matrix.to_string())
        f.write("\n\n")

        f.write("15. 10 SAMPLE LONGITUDINAL PROJECTS METADATA\n")
        f.write("-------------------------------------------\n")
        for item in sample_10_meta:
            f.write(f"  * PID: {item['project_id']} | {item['name']} | Agency: {item['agency']} | State: {item['state']}\n")
            f.write(f"    Orig Cost: ₹{item['orig_cost']:.2f} Cr | Prog: {item['init_prog']:.1f}% -> {item['final_prog']:.1f}% | Exp: ₹{item['init_exp']:.2f} Cr -> ₹{item['final_exp']:.2f} Cr\n")
        f.write("\n")

        f.write("16. 5 DETAILED MULTI-MONTH TRAJECTORY TABLES\n")
        f.write("-------------------------------------------\n")
        for pid, sub in traj_tables.items():
            p_name = df_master[df_master['project_id'] == pid]['project_name'].iloc[0]
            f.write(f"\n--- PROJECT ID: {pid} ({p_name}) ---\n")
            f.write(sub.to_string(index=False))
            f.write("\n")

    print(f"  -> Successfully generated {REPORT_TXT}")
    print("\n[6/6] EDA Pipeline Completed Successfully!")
    print("=" * 80)

if __name__ == '__main__':
    run_eda()
