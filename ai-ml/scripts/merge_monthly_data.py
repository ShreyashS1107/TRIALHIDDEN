import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.extract_pdfs import extract_all_pdfs

def build_canonical_mapping(all_ongoing, all_completed, all_newly_added):
    """
    Builds bidirectional lookup dictionaries for canonical Project IDs, names, agencies, and states.
    """
    ocms_to_pid = {}
    name_to_pid = {}
    pid_to_name = {}
    pid_to_agency = {}
    pid_to_state = {}
    pid_to_ocms = {}
    
    # Collect all records
    for r in all_ongoing + all_completed + all_newly_added:
        pid = r.get('project_id')
        ocms = r.get('legacy_ocms_code')
        name = r.get('project_name')
        agency = r.get('agency')
        state = r.get('state')
        
        # Canonical 5-7 digit numeric ID
        if pid and str(pid).isdigit() and len(str(pid)) in [5, 6, 7]:
            pid_str = str(pid)
            if ocms and len(str(ocms)) in [8, 9, 10]:
                ocms_to_pid[str(ocms)] = pid_str
                if pid_str not in pid_to_ocms:
                    pid_to_ocms[pid_str] = str(ocms)
            if name and len(str(name)) > 5:
                clean_n = ' '.join(str(name).upper().split())
                name_to_pid[clean_n] = pid_str
                if pid_str not in pid_to_name:
                    pid_to_name[pid_str] = str(name)
            if agency and pid_str not in pid_to_agency:
                pid_to_agency[pid_str] = str(agency)
            if state and pid_str not in pid_to_state:
                pid_to_state[pid_str] = str(state)
        elif ocms and len(str(ocms)) in [8, 9, 10]:
            ocms_str = str(ocms)
            if name and len(str(name)) > 5 and ocms_str not in pid_to_name:
                pid_to_name[ocms_str] = str(name)
            if agency and ocms_str not in pid_to_agency:
                pid_to_agency[ocms_str] = str(agency)
            if state and ocms_str not in pid_to_state:
                pid_to_state[ocms_str] = str(state)
                
    return ocms_to_pid, name_to_pid, pid_to_name, pid_to_agency, pid_to_state, pid_to_ocms

