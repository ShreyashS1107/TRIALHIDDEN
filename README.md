# MoSPI / IPMD PAIMANA Longitudinal Project-Monitoring Dataset (SIH26103)

## 📌 Project Overview
This repository contains the extraction, normalization, merging, validation, and profiling pipeline for **SIH 2026 Problem Statement SIH26103**:
> *"Use case on web-based integrated project-monitoring platform"*

The objective of this stage is to build a high-fidelity longitudinal master dataset from **15 monthly PAIMANA / OCMS PDF Flash Reports** published by the **Ministry of Statistics and Programme Implementation (MoSPI) / Infrastructure and Project Monitoring Division (IPMD)**, spanning from **April 2025 to June 2026**.

---

## 🗂️ Project Directory Structure

```
SIH26103/
├── dataset/                               # 15 Raw PDF Monthly Flash Reports
│   ├── FRApril2025.pdf                    # April 2025 (OCMS Legacy Layout)
│   ├── FR_May2025.pdf                     # May 2025 (OCMS Legacy Layout)
│   ├── FR_JUNE_2025.pdf                   # June 2025 (OCMS Legacy Layout)
│   ├── FlashReport_July_2025.pdf          # July 2025 (Early PAIMANA Layout)
│   ├── FlashReport_August_2025.pdf        # August 2025 (Early PAIMANA Layout)
│   ├── FlashReport_September_2025.pdf     # September 2025 (Standard PAIMANA Layout)
│   ├── FlashReport_October_2025.pdf       # October 2025 (Standard PAIMANA Layout)
│   ├── FlashReport_November_2025.pdf      # November 2025 (Standard PAIMANA Layout)
│   ├── FlashReport_December_2025.pdf      # December 2025 (Standard PAIMANA Layout)
│   ├── FlashReport_January_2026.pdf       # January 2026 (Standard PAIMANA Layout)
│   ├── FlashReport_February_2026.pdf      # February 2026 (Standard PAIMANA Layout)
│   ├── FlashReport_March_2026.pdf         # March 2026 (Standard PAIMANA Layout)
│   ├── FlashReport_April2026.pdf          # April 2026 (Standard PAIMANA Layout)
│   ├── FlashReport_May2026.pdf            # May 2026 (Standard PAIMANA Layout)
│   └── FlashReport_June_2026.pdf          # June 2026 (Standard PAIMANA Layout)
│
├── data/                                  # Structured Output Datasets (CSV)
│   ├── paimana_master_dataset.csv         # Longitudinal Ongoing Master Dataset (1 row per project_id + month)
│   ├── paimana_completed_projects.csv     # Historical Completed Projects Dataset (Table 3)
│   └── paimana_newly_added_projects.csv   # Newly Entered Projects Tracking Dataset (Table 4)
│
├── scripts/                               # Data Processing & Validation Pipeline
│   ├── detect_table_ranges.py             # PDF Table Scanner & Page Boundary Resolver
│   ├── normalize_data.py                  # Normalization Rules & Field Cleaning Module
│   ├── extract_pdfs.py                    # Multi-Layout PyMuPDF Table Extraction Engine
│   ├── merge_monthly_data.py              # Canonical Linkage & Master Dataset Assembler
│   ├── validate_paimana_dataset.py        # Comprehensive Data Quality & Anomaly Checker
│   └── profile_dataset.py                 # Summary Profiler & End-to-End Pipeline Runner
│
├── reports/                               # QA, Extraction Logs & Profiling Reports
│   ├── extraction_log.csv                 # Detailed Per-PDF Table & Row Extraction Log
│   ├── data_profile.txt                   # Complete Statistical Data Profile & Quality Audit
│   └── manual_review.csv                  # Flagged Trajectory & Quality Anomalies for Review
│
└── README.md                              # Technical Documentation & Pipeline Guide
```

---

## 📊 Master Dataset Schema (`data/paimana_master_dataset.csv`)

