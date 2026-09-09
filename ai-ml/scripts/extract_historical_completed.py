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
os.makedirs(output_dir, exist_ok=True)

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
    if val in ['', '-', '--', 'NA', 'N.A.', 'NIL', 'Nil', 'null', 'None', 'Unfinalised', 'Not Finalised', 'N. A.']:
        return None
    # Handle formats like 03/2023, 3/2023, 3-2023, 03-2023, Jan-2026, 2023-03
    m = re.search(r'(\d{1,2})[/-](\d{4})', val)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12 and 1950 <= year <= 2050:
            return f"{year:04d}-{month:02d}"
    # Handle Month Year e.g. April, 2023 or April 2023
    m_my = re.search(r'([A-Za-z]+)[,\s]+(\d{4})', val)
    if m_my:
        m_str = m_my.group(1).lower()
        if m_str in months_map:
            month = months_map[m_str]
            year = int(m_my.group(2))
            if 1950 <= year <= 2050:
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

def extract_completed_from_pdf(filepath):
    fname = os.path.basename(filepath)
    doc = fitz.open(filepath)
    num_pages = len(doc)
    
    # Determine report month/year
    first_pages_txt = ""
    for i in range(min(5, num_pages)):
        first_pages_txt += doc[i].get_text() + "\n"
        
    m_date_text = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*(20\d\d|19\d\d)', first_pages_txt, re.IGNORECASE)
    rep_date = None
    if m_date_text:
        m_str = m_date_text.group(1).lower()
        if m_str in months_map:
            rep_date = f"{int(m_date_text.group(2)):04d}-{months_map[m_str]:02d}"
            
    if not rep_date:
        fn_clean = fname.lower()
        fn_m = None
        for m_k in sorted(months_map.keys(), key=lambda x: -len(x)):
            if m_k in fn_clean:
                fn_m = months_map[m_k]
                break
        m_y = re.search(r'(20\d\d|19\d\d)', fname)
        if m_y and fn_m:
            rep_date = f"{int(m_y.group(1)):04d}-{fn_m:02d}"
            
    if not rep_date:
        doc.close()
        return []
        
    extracted_records = []
    
    # Identify pages containing Completed Projects Table
    for pno in range(num_pages):
        txt = doc[pno].get_text()
        txt_lower = txt.lower()
        
        is_completed_page = False
        table_name = None
        
        if "month wise list of completed" in txt_lower or "list of completed projects" in txt_lower:
            is_completed_page = True
            table_name = "Table: Month-wise Completed Projects"
        elif "list of projects completed/dropped/frozen" in txt_lower:
            is_completed_page = True
            table_name = "Table: Projects Completed/Dropped/Frozen"
        elif "table 3: completed projects" in txt_lower or "table 5: completed projects" in txt_lower:
            is_completed_page = True
            table_name = "Table 3: Completed Projects"
            
        if not is_completed_page:
            continue
            
        # Parse blocks on this page
        blocks = doc[pno].get_text("blocks")
        # Sort blocks vertically
        blocks.sort(key=lambda b: b[1])
        
        current_sector = None
        current_completion_month = rep_date # fallback to report month
        
        # Look for month subheaders like 'April,2023', 'May, 2022', etc.
        for b in blocks:
            b_txt = b[4].strip()
            # Check if block is a month header
            m_comp = re.search(r'^(January|February|March|April|May|June|July|August|September|October|November|December)[,\s]+(20\d\d)', b_txt, re.IGNORECASE)
            if m_comp:
                m_s = m_comp.group(1).lower()
                y_s = int(m_comp.group(2))
                if m_s in months_map:
                    current_completion_month = f"{y_s:04d}-{months_map[m_s]:02d}"
                    
            # Check if sector header
            sector_candidates = ['ATOMIC ENERGY', 'CIVIL AVIATION', 'COAL', 'FERTILIZERS', 'MINES', 'STEEL', 'PETROLEUM', 'POWER', 'RAILWAYS', 'ROAD TRANSPORT & HIGHWAYS', 'ROAD TRANSPORT AND HIGHWAYS', 'SHIPPING', 'PORTS', 'TELECOMMUNICATIONS', 'URBAN DEVELOPMENT', 'WATER RESOURCES', 'HEALTH AND FAMILY WELFARE', 'DEFENCE']
            for sc in sector_candidates:
                if sc in b_txt.upper() and len(b_txt.split('\n')) <= 3:
                    current_sector = sc
                    break
                    
            # Check for project description with code [N...] or [0-9...]
            code_matches = re.findall(r'\[([A-Z0-9_-]{6,15})\]', b_txt)
            if code_matches:
                for code in code_matches:
                    code_clean = code.strip().upper()
                    if code_clean.startswith('PAGE') or code_clean.startswith('TOTAL'):
                        continue
                        
                    # Extract project name, agency
                    lines = [l.strip() for l in b_txt.split('\n') if l.strip()]
                    proj_name = lines[0] if lines else b_txt
                    
                    # Look for agency inside parentheses
                    agency = None
                    m_ag = re.search(r'\(([^)]+)\)', b_txt)
                    if m_ag:
                        agency = m_ag.group(1).strip()
                        
                    # Find numbers and dates on or near this block
                    # Search around the block y-coordinates
                    y_top = b[1] - 15
                    y_bot = b[3] + 25
                    
                    row_blocks = [rb for rb in blocks if y_top <= (rb[1]+rb[3])/2 <= y_bot]
                    row_txt = " \n ".join([rb[4] for rb in row_blocks])
                    
                    # Extract dates
                    dates_found = []
                    for w in re.split(r'[\s\n]+', row_txt):
                        d = parse_date_str(w)
                        if d and d not in dates_found:
                            dates_found.append(d)
                            
                    # Extract floats
                    floats_found = []
                    for w in re.split(r'[\s\n]+', row_txt):
                        f = parse_float_val(w)
                        if f is not None and f not in floats_found and f > 1.0: # filter small sl no
                            floats_found.append(f)
                            
                    # Original cost, expenditure, revised cost
                    orig_cost = floats_found[0] if len(floats_found) >= 1 else None
                    cum_exp = floats_found[1] if len(floats_found) >= 2 else (floats_found[0] if len(floats_found) == 1 else None)
                    
                    # Original DOC
                    orig_doc = dates_found[0] if dates_found else None
                    # Actual completion date: use section month if valid, else report date
                    act_doc = current_completion_month if current_completion_month else rep_date
                    
                    extracted_records.append({
                        'project_id': code_clean,
                        'ocms_code': code_clean,
                        'project_name': proj_name,
                        'sector': current_sector if current_sector else "CENTRAL SECTOR",
                        'agency': agency if agency else "UNKNOWN",
                        'ministry': current_sector if current_sector else "UNKNOWN",
                        'state': "CENTRAL / UNKNOWN",
                        'original_cost': orig_cost,
                        'final_or_revised_cost': None, # We will strictly preserve this as None if no separate sanctioned revised cost is given
                        'cumulative_expenditure_crore': cum_exp,
                        'cost_field_used': 'cumulative_expenditure_only' if cum_exp else 'none',
                        'original_doc': orig_doc,
                        'actual_completion_date': act_doc,
                        'time_overrun_months': None,
                        'cost_overrun_pct': None,
                        'report_month': rep_date,
                        'source_file': fname,
                        'source_table': table_name,
                        'source_page': pno + 1
                    })
                    
    doc.close()
    return extracted_records

