import re
import pandas as pd
import numpy as np

MONTH_NAME_MAP = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'september': 9, 'sept': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12
}

def normalize_report_month(val):
    """
    Normalizes report month to YYYY-MM format.
    Example: 'March 2026' -> '2026-03'
    """
    if not val or pd.isna(val):
        return None
    val_str = str(val).strip()
    
    if re.match(r'^\d{4}-\d{2}$', val_str):
        return val_str
        
    m = re.search(r'([A-Za-z]+)[_\s]*(\d{4})', val_str)
    if m:
        mname = m.group(1).lower()
        year = int(m.group(2))
        for k, v in MONTH_NAME_MAP.items():
            if mname.startswith(k):
                return f"{year:04d}-{v:02d}"
                
    m2 = re.search(r'(\d{4})[_\s]*([A-Za-z]+)', val_str)
    if m2:
        year = int(m2.group(1))
        mname = m2.group(2).lower()
        for k, v in MONTH_NAME_MAP.items():
            if mname.startswith(k):
                return f"{year:04d}-{v:02d}"
                
    return val_str

def normalize_date(val):
    """
    Normalizes date string to YYYY-MM format when month and year are provided.
    Converts missing/invalid placeholders ('-', 'NA', 'Nil') to None.
    """
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip('(){}[] \t\r\n')
    if val_str.lower() in ['', '-', '--', '---', 'na', 'n.a.', 'nil', 'null', 'none']:
        return None
        
    m = re.search(r'\b(\d{1,2})[/-](\d{4})\b', val_str)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12 and 1950 <= year <= 2060:
            return f"{year:04d}-{month:02d}"
            
    m_name = re.search(r'\b([A-Za-z]{3,9})[/-](\d{4})\b', val_str)
    if m_name:
        mname = m_name.group(1).lower()
        year = int(m_name.group(2))
        for k, v in MONTH_NAME_MAP.items():
            if mname.startswith(k):
                if 1950 <= year <= 2060:
                    return f"{year:04d}-{v:02d}"
                    
    m_ym = re.search(r'\b(\d{4})[/-](\d{1,2})\b', val_str)
    if m_ym:
        year = int(m_ym.group(1))
        month = int(m_ym.group(2))
        if 1 <= month <= 12 and 1950 <= year <= 2060:
            return f"{year:04d}-{month:02d}"
            
    return None

def normalize_numeric(val, is_percentage=False):
    """
    Normalizes a numerical field to float.
    Removes commas, currency signs, parens.
    Returns None for missing/invalid placeholders.
    Enforces 0 <= percentage <= 100 if is_percentage=True.
    """
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip('(){}[] \t\r\n').replace(',', '')
    if val_str.lower() in ['', '-', '--', '---', 'na', 'n.a.', 'nil', 'null', 'none']:
        return None
    
    # Don't parse dates as numbers
    if re.search(r'\b\d{1,2}/\d{4}\b', val_str) or re.search(r'\b\d{4}-\d{2}\b', val_str):
        return None
        
    m = re.search(r'[-+]?\d*\.?\d+', val_str)
    if m:
        try:
            num = float(m.group(0))
            if is_percentage:
                if 0.0 <= num <= 100.0:
                    return round(num, 2)
                else:
                    return None
            return round(num, 4)
        except ValueError:
            return None
    return None

def clean_text_field(val):
    """
    Cleans text strings, trims excess whitespace, linebreaks, and placeholder symbols.
    """
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip()
    val_str = re.sub(r'\s+', ' ', val_str)
    if val_str.lower() in ['', '-', '--', '---', 'na', 'n.a.', 'nil', 'null', 'none', '(-)', '(-) (-)']:
        return None
    return val_str

def normalize_project_record(record):
    """
    Applies standard normalization rules to a raw project dictionary.
    """
    cleaned = {}
    
    cleaned['project_id'] = clean_text_field(record.get('project_id'))
    cleaned['legacy_ocms_code'] = clean_text_field(record.get('legacy_ocms_code'))
    cleaned['project_name'] = clean_text_field(record.get('project_name'))
    cleaned['agency'] = clean_text_field(record.get('agency'))
    cleaned['state'] = clean_text_field(record.get('state'))
    
    cleaned['approval_start_date'] = normalize_date(record.get('approval_start_date'))
    cleaned['original_completion_date'] = normalize_date(record.get('original_completion_date'))
    cleaned['revised_completion_date'] = normalize_date(record.get('revised_completion_date'))
    
    if 'actual_completion_date' in record:
        cleaned['actual_completion_date'] = normalize_date(record.get('actual_completion_date'))
        
    cleaned['original_cost_crore'] = normalize_numeric(record.get('original_cost_crore'))
    cleaned['revised_cost_crore'] = normalize_numeric(record.get('revised_cost_crore'))
    cleaned['cumulative_expenditure_crore'] = normalize_numeric(record.get('cumulative_expenditure_crore'))
    
    if 'physical_progress_percent' in record:
        cleaned['physical_progress_percent'] = normalize_numeric(record.get('physical_progress_percent'), is_percentage=True)
        
    cleaned['report_month'] = normalize_report_month(record.get('report_month'))
    cleaned['source_file'] = clean_text_field(record.get('source_file'))
    cleaned['source_table'] = clean_text_field(record.get('source_table'))
    
    return cleaned