def merge_and_save_datasets(output_dir='data'):
    """
    Executes extraction, canonical normalization, deduplication, and file generation.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print("Step 1: Extracting raw data from all 15 PDF reports...")
    all_ongoing, all_completed, all_newly_added, extraction_logs = extract_all_pdfs()
    
    print("Step 2: Building canonical project ID linkages...")
    ocms_to_pid, name_to_pid, pid_to_name, pid_to_agency, pid_to_state, pid_to_ocms = build_canonical_mapping(
        all_ongoing, all_completed, all_newly_added
    )
    print(f"  Mapped {len(ocms_to_pid)} legacy OCMS codes to modern PAIMANA Project IDs.")
    
    master_cols = [
        'project_id',
        'project_name',
        'agency',
        'legacy_ocms_code',
        'state',
        'approval_start_date',
        'original_completion_date',
        'revised_completion_date',
        'original_cost_crore',
        'revised_cost_crore',
        'cumulative_expenditure_crore',
        'physical_progress_percent',
        'report_month',
        'source_file',
        'source_table'
    ]
    
    completed_cols = [
        'project_id',
        'project_name',
        'agency',
        'legacy_ocms_code',
        'state',
        'approval_start_date',
        'actual_completion_date',
        'original_completion_date',
        'revised_completion_date',
        'original_cost_crore',
        'revised_cost_crore',
        'cumulative_expenditure_crore',
        'report_month',
        'source_file',
        'source_table'
    ]
    
    newly_added_cols = [
        'project_id',
        'project_name',
        'agency',
        'legacy_ocms_code',
        'state',
        'approval_start_date',
        'original_completion_date',
        'revised_completion_date',
        'original_cost_crore',
        'revised_cost_crore',
        'report_month',
        'source_file',
        'source_table'
    ]
    
    def resolve_record(row):
        pid = row.get('project_id')
        ocms = row.get('legacy_ocms_code')
        name = row.get('project_name')
        agency = row.get('agency')
        state = row.get('state')
        
        canon_pid = pid
        if pid and str(pid).isdigit() and len(str(pid)) in [5, 6, 7]:
            canon_pid = str(pid)
        elif ocms and str(ocms) in ocms_to_pid:
            canon_pid = ocms_to_pid[str(ocms)]
        elif pid and str(pid) in ocms_to_pid:
            canon_pid = ocms_to_pid[str(pid)]
        elif name:
            clean_n = ' '.join(str(name).upper().split())
            if clean_n in name_to_pid:
                canon_pid = name_to_pid[clean_n]
                
        row['project_id'] = canon_pid
        
        # Link legacy OCMS code if missing
        if not ocms or pd.isna(ocms):
            if canon_pid in pid_to_ocms:
                row['legacy_ocms_code'] = pid_to_ocms[canon_pid]
                
        # Link project name if missing
        if not name or pd.isna(name) or str(name).strip() == '':
            if canon_pid in pid_to_name:
                row['project_name'] = pid_to_name[canon_pid]
            elif ocms and str(ocms) in pid_to_name:
                row['project_name'] = pid_to_name[str(ocms)]
                
        # Link agency if missing
        if not agency or pd.isna(agency) or str(agency).strip() == '':
            if canon_pid in pid_to_agency:
                row['agency'] = pid_to_agency[canon_pid]
                
        # Link state if missing
        if not state or pd.isna(state) or str(state).strip() == '':
            if canon_pid in pid_to_state:
                row['state'] = pid_to_state[canon_pid]
                
        return row

    # Process Ongoing
    df_ongoing = pd.DataFrame(all_ongoing)
    df_ongoing = df_ongoing.apply(resolve_record, axis=1)
    df_ongoing = df_ongoing[[c for c in master_cols if c in df_ongoing.columns]]
    df_ongoing = df_ongoing.dropna(subset=['project_id', 'report_month'])
    
    # Deduplicate strictly on (project_id, report_month)
    df_ongoing['non_null_count'] = df_ongoing.notnull().sum(axis=1)
    df_ongoing = df_ongoing.sort_values(by=['project_id', 'report_month', 'non_null_count'], ascending=[True, True, False])
    df_ongoing = df_ongoing.drop_duplicates(subset=['project_id', 'report_month'], keep='first')
    df_ongoing = df_ongoing.drop(columns=['non_null_count'])
    df_ongoing = df_ongoing.sort_values(by=['report_month', 'project_id'])
    
    # Process Completed
    df_completed = pd.DataFrame(all_completed)
    if not df_completed.empty:
        df_completed = df_completed.apply(resolve_record, axis=1)
        df_completed = df_completed[[c for c in completed_cols if c in df_completed.columns]]
        df_completed = df_completed.dropna(subset=['project_id', 'report_month'])
        df_completed['non_null_count'] = df_completed.notnull().sum(axis=1)
        df_completed = df_completed.sort_values(by=['project_id', 'report_month', 'non_null_count'], ascending=[True, True, False])
        df_completed = df_completed.drop_duplicates(subset=['project_id', 'report_month'], keep='first')
        df_completed = df_completed.drop(columns=['non_null_count'])
        df_completed = df_completed.sort_values(by=['report_month', 'project_id'])
    else:
        df_completed = pd.DataFrame(columns=completed_cols)
        
    # Process Newly Added
    df_newly = pd.DataFrame(all_newly_added)
    if not df_newly.empty:
        df_newly = df_newly.apply(resolve_record, axis=1)
        df_newly = df_newly[[c for c in newly_added_cols if c in df_newly.columns]]
        df_newly = df_newly.dropna(subset=['project_id', 'report_month'])
        df_newly['non_null_count'] = df_newly.notnull().sum(axis=1)
        df_newly = df_newly.sort_values(by=['project_id', 'report_month', 'non_null_count'], ascending=[True, True, False])
        df_newly = df_newly.drop_duplicates(subset=['project_id', 'report_month'], keep='first')
        df_newly = df_newly.drop(columns=['non_null_count'])
        df_newly = df_newly.sort_values(by=['report_month', 'project_id'])
    else:
        df_newly = pd.DataFrame(columns=newly_added_cols)
        
    # Save CSVs
    master_path = os.path.join(output_dir, 'paimana_master_dataset.csv')
    completed_path = os.path.join(output_dir, 'paimana_completed_projects.csv')
    newly_added_path = os.path.join(output_dir, 'paimana_newly_added_projects.csv')
    
    df_ongoing.to_csv(master_path, index=False, encoding='utf-8')
    df_completed.to_csv(completed_path, index=False, encoding='utf-8')
    df_newly.to_csv(newly_added_path, index=False, encoding='utf-8')
    
    print(f"\nSaved master dataset: {master_path} ({len(df_ongoing)} rows)")
    print(f"Saved completed projects: {completed_path} ({len(df_completed)} rows)")
    print(f"Saved newly added projects: {newly_added_path} ({len(df_newly)} rows)")
    
    return df_ongoing, df_completed, df_newly, extraction_logs

if __name__ == '__main__':
    merge_and_save_datasets()