print("Starting extraction of completed projects across all 2011–2025 OCMS PDFs...")
all_completed = []
all_pdf_files = sorted(glob.glob(os.path.join(dataset_dir, "*.pdf")))

for idx, p in enumerate(all_pdf_files):
    fname = os.path.basename(p)
    # Filter 2011-2025 OCMS files
    if "FlashReport_" in fname and ("2025" in fname or "2026" in fname):
        continue
    m_y = re.search(r'(20\d\d|19\d\d)', fname)
    if m_y:
        y = int(m_y.group(1))
        if y < 2011:
            continue
            
    recs = extract_completed_from_pdf(p)
    if recs:
        all_completed.extend(recs)
        
print(f"Extracted {len(all_completed)} raw completed project record entries from OCMS reports.")

# Also load existing PAIMANA completed projects
paimana_comp_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_completed_projects.csv"
p_comp_df = pd.read_csv(paimana_comp_path)
print(f"Loaded {len(p_comp_df)} PAIMANA completed project entries.")

for _, r in p_comp_df.iterrows():
    all_completed.append({
        'project_id': str(r.get('project_id', r.get('legacy_ocms_code', 'UNKNOWN'))),
        'ocms_code': str(r.get('legacy_ocms_code', r.get('project_id', 'UNKNOWN'))),
        'project_name': str(r.get('project_name', 'UNKNOWN')),
        'sector': str(r.get('sector', 'UNKNOWN')),
        'agency': str(r.get('agency', 'UNKNOWN')),
        'ministry': str(r.get('ministry', 'UNKNOWN')),
        'state': str(r.get('state', 'UNKNOWN')),
        'original_cost': parse_float_val(r.get('original_cost_crore')),
        'final_or_revised_cost': parse_float_val(r.get('revised_cost_crore')),
        'cumulative_expenditure_crore': parse_float_val(r.get('cumulative_expenditure_crore')),
        'cost_field_used': 'revised_cost_crore' if pd.notna(r.get('revised_cost_crore')) else ('cumulative_expenditure_crore' if pd.notna(r.get('cumulative_expenditure_crore')) else 'none'),
        'original_doc': parse_date_str(r.get('original_completion_date')),
        'actual_completion_date': parse_date_str(r.get('actual_completion_date', r.get('report_month'))),
        'time_overrun_months': None,
        'cost_overrun_pct': None,
        'report_month': parse_date_str(r.get('report_month')),
        'source_file': str(r.get('source_file', 'PAIMANA')),
        'source_table': str(r.get('source_table', 'Table 3: Completed Projects')),
        'source_page': None
    })

