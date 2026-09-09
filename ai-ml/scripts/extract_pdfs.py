import os
import sys
import glob
import re
import pymupdf
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.detect_table_ranges import detect_pdf_tables, get_report_month_from_doc
from scripts.normalize_data import normalize_project_record, normalize_numeric, normalize_date, clean_text_field

SECTOR_HEADER_NAMES = {
    'aviation & aviation infrastructure', 'coal', 'mines', 'steel', 'petroleum', 'petroleum & natural gas',
    'power', 'thermal power', 'hydro power', 'nuclear power', 'renewable energy', 'transmission & distribution',
    'railways', 'roads & highways', 'road transport & highways', 'shipping & ports', 'ports & shipping',
    'telecommunications', 'urban development', 'housing & urban affairs', 'water resources',
    'atomic energy', 'fertilizers', 'chemicals & petrochemicals', 'health & family welfare',
    'higher education', 'education', 'heavy industry', 'defence', 'defence production',
    'commerce', 'industry & internal trade', 'electronics & information technology',
    'development of north eastern region', 'food & public distribution', 'electricity generation',
    'real estate', 'commercial complex', 'tourism', 'waste & water', 'healthcare', 'social infrastructure',
    'civil aviation', 'petroleum', 'road transport and highways', 'department of higher education',
    'ministry of civil aviation', 'ministry of coal', 'ministry of mines', 'ministry of power',
    'ministry of railways', 'ministry of petroleum & natural gas', 'ministry of road transport & highways',
    'ministry of housing & urban affairs', 'ministry of jal shakti', 'ministry of shipping',
    'ministry of steel', 'ministry of chemicals and fertilizers', 'ministry of heavy industries',
    'ministry of ports, shipping and waterways', 'ministry of health and family welfare',
    'ministry of defence', 'ministry of communications', 'department of telecommunications',
    'department for promotion of industry & internal trade'
}

def is_sector_header(text):
    clean_t = text.strip().lower()
    if clean_t in SECTOR_HEADER_NAMES:
        return True
    if clean_t.startswith('ministry of') or clean_t.startswith('department of') or clean_t.startswith('total ('):
        return True
    return False

def strip_outer_brackets(text):
    t = text.strip()
    if (t.startswith('(') and t.endswith(')')) or (t.startswith('[') and t.endswith(']')):
        return t[1:-1].strip()
    return t

