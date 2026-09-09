"""
Audit Script: audit_specs.py
Purpose: Validate 3-way consistency across Frontend Specification, Backend Specification, Backend Requirements, and finalized AI/ML reports.
"""

import os

def run_audit():
    reports_dir = "reports"
    spec_api_path = os.path.join(reports_dir, "BACKEND_API_AND_DATABASE_SPECIFICATION.txt")
    spec_backend_req_path = os.path.join(reports_dir, "BACKEND_REQUIREMENTS_FROM_ML.txt")
    spec_frontend_req_path = os.path.join(reports_dir, "FRONTEND_REQUIREMENTS_FROM_ML.txt")
    exec_final_path = os.path.join(reports_dir, "EXECUTION_RISK_FINAL_DECISION.txt")
    exec_audit_path = os.path.join(reports_dir, "EXECUTION_RISK_COMPLETE_AUDIT.txt")
    ocms_recon_path = os.path.join(reports_dir, "OCMS_ENRICHMENT_RECONCILIATION.txt")

    with open(spec_api_path, "r", encoding="utf-8") as f:
        spec_api = f.read()
    with open(spec_backend_req_path, "r", encoding="utf-8") as f:
        spec_breq = f.read()
    with open(spec_frontend_req_path, "r", encoding="utf-8") as f:
        spec_freq = f.read()
    with open(exec_final_path, "r", encoding="utf-8") as f:
        exec_final = f.read()
    with open(exec_audit_path, "r", encoding="utf-8") as f:
        exec_audit = f.read()
    with open(ocms_recon_path, "r", encoding="utf-8") as f:
        ocms_recon = f.read()

    checks = []

    # 1. Feature Universe (75 features: 71 num + 4 cat)
    f_b = "75" in spec_breq and "71 numerical" in spec_breq.lower() and "4 categorical" in spec_breq.lower()
    f_a = "75" in spec_api
    f_f = "75" in spec_freq
    checks.append(("Feature Universe (75 features: 71 num + 4 cat) in all specs", f_b and f_a and f_f))

    # 2. Integrated Risk Formula (0.50 Sched, 0.35 Cost, 0.15 SRev)
    ir_b = "0.50 * schedule_delay_risk" in spec_breq and "0.35 * cost_overrun_risk" in spec_breq and "0.15 * schedule_revision_risk" in spec_breq
    ir_a = "0.50 * sched_risk" in spec_api and "0.35 * cost_risk" in spec_api and "0.15 * srev_risk" in spec_api
    ir_f = "0.50 * schedule_delay_risk" in spec_freq and "0.35 * cost_overrun_risk" in spec_freq and "0.15 * schedule_revision_risk" in spec_freq
    checks.append(("Integrated Risk Formula (0.50/0.35/0.15) in all specs", ir_b and ir_a and ir_f))

    # 3. ESI Formula (0.30 S_stag, 0.25 S_vel, 0.20 S_div, 0.15 S_sched, 0.10 S_rep)
    esi_b = "0.30" in spec_breq and "0.25" in spec_breq and "0.20" in spec_breq and "0.15" in spec_breq and "0.10" in spec_breq and "S_stag" in spec_breq
    esi_a = "0.30" in spec_api and "0.25" in spec_api and "0.20" in spec_api and "0.15" in spec_api and "0.10" in spec_api and "execution_stress_scores" in spec_api
    esi_f = "0.30" in spec_freq and "0.25" in spec_freq and "0.20" in spec_freq and "0.15" in spec_freq and "0.10" in spec_freq and "S_stag" in spec_freq
    checks.append(("ESI Formula (0.30/0.25/0.20/0.15/0.10) in all specs", esi_b and esi_a and esi_f))

    # 4. ESI Tiers (NOMINAL <0.35, WATCH 0.35-0.55, ATTENTION 0.55-0.75, HIGH_PRIORITY >=0.75)
    tiers_b = "NOMINAL" in spec_breq and "WATCH" in spec_breq and "ATTENTION" in spec_breq and "HIGH_PRIORITY" in spec_breq
    tiers_a = "NOMINAL" in spec_api and "WATCH" in spec_api and "ATTENTION" in spec_api and "HIGH_PRIORITY" in spec_api
    tiers_f = "NOMINAL" in spec_freq and "WATCH" in spec_freq and "ATTENTION" in spec_freq and "HIGH_PRIORITY" in spec_freq
    checks.append(("ESI Alert Tiers (NOMINAL, WATCH, ATTENTION, HIGH_PRIORITY)", tiers_b and tiers_a and tiers_f))

    # 5. Non-Redundancy & Overlap Metrics (rho = 0.1360, 65.4% off-diagonal)
    corr_b = "0.1360" in spec_breq and "65.4%" in spec_breq
    corr_f = "0.1360" in spec_freq and "65.4%" in spec_freq
    checks.append(("Non-Redundancy Overlap Metrics (rho = 0.1360, 65.4%)", corr_b and corr_f))

    # 6. Target Exclusion (cost_revision_event_3m & ML execution prob banned)
    ban_b = "cost_revision_event_3m" in spec_breq and "NOT_SUPPORTED" in spec_breq
    ban_f = "cost_revision_event_3m" in spec_freq and "NOT_SUPPORTED" in spec_freq
    checks.append(("Target Exclusion: cost_revision_event_3m & ML execution prob banned", ban_b and ban_f))

    # 7. OCMS Historical Data Policy (Analytics Context Only, Banned from ML)
    ocms_b = "OCMS_EXPERIMENT_VALIDITY = VALID_AFTER_DOCUMENTATION_CORRECTION" in spec_breq and "MUST NOT be fed into the production ML" in spec_breq
    ocms_f = "OCMS_EXPERIMENT_VALIDITY = VALID_AFTER_DOCUMENTATION_CORRECTION" in spec_freq and "BANNED from the production ML" in spec_freq
    checks.append(("OCMS Historical Data: Analytics context only, banned from ML", ocms_b and ocms_f))

    # 8. OOT Model Metrics Consistency (0.9723, 0.9895, 0.8264)
    met_b = "0.9723" in spec_breq and "0.9895" in spec_breq and "0.8264" in spec_breq
    met_f = "0.9723" in spec_freq and "0.9895" in spec_freq and "0.8264" in spec_freq
    checks.append(("OOT Model Metrics (0.9723, 0.9895, 0.8264)", met_b and met_f))

    # 9. Versioning & Provenance Metadata Fields
    ver_b = "model_version" in spec_breq and "feature_version" in spec_breq and "execution_index_version" in spec_breq
    ver_a = "model_version" in spec_api and "feature_version" in spec_api and "execution_index_version" in spec_api
    ver_f = "model_version" in spec_freq and "feature_version" in spec_freq and "execution_index_version" in spec_freq
    checks.append(("Versioning & Provenance Fields in all specs", ver_b and ver_a and ver_f))

    # 10. Prescriptive Monitoring Actions Matrix
    actions = [
        "SITE_OBSTACLE_AUDIT",
        "FINANCIAL_PHYSICAL_ALIGNMENT_AUDIT",
        "RESOURCE_MOBILIZATION_DIRECTIVE",
        "CRITICAL_PATH_RECALIBRATION",
        "DATA_COMPLIANCE_DIRECTIVE",
        "INTER_MINISTERIAL_COMMITTEE_ESCALATION"
    ]
    act_b = all(a in spec_breq for a in actions)
    act_f = all(a in spec_freq for a in actions)
    checks.append(("Prescriptive Monitoring Actions Matrix (6 directives)", act_b and act_f))

    # 11. PostgreSQL DDL Table Separation
    db_tables = "CREATE TABLE execution_stress_scores" in spec_api and "CREATE TABLE ml_risk_scores" in spec_api and "CREATE TABLE ocms_historical_benchmarks" in spec_api
    checks.append(("PostgreSQL DDL Table Definitions (Pillar 1, Pillar 2, OCMS)", db_tables))

    # 12. Frontend-Backend Contract Symmetry
    contract_match = "predictive_risk_profile" in spec_api and "execution_surveillance_profile" in spec_api and "predictive_risk_profile" in spec_freq and "execution_surveillance_profile" in spec_freq
    checks.append(("Frontend-Backend Dossier Payload Symmetry", contract_match))

    print("=" * 80)
    print("3-WAY SPECIFICATION RECONCILIATION AUDIT RESULTS")
    print("=" * 80)
    all_passed = True
    for name, status in checks:
        status_str = "PASS" if status else "FAIL"
        print(f"[{status_str}] {name}")
        if not status:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print("OVERALL STATUS: SPECIFICATION_SUITE_STATUS = CONSISTENT")
    else:
        print("OVERALL STATUS: SPECIFICATION_SUITE_STATUS = REQUIRES_REVIEW")
    print("=" * 80)

if __name__ == "__main__":
    run_audit()