df_comp = pd.DataFrame(all_completed)
print(f"Total aggregated completed records: {len(df_comp)}")

# Deduplicate by (project_id, actual_completion_date) or take latest known report
# Clean codes
df_comp['project_id'] = df_comp['project_id'].astype(str).str.strip().str.upper()
df_comp['ocms_code'] = df_comp['ocms_code'].astype(str).str.strip().str.upper()
df_comp = df_comp[df_comp['project_id'].str.len() >= 5]

# Sort by report_month descending and drop duplicates per project_id
df_comp.sort_values(by=['report_month', 'source_file'], ascending=[False, False], inplace=True)
df_dedup = df_comp.drop_duplicates(subset=['project_id']).copy()
df_dedup.sort_values(by=['actual_completion_date', 'project_id'], inplace=True)

# -------------------------------------------------------------
# CONSTRUCT HISTORICAL OUTCOME METRICS (STRICT DEFINITIONS)
# -------------------------------------------------------------
# Schedule Outcome:
def calc_delay(row):
    act = row['actual_completion_date']
    orig = row['original_doc']
    if pd.isna(act) or pd.isna(orig):
        return pd.Series([np.nan, np.nan])
    try:
        y_act, m_act = int(act[:4]), int(act[5:7])
        y_orig, m_orig = int(orig[:4]), int(orig[5:7])
        diff_months = (y_act - y_orig) * 12 + (m_act - m_orig)
        flag = 1.0 if diff_months > 0 else 0.0
        return pd.Series([flag, float(diff_months)])
    except Exception:
        return pd.Series([np.nan, np.nan])

delay_res = df_dedup.apply(calc_delay, axis=1)
df_dedup['historical_delay_flag'] = delay_res[0]
df_dedup['historical_delay_months'] = delay_res[1]

# Cost Outcome:
# STRICT RULE: Only calculate when final_or_revised_cost is available.
# If only cumulative_expenditure is available, DO NOT classify as final project cost.
def calc_cost_overrun(row):
    final_c = row['final_or_revised_cost']
    orig_c = row['original_cost']
    if pd.isna(final_c) or pd.isna(orig_c) or orig_c <= 0:
        return pd.Series([np.nan, np.nan])
    try:
        flag = 1.0 if final_c > orig_c else 0.0
        pct = ((final_c - orig_c) / orig_c) * 100.0
        return pd.Series([flag, float(pct)])
    except Exception:
        return pd.Series([np.nan, np.nan])

cost_res = df_dedup.apply(calc_cost_overrun, axis=1)
df_dedup['historical_cost_overrun_flag'] = cost_res[0]
df_dedup['historical_cost_overrun_pct'] = cost_res[1]

output_file = os.path.join(output_dir, "historical_completed_projects.csv")
df_dedup.to_csv(output_file, index=False)
print(f"\nSaved {output_file} with {len(df_dedup)} unique completed projects.")
print(f"Schedule outcomes available: {df_dedup['historical_delay_flag'].notna().sum()} / {len(df_dedup)}")
print(f"Cost outcomes available: {df_dedup['historical_cost_overrun_flag'].notna().sum()} / {len(df_dedup)}")
print(f"Delay rate among known: {df_dedup['historical_delay_flag'].mean()*100:.2f}%")
print(f"Mean delay months: {df_dedup['historical_delay_months'].mean():.2f} months")
print(f"Unique agencies: {df_dedup['agency'].nunique()}")
print(f"Unique sectors: {df_dedup['sector'].nunique()}")
