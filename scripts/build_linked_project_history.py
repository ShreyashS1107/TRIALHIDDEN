import os
import sys
import re
import glob
import pymupdf as fitz
import pandas as pd
import numpy as np
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

dataset_dir = r"c:\Users\Shreyash\Documents\vs work\SIH26103\dataset"
output_dir = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors"
paimana_master_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_master_dataset.csv"

p_df = pd.read_csv(paimana_master_path)
print(f"Loaded PAIMANA Master Dataset ({len(p_df)} rows).")

# 1. Identify all unique linked project IDs and their legacy OCMS codes
linked_projects = p_df[p_df['legacy_ocms_code'].notna()][['project_id', 'legacy_ocms_code', 'project_name', 'agency']].drop_duplicates(subset=['project_id']).copy()
linked_projects['legacy_ocms_code'] = linked_projects['legacy_ocms_code'].astype(str).str.strip().str.upper()
linked_codes_set = set(linked_projects['legacy_ocms_code'].unique())
code_to_pid = dict(zip(linked_projects['legacy_ocms_code'], linked_projects['project_id']))

print(f"Total linked projects with legacy OCMS code: {len(linked_projects)}")

months_map = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'july1': 7, 'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
}

def parse_date_str(val):
    if not val:
        return None
    val = str(val).strip('(){}[] \t\r\n')
    if val in ['', '-', '--', 'NA', 'N.A.', 'NIL', 'Nil', 'null', 'None', 'Unfinalised']:
        return None
    m = re.search(r'(\d{1,2})[/-](\d{4})', val)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12 and 1950 <= year <= 2050:
            return f"{year:04d}-{month:02d}"
    m_ym = re.search(r'(\d{4})[/-](\d{1,2})', val)
    if m_ym:
        year = int(m_ym.group(1))
        month = int(m_ym.group(2))
        if 1 <= month <= 12 and 1950 <= year <= 2050:
            return f"{year:04d}-{month:02d}"
    return None

def parse_float_val(val):
    if val is None:
        return None
    val = str(val).strip('(){}[] \t\r\n').replace(',', '')
    if val in ['', '-', '--', 'NA', 'N.A.', 'NIL', 'Nil', 'null', 'None']:
        return None
    m = re.search(r'-?\d+(?:\.\d+)?', val)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None

def month_diff(d1, d2):
    if not d1 or not d2:
        return 0
    try:
        y1, m1 = int(d1[:4]), int(d1[5:7])
        y2, m2 = int(d2[:4]), int(d2[5:7])
        return (y1 - y2) * 12 + (m1 - m2)
    except Exception:
        return 0

# 2. Select representative longitudinal snapshots across 2014-2025
pdf_files = sorted(glob.glob(os.path.join(dataset_dir, "*.pdf")))

historical_snapshots = []
# Pick April of each year 2014-2024, plus late 2024 and early 2025 snapshots
target_patterns = [
    'FR_APR_2014.pdf', 'FR_APRil_2015.pdf', 'FR_APr_2016.pdf', 'FR_APril_2017.pdf',
    'FR_APr_2018.pdf', 'FR_APr_Report_2019.pdf', 'FR_APril_2020.pdf', 'FR_APr_2021.pdf',
    'FR_APr_2022.pdf', 'FR_august_2023.pdf', 'FR_mar_2024.pdf', 'August_Part-2(List_of_tables).pdf',
    'December.pdf', 'FRMarch2025.pdf', 'FRApril2025.pdf'
]

for p in pdf_files:
    fname = os.path.basename(p)
    if fname in target_patterns:
        fn_clean = fname.lower()
        fn_m = None
        for m_k in sorted(months_map.keys(), key=lambda x: -len(x)):
            if m_k in fn_clean:
                fn_m = months_map[m_k]
                break
        m_y = re.search(r'(20\d\d|19\d\d)', fname)
        if m_y and fn_m:
            y = int(m_y.group(1))
            historical_snapshots.append((p, f"{y:04d}-{fn_m:02d}"))
        elif fname == 'December.pdf':
            historical_snapshots.append((p, '2024-12'))
        elif fname == 'August_Part-2(List_of_tables).pdf':
            historical_snapshots.append((p, '2024-08'))

print(f"Selected {len(historical_snapshots)} milestone OCMS reports for longitudinal extraction:")
for p, m in historical_snapshots:
    print(f"  - {m}: {os.path.basename(p)}")

# Scan reports and extract project occurrences
project_history_records = []

