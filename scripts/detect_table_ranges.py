import os
import glob
import re
import pymupdf

def get_report_month_from_doc(doc, filepath):
    fname = os.path.basename(filepath).lower()
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    for mname, mnum in month_map.items():
        if mname in fname:
            y_match = re.search(r'202[4-7]', fname)
            if y_match:
                return f"{y_match.group(0)}-{mnum}"
    for pno in range(min(3, len(doc))):
        text = doc[pno].get_text()
        for mname, mnum in month_map.items():
            pattern = rf'{mname}[a-z]*\s+(202[4-7])'
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return f"{m.group(1)}-{mnum}"
    return None

def detect_pdf_tables(doc, filepath):
    """
    Returns a dictionary of detected tables and their [start_page, end_page] (1-indexed).
    """
    total_pages = len(doc)
    fname = os.path.basename(filepath)
    tables = {}
    
    # Check if Legacy report (April, May, June 2025)
    if 'FRApril' in fname or 'FR_May' in fname or 'FR_JUNE' in fname:
        if 'FRApril' in fname:
            tables['completed'] = {'name': 'Table 3: Completed Projects', 'start': 11, 'end': 14}
            tables['newly_added'] = {'name': 'Table 4: Newly Added Projects', 'start': 15, 'end': 18}
            tables['north_east'] = {'name': 'Table 5: Ongoing Projects of North-East Region', 'start': 19, 'end': 38}
            tables['ongoing'] = {'name': 'Table 6: All Ongoing Projects', 'start': 39, 'end': total_pages - 1}
        elif 'FR_May' in fname:
            tables['completed'] = {'name': 'Table 3: Completed Projects', 'start': 11, 'end': 15}
            tables['newly_added'] = {'name': 'Table 4: Newly Added Projects', 'start': 16, 'end': 17}
            tables['north_east'] = {'name': 'Table 6: Ongoing Projects of North-East Region', 'start': 19, 'end': 38}
            tables['ongoing'] = {'name': 'Table 7: All Ongoing Projects', 'start': 39, 'end': total_pages - 1}
        elif 'FR_JUNE' in fname:
            tables['completed'] = {'name': 'Table 3: Completed Projects', 'start': 11, 'end': 15}
            tables['newly_added'] = {'name': 'Table 4: Newly Added Projects', 'start': 16, 'end': 16}
            tables['north_east'] = {'name': 'Table 6: Ongoing Projects of North-East Region', 'start': 18, 'end': 36}
            tables['ongoing'] = {'name': 'Table 7: All Ongoing Projects', 'start': 37, 'end': total_pages - 1}
        return tables

    # Modern PAIMANA reports (July 2025 to June 2026)
    # July & August 2025 have only Table 3 (North East) & Table 4 (All Ongoing)
    if 'July_2025' in fname or 'August_2025' in fname:
        tables['north_east'] = {'name': 'Table 3: Ongoing Projects of North Eastern Region', 'start': 32, 'end': 35}
        tables['ongoing'] = {'name': 'Table 4: All Ongoing Projects', 'start': 36, 'end': total_pages}
        return tables

    # Standard PAIMANA (September 2025 to June 2026)
    # Search headings across pages
    t3_start, t4_start, t5_start, t6_start = None, None, None, None
    for pno in range(15, min(70, total_pages)):
        text = doc[pno].get_text()
        first_lines = '\n'.join([l.strip() for l in text.splitlines() if l.strip()][:10])
        if re.search(r'Table\s*3\s*:\s*Completed', first_lines, re.IGNORECASE) and not t3_start:
            t3_start = pno + 1
        elif re.search(r'Table\s*4\s*:\s*Newly\s*Added', first_lines, re.IGNORECASE) and not t4_start:
            t4_start = pno + 1
        elif re.search(r'Table\s*5\s*:\s*Ongoing\s*Projects', first_lines, re.IGNORECASE) and not t5_start:
            t5_start = pno + 1
        elif re.search(r'Table\s*6\s*:\s*All\s*Ongoing', first_lines, re.IGNORECASE) and not t6_start:
            t6_start = pno + 1

    if t3_start:
        t3_data_start = t3_start + 1 # First data page after title divider
        t4_data_start = (t4_start + 1) if t4_start else (t5_start or t6_start)
        t5_data_start = (t5_start + 1) if t5_start else t6_start
        t6_data_start = (t6_start + 1) if t6_start else total_pages
        
        tables['completed'] = {'name': 'Table 3: Completed Projects', 'start': t3_data_start, 'end': t4_start - 1 if t4_start else t5_start - 1}
        if t4_start:
            tables['newly_added'] = {'name': 'Table 4: Newly Added Projects', 'start': t4_data_start, 'end': t5_start - 1 if t5_start else t6_start - 1}
        if t5_start:
            tables['north_east'] = {'name': 'Table 5: Ongoing Projects of North Eastern Region', 'start': t5_data_start, 'end': t6_start - 1}
        if t6_start:
            tables['ongoing'] = {'name': 'Table 6: All Ongoing Projects', 'start': t6_data_start, 'end': total_pages}
            
    return tables

if __name__ == '__main__':
    for pf in sorted(glob.glob('dataset/*.pdf')):
        doc = pymupdf.open(pf)
        rmonth = get_report_month_from_doc(doc, pf)
        tbls = detect_pdf_tables(doc, pf)
        print(f"=== {pf} ({rmonth}) ===")
        for k, v in tbls.items():
            print(f"  {k:12}: {v['name']} (Pages {v['start']} - {v['end']})")