def extract_ongoing_modern(doc, start_page, end_page, report_month, filename, table_name, warnings_list):
    """
    Extracts 'All Ongoing Projects' from modern PAIMANA reports (July 2025 to June 2026).
    """
    rows = []
    
    for pno in range(start_page - 1, end_page):
        page = doc[pno]
        blocks = page.get_text('blocks')
        p_height = page.rect.height
        
        content_blocks = [
            b for b in blocks 
            if b[1] >= 180 and b[3] <= p_height - 35
        ]
        
        # Find row starters (either standalone Sl block or project block)
        # Check blocks at x0 between 50 and 130
        row_starters = []
        for b in content_blocks:
            x0, y0, text = b[0], b[1], b[4].strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if 50 <= x0 <= 130 and y0 >= 220:
                if is_sector_header(text):
                    continue
                if text.startswith('Sl.No') or text.startswith('Project Name') or text.startswith('Page '):
                    continue
                row_starters.append(b)
                
        row_starters.sort(key=lambda b: b[1])
        
        for i, pb in enumerate(row_starters):
            y_top = pb[1] - 4
            y_bot = row_starters[i+1][1] - 4 if i+1 < len(row_starters) else (p_height - 35)
            
            slice_blocks = [
                b for b in content_blocks 
                if y_top <= (b[1] + b[3]) / 2 <= y_bot
            ]
            slice_blocks.sort(key=lambda b: b[0])
            
            # Project description blocks are at x < 475
            p_blocks = [b for b in slice_blocks if b[0] < 475]
            pb_text = '\n'.join([b[4].strip() for b in p_blocks])
            pb_lines = [l.strip() for l in pb_text.splitlines() if l.strip()]
            
            if not pb_lines or (is_sector_header(pb_lines[0]) and len(pb_lines) == 1):
                continue
                
            proj_name_parts = []
            agency = None
            project_id = None
            legacy_ocms_code = None
            
            for line in pb_lines:
                if line.isdigit() and not proj_name_parts:
                    continue
                    
                code_match = re.search(r'\(?\b(\d{5,9})\b\)?', line)
                ocms_match = re.search(r'\(?\b([A-Za-z]\d{8})\b\)?', line)
                
                if ocms_match:
                    legacy_ocms_code = ocms_match.group(1)
                
                is_enclosed = (line.startswith('(') and line.endswith(')')) or (line.startswith('[') and line.endswith(']'))
                if is_enclosed:
                    clean_line = strip_outer_brackets(line)
                    if code_match and not project_id and not ocms_match:
                        project_id = code_match.group(1)
                    if not ocms_match and not (clean_line.replace('-','').strip().isdigit() or clean_line.strip() in ['-', '--']):
                        if not agency:
                            agency = clean_line
                else:
                    if not project_id and code_match:
                        project_id = code_match.group(1)
                    if not legacy_ocms_code and ocms_match:
                        legacy_ocms_code = ocms_match.group(1)
                    if not code_match and not ocms_match:
                        proj_name_parts.append(line)
                        
            project_name = ' '.join(proj_name_parts).strip()
            
            if not project_id:
                m_pid = re.search(r'\((\d{5,9})\)', pb_text)
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
                    
            state = None
            approval_date = None
            start_date = None
            orig_doc = None
            rev_doc = None
            orig_cost = None
            rev_cost = None
            cum_exp = None
            phy_prog = None
            
            data_blocks = [b for b in slice_blocks if b[0] >= 470]
            
            # Check if single wide merged block
            if len(data_blocks) == 1 and (data_blocks[0][2] - data_blocks[0][0]) > 300:
                lines = [l.strip() for l in data_blocks[0][4].splitlines() if l.strip()]
                state_parts, dates, costs = [], [], []
                for l in lines:
                    d_m = re.findall(r'\(?(\d{1,2}/\d{4})\)?', l)
                    if d_m:
                        dates.extend(d_m)
                    elif l.replace('(','').replace(')','').replace('-','').strip() in ['-', '--', '(-)', 'NA']:
                        pass
                    else:
                        num_m = re.findall(r'\(?(\d+(?:\.\d+)?)\)?', l.replace(',', ''))
                        if num_m:
                            costs.extend([float(x) for x in num_m])
                        else:
                            state_parts.append(l)
                state = ' '.join(state_parts) if state_parts else None
                if len(dates) >= 1: approval_date = dates[0]
                if len(dates) >= 2: orig_doc = dates[1]
                if len(dates) >= 3: rev_doc = dates[2]
                if len(costs) >= 1: orig_cost = costs[0]
                if len(costs) >= 2: rev_cost = costs[1]
                if len(costs) >= 3: cum_exp = costs[2]
                if len(costs) >= 4: phy_prog = costs[3]
            else:
                for sb in data_blocks:
                    x_mid = (sb[0] + sb[2]) / 2
                    sb_text = sb[4].strip()
                    sb_lines = [l.strip() for l in sb_text.splitlines() if l.strip()]
                    
                    if x_mid < 650:
                        for sl in sb_lines:
                            dm = re.findall(r'\(?(\d{1,2}/\d{4})\)?', sl)
                            if dm:
                                if not approval_date:
                                    approval_date = dm[0]
                                if len(dm) > 1 and not start_date:
                                    start_date = dm[1]
                            else:
                                if sl not in ['-', '--', 'NA', 'N.A.']:
                                    state = (state + ' ' + sl) if state else sl
                    elif 650 <= x_mid < 750:
                        for sl in sb_lines:
                            dm = re.findall(r'\(?(\d{1,2}/\d{4})\)?', sl)
                            if dm:
                                if not orig_doc:
                                    orig_doc = dm[0]
                                if len(dm) > 1 and not rev_doc:
                                    rev_doc = dm[1]
                            elif '(' in sl and ')' in sl:
                                clean_d = sl.strip('() ')
                                if re.match(r'^\d{1,2}/\d{4}$', clean_d) and not rev_doc:
                                    rev_doc = clean_d
                    elif x_mid >= 750:
                        for sl in sb_lines:
                            num_matches = re.findall(r'\(?(\d+(?:\.\d+)?)\)?', sl.replace(',', ''))
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
                                    
            if not project_id and orig_cost is None and cum_exp is None:
                continue
                
            if not project_id:
                warnings_list.append(f"{filename} P.{pno+1}: Missing project_id for '{project_name[:30]}'")
                
            raw_rec = {
                'project_id': project_id,
                'project_name': project_name,
                'agency': agency,
                'legacy_ocms_code': legacy_ocms_code,
                'state': state,
                'approval_start_date': approval_date or start_date,
                'original_completion_date': orig_doc,
                'revised_completion_date': rev_doc,
                'original_cost_crore': orig_cost,
                'revised_cost_crore': rev_cost,
                'cumulative_expenditure_crore': cum_exp,
                'physical_progress_percent': phy_prog,
                'report_month': report_month,
                'source_file': filename,
                'source_table': table_name
            }
            rows.append(normalize_project_record(raw_rec))
            
    return rows

