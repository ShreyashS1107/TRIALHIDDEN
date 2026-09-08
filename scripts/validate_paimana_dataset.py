import os
import re
import pandas as pd
import numpy as np

def validate_dataset(master_csv_path='data/paimana_master_dataset.csv', output_report_path='reports/manual_review.csv'):
    """
    Performs comprehensive quality control, integrity checks, and longitudinal anomaly detection.
    Flags suspicious records into manual_review.csv without dropping them.
    """
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    
    df = pd.read_csv(master_csv_path)
    print(f"Loaded master dataset from {master_csv_path} ({len(df)} rows).")
    
    manual_review_records = []
    
    # 1. Check for Duplicate (project_id + report_month)
    dupes = df[df.duplicated(subset=['project_id', 'report_month'], keep=False)]
    for _, r in dupes.iterrows():
        manual_review_records.append({
            'project_id': r.get('project_id'),
            'report_month': r.get('report_month'),
            'project_name': r.get('project_name'),
            'source_file': r.get('source_file'),
            'flag_category': 'DUPLICATE_KEY',
            'severity': 'HIGH',
            'flag_reason': f"Duplicate (project_id, report_month) detected for {r.get('project_id')} in {r.get('report_month')}"
        })
        
    # 2. Check for Missing Critical Keys
    missing_keys = df[df['project_id'].isnull() | df['report_month'].isnull()]
    for _, r in missing_keys.iterrows():
        manual_review_records.append({
            'project_id': r.get('project_id'),
            'report_month': r.get('report_month'),
            'project_name': r.get('project_name'),
            'source_file': r.get('source_file'),
            'flag_category': 'MISSING_KEY',
            'severity': 'CRITICAL',
            'flag_reason': "Missing project_id or report_month"
        })
        
    # 3. Check for Out-of-Bound Physical Progress
    invalid_prog = df[df['physical_progress_percent'].notnull() & ((df['physical_progress_percent'] < 0) | (df['physical_progress_percent'] > 100))]
    for _, r in invalid_prog.iterrows():
        manual_review_records.append({
            'project_id': r.get('project_id'),
            'report_month': r.get('report_month'),
            'project_name': r.get('project_name'),
            'source_file': r.get('source_file'),
            'flag_category': 'INVALID_PROGRESS',
            'severity': 'MEDIUM',
            'flag_reason': f"Physical progress ({r['physical_progress_percent']}%) is outside valid range [0, 100]"
        })
        
    # 4. Check for Negative Costs or Expenditures
    neg_costs = df[
        (df['original_cost_crore'].notnull() & (df['original_cost_crore'] < 0)) |
        (df['revised_cost_crore'].notnull() & (df['revised_cost_crore'] < 0)) |
        (df['cumulative_expenditure_crore'].notnull() & (df['cumulative_expenditure_crore'] < 0))
    ]
    for _, r in neg_costs.iterrows():
        manual_review_records.append({
            'project_id': r.get('project_id'),
            'report_month': r.get('report_month'),
            'project_name': r.get('project_name'),
            'source_file': r.get('source_file'),
            'flag_category': 'NEGATIVE_VALUE',
            'severity': 'HIGH',
            'flag_reason': f"Negative monetary value detected: OrigCost={r.get('original_cost_crore')}, RevCost={r.get('revised_cost_crore')}, CumExp={r.get('cumulative_expenditure_crore')}"
        })
        
    # 5. Check Date Format Validity
    date_cols = ['approval_start_date', 'original_completion_date', 'revised_completion_date']
    for col in date_cols:
        bad_dates = df[df[col].notnull() & (~df[col].astype(str).str.match(r'^\d{4}-\d{2}$'))]
        for _, r in bad_dates.iterrows():
            manual_review_records.append({
                'project_id': r.get('project_id'),
                'report_month': r.get('report_month'),
                'project_name': r.get('project_name'),
                'source_file': r.get('source_file'),
                'flag_category': 'INVALID_DATE_FORMAT',
                'severity': 'LOW',
                'flag_reason': f"Column {col} has non-standard date value: {r.get(col)}"
            })
            
    # 6. Longitudinal Analysis: Trajectory Anomalies per Project
    # Sort chronologically
    df_sorted = df.sort_values(by=['project_id', 'report_month']).copy()
    
    for pid, group in df_sorted.groupby('project_id'):
        if len(group) < 2:
            continue
            
        group = group.reset_index(drop=True)
        
        # Check for progress drops (> 20% drop from previous observed month)
        for i in range(1, len(group)):
            prev_prog = group.loc[i-1, 'physical_progress_percent']
            curr_prog = group.loc[i, 'physical_progress_percent']
            
            if pd.notnull(prev_prog) and pd.notnull(curr_prog):
                prog_drop = prev_prog - curr_prog
                if prog_drop > 25.0:
                    manual_review_records.append({
                        'project_id': pid,
                        'report_month': group.loc[i, 'report_month'],
                        'project_name': group.loc[i, 'project_name'],
                        'source_file': group.loc[i, 'source_file'],
                        'flag_category': 'PROGRESS_REGRESSION',
                        'severity': 'MEDIUM',
                        'flag_reason': f"Physical progress dropped by {prog_drop:.1f}% (from {prev_prog}% in {group.loc[i-1, 'report_month']} to {curr_prog}% in {group.loc[i, 'report_month']})"
                    })
                    
            # Check for sudden massive cost revisions (> 400% increase in 1 step)
            prev_cost = group.loc[i-1, 'original_cost_crore']
            curr_cost = group.loc[i, 'original_cost_crore']
            if pd.notnull(prev_cost) and pd.notnull(curr_cost) and prev_cost > 0:
                cost_ratio = curr_cost / prev_cost
                if cost_ratio > 5.0 or cost_ratio < 0.2:
                    manual_review_records.append({
                        'project_id': pid,
                        'report_month': group.loc[i, 'report_month'],
                        'project_name': group.loc[i, 'project_name'],
                        'source_file': group.loc[i, 'source_file'],
                        'flag_category': 'LARGE_COST_SHIFT',
                        'severity': 'MEDIUM',
                        'flag_reason': f"Original cost changed significantly from {prev_cost} Cr ({group.loc[i-1, 'report_month']}) to {curr_cost} Cr ({group.loc[i, 'report_month']})"
                    })
                    
            # Check for cumulative expenditure dropping significantly (> 50% drop)
            prev_exp = group.loc[i-1, 'cumulative_expenditure_crore']
            curr_exp = group.loc[i, 'cumulative_expenditure_crore']
            if pd.notnull(prev_exp) and pd.notnull(curr_exp) and prev_exp > 50.0:
                if curr_exp < prev_exp * 0.5:
                    manual_review_records.append({
                        'project_id': pid,
                        'report_month': group.loc[i, 'report_month'],
                        'project_name': group.loc[i, 'project_name'],
                        'source_file': group.loc[i, 'source_file'],
                        'flag_category': 'EXPENDITURE_DROP',
                        'severity': 'MEDIUM',
                        'flag_reason': f"Cumulative expenditure dropped from {prev_exp} Cr ({group.loc[i-1, 'report_month']}) to {curr_exp} Cr ({group.loc[i, 'report_month']})"
                    })
                    
    # Save Manual Review CSV
    df_review = pd.DataFrame(manual_review_records)
    if not df_review.empty:
        df_review = df_review.drop_duplicates(subset=['project_id', 'report_month', 'flag_category', 'flag_reason'])
    else:
        df_review = pd.DataFrame(columns=['project_id', 'report_month', 'project_name', 'source_file', 'flag_category', 'severity', 'flag_reason'])
        
    df_review.to_csv(output_report_path, index=False, encoding='utf-8')
    print(f"Validation complete: flagged {len(df_review)} rows for review in {output_report_path}")
    
    return df_review

if __name__ == '__main__':
    validate_dataset()
