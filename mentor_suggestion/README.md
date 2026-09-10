# Mentor Suggestion: Project-Similarity Historical Benchmarking

**SIH 2026 Problem Statement SIH26103**: Ministry of Statistics and Programme Implementation (MoSPI) / Infrastructure and Project Monitoring Division (IPMD) Integrated Project-Monitoring Platform  
**Current Status**: `PHASE_2B_STATUS = COMPLETE`  
**Benchmark Layer Decision**: `BENCHMARK_LAYER_DECISION = NO_CLEAR_INCREMENTAL_VALUE`  
**Production ML Change**: `PRODUCTION_ML_CHANGE = NO`  
**Experimental Isolation Directory**: `SIH26103/mentor_suggestion/`  

---

## 1. System Architecture & Conceptual Flow

```
                      OCMS (2011–2025) + PAIMANA (2025–2026)
                                        |
                                        v
                     1,442 Comprehensively Linked Projects
                                        |
                                        v
                    Historical Pre-Transition Project Profiles
                                        |
                                        v
                    Project-Similarity Clustering (K = 4)
                                        |
                                        v
                           4 Distinct Project Archetypes
                                        |
                                        v
                   Point-in-Time Historical Archetype Benchmarks
                                        |
                                        v
                    Benchmark Deviations & Contextual Features
                                        |
                                        v
                    Phase 2B: Controlled Predictive ML Experiment
                                        |
                     ---------------------------------------
                     |                                     |
                     v                                     v
             MODEL A (Baseline)                   MODEL B (Candidate)
             PAIMANA-Only (75 Feats)              PAIMANA + Benchmarks (81 Feats)
                     |                                     |
                     ---------------------------------------
                                        |
                                        v
                    Out-of-Time Generalization (Feb–Mar 2026)
             Schedule Delay : OOT PR-AUC 0.9722 (A) vs 0.9713 (B) [Δ = -0.0009]
             Cost Overrun   : OOT PR-AUC 0.9881 (A) vs 0.9881 (B) [Δ = -0.0000]
             Sched Revision : OOT PR-AUC 0.0519 (A) vs 0.0641 (B) [Δ = +0.0121, Worse Calib]
                                        |
                                        v
          CONCLUSION: RETAIN ARCHETYPES FOR CONTEXTUAL BENCHMARKING ONLY
                         DO NOT ADD BENCHMARKS TO PRODUCTION ML
```

---

## 2. Phase 1 Summary: Project Archetypes ($K = 4$)

Phase 1 established that the 1,442 overlapping projects partition into 4 distinct physical archetypes using standardized K-Means:

| Cluster ID | Neutral Physical Archetype Label | Project Count (N) | Cohort % | Mean Cost | Planned Duration | Pre-PAIMANA Slippage | Pre-PAIMANA Cost Revisions |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | **High Administrative Cost-Revision Volatility** | 252 | 17.5% | ₹494.6 Cr | 36.6 mos | 15.7 mos | **2.64 revs** |
| **1** | **Standard Rapid-Execution / Linear Infrastructure** | 946 | 65.6% | ₹794.9 Cr | 40.9 mos | 1.6 mos | 0.22 revs |
| **2** | **Severe Legacy Stagnation & Chronic Slippage** | 69 | 4.8% | ₹1,566.0 Cr | **153.5 mos** | **159.0 mos** | 1.29 revs |
| **3** | **Mega Capital High-Value Infrastructure** | 175 | 12.1% | **₹7,588.0 Cr** | 95.6 mos | 7.1 mos | 0.91 revs |

---

## 3. Phase 2A Summary: Point-in-Time Benchmarks

Phase 2A built and validated a strict point-in-time historical benchmarking layer across all 15,769 candidate snapshot rows across 12 prediction epochs (`2025-04` through `2026-03`) with zero temporal leakage violations (`BENCHMARK_LEAKAGE_STATUS = CERTIFIED_LEAKAGE_FREE`).

