import glob
import re
import pymupdf

pdf_files = sorted(glob.glob('dataset/*.pdf'))

def get_report_month(filename, doc):
    fname = filename.lower()
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

for pf in pdf_files:
    doc = pymupdf.open(pf)
    rmonth = get_report_month(pf, doc)
    print(f"=== {pf} -> Month: {rmonth}, Pages: {len(doc)} ===")
    
    # Scan for table headings
    seen_headers = set()
    for pno in range(len(doc)):
        text = doc[pno].get_text()
        first_few = [l.strip() for l in text.splitlines() if l.strip()][:15]
        for line in first_few:
            if re.search(r'Table\s*[:-]?\s*\d+', line, re.IGNORECASE) or 'All Ongoing Projects' in line or 'Completed Projects' in line or 'Newly Added Projects' in line:
                if len(line) < 120 and line not in seen_headers:
                    seen_headers.add(line)
                    print(f"  P.{pno+1}: {line}")