def extract_ongoing_legacy(doc, start_page, end_page, report_month, filename, table_name, warnings_list):
    """
    Extracts 'All Ongoing Projects' from legacy OCMS layout (Apr, May, Jun 2025).
    """
    rows = []
    current_state = None
    
    for pno in range(start_page - 1, end_page):
        page = doc[pno]
        blocks = page.get_text('blocks')
        p_height = page.rect.height
        
        content_blocks = [
            b for b in blocks 
            if 100 <= b[1] <= p_height - 35
        ]
        
        # Track State changes in the far left margin (x < 70)
        for b in content_blocks:
            if b[0] < 70 and b[1] >= 140:
                clean_t = ' '.join(b[4].strip().split())
                if clean_t not in ['State', 'Sl. No.', 'Sl No', 'Sector'] and not clean_t.isdigit():
                    current_state = clean_t
                    
        # Find row start blocks (x0 between 95 and 175 where line 0 is a number)
        sl_blocks = []
        for b in content_blocks:
            if 95 <= b[0] <= 175 and b[1] >= 140:
                lines = [l.strip() for l in b[4].splitlines() if l.strip()]
                if lines and lines[0].isdigit():
                    sl_blocks.append(b)
                    
        sl_blocks.sort(key=lambda b: b[1])
        
        for i, sb in enumerate(sl_blocks):
            y_top = sb[1] - 2
            y_bot = sl_blocks[i+1][1] - 2 if i+1 < len(sl_blocks) else (p_height - 35)
            
            row_blocks = [b for b in content_blocks if y_top <= (b[1]+b[3])/2 < y_bot]
            
            st_b = [b for b in row_blocks if b[0] < 70]
            if st_b:
                clean_st = ' '.join(st_b[0][4].strip().split())
                if clean_st not in ['State', 'Sl. No.', 'Sl No', 'Sector'] and not clean_st.isdigit():
                    current_state = clean_st
                    
            p_blocks = [b for b in row_blocks if 95 <= b[0] < 310]
            p_text = '\n'.join([b[4].strip() for b in p_blocks])
            p_lines = [l.strip() for l in p_text.splitlines() if l.strip()]
            
            proj_name_parts = []
            agency = None
            project_id = None
            legacy_ocms_code = None
            
            for line in p_lines:
                if line.isdigit() and not proj_name_parts:
                    continue
                code_match = re.search(r'\(?\b([A-Za-z]?\d{5,9})\b\)?', line)
                ocms_match = re.search(r'\(?\b([A-Za-z]\d{8})\b\)?', line)
                if ocms_match:
                    legacy_ocms_code = ocms_match.group(1)
                    project_id = legacy_ocms_code
                elif code_match and not project_id:
                    project_id = code_match.group(1)
                    legacy_ocms_code = project_id
                elif (line.startswith('(') and line.endswith(')')) or (line.startswith('[') and line.endswith(']')):
                    clean_ag = strip_outer_brackets(line)
                    if not agency and clean_ag not in ['-', '--', 'NA', 'N.A.']:
                        agency = clean_ag
                else:
                    proj_name_parts.append(line)
                    
            project_name = ' '.join(proj_name_parts).strip()
            if not project_id:
                m_ocms = re.search(r'([A-Za-z]?\d{5,9})', p_text)
                if m_ocms:
                    project_id = m_ocms.group(1)
                    legacy_ocms_code = project_id
                    
            approval_date = None
            orig_doc = None
            rev_doc = None
            orig_cost = None
            rev_cost = None
            cum_exp = None
            phy_prog = None
            
            date_blocks = [b for b in row_blocks if 270 <= b[0] < 440]
            date_lines = []
            for db in date_blocks:
                date_lines.extend([l.strip() for l in db[4].splitlines() if l.strip()])
                
            for dl in date_lines:
                dm = re.findall(r'\(?(\d{1,2}[/-]\d{4})\)?', dl)
                for d in dm:
                    d_clean = normalize_date(d)
                    if d_clean:
                        if not approval_date and not ('(' in dl or '{' in dl):
                            approval_date = d_clean
                        elif not orig_doc and not ('(' in dl or '{' in dl):
                            orig_doc = d_clean
                        elif not rev_doc:
                            rev_doc = d_clean
                            
            cost_blocks = [b for b in row_blocks if 415 <= b[0] < 510]
            cost_lines = []
            for cb in cost_blocks:
                cost_lines.extend([l.strip() for l in cb[4].splitlines() if l.strip()])
            for cl in cost_lines:
                num = normalize_numeric(cl)
                if num is not None:
                    if orig_cost is None and not ('(' in cl or '{' in cl):
                        orig_cost = num
                    elif rev_cost is None:
                        rev_cost = num
                        
            exp_blocks = [b for b in row_blocks if b[0] >= 500]
            nums = []
            for eb in exp_blocks:
                for n in re.findall(r'\d+(?:\.\d+)?', eb[4].replace(',', '')):
                    nums.append(float(n))
            if len(nums) >= 2:
                cum_exp, phy_prog = nums[0], nums[1]
            elif len(nums) == 1:
                cum_exp = nums[0]
                
            if not project_id:
                warnings_list.append(f"{filename} P.{pno+1}: Missing project_id for '{project_name[:30]}'")
                
            raw_rec = {
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
                'source_file': filename,
                'source_table': table_name
            }
            rows.append(normalize_project_record(raw_rec))
            
    return rows