---

## 4. Phase 2B Implementation & Controlled Predictive Experiment Results

Phase 2B rigorously tested whether adding historical project-archetype benchmarks provides incremental predictive value beyond the frozen 75-feature PAIMANA baseline.

### Out-of-Time Performance Comparison (Feb–Mar 2026)

| Target | Model Family | Configuration | # Feat | Val PR | OOT PR | OOT ROC | OOT Brier | OOT ECE | Δ OOT PR | Δ OOT ROC | 95% Bootstrap CI (Δ OOT PR) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **schedule_delay_3m** | RF_Calibrated | Model A (PAIMANA-Only) | 75 | **0.9910** | **0.9722** | **0.9723** | **0.0391** | **0.0302** | Baseline | Baseline | Baseline |
| | | Model B (PAIMANA + Benchmarks) | 81 | 0.9906 | 0.9713 | 0.9710 | 0.0394 | 0.0342 | **-0.0009** | -0.0013 | [-0.0020, +0.0014] |
| **cost_overrun_state_3m** | Balanced_RF | Model A (PAIMANA-Only) | 75 | **0.9914** | **0.9881** | **0.9895** | 0.0386 | 0.1446 | Baseline | Baseline | Baseline |
| | | Model B (PAIMANA + Benchmarks) | 81 | 0.9913 | 0.9881 | 0.9894 | **0.0373** | **0.1401** | **-0.0000** | -0.0001 | [-0.0009, +0.0001] |
| **schedule_revision_3m** | Logistic_L2 | Model A (PAIMANA-Only) | 75 | 0.0978 | 0.0519 | 0.8264 | **0.0176** | **0.0202** | Baseline | Baseline | Baseline |
| | | Model B (PAIMANA + Benchmarks) | 81 | **0.1230** | **0.0641** | **0.8455** | 0.0212 | 0.0236 | **+0.0121** | +0.0191 | [+0.0049, +0.0303] |

### Key Experimental Insights:
1. **Schedule Delay**: Model A is strictly superior. Direct physical progress metrics (`months_to_original_doc_t`, `current_schedule_status`) capture schedule velocity far more accurately than broad archetype aggregates.
2. **Cost Overrun**: Exact tie. PAIMANA's direct expenditure and cost revision features (`cost_escalation_pct_t`, `has_cost_revision_t`) dominate with >46% combined feature importance; benchmark features contribute zero incremental discrimination.
3. **Schedule Revision**: While Model B showed a small statistical PR-AUC increase (+0.0121 on a 1.19% base rate), feature ablation proved this was driven entirely by the static legacy indicator (`is_legacy_linked`), not archetype benchmarking. Crucially, Model B degraded probability calibration (Brier worsened from 0.0176 to 0.0212) and achieved an operational F1 of only 0.1176.

---

## 5. Feature Ablation Breakdown

- **Config A (PAIMANA Baseline, 75 Feats)**: Champion model across all primary targets.
- **Config B (PAIMANA + 6 Valid Benchmarks, 81 Feats)**: No incremental value on delay/cost.
- **Config C (PAIMANA + Outcome Stats Only, 78 Feats)**: Δ OOT PR = -0.0008 (Delay), -0.0004 (Cost), -0.0003 (Revision). Outcome averages add zero predictive signal.
- **Config D (PAIMANA + Deviations Only, 77 Feats)**: Δ OOT PR = -0.0011 (Delay), -0.0001 (Cost). Deviations add no discriminative power.
- **Config E (PAIMANA + Distance & Continuity, 77 Feats)**: Isolates legacy project correlation on revision target, but worsens calibration.
- **Config F (Research Diagnostic: PAIMANA + Cluster ID, 76 Feats)**: Δ OOT PR = -0.0012 (Delay), -0.0003 (Cost), +0.0005 (Revision). Proves raw cluster membership is uninformative for ML trees.

---

## 6. Strategic Recommendation for Judges & Production

