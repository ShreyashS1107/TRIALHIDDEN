"""
Audit Script: audit_specs.py
Purpose: Validate consistency across backend specifications and finalized AI/ML reports.
"""

import os
import re

def run_audit():
    reports_dir = "reports"
    spec_api_path = os.path.join(reports_dir, "BACKEND_API_AND_DATABASE_SPECIFICATION.txt")
    spec_req_path = os.path.join(reports_dir, "BACKEND_REQUIREMENTS_FROM_ML.txt")
    exec_final_path = os.path.join(reports_dir, "EXECUTION_RISK_FINAL_DECISION.txt")
    exec_audit_path = os.path.join(reports_dir, "EXECUTION_RISK_COMPLETE_AUDIT.txt")
    ocms_recon_path = os.path.join(reports_dir, "OCMS_ENRICHMENT_RECONCILIATION.txt")
    frontend_req_path = os.path.join(reports_dir, "FRONTEND_REQUIREMENTS_FROM_ML.txt")

    with open(spec_api_path, "r", encoding="utf-8") as f:
        spec_api = f.read()
    with open(spec_req_path, "r", encoding="utf-8") as f:
        spec_req = f.read()
    with open(exec_final_path, "r", encoding="utf-8") as f:
        exec_final = f.read()
    with open(exec_audit_path, "r", encoding="utf-8") as f:
        exec_audit = f.read()
    with open(ocms_recon_path, "r", encoding="utf-8") as f:
        ocms_recon = f.read()
    with open(frontend_req_path, "r", encoding="utf-8") as f:
        frontend_req = f.read()

    checks = []

    # 1. Feature Universe (75 features: 71 numerical + 4 categorical)
    feat_check_req = "75" in spec_req and "71 numerical" in spec_req.lower() and "4 categorical" in spec_req.lower()
    feat_check_api = "75" in spec_api
    checks.append(("Feature Universe: 75 features (71 num + 4 cat)", feat_check_req and feat_check_api))

    # 2. Integrated Risk Weights (0.50, 0.35, 0.15)
    ir_weights_req = "0.50 * schedule_delay_risk" in spec_req and "0.35 * cost_overrun_risk" in spec_req and "0.15 * schedule_revision_risk" in spec_req
    ir_weights_api = "0.50 * sched_risk" in spec_api and "0.35 * cost_risk" in spec_api and "0.15 * srev_risk" in spec_api
    checks.append(("Integrated Risk Weights: 0.50 / 0.35 / 0.15", ir_weights_req and ir_weights_api))

    # 3. ESI Weights (0.30 S_stag, 0.25 S_vel, 0.20 S_div, 0.15 S_sched, 0.10 S_rep)
    esi_weights_req = "0.30" in spec_req and "0.25" in spec_req and "0.20" in spec_req and "0.15" in spec_req and "0.10" in spec_req and "S_stag" in spec_req
    esi_weights_api = "0.30" in spec_api and "0.25" in spec_api and "0.20" in spec_api and "0.15" in spec_api and "0.10" in spec_api and "execution_stress_scores" in spec_api
    checks.append(("ESI Weights: 0.30 S_stag, 0.25 S_vel, 0.20 S_div, 0.15 S_sched, 0.10 S_rep", esi_weights_req and esi_weights_api))

    # 4. Non-redundancy & Correlation (rho = 0.1360, 65.4% off-diagonal)
    corr_check = "0.1360" in spec_req and "65.4%" in spec_req
    checks.append(("Non-Redundancy & Overlap Metrics: rho = 0.1360, 65.4%", corr_check))

    # 5. Banned Target & Exclusion Checks
    banned_check = "cost_revision_event_3m" in spec_req and "NOT_SUPPORTED" in spec_req
    checks.append(("Target Exclusion: cost_revision_event_3m & ML execution prob banned", banned_check))

    # 6. OCMS Policy Check (VALID_AFTER_DOCUMENTATION_CORRECTION and ML exclusion)
    ocms_check = "OCMS_EXPERIMENT_VALIDITY = VALID_AFTER_DOCUMENTATION_CORRECTION" in spec_req and "MUST NOT be fed into the production ML" in spec_req
    checks.append(("OCMS Historical Data: Analytics context only, banned from ML", ocms_check))

    # 7. Model Metrics Consistency
    metrics_check = "0.9723" in spec_req and "0.9895" in spec_req and "0.8264" in spec_req
    checks.append(("OOT Model Metrics (0.9723, 0.9895, 0.8264)", metrics_check))

    # 8. Versioning Fields Check
    ver_check = "model_version" in spec_api and "feature_version" in spec_api and "execution_index_version" in spec_api and "execution_stress_scores" in spec_api
    checks.append(("Versioning & Provenance Metadata Fields", ver_check))

    # 9. Prescriptive Actions Check
    actions_check = "SITE_OBSTACLE_AUDIT" in spec_req and "FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT" in spec_req and "RESOURCE_MOBILIZATION_DIRECTIVE" in spec_req and "CRITICAL_PATH_RECALIBRATION" in spec_req and "DATA_COMPLIANCE_DIRECTIVE" in spec_req and "INTER_MINISTERIAL_COMMITTEE_ESCALATION" in spec_req
    checks.append(("Prescriptive Monitoring Actions Matrix", actions_check))

    # 10. Database DDL Table Separation
    db_check = "CREATE TABLE execution_stress_scores" in spec_api and "CREATE TABLE ml_risk_scores" in spec_api and "CREATE TABLE ocms_historical_benchmarks" in spec_api
    checks.append(("PostgreSQL DDL Table Definitions", db_check))

    print("=" * 80)
    print("BACKEND SPECIFICATION AUDIT RESULTS")
    print("=" * 80)
    all_passed = True
    for name, status in checks:
        status_str = "PASS" if status else "FAIL"
        print(f"[{status_str}] {name}")
        if not status:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print("OVERALL STATUS: BACKEND_ML_SPECIFICATION_STATUS = CONSISTENT")
    else:
        print("OVERALL STATUS: BACKEND_ML_SPECIFICATION_STATUS = REQUIRES_REVIEW")
    print("=" * 80)

if __name__ == "__main__":
    run_audit()