def extract_completed_projects(doc, start_page, end_page, report_month, filename, table_name, warnings_list):
    """
    Extracts Table 3 (Completed Projects) across all reports where available.
    """
    rows = []
    is_legacy = ('FRApril' in filename or 'FR_May' in filename or 'FR_JUNE' in filename)
    
    if is_legacy:
        for pno in range(start_page - 1, end_page):
            page = doc[pno]
            blocks = page.get_text('blocks')
            p_height = page.rect.height
            content_blocks = [b for b in blocks if 120 <= b[1] <= p_height - 35]
            
            sl_blocks = [b for b in content_blocks if 80 <= b[0] <= 140 and b[4].strip().splitlines()[0].isdigit()]
            sl_blocks.sort(key=lambda b: b[1])
            
            for i, sb in enumerate(sl_blocks):
                y_top = sb[1] - 4
                y_bot = sl_blocks[i+1][1] - 4 if i+1 < len(sl_blocks) else (p_height - 35)
                row_blocks = [b for b in content_blocks if y_top <= (b[1]+b[3])/2 < y_bot]
                
                p_text = '\n'.join([b[4].strip() for b in row_blocks if b[0] < 330])
                m_ocms = re.search(r'\(?\b([A-Za-z]?\d{5,9})\b\)?', p_text)
                ocms = m_ocms.group(1) if m_ocms else None
                
                m_ag = re.findall(r'\(([A-Za-z0-9\s&.,/-]+)\)', p_text)
                agency = m_ag[0] if m_ag else None
                state = m_ag[1] if len(m_ag) > 1 else None
                
                proj_name = ' '.join([l.strip() for l in p_text.splitlines() if not l.strip().startswith('(') and not l.strip().isdigit()])
                
                data_b = [b for b in row_blocks if b[0] >= 330]
                d_lines = []
                for db in data_b:
                    d_lines.extend([l.strip() for l in db[4].splitlines() if l.strip()])
                    
                orig_cost, actual_doc, cum_exp = None, None, None
                for dl in d_lines:
                    dm = re.findall(r'(\d{1,2}[/-]\d{4})', dl)
                    if dm and not actual_doc:
                        actual_doc = normalize_date(dm[0])
                    num = normalize_numeric(dl)
                    if num is not None:
                        if orig_cost is None:
                            orig_cost = num
                        elif cum_exp is None:
                            cum_exp = num
                            
                raw_rec = {
                    'project_id': ocms,
                    'project_name': proj_name,
                    'agency': agency,
                    'legacy_ocms_code': ocms,
                    'state': state,
                    'approval_start_date': None,
                    'actual_completion_date': actual_doc,
                    'original_completion_date': actual_doc,
                    'revised_completion_date': None,
                    'original_cost_crore': orig_cost,
                    'revised_cost_crore': None,
                    'cumulative_expenditure_crore': cum_exp,
                    'report_month': report_month,
                    'source_file': filename,
                    'source_table': table_name
                }
                rows.append(normalize_project_record(raw_rec))
    else:
        for pno in range(start_page - 1, end_page):
            page = doc[pno]
            blocks = page.get_text('blocks')
            p_height = page.rect.height
            content_blocks = [b for b in blocks if 180 <= b[1] <= p_height - 35]
            
            proj_blocks = [b for b in content_blocks if 50 <= b[0] <= 130 and b[1] >= 220 and not is_sector_header(b[4])]
            proj_blocks.sort(key=lambda b: b[1])
            
            for i, pb in enumerate(proj_blocks):
                y_top = pb[1] - 4
                y_bot = proj_blocks[i+1][1] - 4 if i+1 < len(proj_blocks) else (p_height - 35)
                slice_blocks = [b for b in content_blocks if y_top <= (b[1]+b[3])/2 <= y_bot]
                slice_blocks.sort(key=lambda b: b[0])
                
                p_blocks = [b for b in slice_blocks if b[0] < 475]
                pb_text = '\n'.join([b[4].strip() for b in p_blocks])
                if is_sector_header(pb_text):
                    continue
                    
                m_pid = re.search(r'\b(\d{5,9})\b', pb_text)
                project_id = m_pid.group(1) if m_pid else None
                m_ocms = re.search(r'\b([A-Za-z]\d{8})\b', pb_text)
                legacy_ocms_code = m_ocms.group(1) if m_ocms else None
                
                m_ag = re.search(r'\(([^()]+)\)', pb_text)
                agency = m_ag.group(1) if m_ag else None
                
                proj_name = ' '.join([l.strip() for l in pb_text.splitlines() if not l.strip().startswith('(') and not l.strip().isdigit()])
                
                state = None
                appr_date = None
                act_doc = None
                orig_doc = None
                rev_doc = None
                orig_cost = None
                rev_cost = None
                cum_exp = None
                
                data_blocks = [b for b in slice_blocks if b[0] >= 470]
                for sb in data_blocks:
                    x_mid = (sb[0] + sb[2]) / 2
                    sb_lines = [l.strip() for l in sb[4].splitlines() if l.strip()]
                    if x_mid < 650:
                        for sl in sb_lines:
                            dm = re.findall(r'\(?(\d{1,2}/\d{4})\)?', sl)
                            if dm and not appr_date:
                                appr_date = dm[0]
                            elif sl not in ['-', '--', 'NA']:
                                state = (state + ' ' + sl) if state else sl
                    elif 650 <= x_mid < 800:
                        for sl in sb_lines:
                            dm = re.findall(r'\(?(\d{1,2}/\d{4})\)?', sl)
                            if dm:
                                if not act_doc:
                                    act_doc = dm[0]
                                elif not orig_doc:
                                    orig_doc = dm[0]
                                elif not rev_doc:
                                    rev_doc = dm[0]
                    elif x_mid >= 800:
                        for sl in sb_lines:
                            num_matches = re.findall(r'\(?(\d+(?:\.\d+)?)\)?', sl.replace(',', ''))
                            for nm in num_matches:
                                val = float(nm)
                                if orig_cost is None:
                                    orig_cost = val
                                elif rev_cost is None and ('(' in sl or len(num_matches) > 1):
                                    rev_cost = val
                                elif cum_exp is None:
                                    cum_exp = val
                                    
                if not project_id and orig_cost is None:
                    continue
                    
                raw_rec = {
                    'project_id': project_id,
                    'project_name': proj_name,
                    'agency': agency,
                    'legacy_ocms_code': legacy_ocms_code,
                    'state': state,
                    'approval_start_date': appr_date,
                    'actual_completion_date': act_doc,
                    'original_completion_date': orig_doc,
                    'revised_completion_date': rev_doc,
                    'original_cost_crore': orig_cost,
                    'revised_cost_crore': rev_cost,
                    'cumulative_expenditure_crore': cum_exp,
                    'report_month': report_month,
                    'source_file': filename,
                    'source_table': table_name
                }
                rows.append(normalize_project_record(raw_rec))
                
    return rows

