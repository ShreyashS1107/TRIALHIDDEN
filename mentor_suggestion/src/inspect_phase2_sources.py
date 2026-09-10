import os
import sys
import json
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("INSPECTING PHASE 1 OUTPUTS & HISTORICAL OUTCOME SOURCES")
print("="*80)

# Phase 1 files
cohort_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\data\clustering_cohort.csv"
profiles_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\data\project_clustering_profiles.csv"
assignments_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering\cluster_assignments.csv"
meta_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering\clustering_metadata.json"

cohort_df = pd.read_csv(cohort_path)
profiles_df = pd.read_csv(profiles_path)
assignments_df = pd.read_csv(assignments_path)

with open(meta_path) as f:
    meta = json.load(f)

print(f"Cohort CSV: {len(cohort_df)} rows, {cohort_df['project_id'].nunique()} unique project_ids")
print(f"Profiles CSV: {len(profiles_df)} rows, {profiles_df['project_id'].nunique()} unique project_ids")
print(f"Assignments CSV: {len(assignments_df)} rows, {assignments_df['project_id'].nunique()} unique project_ids")
print(f"Null cluster_id in assignments: {assignments_df['cluster_id'].isnull().sum()}")
print(f"Duplicate project_ids: {assignments_df['project_id'].duplicated().sum()}")
print("Cluster distribution in assignments:")
print(assignments_df['cluster_id'].value_counts().sort_index())

# Historical sources
hist_comp_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\historical_completed_projects.csv"
linked_hist_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\linked_project_history.csv"
features_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\features\feature_dataset_v1.csv"
paimana_comp_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_completed_projects.csv"

hist_comp = pd.read_csv(hist_comp_path)
linked_hist = pd.read_csv(linked_hist_path)
f_df = pd.read_csv(features_path, low_memory=False)
p_comp = pd.read_csv(paimana_comp_path)

print(f"\nHistorical Completed Projects ({hist_comp_path}):")
print(f"  Rows: {len(hist_comp)}, Unique projects: {hist_comp['project_id'].nunique()}")
print(f"  Columns: {list(hist_comp.columns)}")
print(f"  Date range: {hist_comp['actual_completion_date'].min()} to {hist_comp['actual_completion_date'].max()}")
print(f"  Schedule delay stats: {hist_comp['historical_delay_months'].describe().to_dict()}")
print(f"  Cost overrun obs count: {hist_comp['historical_cost_overrun_pct'].dropna().count()}")

print(f"\nPAIMANA Completed Projects ({paimana_comp_path}):")
print(f"  Rows: {len(p_comp)}, Unique projects: {p_comp['project_id'].nunique()}")
print(f"  Columns: {list(p_comp.columns)}")

print(f"\nFeature Dataset V1 ({features_path}):")
print(f"  Rows: {len(f_df)}, Unique projects: {f_df['project_id'].nunique()}, Prediction months: {f_df['prediction_month'].nunique()}")
print(f"  Prediction months list: {sorted(f_df['prediction_month'].unique())}")
print(f"  Snapshot distribution by month:\n{f_df['prediction_month'].value_counts().sort_index()}")