| Column Name | Data Type | Description | Format / Units |
| :--- | :--- | :--- | :--- |
| `project_id` | `string` | Canonical unique project identifier (PAIMANA Project Code or OCMS Code) | e.g. `612786`, `N04000106` |
| `project_name` | `string` | Full official project title | Title case string |
| `agency` | `string` | Central Implementing Agency / CPSU | e.g. `AAI`, `NTPC`, `NHIDCL`, `PGCIL` |
| `legacy_ocms_code` | `string` | Legacy MoSPI OCMS Project Code (cross-referenced) | e.g. `N04000106` |
| `state` | `string` | State or Multi-State jurisdiction | e.g. `Andhra Pradesh`, `Multi-States (...)` |
| `approval_start_date`| `string` | Date of government approval / project commencement | `YYYY-MM` |
| `original_completion_date` | `string` | Original / initial targeted date of commissioning | `YYYY-MM` |
| `revised_completion_date` | `string` | Revised / anticipated date of commissioning | `YYYY-MM` (or empty if unrevised) |
| `original_cost_crore` | `float` | Sanctioned / initial project cost | ₹ Crore |
| `revised_cost_crore` | `float` | Revised / anticipated project cost | ₹ Crore |
| `cumulative_expenditure_crore` | `float` | Total expenditure incurred up to report month | ₹ Crore |
| `physical_progress_percent` | `float` | Cumulative physical completion percentage | `0.00` to `100.00` (%) |
| `report_month` | `string` | Monthly snapshot reporting timestamp | `YYYY-MM` |
| `source_file` | `string` | Source PDF report filename | e.g. `FlashReport_April2026.pdf` |
| `source_table` | `string` | Source table within the PDF | e.g. `Table 6: All Ongoing Projects` |

---

## 🛠️ Data Normalization Standards
1. **Longitudinal Granularity**: Exactly **one row per `project_id + report_month`**. Never overwrites historical snapshots with future values.
2. **Canonical Identifiers**: Maps legacy 8-character OCMS codes (`N04000106`) to 6-digit PAIMANA IDs (`612786`) across the full timeline using bidirectional lookups.
3. **Temporal Normalization**: All dates and report months are normalized to standard ISO-8601 `YYYY-MM` format (e.g. `2026-03`).
4. **Financial Consistency**: All financial values are preserved in **₹ crore**, maintaining exact decimal precision without conversion errors.
5. **Progress Bounding**: Physical progress is cleaned into a floating-point number bounded strictly between `0.0` and `100.0%`.
6. **Missing Data Standards**: Missing values, non-reporting indicators (`"-"`, `"NA"`, `"Nil"`, whitespace) are converted to empty/null values, never artificially imputed.
7. **Traceability Guarantee**: Every single row retains its exact `source_file`, `source_table`, and `report_month` metadata.

---

## 🚀 How to Run the Pipeline

### Prerequisites
```bash
pip install pymupdf pdfplumber pandas numpy
```

### Full End-to-End Execution
Run the orchestrator script to execute extraction, normalization, merging, validation, and profiling in one command:
```bash
python scripts/profile_dataset.py
```

### Modular Execution
```bash
# 1. Scan tables across all 15 PDFs
python scripts/detect_table_ranges.py

# 2. Extract tables into structured data
python scripts/extract_pdfs.py

# 3. Assemble and save CSV datasets in data/
python scripts/merge_monthly_data.py

# 4. Run data quality and longitudinal anomaly validation
python scripts/validate_paimana_dataset.py

# 5. Generate comprehensive summary profile report
python scripts/profile_dataset.py
```

---

## 📈 Key Findings & Dataset Summary

| Metric | Result |
| :--- | :--- |
| **Total Monthly PDF Reports Processed** | **15 / 15 (100.0%)** |
| **Temporal Coverage** | **April 2025 to June 2026 (15 consecutive months)** |
| **Total Project-Month Records (Master Dataset)** | **21,555 rows** |
| **Total Unique Projects Monitored** | **2,741 projects** |
| **Completed Projects Dataset (`Table 3`)** | **350 rows** |
| **Newly Added Projects Dataset (`Table 4`)** | **743 rows** |
| **Duplicate (`project_id + report_month`) Rows** | **0 (Strictly 0 duplicates)** |
| **Projects Observed in All 15 Months** | **418 projects** |
| **Projects Observed in 10–14 Months** | **730 projects** |
| **Projects Observed in 5–9 Months** | **814 projects** |
| **Projects Observed in 2–4 Months** | **680 projects** |
| **Projects Observed in a Single Month** | **99 projects** |
| **Rows Flagged for Quality Audit (`reports/manual_review.csv`)** | **1,868 rows** (flagged without dropping) |

---

## 🛡️ Validation & Anomaly Detection Framework
The validation engine (`scripts/validate_paimana_dataset.py`) verifies data integrity across multiple dimensions:
- **Key Uniqueness**: Asserts zero duplicate combinations of `(project_id, report_month)`.
- **Value Bounds**: Enforces `0 <= physical_progress_percent <= 100`, flags negative monetary values.
- **Trajectory Audits**: Flags sudden progress regressions (>25% drop), cumulative expenditure drops (>50%), and massive cost revisions (>400% shift) for human domain review in `reports/manual_review.csv`.