def extract_newly_added_projects(doc, start_page, end_page, report_month, filename, table_name, warnings_list):
    """
    Extracts Table 4 (Newly Added Projects) across all reports where available.
    """
    rows = []
    is_legacy = ('FRApril' in filename or 'FR_May' in filename or 'FR_JUNE' in filename)
    
    if is_legacy:
        for pno in range(start_page - 1, end_page):
            page = doc[pno]
            blocks = page.get_text('blocks')
            p_height = page.rect.height
            content_blocks = [b for b in blocks if 120 <= b[1] <= p_height - 35]
            
            sl_blocks = [b for b in content_blocks if 80 <= b[0] <= 140 and b[4].strip().splitlines()[0].isdigit()]
            sl_blocks.sort(key=lambda b: b[1])
            
            for i, sb in enumerate(sl_blocks):
                y_top = sb[1] - 4
                y_bot = sl_blocks[i+1][1] - 4 if i+1 < len(sl_blocks) else (p_height - 35)
                row_blocks = [b for b in content_blocks if y_top <= (b[1]+b[3])/2 < y_bot]
                
                p_text = '\n'.join([b[4].strip() for b in row_blocks if b[0] < 330])
                m_ocms = re.search(r'\(?\b([A-Za-z]?\d{5,9})\b\)?', p_text)
                ocms = m_ocms.group(1) if m_ocms else None
                
                m_ag = re.findall(r'\(([A-Za-z0-9\s&.,/-]+)\)', p_text)
                agency = m_ag[0] if m_ag else None
                state = m_ag[1] if len(m_ag) > 1 else None
                
                proj_name = ' '.join([l.strip() for l in p_text.splitlines() if not l.strip().startswith('(') and not l.strip().isdigit()])
                
                data_b = [b for b in row_blocks if b[0] >= 330]
                d_lines = []
                for db in data_b:
                    d_lines.extend([l.strip() for l in db[4].splitlines() if l.strip()])
                    
                appr_date, orig_cost, rev_cost, orig_doc, rev_doc = None, None, None, None, None
                for dl in d_lines:
                    dm = re.findall(r'(\d{1,2}[/-]\d{4})', dl)
                    for d in dm:
                        d_norm = normalize_date(d)
                        if not appr_date:
                            appr_date = d_norm
                        elif not orig_doc:
                            orig_doc = d_norm
                        elif not rev_doc:
                            rev_doc = d_norm
                    num = normalize_numeric(dl)
                    if num is not None:
                        if orig_cost is None and not ('(' in dl or '{' in dl):
                            orig_cost = num
                        elif rev_cost is None:
                            rev_cost = num
                            
                raw_rec = {
                    'project_id': ocms,
                    'project_name': proj_name,
                    'agency': agency,
                    'legacy_ocms_code': ocms,
                    'state': state,
                    'approval_start_date': appr_date,
                    'original_completion_date': orig_doc,
                    'revised_completion_date': rev_doc,
                    'original_cost_crore': orig_cost,
                    'revised_cost_crore': rev_cost,
                    'report_month': report_month,
                    'source_file': filename,
                    'source_table': table_name
                }
                rows.append(normalize_project_record(raw_rec))
    else:
        for pno in range(start_page - 1, end_page):
            page = doc[pno]
            blocks = page.get_text('blocks')
            p_height = page.rect.height
            content_blocks = [b for b in blocks if 180 <= b[1] <= p_height - 35]
            
            proj_blocks = [b for b in content_blocks if 50 <= b[0] <= 130 and b[1] >= 220 and not is_sector_header(b[4])]
            proj_blocks.sort(key=lambda b: b[1])
            
            for i, pb in enumerate(proj_blocks):
                y_top = pb[1] - 4
                y_bot = proj_blocks[i+1][1] - 4 if i+1 < len(proj_blocks) else (p_height - 35)
                slice_blocks = [b for b in content_blocks if y_top <= (b[1]+b[3])/2 <= y_bot]
                slice_blocks.sort(key=lambda b: b[0])
                
                p_blocks = [b for b in slice_blocks if b[0] < 475]
                pb_text = '\n'.join([b[4].strip() for b in p_blocks])
                if is_sector_header(pb_text):
                    continue
                    
                m_pid = re.search(r'\b(\d{5,9})\b', pb_text)
                project_id = m_pid.group(1) if m_pid else None
                m_ocms = re.search(r'\b([A-Za-z]\d{8})\b', pb_text)
                legacy_ocms_code = m_ocms.group(1) if m_ocms else None
                
                m_ag = re.search(r'\(([^()]+)\)', pb_text)
                agency = m_ag.group(1) if m_ag else None
                
                proj_name = ' '.join([l.strip() for l in pb_text.splitlines() if not l.strip().startswith('(') and not l.strip().isdigit()])
                
                state = None
                appr_date = None
                orig_doc = None
                rev_doc = None
                orig_cost = None
                rev_cost = None
                
                data_blocks = [b for b in slice_blocks if b[0] >= 470]
                for sb in data_blocks:
                    x_mid = (sb[0] + sb[2]) / 2
                    sb_lines = [l.strip() for l in sb[4].splitlines() if l.strip()]
                    if x_mid < 650:
                        for sl in sb_lines:
                            dm = re.findall(r'\(?(\d{1,2}/\d{4})\)?', sl)
                            if dm and not appr_date:
                                appr_date = dm[0]
                            elif sl not in ['-', '--', 'NA']:
                                state = (state + ' ' + sl) if state else sl
                    elif 650 <= x_mid < 800:
                        for sl in sb_lines:
                            dm = re.findall(r'\(?(\d{1,2}/\d{4})\)?', sl)
                            if dm:
                                if not orig_doc:
                                    orig_doc = dm[0]
                                elif not rev_doc:
                                    rev_doc = dm[0]
                    elif x_mid >= 800:
                        for sl in sb_lines:
                            num_matches = re.findall(r'\(?(\d+(?:\.\d+)?)\)?', sl.replace(',', ''))
                            for nm in num_matches:
                                val = float(nm)
                                if orig_cost is None:
                                    orig_cost = val
                                elif rev_cost is None and ('(' in sl or len(num_matches) > 1):
                                    rev_cost = val
                                    
                if not project_id and orig_cost is None:
                    continue
                    
                raw_rec = {
                    'project_id': project_id,
                    'project_name': proj_name,
                    'agency': agency,
                    'legacy_ocms_code': legacy_ocms_code,
                    'state': state,
                    'approval_start_date': appr_date,
                    'original_completion_date': orig_doc,
                    'revised_completion_date': rev_doc,
                    'original_cost_crore': orig_cost,
                    'revised_cost_crore': rev_cost,
                    'report_month': report_month,
                    'source_file': filename,
                    'source_table': table_name
                }
                rows.append(normalize_project_record(raw_rec))
                
    return rows

