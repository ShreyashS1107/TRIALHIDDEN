import os
import re
import pymupdf
import pandas as pd

def parse_date_str(val):
    if not val:
        return None
    val = str(val).strip('(){}[] \t\r\n')
    if val in ['', '-', '--', 'NA', 'N.A.', 'NIL', 'Nil', 'null', 'None']:
        return None
    # Handle formats like 03/2023, 3/2023, 3-2023, 03-2023, Jan-2026, 2023-03
    m = re.search(r'(\d{1,2})[/-](\d{4})', val)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12 and 1950 <= year <= 2050:
            return f"{year:04d}-{month:02d}"
    # Handle Year-Month e.g. 2024-03
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

def extract_ongoing_legacy(doc, start_page, end_page, report_month, filename, table_name):
    """
    Extracts Ongoing Projects from Legacy OCMS layout (Apr, May, Jun 2025).
    """
    rows = []
    current_state = None
    current_sector = None
    
    for pno in range(start_page - 1, end_page):
        page = doc[pno]
        blocks = page.get_text('blocks')
        
        # Sort blocks top-to-bottom
        p_height = page.rect.height
        
        # Filter table content blocks
        content_blocks = [
            b for b in blocks 
            if 100 <= b[1] <= p_height - 35
        ]
        
        # Track State changes in the far left margin (x < 70)
        # Track Sector changes at x between 70 and 140
        # Project blocks are at x between 140 and 310
        
        proj_blocks = []
        for b in content_blocks:
            x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4].strip()
            # If in left margin and single or few uppercase words -> State
            if x0 < 70 and y0 >= 140:
                clean_t = ' '.join(text.split())
                if clean_t not in ['State', 'Sl. No.', 'Sl No', 'Sector']:
                    current_state = clean_t
            # Check for project description block
            if 135 <= x0 <= 155 and y0 >= 140:
                if not text.startswith('Total') and not text.startswith('Sl No') and not text.startswith('Project Name'):
                    proj_blocks.append(b)
        
        proj_blocks.sort(key=lambda b: b[1])
        
        for pb in proj_blocks:
            y_top = pb[1] - 4
            y_bot = pb[3] + 4
            
            # Find state on the same row if explicitly present
            state_blocks = [b for b in content_blocks if y_top <= (b[1]+b[3])/2 <= y_bot and b[0] < 70]
            if state_blocks:
                clean_st = ' '.join(state_blocks[0][4].strip().split())
                if clean_st not in ['State', 'Sl. No.', 'Sl No', 'Sector']:
                    current_state = clean_st
            
            # Find all other blocks on this page in this y-slice
            slice_blocks = [
                b for b in content_blocks 
                if y_top <= (b[1] + b[3]) / 2 <= y_bot and b != pb and b[0] >= 300
            ]
            slice_blocks.sort(key=lambda b: b[0])
            
            # Parse project description block
            pb_text = pb[4].strip()
            pb_lines = [l.strip() for l in pb_text.splitlines() if l.strip()]
            
            # In legacy layout, first line may be Sl No, followed by Name, (Agency ), (Project Code )
            sl_no = None
            proj_name_parts = []
            agency = None
            project_id = None
            legacy_ocms_code = None
            
            for line in pb_lines:
                if line.isdigit() and sl_no is None and not proj_name_parts:
                    sl_no = line
                    continue
                
                # Check for agency in parentheses e.g. (NHIDCL )
                ocms_match = re.search(r'\(?\b([A-Za-z]\d{8})\b\)?', line)
                if ocms_match:
                    legacy_ocms_code = ocms_match.group(1)
                    project_id = legacy_ocms_code
                elif (line.startswith('(') and line.endswith(')')) or (line.startswith('(') and ')' in line):
                    clean_ag = line.strip('() ')
                    if not agency and clean_ag not in ['-', '--', 'NA']:
                        agency = clean_ag
                else:
                    proj_name_parts.append(line)
                    
            project_name = ' '.join(proj_name_parts).strip()
            
            if not project_id:
                m_ocms = re.search(r'([A-Za-z]\d{8})', pb_text)
                if m_ocms:
                    project_id = m_ocms.group(1)
                    legacy_ocms_code = project_id
            
            # Parse slice blocks for Dates, Cost, Expenditure, Progress
            approval_date = None
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
                
                if 300 <= x_mid < 440:
                    # Dates: Approval date & Commissioning dates
                    for sl in sb_lines:
                        # check for date
                        d_parsed = parse_date_str(sl)
                        if d_parsed:
                            if not approval_date and ('-' in sl or '/' in sl) and not ('(' in sl or '{' in sl):
                                approval_date = d_parsed
                            elif not orig_doc and not ('(' in sl or '{' in sl):
                                orig_doc = d_parsed
                            elif not rev_doc:
                                rev_doc = d_parsed
                elif 440 <= x_mid < 510:
                    # Costs: Original, Revised, Anticipated
                    for sl in sb_lines:
                        f_val = parse_float_val(sl)
                        if f_val is not None:
                            if orig_cost is None and not ('(' in sl or '{' in sl):
                                orig_cost = f_val
                            elif rev_cost is None:
                                rev_cost = f_val
                elif 510 <= x_mid < 560:
                    # Cumulative Expenditure
                    for sl in sb_lines:
                        f_val = parse_float_val(sl)
                        if f_val is not None and cum_exp is None:
                            cum_exp = f_val
                elif 560 <= x_mid <= 620:
                    # Physical Progress (%)
                    for sl in sb_lines:
                        f_val = parse_float_val(sl)
                        if f_val is not None and phy_prog is None:
                            phy_prog = f_val
            
            rows.append({
                'project_id': project_id,
                'project_name': project_name,
                'agency': agency,
                'legacy_ocms_code': legacy_ocms_code,
                'state': current_state,
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
