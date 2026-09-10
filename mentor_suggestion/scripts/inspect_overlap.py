import os
import sys
import pandas as pd
import numpy as np

paimana_master_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_master_dataset.csv"
features_v1_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\features\feature_dataset_v1.csv"
target_v2_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\target_labels_v2\target_dataset_v2.csv"
linked_hist_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\linked_project_history.csv"
hist_completed_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\historical_completed_projects.csv"
agency_priors_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\agency_historical_priors.csv"
sector_priors_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\sector_historical_priors.csv"

# Load datasets
p_df = pd.read_csv(paimana_master_path)
f_df = pd.read_csv(features_v1_path)
t_df = pd.read_csv(target_v2_path)
l_df = pd.read_csv(linked_hist_path)
c_df = pd.read_csv(hist_completed_path)

print("=== 1. POPULATION & OVERLAP AUDIT ===")
total_paimana_rows = len(p_df)
unique_p_projects = p_df['project_id'].nunique()
unique_p_months = p_df['report_month'].nunique()
print(f"PAIMANA Master: {total_paimana_rows} rows, {unique_p_projects} unique projects, {unique_p_months} months ({p_df['report_month'].min()} to {p_df['report_month'].max()})")

# Legacy code distribution
legacy_notna = p_df[p_df['legacy_ocms_code'].notna()]
p_with_legacy = legacy_notna['project_id'].nunique()
unique_legacy_codes = legacy_notna['legacy_ocms_code'].nunique()
print(f"Projects with legacy_ocms_code: {p_with_legacy} (mapped to {unique_legacy_codes} unique legacy code strings)")

# Linked project history
l_pids = l_df['project_id'].nunique()
l_obs = l_df[l_df['pre_paimana_observation_months'] > 0]['project_id'].nunique()
l_zero_obs = l_df[l_df['pre_paimana_observation_months'] == 0]['project_id'].nunique()
print(f"Linked Project History rows: {len(l_df)}, unique project_ids: {l_pids}")
print(f"Projects with pre-PAIMANA obs > 0: {l_obs}")
print(f"Projects with pre-PAIMANA obs == 0 (transition boundary): {l_zero_obs}")
print(f"Unmatched PAIMANA projects (no legacy code): {unique_p_projects - p_with_legacy}")

# Feature dataset rows
print(f"\nFeature Dataset V1: {len(f_df)} rows, {f_df['project_id'].nunique()} unique projects, {f_df['prediction_month'].nunique()} prediction months")

# Distribution of pre-PAIMANA observation months as of 2025-04
l_apr2025 = l_df[l_df['as_of_date'] == '2025-04']
print(f"\nAs of 2025-04 (First PAIMANA month):")
print(l_apr2025['pre_paimana_observation_months'].describe())
print(f"Distribution of pre-PAIMANA observation months count:")
print(l_apr2025['pre_paimana_observation_months'].value_counts().sort_index())

# Start dates analysis in PAIMANA master
p_first = p_df.sort_values('report_month').groupby('project_id').first().reset_index()
print(f"\nApproval / Start Year Distribution across all {len(p_first)} PAIMANA projects:")
p_first['start_year'] = pd.to_datetime(p_first['approval_start_date'], errors='coerce').dt.year
print(p_first['start_year'].value_counts(dropna=False).sort_index())

# Start year for linked vs non-linked
p_first['is_linked_obs'] = p_first['project_id'].isin(l_df[l_df['pre_paimana_observation_months'] > 0]['project_id'].unique())
print(f"\nStart Year for Projects with Pre-PAIMANA Observations (N={l_obs}):")
print(p_first[p_first['is_linked_obs']]['start_year'].value_counts(dropna=False).sort_index())

print(f"\nStart Year for Projects without Pre-PAIMANA Observations (N={len(p_first) - l_obs}):")
print(p_first[~p_first['is_linked_obs']]['start_year'].value_counts(dropna=False).sort_index())

# Sector distribution for linked vs all
print("\nSector breakdown for all vs linked:")
s_all = p_first['sector'].value_counts()
s_linked = p_first[p_first['is_linked_obs']]['sector'].value_counts()
sector_comp = pd.DataFrame({'all_projects': s_all, 'linked_with_obs': s_linked})
sector_comp['coverage_pct'] = (sector_comp['linked_with_obs'] / sector_comp['all_projects'] * 100).round(1)
print(sector_comp)
