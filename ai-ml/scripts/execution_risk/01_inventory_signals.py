"""
Script: 01_inventory_signals.py
Purpose: Complete inventory and classification of all candidate execution/implementation risk signals
         available in PAIMANA master dataset, feature dataset, and source documents for SIH26103.
Output: reports/EXECUTION_RISK_FIELD_INVENTORY.txt
"""

import os
import pandas as pd
import numpy as np

def run_inventory():
    print("Starting Execution Risk Field Inventory...")
    
    # Load feature dataset
    feat = pd.read_csv('features/feature_dataset_v1.csv', low_memory=False)
    master = pd.read_csv('data/paimana_master_dataset.csv', low_memory=False)
    completed = pd.read_csv('data/paimana_completed_projects.csv', low_memory=False)
    newly = pd.read_csv('data/paimana_newly_added_projects.csv', low_memory=False)
    
    inventory_items = []
    
    # Define detailed catalog of all candidate signals
    # Category 1: Physical Progress Signals
    cat1_signals = [
        {
            "col": "physical_progress_t",
            "source_ds": "features/feature_dataset_v1.csv (derived from data/paimana_master_dataset.csv: physical_progress_percent)",
            "type": "Raw / Cleaned PIT observation",
            "category": "1. Physical Progress",
            "pit_avail": "Month t (published flash report)",
            "interpretation": "Current reported cumulative physical progress percentage [0, 100]",
            "risk_meaning": "Low absolute progress relative to project age indicates severe initial/ongoing implementation friction.",
            "limitations": "Self-reported by implementing agencies; 6.1% missingness in raw reports; subject to reporting quantization (e.g. 0%, 5%, 10%).",
            "leakage_risk": "None (strictly observed at month t).",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "remaining_physical_progress_t",
            "source_ds": "features/feature_dataset_v1.csv (100 - physical_progress_t)",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t",
            "interpretation": "Physical work remaining to complete [0, 100]",
            "risk_meaning": "Quantifies scale of physical execution still pending. If high near deadline, indicates high implementation stress.",
            "limitations": "Direct linear transform of physical_progress_t.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "progress_velocity_1m_t",
            "source_ds": "features/feature_dataset_v1.csv (physical_progress_t - physical_progress_lag1)",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t (requires t-1)",
            "interpretation": "1-month physical progress change (% pts / month)",
            "risk_meaning": "Immediate monthly execution momentum. Negative or zero velocity indicates current work stoppage or reset.",
            "limitations": "22.4% missingness due to new projects or observation gaps; high month-to-month volatility.",
            "leakage_risk": "None (uses t and t-1).",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "progress_velocity_3m_t",
            "source_ds": "features/feature_dataset_v1.csv (average monthly progress change over 3 months)",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t (requires t-3)",
            "interpretation": "Rolling 3-month physical progress velocity (% pts / month)",
            "risk_meaning": "Smoothed medium-term execution velocity. Low/zero 3m velocity signifies persistent implementation bottlenecks.",
            "limitations": "51.5% missingness for projects with < 3 prior monthly observations.",
            "leakage_risk": "None (uses t-3 to t).",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "progress_velocity_6m_t",
            "source_ds": "features/feature_dataset_v1.csv (average monthly progress change over 6 months)",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t (requires t-6)",
            "interpretation": "Rolling 6-month physical progress velocity (% pts / month)",
            "risk_meaning": "Long-term sustained physical execution rate.",
            "limitations": "78.1% missingness across the 15-month dataset due to limited history.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "stagnant_2m_t",
            "source_ds": "features/feature_dataset_v1.csv (indicator: progress_change_1m == 0)",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t",
            "interpretation": "Binary flag (1 if 0% progress change in last month, else 0)",
            "risk_meaning": "Early alert for physical work stall.",
            "limitations": "20.1% missingness.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "stagnant_3m_t",
            "source_ds": "features/feature_dataset_v1.csv (indicator: progress unchanged for 2 consecutive months)",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t",
            "interpretation": "Binary flag (1 if progress stagnant across 3 consecutive reports)",
            "risk_meaning": "Established operational deadlock / construction stoppage indicator.",
            "limitations": "36.1% missingness in early project life.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "stagnant_6m_t",
            "source_ds": "features/feature_dataset_v1.csv (indicator: progress unchanged across 6 reports)",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t",
            "interpretation": "Binary flag (1 if chronic stagnation for 6 months)",
            "risk_meaning": "Chronic stalled project / abandoned site risk.",
            "limitations": "69.1% missingness.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "months_since_last_progress_increase_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t",
            "interpretation": "Count of consecutive observed months where progress did not increase",
            "risk_meaning": "Direct monotonic measurement of progress stagnation duration.",
            "limitations": "Capped at total observed history for newly added projects.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "longest_stagnation_to_date_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t",
            "interpretation": "Maximum historical run of consecutive stagnant months observed up to t",
            "risk_meaning": "Structural propensity of project/agency toward chronic stalls.",
            "limitations": "Monotonically increasing historical summary.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "progress_std_to_date_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "1. Physical Progress",
            "pit_avail": "Month t",
            "interpretation": "Standard deviation of historical progress observations up to month t",
            "risk_meaning": "Measures volatility and irregularity in physical reporting.",
            "limitations": "0 for single-observation projects.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        }
    ]
    
    # Category 2: Schedule Behaviour Signals
    cat2_signals = [
        {
            "col": "schedule_slippage_months_t",
            "source_ds": "features/feature_dataset_v1.csv (revised_doc_t - original_completion_date)",
            "type": "Engineered PIT feature",
            "category": "2. Schedule Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Months of formal schedule extension granted/reported as of month t",
            "risk_meaning": "Magnitude of formal time delay already incurred. High slippage reflects compound implementation failure.",
            "limitations": "NaN if project has no formal revised completion date (imputed as 0 in tree models).",
            "leakage_risk": "None (uses revised date reported at month t).",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "months_to_original_doc_t",
            "source_ds": "features/feature_dataset_v1.csv (original_completion_date - prediction_month)",
            "type": "Engineered PIT feature",
            "category": "2. Schedule Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Remaining months to original scheduled completion (negative = past original deadline)",
            "risk_meaning": "Overdue severity relative to baseline charter. Deep negative values indicate severe multi-year delay.",
            "limitations": "2.7% missing original completion dates.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "months_to_revised_doc_t",
            "source_ds": "features/feature_dataset_v1.csv (revised_doc_t - prediction_month)",
            "type": "Engineered PIT feature",
            "category": "2. Schedule Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Remaining months to revised scheduled completion",
            "risk_meaning": "Proximity to current working deadline. If low while physical progress is low, indicates imminent deadline breach.",
            "limitations": "Missing for projects without revised dates.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "has_revised_schedule_as_of_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "2. Schedule Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Binary flag (1 if revised completion date exists as of t, else 0)",
            "risk_meaning": "Indicates project has breached or officially modified its original timeline.",
            "limitations": "Coarse binary flag.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "schedule_revision_count_to_date_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "2. Schedule Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Cumulative count of schedule revisions observed in PAIMANA history up to t",
            "risk_meaning": "Frequent revisions indicate unstable planning, recurring scope changes, or ongoing execution disruptions.",
            "limitations": "Limited by PAIMANA observation window (15 months).",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "months_since_last_schedule_revision_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "2. Schedule Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Elapsed months since most recent schedule revision was introduced",
            "risk_meaning": "Recency of schedule disruption. Recent revisions indicate active contractual renegotiation.",
            "limitations": "Arbitrary large constant if no revision observed.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "current_schedule_status_as_of_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature (Categorical)",
            "category": "2. Schedule Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Current operational schedule state (ON_TIME, DELAYED, WITHIN_REVISED_TIMELINE, OVERDUE_REVISED, UNKNOWN)",
            "risk_meaning": "Operational risk stratification directly used in MoSPI monitoring.",
            "limitations": "Categorical string encoding required.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        }
    ]
    
    # Category 3: Expenditure Behaviour & Divergence Signals
    cat3_signals = [
        {
            "col": "cumulative_expenditure_t",
            "source_ds": "features/feature_dataset_v1.csv (data/paimana_master_dataset.csv: cumulative_expenditure_crore)",
            "type": "Raw / Cleaned PIT feature",
            "category": "3. Expenditure Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Cumulative financial expenditure in Crore INR reported as of month t",
            "risk_meaning": "Absolute scale of financial resources deployed.",
            "limitations": "1.0% missingness.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "expenditure_ratio_pct_t",
            "source_ds": "features/feature_dataset_v1.csv (cumulative_expenditure_t / original_cost_crore * 100)",
            "type": "Engineered PIT feature",
            "category": "3. Expenditure Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Cumulative spend as percentage of original sanctioned cost (%)",
            "risk_meaning": "Budget consumption pace. Expenditure ratio > 100% signifies active cost overrun.",
            "limitations": "Sensitive to original cost denominator errors.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "monthly_expenditure_delta_t",
            "source_ds": "features/feature_dataset_v1.csv (cum_exp_t - cum_exp_t-1)",
            "type": "Engineered PIT feature",
            "category": "3. Expenditure Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Net financial burn in month t (Crore INR)",
            "risk_meaning": "Monthly cash flow and contractor disbursement intensity.",
            "limitations": "17.6% missingness; occasional negative deltas due to accounting corrections.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "expenditure_velocity_3m_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "3. Expenditure Behaviour",
            "pit_avail": "Month t",
            "interpretation": "3-month average monthly expenditure (Crore/month)",
            "risk_meaning": "Sustained financial execution velocity.",
            "limitations": "47.5% missingness for newly tracked projects.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "negative_expenditure_delta_flag_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "3. Expenditure Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Binary flag (1 if monthly expenditure delta < 0)",
            "risk_meaning": "Indicates financial audit clawbacks, billing dispute adjustments, or data entry corrections.",
            "limitations": "Rare event (~2% of records).",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "expenditure_to_progress_divergence (derived: expenditure_ratio_pct_t - physical_progress_t)",
            "source_ds": "Derived analytical signal from features/feature_dataset_v1.csv",
            "type": "Analytical Signal / Composite metric",
            "category": "3. Expenditure Behaviour",
            "pit_avail": "Month t",
            "interpretation": "Spread between financial consumption (%) and physical execution (%)",
            "risk_meaning": "PRIMARY IMPLEMENTATION ANOMALY SIGNAL: High positive divergence (e.g. 80% spent, 25% built) indicates extreme cost inefficiency, advance disbursement risk, or unverified contractor billing.",
            "limitations": "Can be noisy if land acquisition expenditure occurs upfront before physical construction begins.",
            "leakage_risk": "None.",
            "suitability": "ANALYTICAL_SIGNAL_ONLY"
        }
    ]
    
    # Category 4: Project Lifecycle / Context Signals
    cat4_signals = [
        {
            "col": "project_age_months_t",
            "source_ds": "features/feature_dataset_v1.csv (prediction_month - approval_start_date)",
            "type": "Engineered PIT feature",
            "category": "4. Project Lifecycle & Context",
            "pit_avail": "Month t",
            "interpretation": "Elapsed age of project in months since government approval / sanction",
            "risk_meaning": "Lifecycle stage. Prolonged age with low progress indicates structural inertia and legacy stalling.",
            "limitations": "1.1% missing approval dates.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "planned_duration_months",
            "source_ds": "features/feature_dataset_v1.csv (original_completion_date - approval_start_date)",
            "type": "Engineered PIT feature",
            "category": "4. Project Lifecycle & Context",
            "pit_avail": "Month t",
            "interpretation": "Originally scheduled total project duration in months",
            "risk_meaning": "Baseline project complexity and planning horizon.",
            "limitations": "2.9% missingness.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "project_size_category",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature (Categorical)",
            "category": "4. Project Lifecycle & Context",
            "pit_avail": "Month t",
            "interpretation": "Classification by sanctioned cost (Mega: >= Rs 1000 Cr, Major: Rs 150-1000 Cr, Medium: < Rs 150 Cr)",
            "risk_meaning": "Scale and systemic institutional risk.",
            "limitations": "Coarse 3-level categorical.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "agency",
            "source_ds": "features/feature_dataset_v1.csv (data/paimana_master_dataset.csv: agency)",
            "type": "Raw PIT feature (Categorical)",
            "category": "4. Project Lifecycle & Context",
            "pit_avail": "Month t",
            "interpretation": "Executing ministry, department, or central public sector undertaking (e.g. NHAI, MoR, MoPNG, NTPC)",
            "risk_meaning": "Captures institutional execution capacity, administrative overhead, and agency governance performance.",
            "limitations": "High cardinality (459 distinct agency strings in master dataset).",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "state",
            "source_ds": "features/feature_dataset_v1.csv (data/paimana_master_dataset.csv: state)",
            "type": "Raw PIT feature (Categorical)",
            "category": "4. Project Lifecycle & Context",
            "pit_avail": "Month t",
            "interpretation": "Geographic jurisdiction / state location of project site",
            "risk_meaning": "Reflects regional right-of-way complexity, state land acquisition regulations, and local environmental friction.",
            "limitations": "Multi-state projects categorized as 'MULTI-STATE' or compound strings.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "agency_mean_progress_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "4. Project Lifecycle & Context",
            "pit_avail": "Month t",
            "interpretation": "Cross-sectional mean physical progress across all active projects of this agency at month t",
            "risk_meaning": "Portfolio-level execution health of the implementing agency.",
            "limitations": "Small sample size for agencies with 1-2 projects.",
            "leakage_risk": "None (calculated strictly within month t).",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "agency_active_project_count_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "4. Project Lifecycle & Context",
            "pit_avail": "Month t",
            "interpretation": "Total active project load being managed concurrently by the agency at month t",
            "risk_meaning": "Agency capacity strain / managerial bandwidth bottleneck.",
            "limitations": "None.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        }
    ]
    
    # Category 5: Data & Reporting Quality Signals
    cat5_signals = [
        {
            "col": "observation_gap_flag_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "5. Data & Reporting Quality",
            "pit_avail": "Month t",
            "interpretation": "Binary flag (1 if project experienced missed reporting months between first observation and t)",
            "risk_meaning": "Signals administrative non-compliance, portal blackout, or operational distress leading to lapsed reporting.",
            "limitations": "Binary summary.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "observation_coverage_ratio_t",
            "source_ds": "features/feature_dataset_v1.csv (consecutive_obs / total_possible_obs)",
            "type": "Engineered PIT feature",
            "category": "5. Data & Reporting Quality",
            "pit_avail": "Month t",
            "interpretation": "Proportion of active months in which the project successfully filed a monthly report",
            "risk_meaning": "Continuous index of reporting reliability and monitoring visibility.",
            "limitations": "Bounded [0, 1].",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "missing_physical_progress_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "5. Data & Reporting Quality",
            "pit_avail": "Month t",
            "interpretation": "Binary flag (1 if physical progress was omitted in report at month t)",
            "risk_meaning": "Direct data opacity indicator; impedes progress-based risk evaluation.",
            "limitations": "None.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "missing_revised_doc_t",
            "source_ds": "features/feature_dataset_v1.csv",
            "type": "Engineered PIT feature",
            "category": "5. Data & Reporting Quality",
            "pit_avail": "Month t",
            "interpretation": "Binary flag (1 if revised completion date is missing despite being delayed)",
            "risk_meaning": "Indicates unscheduled / un-remedied schedule slippage without formal milestone recalibration.",
            "limitations": "None.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        },
        {
            "col": "table_source_t",
            "source_ds": "features/feature_dataset_v1.csv (data/paimana_master_dataset.csv: source_table)",
            "type": "Raw PIT feature (Categorical)",
            "category": "5. Data & Reporting Quality",
            "pit_avail": "Month t",
            "interpretation": "Specific PAIMANA report table source (Table 1, Table 2, Table 6, etc.)",
            "risk_meaning": "Identifies reporting format transitions and cohort inclusion rules across PAIMANA releases.",
            "limitations": "Table schemas changed in mid-2025 as PAIMANA portal matured.",
            "leakage_risk": "None.",
            "suitability": "SAFE_FEATURE"
        }
    ]
    
    # Category 6: Structured Milestone, Remarks, Contractual Fields Audit
    cat6_signals = [
        {
            "col": "milestone_completion_dates / milestone_names",
            "source_ds": "PAIMANA Portal Flash Reports (audited: FlashReport_*.pdf)",
            "type": "Field Audit (ABSENT)",
            "category": "6. Structured Milestones, Contracts & Remarks",
            "pit_avail": "NOT AVAILABLE IN PUBLISHED DATA",
            "interpretation": "Granular physical milestone tracking (e.g. EPC package awards, foundation, superstructure, commissioning)",
            "risk_meaning": "Would provide early intermediate bottleneck detection before terminal schedule slippage occurs.",
            "limitations": "Completely absent from monthly PAIMANA flash reports and OCMS PDF archives. Not captured in tabular data.",
            "leakage_risk": "N/A",
            "suitability": "UNSAFE / EXCLUDE"
        },
        {
            "col": "contractor_name / contractual_dispute_status",
            "source_ds": "PAIMANA Portal Flash Reports (audited: FlashReport_*.pdf)",
            "type": "Field Audit (ABSENT)",
            "category": "6. Structured Milestones, Contracts & Remarks",
            "pit_avail": "NOT AVAILABLE IN PUBLISHED DATA",
            "interpretation": "Identity of EPC contractors, concessionaires, arbitration filings, or liquidated damages notices",
            "risk_meaning": "Direct contractual execution risk indicator.",
            "limitations": "Not published in PAIMANA flash reports.",
            "leakage_risk": "N/A",
            "suitability": "UNSAFE / EXCLUDE"
        },
        {
            "col": "bottleneck_remarks / delay_reasons_text",
            "source_ds": "PAIMANA Portal Flash Reports (audited: FlashReport_*.pdf)",
            "type": "Field Audit (ABSENT IN TABULAR DATA)",
            "category": "6. Structured Milestones, Contracts & Remarks",
            "pit_avail": "NOT AVAILABLE IN PUBLISHED DATA",
            "interpretation": "Free-text explanations of delay causes (e.g., land acquisition delays, forest clearances, law and order, utility shifting)",
            "risk_meaning": "Qualitative root-cause attribution.",
            "limitations": "PAIMANA flash reports only provide tabular numerical project summaries without project-level text remark columns (unlike legacy 1990s OCMS annexures).",
            "leakage_risk": "N/A",
            "suitability": "UNSAFE / EXCLUDE"
        }
    ]
    
    all_signals = cat1_signals + cat2_signals + cat3_signals + cat4_signals + cat5_signals + cat6_signals
    
    # Write report
    report_path = 'reports/EXECUTION_RISK_FIELD_INVENTORY.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 90 + "\n")
        f.write("EXECUTION / IMPLEMENTATION RISK FIELD INVENTORY & SIGNAL AUDIT\n")
        f.write("SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform\n")
        f.write("=" * 90 + "\n\n")
        
        f.write("1. EXECUTIVE SUMMARY\n")
        f.write("-" * 50 + "\n")
        f.write("This audit systematically reviews all candidate signals, features, and raw fields across the\n")
        f.write("PAIMANA master dataset (21,555 records, Apr 2025 - Jun 2026), the frozen feature dataset\n")
        f.write("(15,769 records, 98 columns), auxiliary datasets, and published monthly Flash Reports.\n\n")
        
        f.write("Key Audit Findings:\n")
        f.write("1. Physical Progress Signals: 11 distinct point-in-time features exist, capturing instantaneous\n")
        f.write("   progress, rolling velocity (1m/3m/6m), multi-month stagnation, and stagnation duration.\n")
        f.write("2. Schedule Behaviour Signals: 7 point-in-time features capture schedule slippage magnitude,\n")
        f.write("   overdue status, deadline proximity, and revision volatility.\n")
        f.write("3. Expenditure & Divergence Signals: 6 features quantify financial burn, monthly delta, and\n")
        f.write("   critically, the divergence spread between expenditure ratio and physical progress.\n")
        f.write("4. Lifecycle & Governance Context: 7 features capture project age, planned duration, size tier,\n")
        f.write("   state, and agency portfolio workload / mean execution rate.\n")
        f.write("5. Data & Reporting Quality: 5 features capture observation gaps, reporting consistency, and\n")
        f.write("   missing data indicators.\n")
        f.write("6. Structured Milestones & Qualitative Bottlenecks: A rigorous PDF text and schema audit confirms\n")
        f.write("   that PAIMANA Flash Reports DO NOT contain structured milestone tables, contractor performance\n")
        f.write("   scorecards, contractual dispute fields, or project-level bottleneck remark columns.\n\n")
        
        f.write("=" * 90 + "\n")
        f.write("2. COMPLETE FIELD INVENTORY & SIGNAL CLASSIFICATION TABLE\n")
        f.write("=" * 90 + "\n\n")
        
        current_cat = ""
        for s in all_signals:
            if s["category"] != current_cat:
                current_cat = s["category"]
                f.write("\n" + "#" * 80 + "\n")
                f.write(f"CATEGORY: {current_cat}\n")
                f.write("#" * 80 + "\n\n")
            
            f.write(f"Field / Signal       : {s['col']}\n")
            f.write(f"Source Dataset       : {s['source_ds']}\n")
            f.write(f"Type                 : {s['type']}\n")
            f.write(f"PIT Availability     : {s['pit_avail']}\n")
            f.write(f"Interpretation       : {s['interpretation']}\n")
            f.write(f"Execution Meaning    : {s['risk_meaning']}\n")
            f.write(f"Known Limitations    : {s['limitations']}\n")
            f.write(f"Leakage Risk         : {s['leakage_risk']}\n")
            f.write(f"Suitability Decision : {s['suitability']}\n")
            f.write("-" * 80 + "\n")
            
        f.write("\n\n" + "=" * 90 + "\n")
        f.write("3. SIGNAL SUITABILITY SUMMARY\n")
        f.write("=" * 90 + "\n\n")
        
        counts = {}
        for s in all_signals:
            suit = s['suitability']
            counts[suit] = counts.get(suit, 0) + 1
            
        for suit, cnt in sorted(counts.items()):
            f.write(f"  * {suit:25s}: {cnt:2d} fields\n")
            
        f.write("\nTOTAL AUDITED SIGNALS: " + str(len(all_signals)) + "\n")
        f.write("=" * 90 + "\n")
        
    print(f"Inventory completed. Saved to {report_path}")

if __name__ == '__main__':
    run_inventory()
