import os
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

benchmarks_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\data\point_in_time_cluster_benchmarks.csv"
features_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\features\feature_dataset_v1.csv"

b_df = pd.read_csv(benchmarks_path)
f_df = pd.read_csv(features_path, low_memory=False)

print("="*80)
print("AUDITING POINT-IN-TIME BENCHMARKS & CLUSTER DIFFERENTIATION")
print("="*80)

print(f"Total snapshot rows: {len(b_df):,}")
print(f"Prediction months: {sorted(b_df['prediction_month'].unique())}")
print(f"Unique projects: {b_df['project_id'].nunique()}")

# 1. Leakage Verification
# Verify latest_evidence_date < prediction_month for 100% of rows
leakage_mask = b_df['latest_evidence_date'] >= b_df['prediction_month']
leakage_count = leakage_mask.sum()
print(f"\nTemporal Leakage Violations (latest_evidence_date >= prediction_month): {leakage_count} / {len(b_df)}")
assert leakage_count == 0, "ERROR: Temporal leakage detected!"

# 2. Benchmark Differentiation across Clusters (as of 2025-04 and 2026-03)
print("\n--- Benchmark Differentiation across Archetypes (as of 2025-04) ---")
b_apr = b_df[b_df['prediction_month'] == '2025-04'].drop_duplicates('cluster_id')
cols_show = [
    'cluster_id', 'cluster_label', 'cluster_hist_delay_rate_smoothed_t',
    'cluster_hist_median_delay_months_t', 'cluster_hist_mean_delay_months_t',
    'cluster_hist_stagnation_rate_t', 'cluster_hist_schedule_revision_rate_t',
    'cluster_hist_cost_revision_rate_t', 'historical_sample_count', 'reliability_tier'
]
print(b_apr[cols_show].to_string(index=False))

# 3. Cluster vs Global Differentiation Table
global_delay_rate = 0.8266
global_median_delay = 28.00

diff_records = []
for _, r in b_apr.iterrows():
    diff_records.append({
        'Cluster ID': int(r['cluster_id']),
        'Archetype Label': r['cluster_label'],
        'Sample Count': int(r['historical_sample_count']),
        'Cluster Delay Rate': f"{r['cluster_hist_delay_rate_smoothed_t']*100:.1f}%",
        'Global Delay Rate': f"{global_delay_rate*100:.1f}%",
        'Rate Diff': f"{(r['cluster_hist_delay_rate_smoothed_t'] - global_delay_rate)*100:+.1f}%",
        'Cluster Median Delay': f"{r['cluster_hist_median_delay_months_t']:.1f}m",
        'Global Median Delay': f"{global_median_delay:.1f}m",
        'Median Delay Diff': f"{(r['cluster_hist_median_delay_months_t'] - global_median_delay):+.1f}m",
        'Historical Sched Rev Rate': f"{r['cluster_hist_schedule_revision_rate_t']*100:.1f}%",
        'Historical Cost Rev Rate': f"{r['cluster_hist_cost_revision_rate_t']*100:.1f}%",
        'Historical Stagnation Rate': f"{r['cluster_hist_stagnation_rate_t']*100:.1f}%"
    })

diff_df = pd.DataFrame(diff_records)
print("\n--- Cluster vs Global Differentiation Matrix ---")
print(diff_df.to_string(index=False))

# 4. Temporal Stability across Prediction Epochs (2025-04 to 2026-03)
print("\n--- Temporal Evolution of Smoothed Delay Rate across Epochs ---")
piv_rate = b_df.pivot_table(index='prediction_month', columns='cluster_id', values='cluster_hist_delay_rate_smoothed_t', aggfunc='first')
piv_rate.columns = [f"Cluster {c}" for c in piv_rate.columns]
print(piv_rate.round(4))

print("\n--- Temporal Evolution of Median Delay (Months) across Epochs ---")
piv_median = b_df.pivot_table(index='prediction_month', columns='cluster_id', values='cluster_hist_median_delay_months_t', aggfunc='first')
piv_median.columns = [f"Cluster {c}" for c in piv_median.columns]
print(piv_median.round(1))

# 5. Missingness & Coverage Summary
print("\n--- Benchmark Feature Missingness Summary ---")
print(b_df.isnull().sum())