```
                                  THREE-PILLAR ARCHITECTURE
┌──────────────────────────────────────────┬──────────────────────────────────────────┬──────────────────────────────────────────┐
│        PILLAR 1: PREDICTIVE ML           │         PILLAR 2: STRESS ENGINE          │     PILLAR 3: CONTEXTUAL BENCHMARKS      │
├──────────────────────────────────────────┼──────────────────────────────────────────┼──────────────────────────────────────────┤
│ - Model: Frozen PAIMANA-Only (75 Feats)  │ - Model: Execution Stress Index (ESI)    │ - Model: Longitudinal Archetypes (K=4)   │
│ - Output: 3-Month Future Probabilities   │ - Output: Current Friction & Bottlenecks │ - Output: Peer Comparisons & Baselines   │
│ - Delay PR: 0.9722 | Cost PR: 0.9881     │ - Deterministic Formula (No ML)          │ - Descriptive Decision Support (No ML)   │
│ - Role: Automated Early-Warning Alerts   │ - Role: Instant Operational Stress Score │ - Role: Explainability & Peer Context    │
└──────────────────────────────────────────┴──────────────────────────────────────────┴──────────────────────────────────────────┘
```

**Final Decision**:
- **Production ML Models**: Retain frozen 75-feature PAIMANA-only models. Do NOT add benchmark features to ML.
- **Project Archetypes**: Retain the 4 physical archetypes and point-in-time peer benchmarks in the MoSPI dashboard as a rich contextual explainability and peer-comparison layer.

---

## 7. Persisted Phase 2B Reports & Artifacts

```
SIH26103/mentor_suggestion/
├── reports/
│   ├── BENCHMARK_SEMANTIC_AUDIT.txt                   # Complete audit of benchmark statistics & denominators
│   ├── PHASE_2B_EXPERIMENT_RESULTS.txt                # Full tabular metrics, confusion matrices, & CIs
│   ├── PHASE_2B_FEATURE_ABLATION.txt                  # 6-configuration ablation comparison (Configs A-F)
│   ├── PHASE_2B_LEAKAGE_AUDIT.txt                     # Point-in-time causal integrity certification (0 violations)
│   ├── PHASE_2B_RECOMMENDATION.txt                    # Strategic architectural recommendations & answers to 12 Qs
│   ├── PHASE_2B_EXPERIMENT_RESULTS.csv                # Machine-readable evaluation dataset
│   ├── benchmark_coverage_analysis.csv                # Feature coverage by split & cluster
│   ├── benchmark_redundancy_correlation.csv           # Cross-layer correlation matrix
│   ├── feature_importances_schedule_delay_3m.csv      # Gini feature importances for schedule delay
│   ├── feature_importances_cost_overrun_state_3m.csv   # Gini feature importances for cost overrun
│   └── feature_coefficients_schedule_revision_3m.csv  # Standardized coefficients for schedule revision
│
└── src/
    ├── audit_semantic_denominators.py                 # Semantic denominator audit script
    ├── run_phase2b_experiment.py                      # Phase 2B controlled modeling experiment script
    ├── compute_phase2b_diagnostics.py                 # Diagnostics, coverage, & bootstrap script
    └── verify_hashes.py                               # Production SHA-256 hash verifier
```

---

## 8. Production Invariance Guarantee

- **Zero Modifications to Production Files**:
  * `data/paimana_master_dataset.csv`: MATCHED (`6a366499...`)
  * `data/paimana_completed_projects.csv`: MATCHED (`48b942e1...`)
  * `data/paimana_newly_added_projects.csv`: MATCHED (`588fdb59...`)
  * `target_labels_v2/target_dataset_v2.csv`: MATCHED (`6ca7a502...`)
  * `features/feature_dataset_v1.csv`: MATCHED (`60e30f25...`)
  * `ml/models/best_model_random_forest.joblib`: MATCHED (`35808a0e...`)
  * **Production Hash Violations**: **0 (ZERO)**.
