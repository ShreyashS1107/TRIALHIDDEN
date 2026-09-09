import os
import re
import pymupdf
import pandas as pd

def extract_ongoing_paimana_standard(doc, start_page, end_page, report_month, filename, table_name):
    """
    Extracts 'All Ongoing Projects' from standard PAIMANA layout (Jul 2025 - Jun 2026).
    """
    rows = []
    
    for pno in range(start_page - 1, end_page):
        page = doc[pno]
        blocks = page.get_text('blocks')
        
        # Filter content blocks
        # Header ends around y=250, footer starts around y=1430 (or page.rect.height - 40)
        p_height = page.rect.height
        p_width = page.rect.width
        
        content_blocks = [
            b for b in blocks 
            if b[1] >= 180 and b[3] <= p_height - 35
        ]
        
        # Identify project description blocks
        # Usually located at x0 between 75 and 110, with width spanning to ~450
        # Exclude Ministry headers, sector subtitles, and 'Total' summary lines
        proj_blocks = []
        for b in content_blocks:
            x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
            # Check if this looks like a project description block
            if 70 <= x0 <= 120 and y0 >= 220:
                if text.startswith('Ministry of') or text.startswith('Department of') or text.startswith('Total ('):
                    continue
                if 'Aviation Infrastructure' in text or 'Thermal Power' in text or 'Hydro Power' in text:
                    continue
                if text.startswith('Sl.No') or text.startswith('Project Name'):
                    continue
                proj_blocks.append(b)
        
        # Sort project blocks by y0
        proj_blocks.sort(key=lambda b: b[1])
        
        for i, pb in enumerate(proj_blocks):
            y_top = pb[1] - 4
            y_bot = pb[3] + 4
            
            # Find all other blocks on this page in this vertical slice
            slice_blocks = [
                b for b in content_blocks 
                if y_top <= (b[1] + b[3]) / 2 <= y_bot and b != pb and b[0] > 65
            ]
            slice_blocks.sort(key=lambda b: b[0])
            
            # Parse project description block (pb)
            pb_text = pb[4].strip()
            pb_lines = [l.strip() for l in pb_text.splitlines() if l.strip()]
            
            # Extract Project Name, Agency, Project Code, Legacy OCMS Code, PMGID
            # Project name is usually top lines
            # Agency is usually in parentheses e.g. (Airport Authority of India [AAI])
            # Project code is (612786) or 6-digit number
            # Legacy OCMS is (N04000106)
            proj_name_parts = []
            agency = None
            project_id = None
            legacy_ocms_code = None
            
            for line in pb_lines:
                # check for project code e.g. (612786) or 612786
                code_match = re.search(r'\(?\b(\d{5,7})\b\)?', line)
                ocms_match = re.search(r'\(?\b([A-Za-z]\d{8})\b\)?', line)
                
                # Check for agency in parentheses
                if (line.startswith('(') and line.endswith(')')) or ('[' in line and ']' in line):
                    # Check if it's code line
                    if ocms_match:
                        legacy_ocms_code = ocms_match.group(1)
                    if code_match and not project_id:
                        # Ensure it's not PMGID
                        project_id = code_match.group(1)
                    if not ocms_match and not (line.replace('(','').replace(')','').replace('-','').strip().isdigit() or line.replace('(','').replace(')','').strip() in ['-', '--']):
                        if not agency:
                            agency = line.strip('() ')
                else:
                    if not project_id and code_match:
                        project_id = code_match.group(1)
                    if not legacy_ocms_code and ocms_match:
                        legacy_ocms_code = ocms_match.group(1)
                    if not code_match and not ocms_match:
                        proj_name_parts.append(line)
            
            project_name = ' '.join(proj_name_parts).strip()
            
            # If project_id was not found in pb_lines, search anywhere in pb_text
            if not project_id:
                m_pid = re.search(r'\((\d{5,7})\)', pb_text)
                if m_pid:
                    project_id = m_pid.group(1)
                else:
                    m_ocms = re.search(r'\(([A-Za-z]\d{8})\)', pb_text)
                    if m_ocms:
                        project_id = m_ocms.group(1)
            
            if not legacy_ocms_code:
                m_ocms = re.search(r'\(([A-Za-z]\d{8})\)', pb_text)
                if m_ocms:
                    legacy_ocms_code = m_ocms.group(1)
            
            # Parse slice blocks for State, Dates, Cost, Expenditure, Progress
            state = None
            approval_date = None
            start_date = None
            orig_doc = None
            rev_doc = None
            orig_cost = None
            rev_cost = None
            cum_exp = None
            phy_prog = None
            
            for sb in slice_blocks:
                x_mid = (sb[0] + sb[2]) / 2
                sb_text = sb[4].strip()
                sb_lines = [l.strip() for l in sb_text.splitlines() if l.strip()]
                
                if x_mid < 650:
                    # State & Approval / Start date column
                    for sl in sb_lines:
                        # check for date MM/YYYY or (MM/YYYY)
                        dm = re.findall(r'\(?(\d{1,2}/\d{4})\)?', sl)
                        if dm:
                            if not approval_date:
                                approval_date = dm[0]
                            if len(dm) > 1 and not start_date:
                                start_date = dm[1]
                        else:
                            # State text
                            if sl not in ['-', '--', 'NA', 'N.A.']:
                                if not state:
                                    state = sl
                                else:
                                    state += ' ' + sl
                elif 650 <= x_mid < 750:
                    # DoC column: Original DoC & Revised DoC
                    for sl in sb_lines:
                        dm = re.findall(r'\(?(\d{1,2}/\d{4})\)?', sl)
                        if dm:
                            if not orig_doc:
                                orig_doc = dm[0]
                            if len(dm) > 1 and not rev_doc:
                                rev_doc = dm[1]
                        elif '(' in sl and ')' in sl:
                            # Might be revised DoC in parens
                            clean_d = sl.strip('() ')
                            if re.match(r'^\d{1,2}/\d{4}$', clean_d) and not rev_doc:
                                rev_doc = clean_d
                elif x_mid >= 750:
                    # Cost, Cumulative Exp, Physical Progress
                    # Extract numbers from lines
                    for sl in sb_lines:
                        # Extract float/int values
                        num_matches = re.findall(r'\(?(\d+(?:\.\d+)?)\)?', sl.replace(',', ''))
                        # Also handle "-"
                        # If a line has numbers, distribute them
                        for nm in num_matches:
                            val = float(nm)
                            if orig_cost is None:
                                orig_cost = val
                            elif rev_cost is None and ('(' in sl or len(num_matches) > 1):
                                rev_cost = val
                            elif cum_exp is None:
                                cum_exp = val
                            elif phy_prog is None:
                                phy_prog = val
            
            rows.append({
                'project_id': project_id,
                'project_name': project_name,
                'agency': agency,
                'legacy_ocms_code': legacy_ocms_code,
                'state': state,
                'approval_start_date': approval_date,
                'original_completion_date': orig_doc,
                'revised_completion_date': rev_doc,
                'original_cost_crore': orig_cost,
                'revised_cost_crore': rev_cost,
                'cumulative_expenditure_crore': cum_exp,
                'physical_progress_percent': phy_prog,
                'report_month': report_month,
                'source_file': os.path.basename(filename),
                'source_table': table_name
            })
            
    return rows

print("Function defined successfully.")
