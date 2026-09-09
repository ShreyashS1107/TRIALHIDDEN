# Production Inference Adapter Specification & Integration Guide

**Problem Statement:** SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform  
**Component:** AI/ML Production Inference Adapter  
**File Path:** [`inference/adapter.py`](file:///c:/Users/Shreyash/Documents/vs%20work/SIH26103/inference/adapter.py)  
**Status:** IMPLEMENTED & PRODUCTION READY  

---

## 1. Executive Summary

The **Production Inference Adapter** provides an authoritative, leak-free bridge connecting:
$$\text{New PAIMANA PDF} + \text{report\_month} + \text{PostgreSQL Historical Data} \longrightarrow \begin{cases} \text{75 Production ML Features (71 Numerical + 4 Categorical)} \\ \text{12 ESI Operational Surveillance Inputs} \end{cases} \longrightarrow \text{Model Scoring}$$

> [!IMPORTANT]
> **Backend Integration Rule:**  
> The backend service (FastAPI / Celery) **MUST NOT** reimplement any feature engineering formulas, ESI stress calculations, or model preprocessing pipelines. The backend must invoke this adapter.

---

## 2. Public Interface Contract

### Primary Functional Entrypoint

```python
from inference import extract_features_for_inference

features_df, esi_df = extract_features_for_inference(
    pdf_path="path/to/FlashReport_July_2026.pdf",
    report_month="2026-07",
    db_session=db_session
)
```

### Class-Based Interface (with Metadata & Scoring)

```python
from inference import InferenceAdapter, ProductionScorer

# 1. Extract Features strictly as of report_month
adapter = InferenceAdapter(db_session=db_session)
features_df, esi_df, metadata_df = adapter.extract_features(
    pdf_path="path/to/FlashReport_July_2026.pdf",
    report_month="2026-07"
)

# 2. Execute Dual-Pillar Inference
scorer = ProductionScorer()
ml_scores_df, esi_scores_df = scorer.score(features_df, esi_df)
```

---

## 3. Input & Output Contract

### Inputs
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `pdf_path` | `str` | Yes | Filesystem path to the monthly MoSPI PAIMANA Flash Report PDF. |
| `report_month` | `str` | Yes | Point-in-time boundary epoch in ISO format (`YYYY-MM`). |
| `db_session` | `Any` | Yes | Database session abstraction (SQLAlchemy `Session`, `DataFrame`, or query callback). |

### Outputs
1. **`features_df` (Exact 75 Production ML Features):**
   - **71 Numerical Features**: Cost metrics, project age, planned duration, lag features, velocities (1m, 3m, 6m), stagnation streaks, escalation ratios, agency/state context aggregates.
   - **4 Categorical Features**: `project_size_category`, `current_schedule_status_as_of_t`, `reporting_structure_version_t`, `table_source_t`.
   - Strictly excludes target labels, target metadata, raw date strings, and OCMS historical priors.

2. **`esi_df` (Exact 12 ESI Input Features):**
   - `months_since_last_progress_increase_t` ($S_{\text{stag}}$)
   - `stagnant_3m_t` ($S_{\text{stag}}$)
   - `remaining_physical_progress_t` ($S_{\text{stag}}$)
   - `progress_velocity_3m_t` ($S_{\text{vel}}$)
   - `progress_change_1m_t` ($S_{\text{vel}}$)
   - `schedule_slippage_months_t` ($S_{\text{sched}}$)
   - `months_to_original_doc_t` ($S_{\text{sched}}$)
   - `expenditure_ratio_pct_t` ($S_{\text{div}}$)
   - `physical_progress_t` ($S_{\text{div}}$)
   - `observation_gap_flag_t` ($S_{\text{rep}}$)
   - `missing_physical_progress_t` ($S_{\text{rep}}$)
   - `schedule_revision_count_to_date_t` ($S_{\text{rep}}$)

3. **`metadata_df` (Project Identifiers & Traceability):**
   - `project_id`, `project_name`, `agency`, `state`, `report_month`, `approval_start_date`, `original_completion_date`, `revised_completion_date`, `legacy_ocms_code`.

---

## 4. Point-in-Time Safeguards & Governance

1. **Zero Future Leakage:**  
   Historical lookups strictly filter $\text{report\_month} < \text{as\_of\_month}$. Future observations are discarded before feature generation.
2. **Deterministic Aggregations:**  
   Agency and state aggregates are computed dynamically from projects active at $\text{month } t$, strictly avoiding global lifetime pooling.
3. **OCMS Data Separation:**  
   Multi-decade OCMS priors remain dedicated to analytical context and are strictly prohibited from entering the 75 ML feature matrix.

---

## 5. End-to-End Scoring Outputs

| Output Column | Pillar | Data Type | Range / Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `schedule_delay_risk` | Pillar 1 | Float64 | [0.0000, 1.0000] | Platt-calibrated delay probability (RF_02) |
| `cost_overrun_risk` | Pillar 1 | Float64 | [0.0000, 1.0000] | Balanced Random Forest score |
| `schedule_revision_risk` | Pillar 1 | Float64 | [0.0000, 1.0000] | Logistic Regression revision score |
| `selected_integrated_risk` | Pillar 1 | Float64 | [0.0000, 1.0000] | Candidate B index ($0.50 \times \text{Sched} + 0.35 \times \text{Cost} + 0.15 \times \text{Rev}$) |
| `risk_band` | Pillar 1 | String | `LOW`, `MODERATE`, `HIGH`, `VERY_HIGH` | Calibrated operational risk band |
| `dominant_component` | Pillar 1 | String | `Schedule Delay`, `Cost Overrun`, `Schedule Revision` | Primary predictive risk contributor |
| `execution_stress_index` | Pillar 2 | Float64 | [0.0000, 1.0000] | 5-dimension deterministic ESI score |
| `esi_tier` | Pillar 2 | String | `NOMINAL`, `WATCH`, `ATTENTION`, `HIGH_PRIORITY` | Observable site-stress triage tier |
| `dominant_stressor` | Pillar 2 | String | 5 stressor categories | Highest weighted site friction factor |
| `suggested_action` | Pillar 2 | String | 6 action codes | Automated prescriptive directive |

---

## 6. Celery / Background Ingestion Task Example

```python
# tasks/ingestion_tasks.py
from celery import Celery
from inference import InferenceAdapter, ProductionScorer
from database import get_db_session

celery_app = Celery("mospi_tasks", broker="redis://localhost:6379/1")

@celery_app.task(name="tasks.ingest_flash_report_pdf")
def ingest_flash_report_pdf(pdf_path: str, report_month: str):
    with get_db_session() as db_session:
        adapter = InferenceAdapter(db_session=db_session)
        features_df, esi_df, metadata_df = adapter.extract_features(
            pdf_path=pdf_path,
            report_month=report_month
        )

        scorer = ProductionScorer()
        ml_scores_df, esi_scores_df = scorer.score(features_df, esi_df)

        # Bulk insert into PostgreSQL monthly_snapshots, ml_risk_scores, execution_stress_scores
        save_to_database(db_session, metadata_df, ml_scores_df, esi_scores_df)

    return {"status": "SUCCESS", "report_month": report_month, "count": len(features_df)}
```