def extract_all_pdfs(dataset_dir='dataset'):
    """
    Orchestrates extraction across all 15 PDF files.
    Returns:
      all_ongoing, all_completed, all_newly_added, extraction_logs
    """
    pdf_files = sorted(glob.glob(os.path.join(dataset_dir, '*.pdf')))
    
    all_ongoing = []
    all_completed = []
    all_newly_added = []
    extraction_logs = []
    
    for pf in pdf_files:
        fname = os.path.basename(pf)
        doc = pymupdf.open(pf)
        rmonth = get_report_month_from_doc(doc, pf)
        tbl_ranges = detect_pdf_tables(doc, pf)
        
        warnings_list = []
        tables_detected = list(tbl_ranges.keys())
        
        ongoing_cnt, completed_cnt, newly_cnt = 0, 0, 0
        
        # 1. Extract Ongoing Projects
        if 'ongoing' in tbl_ranges:
            info = tbl_ranges['ongoing']
            if 'FRApril' in fname or 'FR_May' in fname or 'FR_JUNE' in fname:
                rows = extract_ongoing_legacy(doc, info['start'], info['end'], rmonth, fname, info['name'], warnings_list)
            else:
                rows = extract_ongoing_modern(doc, info['start'], info['end'], rmonth, fname, info['name'], warnings_list)
            all_ongoing.extend(rows)
            ongoing_cnt = len(rows)
            
        # 2. Extract Completed Projects
        if 'completed' in tbl_ranges:
            info = tbl_ranges['completed']
            rows = extract_completed_projects(doc, info['start'], info['end'], rmonth, fname, info['name'], warnings_list)
            all_completed.extend(rows)
            completed_cnt = len(rows)
            
        # 3. Extract Newly Added Projects
        if 'newly_added' in tbl_ranges:
            info = tbl_ranges['newly_added']
            rows = extract_newly_added_projects(doc, info['start'], info['end'], rmonth, fname, info['name'], warnings_list)
            all_newly_added.extend(rows)
            newly_cnt = len(rows)
            
        total_extracted = ongoing_cnt + completed_cnt + newly_cnt
        rejected_cnt = len(warnings_list)
        
        extraction_logs.append({
            'pdf_filename': fname,
            'report_month': rmonth,
            'tables_detected': '; '.join(tables_detected),
            'ongoing_rows_extracted': ongoing_cnt,
            'completed_rows_extracted': completed_cnt,
            'newly_added_rows_extracted': newly_cnt,
            'total_rows_extracted': total_extracted,
            'rows_rejected': rejected_cnt,
            'warnings': '; '.join(warnings_list[:3]) if warnings_list else 'None'
        })
        print(f"Processed {fname} ({rmonth}): Ongoing={ongoing_cnt}, Completed={completed_cnt}, Newly Added={newly_cnt}, Warnings={rejected_cnt}")
        
    return all_ongoing, all_completed, all_newly_added, extraction_logs

if __name__ == '__main__':
    all_ongoing, all_completed, all_newly_added, logs = extract_all_pdfs()
    print("\n--- EXTRACTION COMPLETE ---")
    print(f"Total Ongoing Rows Extracted: {len(all_ongoing)}")
    print(f"Total Completed Rows Extracted: {len(all_completed)}")
    print(f"Total Newly Added Rows Extracted: {len(all_newly_added)}")
