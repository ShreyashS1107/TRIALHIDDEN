"""
Single-PDF Extraction Pipeline for Inference Adapter
SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform

Reuses existing extraction & normalization logic to parse a newly uploaded PAIMANA PDF.
"""

import os
import pymupdf
import pandas as pd

# The inference/__init__.py sets up sys.path to include ai-ml/,
# so we can directly import the authoritative scripts:
from scripts.detect_table_ranges import detect_pdf_tables, get_report_month_from_doc
from scripts.normalize_data import normalize_project_record
from scripts.extract_pdfs import extract_ongoing_legacy, extract_ongoing_modern

def extract_monthly_paimana_pdf(
    pdf_path: str,
    report_month: str = None
) -> tuple[pd.DataFrame, str]:
    """
    Extracts and normalizes ongoing project records from a single PAIMANA Flash Report PDF.

    Parameters:
        pdf_path: Filepath to the PAIMANA Flash Report PDF.
        report_month: Optional expected report month in 'YYYY-MM' format. If None, auto-detected from doc.

    Returns:
        tuple (ongoing_df, detected_report_month):
            - ongoing_df: DataFrame of normalized project records for the report epoch.
            - detected_report_month: Resolved report month epoch string.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

    filename = os.path.basename(pdf_path)
    doc = pymupdf.open(pdf_path)

    try:
        # Detect report month if not provided
        detected_month = get_report_month_from_doc(doc, pdf_path)
        if report_month:
            report_month = str(report_month).strip()[:7]
            if detected_month and detected_month != report_month:
                pass
            final_month = report_month
        else:
            if not detected_month:
                raise ValueError(f"Could not auto-detect report month from PDF {filename}. Please provide report_month explicitly.")
            final_month = detected_month

        # Detect table boundaries
        tbl_ranges = detect_pdf_tables(doc, pdf_path)
        warnings_list = []

        if 'ongoing' not in tbl_ranges:
            raise ValueError(f"Could not locate Ongoing Projects table in PDF {filename}.")

        info = tbl_ranges['ongoing']
        start_p = info['start']
        end_p = info['end']
        tbl_name = info['name']

        # Choose legacy vs modern extraction routine based on report month / filename
        is_legacy = any(x in filename for x in ['FRApril', 'FR_May', 'FR_JUNE']) or final_month in ['2025-04', '2025-05', '2025-06']

        if is_legacy:
            raw_rows = extract_ongoing_legacy(doc, start_p, end_p, final_month, filename, tbl_name, warnings_list)
        else:
            raw_rows = extract_ongoing_modern(doc, start_p, end_p, final_month, filename, tbl_name, warnings_list)

        if not raw_rows:
            raise ValueError(f"Zero project rows extracted from Ongoing Projects table in {filename}.")

        # Convert to DataFrame and drop any accidental duplicate (project_id, report_month)
        df_ongoing = pd.DataFrame(raw_rows)
        if 'project_id' in df_ongoing.columns:
            df_ongoing['project_id'] = df_ongoing['project_id'].astype(str).str.strip()
            df_ongoing = df_ongoing.drop_duplicates(subset=['project_id']).reset_index(drop=True)

        return df_ongoing, final_month

    finally:
        doc.close()
