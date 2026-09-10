import os
import sys
import pandas as pd
import numpy as np

features_v1_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\features\feature_dataset_v1.csv"
linked_hist_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\linked_project_history.csv"

f_df = pd.read_csv(features_v1_path, low_memory=False)
l_df = pd.read_csv(linked_hist_path, low_memory=False)

f_apr = f_df[f_df['prediction_month'] == '2025-04'].copy()
l_apr = l_df[l_df['as_of_date'] == '2025-04'].copy()

merged = f_apr.merge(l_apr, on='project_id', how='inner')
print(f"Merged {len(merged)} records for correlation analysis.")

corr_cols_paimana = [
    'schedule_slippage_months_t',
    'months_to_original_doc_t',
    'months_to_revised_doc_t',
    'physical_progress_t',
    'project_age_months_t',
    'original_cost_log',
    'planned_duration_months',
    'expenditure_ratio_pct_t',
    'stagnant_3m_t'
]

corr_cols_ocms = [
    'pre_paimana_observation_months',
    'pre_paimana_schedule_revision_count',
    'pre_paimana_cost_revision_count',
    'pre_paimana_max_schedule_slippage_months'
]

for col in corr_cols_paimana + corr_cols_ocms:
    merged[col] = pd.to_numeric(merged[col], errors='coerce')

corr_matrix = merged[corr_cols_paimana + corr_cols_ocms].corr().round(3)
print("\nCorrelation Matrix between PAIMANA Active Features and Pre-PAIMANA History:")
print(corr_matrix[corr_cols_ocms].loc[corr_cols_paimana].to_string())
