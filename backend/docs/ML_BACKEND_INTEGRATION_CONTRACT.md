# ML-Backend Integration Contract (Phase 4B)

## 1. Purpose
This document defines the strict integration boundary between the Backend Ingestion Worker (Celery) and the ML Feature Extraction Pipeline. Because the ML inference models (`BatchScorer` and `ExecutionSurveillanceEngine`) require exact feature matrices (75 and 12 features respectively) that rely heavily on longitudinal historical data, the Backend cannot simply parse a single PDF to generate these features. The ML team must provide a robust feature extraction adapter.

## 2. Ownership Boundary
**Backend Owns:**
- PDF upload handling, security validation, and temp storage.
- Background task queuing (Celery/Redis).
- Calling the ML-provided extraction adapter.
- Validating the returned feature DataFrames against the contract.
- Passing validated DataFrames to the existing `BatchScorer` and `ExecutionSurveillanceEngine`.
- Persisting ML/ESI outputs via `IngestionPersistenceService`.
- Generating system alerts via `AlertGenerationService`.

**ML Team Owns:**
- The actual extraction of raw data from the PDF.
- The stateful longitudinal feature engineering (using historical database context + new PDF data).
- Providing exactly 75 features for the Risk model and 12 features for the ESI model.

## 3. Risk Input Contract (75 Features)
The provided Risk DataFrame must contain EXACTLY the following 71 numeric and 4 categorical features, strictly matching `ai-ml/ml/inference/contracts.py`:

**Numerical Features (71):**
`original_cost_crore`, `project_age_months_t`, `planned_duration_months`, `original_cost_log`, `physical_progress_t`, `cumulative_expenditure_t`, `revised_cost_t`, `cost_escalation_pct_t`, `expenditure_ratio_pct_t`, `remaining_physical_progress_t`, `schedule_slippage_months_t`, `months_to_original_doc_t`, `months_to_revised_doc_t`, `physical_progress_lag1`, `physical_progress_lag2`, `physical_progress_lag3`, `progress_change_1m_t`, `progress_change_2m_t`, `progress_change_3m_t`, `progress_velocity_1m_t`, `progress_velocity_3m_t`, `progress_velocity_6m_t`, `max_progress_to_date_t`, `min_progress_to_date_t`, `average_progress_to_date_t`, `progress_std_to_date_t`, `cumulative_expenditure_lag1`, `cumulative_expenditure_lag3`, `monthly_expenditure_delta_t`, `expenditure_change_1m_t`, `expenditure_change_3m_t`, `expenditure_velocity_3m_t`, `expenditure_velocity_6m_t`, `avg_monthly_expenditure_to_date_t`, `expenditure_growth_rate_t`, `negative_expenditure_delta_flag_t`, `stagnant_2m_t`, `stagnant_3m_t`, `stagnant_6m_t`, `months_since_last_progress_increase_t`, `longest_stagnation_to_date_t`, `progress_change_last_3m_t`, `has_cost_revision_t`, `cost_revision_count_to_date_t`, `months_since_last_cost_revision_t`, `largest_cost_revision_pct_to_date_t`, `cost_reduction_pct_as_of_t`, `has_revised_schedule_as_of_t`, `schedule_revision_count_to_date_t`, `months_since_last_schedule_revision_t`, `months_observed_to_date_t`, `months_since_first_observed_t`, `observation_coverage_ratio_t`, `consecutive_observation_count_t`, `months_since_last_observation_t`, `missing_physical_progress_t`, `missing_expenditure_t`, `missing_revised_cost_t`, `missing_revised_doc_t`, `observation_gap_flag_t`, `state_active_project_count_t`, `state_mean_progress_t`, `state_median_progress_t`, `state_mean_cost_t`, `state_mean_expenditure_ratio_t`, `agency_active_project_count_t`, `agency_mean_progress_t`, `agency_median_progress_t`, `agency_mean_cost_t`, `agency_mean_expenditure_ratio_t`, `focused_cohort_indicator_t`

**Categorical Features (4):**
`project_size_category`, `current_schedule_status_as_of_t`, `reporting_structure_version_t`, `table_source_t`

*Note: Future/target columns (e.g., `schedule_delay_3m`, `cost_overrun_state_3m`) MUST NEVER be included in this matrix.*

