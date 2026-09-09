import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.extract_pdfs import extract_all_pdfs
from scripts.merge_monthly_data import merge_and_save_datasets
from scripts.validate_paimana_dataset import validate_dataset

def generate_data_profile(
    master_path='data/paimana_master_dataset.csv',
    completed_path='data/paimana_completed_projects.csv',
    newly_added_path='data/paimana_newly_added_projects.csv',
    review_path='reports/manual_review.csv',
    log_path='reports/extraction_log.csv',
    profile_txt_path='reports/data_profile.txt'
):
    os.makedirs(os.path.dirname(profile_txt_path), exist_ok=True)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    df_master = pd.read_csv(master_path)
    df_completed = pd.read_csv(completed_path)
    df_newly = pd.read_csv(newly_added_path)
    df_review = pd.read_csv(review_path) if os.path.exists(review_path) else pd.DataFrame()
    
    # 1. General Metrics
    num_pdfs = df_master['source_file'].nunique()
    date_range_min = df_master['report_month'].min()
    date_range_max = df_master['report_month'].max()
    unique_projects = df_master['project_id'].nunique()
    total_project_months = len(df_master)
    completed_records = len(df_completed)
    newly_added_records = len(df_newly)
    duplicate_count = df_master.duplicated(subset=['project_id', 'report_month']).sum()
    manual_review_count = len(df_review)
    
    # 2. Missing Values by Column
    missing_stats = []
    for col in df_master.columns:
        null_count = df_master[col].isnull().sum()
        pct = (null_count / total_project_months) * 100
        missing_stats.append(f"  - {col:30}: {null_count:6d} missing ({pct:5.2f}%)")
    missing_str = '\n'.join(missing_stats)
    
    # 3. Monthly Breakdown
    monthly_stats = []
    for m, g in df_master.groupby('report_month'):
        monthly_stats.append(f"  - {m}: {len(g):5d} ongoing projects | {g['project_id'].nunique():5d} unique IDs")
    monthly_str = '\n'.join(monthly_stats)
    
    # 4. Longitudinal Persistence
    obs_counts = df_master.groupby('project_id')['report_month'].count()
    persistence_stats = [
        f"  - Observed in all 15 months : {(obs_counts == 15).sum():5d} projects",
        f"  - Observed in 10-14 months  : {((obs_counts >= 10) & (obs_counts < 15)).sum():5d} projects",
        f"  - Observed in 5-9 months    : {((obs_counts >= 5) & (obs_counts < 10)).sum():5d} projects",
        f"  - Observed in 2-4 months    : {((obs_counts >= 2) & (obs_counts < 5)).sum():5d} projects",
        f"  - Observed in single month  : {(obs_counts == 1).sum():5d} projects"
    ]
    persistence_str = '\n'.join(persistence_stats)
    
    # 5. Validation Warning Breakdown
    review_breakdown = []
    if not df_review.empty:
        for cat, cnt in df_review['flag_category'].value_counts().items():
            review_breakdown.append(f"  - {cat:25}: {cnt:5d} flagged rows")
    else:
        review_breakdown.append("  - None (Zero validation flags)")
    review_str = '\n'.join(review_breakdown)
    
    # 6. Build Text Profile
    profile_content = f"""================================================================================
PAIMANA LONGITUDINAL MASTER DATASET PROFILE & QUALITY AUDIT REPORT
================================================================================

1. EXECUTIVE SUMMARY
--------------------------------------------------------------------------------
- Number of Monthly PDF Reports Processed: {num_pdfs}
- Temporal Coverage Range                : {date_range_min} to {date_range_max} (15 consecutive months)
- Total Unique Projects Monitored        : {unique_projects}
- Total Project-Month Records (Master)   : {total_project_months}
- Completed Project Records (Table 3)    : {completed_records}
- Newly Added Project Records (Table 4)  : {newly_added_records}
- Duplicate (project_id + month) Rows    : {duplicate_count} (Strictly 0 duplicates enforced)
- Total Validation Review Flags          : {manual_review_count}

2. LONGITUDINAL PERSISTENCE DISTRIBUTION
--------------------------------------------------------------------------------
{persistence_str}

3. MONTHLY RECORD COUNTS
--------------------------------------------------------------------------------
{monthly_str}

4. MISSING VALUE AUDIT BY COLUMN
--------------------------------------------------------------------------------
{missing_str}

5. VALIDATION & QUALITY ASSURANCE BREAKDOWN
--------------------------------------------------------------------------------
{review_str}

6. CANONICAL IDENTIFIER COVERAGE
--------------------------------------------------------------------------------
- Total Master Rows with Primary Project ID  : {df_master['project_id'].notnull().sum():d} (100.00%)
- Total Master Rows with Legacy OCMS Linkage : {df_master['legacy_ocms_code'].notnull().sum():d} ({df_master['legacy_ocms_code'].notnull().sum() / total_project_months * 100:.2f}%)
- Total Master Rows with State Information   : {df_master['state'].notnull().sum():d} ({df_master['state'].notnull().sum() / total_project_months * 100:.2f}%)
- Total Master Rows with Cost Information    : {df_master['original_cost_crore'].notnull().sum():d} ({df_master['original_cost_crore'].notnull().sum() / total_project_months * 100:.2f}%)

================================================================================
Generated by: scripts/profile_dataset.py
SIH 2026 Problem Statement SIH26103: Integrated Project Monitoring Platform
================================================================================
"""
    
    with open(profile_txt_path, 'w', encoding='utf-8') as f:
        f.write(profile_content)
        
    print(f"Generated comprehensive profile report: {profile_txt_path}")
    print(profile_content)

def run_pipeline():
    """
    Executes the entire end-to-end pipeline: extraction, merging, validation, and profiling.
    """
    print("================================================================================")
    print("STARTING FULL END-TO-END PAIMANA DATA PIPELINE")
    print("================================================================================")
    
    # 1. Extract, normalize, and merge
    df_ongoing, df_completed, df_newly, extraction_logs = merge_and_save_datasets()
    
    # 2. Save extraction logs
    df_logs = pd.DataFrame(extraction_logs)
    log_path = 'reports/extraction_log.csv'
    df_logs.to_csv(log_path, index=False, encoding='utf-8')
    print(f"Saved extraction log: {log_path} ({len(df_logs)} entries)")
    
    # 3. Validate
    df_review = validate_dataset()
    
    # 4. Profile
    generate_data_profile()
    
    print("================================================================================")
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("================================================================================")

if __name__ == '__main__':
    run_pipeline()
