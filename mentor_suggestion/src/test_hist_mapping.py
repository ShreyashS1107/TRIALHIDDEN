import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

# Load frozen Phase 1 models
scaler_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering\clustering_scaler.joblib"
model_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering\clustering_model.joblib"
assignments_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering\cluster_assignments.csv"
hist_comp_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\historical_completed_projects.csv"
paimana_comp_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_completed_projects.csv"
features_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\features\feature_dataset_v1.csv"
linked_hist_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\linked_project_history.csv"

scaler = joblib.load(scaler_path)
kmeans = joblib.load(model_path)
assignments = pd.read_csv(assignments_path)
hist_comp = pd.read_csv(hist_comp_path)
p_comp = pd.read_csv(paimana_comp_path)
f_df = pd.read_csv(features_path, low_memory=False)
l_df = pd.read_csv(linked_hist_path, low_memory=False)

print("="*80)
print("EXPLORING HISTORICAL COMPLETED PROJECTS -> CLUSTER MAPPING")
print("="*80)

# Historical completed project dates and validity
print(f"Historical completed rows: {len(hist_comp)}")
valid_dates = hist_comp[hist_comp['actual_completion_date'].str.match(r'^\d{4}-\d{2}$', na=False)].copy()
print(f"Rows with valid actual_completion_date YYYY-MM: {len(valid_dates)}")

# Feature extraction for historical completed projects
# 6 features: original_cost_log, planned_duration_months, pre_paimana_obs_months, historical_schedule_revision_count, historical_cost_revision_count, pre_paimana_max_schedule_slippage_months
valid_dates['original_cost_crore'] = pd.to_numeric(valid_dates['original_cost'], errors='coerce')
valid_dates['original_cost_log'] = np.log1p(valid_dates['original_cost_crore'].clip(lower=0).fillna(valid_dates['original_cost_crore'].median()))

def calc_dur(r):
    if pd.isna(r['original_doc']) or pd.isna(r['report_month']):
        return 38.0
    try:
        y1, m1 = map(int, str(r['report_month'])[:7].split('-'))
        y2, m2 = map(int, str(r['original_doc'])[:7].split('-'))
        dur = (y2 - y1) * 12 + (m2 - m1)
        return float(dur) if 0 <= dur <= 300 else 38.0
    except:
        return 38.0

valid_dates['planned_duration_months'] = valid_dates.apply(calc_dur, axis=1)
valid_dates['pre_paimana_obs_months'] = 1.0 # historical completed observed in reports
valid_dates['historical_schedule_revision_count'] = 0.0
valid_dates['historical_cost_revision_count'] = 0.0
valid_dates['pre_paimana_max_schedule_slippage_months'] = valid_dates['historical_delay_months'].clip(lower=0).fillna(0)

# Let's see how they project into K-Means clusters
X_hist = valid_dates[['original_cost_log', 'planned_duration_months', 'pre_paimana_obs_months', 'historical_schedule_revision_count', 'historical_cost_revision_count', 'pre_paimana_max_schedule_slippage_months']]
X_hist_scaled = scaler.transform(X_hist)
valid_dates['cluster_id'] = kmeans.predict(X_hist_scaled)

print("\nHistorical Completed Projects Cluster Distribution:")
print(valid_dates['cluster_id'].value_counts().sort_index())

# Historical delay by cluster across all historical completed projects strictly before 2025-04
hist_pre2025 = valid_dates[valid_dates['actual_completion_date'] < '2025-04']
print(f"\nHistorical Completed Projects Strictly Before 2025-04 (N = {len(hist_pre2025)}):")
for cid in range(4):
    sub = hist_pre2025[hist_pre2025['cluster_id'] == cid]
    delay_obs = sub['historical_delay_months'].dropna()
    delay_rate = (delay_obs > 0).mean() * 100 if len(delay_obs) > 0 else 0
    mean_delay = delay_obs.mean() if len(delay_obs) > 0 else 0
    median_delay = delay_obs.median() if len(delay_obs) > 0 else 0
    print(f"Cluster {cid} (N={len(sub)}, Delay Obs={len(delay_obs)}): Delay Rate = {delay_rate:.1f}%, Mean Delay = {mean_delay:.1f}m, Median Delay = {median_delay:.1f}m")

# Global baseline
global_delays = hist_pre2025['historical_delay_months'].dropna()
print(f"GLOBAL Portfolio (< 2025-04, N={len(global_delays)}): Delay Rate = {(global_delays > 0).mean()*100:.1f}%, Mean Delay = {global_delays.mean():.1f}m, Median Delay = {global_delays.median():.1f}m")