for p_path, rep_m in historical_snapshots:
    doc = fitz.open(p_path)
    fname = os.path.basename(p_path)
    print(f"Scanning {fname} ({rep_m}) - {len(doc)} pages...")
    
    for pno in range(len(doc)):
        txt = doc[pno].get_text()
        # Fast check if any bracketed code appears
        if "[" not in txt:
            continue
            
        codes = re.findall(r'\[([A-Z0-9_-]{6,15})\]', txt)
        matched_in_page = [c.strip().upper() for c in codes if c.strip().upper() in linked_codes_set]
        
        if not matched_in_page:
            continue
            
        blocks = doc[pno].get_text("blocks")
        for b in blocks:
            b_txt = b[4]
            for c in matched_in_page:
                if f"[{c}]" in b_txt or c in b_txt:
                    y_top = b[1] - 8
                    y_bot = b[3] + 16
                    row_blocks = [rb for rb in blocks if y_top <= (rb[1]+rb[3])/2 <= y_bot]
                    row_txt = " \n ".join([rb[4] for rb in row_blocks])
                    
                    dates_found = []
                    for w in re.split(r'[\s\n]+', row_txt):
                        d = parse_date_str(w)
                        if d and d not in dates_found:
                            dates_found.append(d)
                            
                    floats_found = []
                    for w in re.split(r'[\s\n]+', row_txt):
                        f = parse_float_val(w)
                        if f is not None and f not in floats_found and f > 1.0:
                            floats_found.append(f)
                            
                    orig_cost = floats_found[0] if len(floats_found) >= 1 else None
                    ant_cost = floats_found[1] if len(floats_found) >= 2 else orig_cost
                    cum_exp = floats_found[2] if len(floats_found) >= 3 else None
                    orig_doc = dates_found[0] if len(dates_found) >= 1 else None
                    ant_doc = dates_found[1] if len(dates_found) >= 2 else orig_doc
                    
                    project_history_records.append({
                        'project_id': code_to_pid.get(c),
                        'legacy_ocms_code': c,
                        'report_month': rep_m,
                        'original_cost': orig_cost,
                        'anticipated_cost': ant_cost,
                        'cumulative_expenditure': cum_exp,
                        'original_doc': orig_doc,
                        'anticipated_doc': ant_doc,
                        'source_file': fname,
                        'source_page': pno + 1
                    })
    doc.close()

df_hist = pd.DataFrame(project_history_records)
print(f"Extracted {len(df_hist)} historical project-month snapshot records for linked projects.")

# Deduplicate by (project_id, report_month)
df_hist.drop_duplicates(subset=['project_id', 'report_month'], inplace=True)
df_hist.sort_values(by=['project_id', 'report_month'], inplace=True)

# 3. Compute Pre-PAIMANA Linked Project Features for every prediction month t
prediction_months = [
    f"{y:04d}-{m:02d}"
    for y in [2025, 2026]
    for m in range(1, 13)
    if (y == 2025 and m >= 4) or (y == 2026 and m <= 6)
]

linked_priors_records = []

for as_of_t in prediction_months:
    # STRICT POINT-IN-TIME CONDITION: report_month < as_of_t
    valid_p_hist = df_hist[df_hist['report_month'] < as_of_t]
    
    for pid in linked_projects['project_id'].unique():
        p_sub = valid_p_hist[valid_p_hist['project_id'] == pid]
        leg_code = linked_projects[linked_projects['project_id'] == pid]['legacy_ocms_code'].iloc[0]
        
        if len(p_sub) == 0:
            linked_priors_records.append({
                'project_id': pid,
                'legacy_ocms_code': leg_code,
                'as_of_date': as_of_t,
                'pre_paimana_observation_months': 0,
                'pre_paimana_schedule_revision_count': 0,
                'pre_paimana_cost_revision_count': 0,
                'pre_paimana_initial_cost': np.nan,
                'pre_paimana_latest_known_cost': np.nan,
                'pre_paimana_max_cost_escalation_pct': 0.0,
                'pre_paimana_initial_doc': None,
                'pre_paimana_latest_doc': None,
                'pre_paimana_max_schedule_slippage_months': 0.0,
                'max_source_date': None
            })
            continue
            
        n_obs = len(p_sub)
        max_src_d = p_sub['report_month'].max()
        
        # Initial vs Latest Cost
        costs = p_sub['anticipated_cost'].dropna().tolist()
        init_cost = costs[0] if costs else np.nan
        latest_cost = costs[-1] if costs else np.nan
        
        # Cost Revisions: cost_k != cost_{k-1} with tolerance > 0.05 Cr
        cost_revs = 0
        for i in range(1, len(costs)):
            if abs(costs[i] - costs[i-1]) > 0.05:
                cost_revs += 1
                
        max_cost_esc_pct = 0.0
        if pd.notna(init_cost) and init_cost > 0 and costs:
            max_cost_esc_pct = max(0.0, ((max(costs) - init_cost) / init_cost) * 100.0)
            
        # Schedule Revisions & Slippage
        docs = p_sub['anticipated_doc'].dropna().tolist()
        init_doc = docs[0] if docs else None
        latest_doc = docs[-1] if docs else None
        
        sched_revs = 0
        for i in range(1, len(docs)):
            if docs[i] != docs[i-1]:
                sched_revs += 1
                
        max_slip_months = 0.0
        if init_doc and docs:
            slips = [month_diff(d, init_doc) for d in docs]
            max_slip_months = max(0.0, float(max(slips)))
            
        linked_priors_records.append({
            'project_id': pid,
            'legacy_ocms_code': leg_code,
            'as_of_date': as_of_t,
            'pre_paimana_observation_months': n_obs,
            'pre_paimana_schedule_revision_count': sched_revs,
            'pre_paimana_cost_revision_count': cost_revs,
            'pre_paimana_initial_cost': init_cost,
            'pre_paimana_latest_known_cost': latest_cost,
            'pre_paimana_max_cost_escalation_pct': max_cost_esc_pct,
            'pre_paimana_initial_doc': init_doc,
            'pre_paimana_latest_doc': latest_doc,
            'pre_paimana_max_schedule_slippage_months': max_slip_months,
            'max_source_date': max_src_d
        })

df_linked_priors = pd.DataFrame(linked_priors_records)
output_path = os.path.join(output_dir, "linked_project_history.csv")
df_linked_priors.to_csv(output_path, index=False)
print(f"\nSaved {output_path} with {len(df_linked_priors)} records across {len(linked_projects)} linked projects and {len(prediction_months)} prediction months.")
print(f"Projects with pre-PAIMANA historical observations: {df_linked_priors[df_linked_priors['pre_paimana_observation_months'] > 0]['project_id'].nunique()} / {len(linked_projects)}")
print("Component 3 complete.")