## 4. ESI Input Contract (12 Features)
The ESI DataFrame must contain EXACTLY the following 12 features, matching `ai-ml/ml/surveillance/contracts.py`:
`months_since_last_progress_increase_t`, `stagnant_3m_t`, `remaining_physical_progress_t`, `progress_velocity_3m_t`, `progress_change_1m_t`, `schedule_slippage_months_t`, `months_to_original_doc_t`, `expenditure_ratio_pct_t`, `physical_progress_t`, `observation_gap_flag_t`, `missing_physical_progress_t`, `schedule_revision_count_to_date_t`

## 5. Risk Output Contract
The `BatchScorer` returns a DataFrame with:
`project_id`, `report_month`, `schedule_delay_risk`, `cost_overrun_risk`, `schedule_revision_risk`, `selected_integrated_risk`, `risk_band`, `dominant_component`, `schedule_contribution`, `cost_contribution`, `schedule_revision_contribution`, `model_version`.

## 6. ESI Output Contract
The `ExecutionSurveillanceEngine` returns a DataFrame with:
`project_id`, `report_month`, `s_stag`, `s_vel`, `s_div`, `s_sched`, `s_rep`, `flag_stag`, `flag_vel`, `flag_div`, `flag_sched`, `flag_rep`, `total_stress_flags`, `execution_stress_index`, `esi_tier`, `dominant_stressor`, `suggested_action`, `execution_index_version`.

## 7. Required Metadata
Both DataFrames passed to the backend from the ML pipeline must contain:
- `project_id` (str)
- `report_month` (str, format YYYY-MM)

## 8. PDF Extraction Interface
The ML team must provide a Python function/class matching this protocol:

```python
import pandas as pd
from sqlalchemy.orm import Session
from typing import Tuple

def extract_features_for_inference(
    pdf_path: str, 
    report_month: str, 
    db_session: Session
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parses a PDF, retrieves historical context from DB, and returns:
    1. risk_features_df (containing 75 exact ML features + project_id + report_month)
    2. esi_features_df (containing 12 exact ESI features + project_id + report_month)
    """
    pass
```
*Note: The existing script `ai-ml/scripts/extract_pdfs.py` is strictly a RAW DATA extractor (dates, costs). It is NOT production-ready for the 75-feature contract and cannot be plugged in directly.*

## 9. Validation Rules
The Backend Integration layer will enforce:
- DataFrame shape/columns match the exact required lists.
- No leakage/target columns are present.
- `project_id` and `report_month` exist.
- Will REJECT the execution if any feature is missing, rather than fabricating default/zero/mean values.

## 10. Error Handling
- If the ML pipeline fails, the Backend catches the Exception, safely deletes the `/tmp` PDF, logs a Server Error, and aborts persistence to avoid partial corrupt database states.

## 11. Database Context Requirements
Longitudinal features (e.g. `progress_velocity_3m_t`, `physical_progress_lag1`) mathematically require historical data. The ML extractor MUST use the provided `db_session` to query the previous months' data from PostgreSQL to compute the current month's features. The backend cannot and will not calculate these.

## 12. End-to-End Sequence
1. API receives PDF upload -> HTTP 202 -> Task Queued.
2. Celery Worker starts -> passes PDF path and `db_session` to `extract_features_for_inference`.
3. ML Layer returns `risk_df` (75 features) and `esi_df` (12 features).
4. Backend Validates DataFrames.
5. Backend invokes `BatchScorer.score_batch(risk_df)`.
6. Backend invokes `ExecutionSurveillanceEngine.compute_scores(esi_df)`.
7. Backend invokes `IngestionPersistenceService` (Upsert to DB).
8. Backend invokes `AlertGenerationService` (Insert to DB).
9. Cleanup `/tmp` PDF. Task COMPLETE.

## 13. Explicit Non-Responsibilities of Backend
The Backend will NOT:
- Fill missing NaN feature values.
- Calculate Lag/Velocity features.
- Calculate State/Agency group means (`state_mean_progress_t`).
- Alter the mathematical outputs of the models.

## 14. Exact Information ML Team Must Provide
- The fully operational implementation of `extract_features_for_inference(...)` as an importable Python module, handling both raw PDF parsing and historical database-backed feature engineering.
