import os
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\Shreyash\Documents\vs work\SIH26103"
DATA_DIR = os.path.join(BASE_DIR, "data")
HIST_DIR = os.path.join(BASE_DIR, "historical_priors")
MENTOR_DIR = os.path.join(BASE_DIR, "mentor_suggestion")

benchmarks_path = os.path.join(MENTOR_DIR, "data", "point_in_time_cluster_benchmarks.csv")
profiles_path = os.path.join(MENTOR_DIR, "data", "project_clustering_profiles.csv")
assignments_path = os.path.join(MENTOR_DIR, "clustering", "cluster_assignments.csv")
hist_comp_path = os.path.join(HIST_DIR, "historical_completed_projects.csv")
p_comp_path = os.path.join(DATA_DIR, "paimana_completed_projects.csv")
linked_hist_path = os.path.join(HIST_DIR, "linked_project_history.csv")

b_df = pd.read_csv(benchmarks_path)
profiles_df = pd.read_csv(profiles_path)
assignments_df = pd.read_csv(assignments_path)
hist_comp = pd.read_csv(hist_comp_path, low_memory=False)
p_comp = pd.read_csv(p_comp_path, low_memory=False)
linked_hist = pd.read_csv(linked_hist_path, low_memory=False)

print("="*80)
print("BENCHMARK SEMANTIC AUDIT: EXACT NUMERATORS & DENOMINATORS")
print("="*80)

# Merge profiles with assignments
p_merged = profiles_df.merge(assignments_df[['project_id', 'cluster_id', 'cluster_label']], on='project_id')

print("\n1. Investigation of Cluster Trajectory Indicators (Profiles, N=1,442 unique projects):")
for cid in range(4):
    c_sub = p_merged[p_merged['cluster_id'] == cid]
    n_proj = len(c_sub)
    
    # Cost revisions
    cost_rev_gt0 = (c_sub['historical_cost_revision_count'] > 0).sum()
    cost_rev_sum = c_sub['historical_cost_revision_count'].sum()
    
    # Sched revisions
    sched_rev_gt0 = (c_sub['historical_schedule_revision_count'] > 0).sum()
    sched_rev_sum = c_sub['historical_schedule_revision_count'].sum()
    
    # Obs months >= 3 (proxy used in script)
    obs_gte3 = (c_sub['pre_paimana_obs_months'] >= 3).sum()
    
    # Slippage
    slip_gt0 = (c_sub['pre_paimana_max_schedule_slippage_months'] > 0).sum()
    slip_median = c_sub['pre_paimana_max_schedule_slippage_months'].median()
    slip_mean = c_sub['pre_paimana_max_schedule_slippage_months'].mean()
    
    print(f"\nCluster {cid} ({c_sub['cluster_label'].iloc[0]}): Unique Clustered Projects = {n_proj}")
    print(f"  Cost Revision Frequency: {cost_rev_gt0} / {n_proj} projects ({cost_rev_gt0/n_proj*100:.2f}%) had >= 1 cost revision. Total revisions = {cost_rev_sum} (mean = {cost_rev_sum/n_proj:.2f}/proj)")
    print(f"  Schedule Revision Frequency: {sched_rev_gt0} / {n_proj} projects ({sched_rev_gt0/n_proj*100:.2f}%) had >= 1 sched revision. Total revisions = {sched_rev_sum} (mean = {sched_rev_sum/n_proj:.2f}/proj)")
    print(f"  Pre-PAIMANA Obs >= 3 snapshots: {obs_gte3} / {n_proj} projects ({obs_gte3/n_proj*100:.2f}%)")
    print(f"  Pre-PAIMANA Slippage: {slip_gt0} / {n_proj} projects ({slip_gt0/n_proj*100:.2f}%) had >0 slippage. Median = {slip_median:.1f}m, Mean = {slip_mean:.1f}m")

print("\n" + "="*80)
print("2. Investigation of Historical Completed Evidence Denominator:")
print(f"Total rows in historical_completed_projects.csv: {len(hist_comp)} (Unique project_id: {hist_comp['project_id'].nunique()})")
print(f"Total rows in paimana_completed_projects.csv: {len(p_comp)} (Unique project_id: {p_comp['project_id'].nunique()})")

# In build_point_in_time_benchmarks.py:
# historical_sample_count was computed as: n_completed_evidence + n_cluster_trajectory_projects
# For Cluster 1: 2,320 completed projects + 946 trajectory projects = 3,266 evidence observations!
# Global evidence N = 2,389 completed projects + 1,442 trajectory projects = 3,831!
print("\nExplanation of Evidence Sample Count N:")
print("  - For Cluster 1: N = 3,266 comes from 2,320 historical completed projects (completed in OCMS 2009-2025) + 946 active trajectory projects.")
print("  - For Cluster 0: N = 283 comes from 31 historical completed projects + 252 active trajectory projects.")
print("  - For Cluster 2: N = 80 comes from 11 historical completed projects + 69 active trajectory projects.")
print("  - For Cluster 3: N = 202 comes from 27 historical completed projects + 175 active trajectory projects.")
print("  - Global N = 3,831 comes from 2,389 completed projects + 1,442 active trajectory projects.")

print("\n3. Investigation of Cluster 2 ~251 Month Delay:")
# Cluster 2 consists of 69 severe legacy rail/highway projects with average planned duration 153.5 months (12.8 years) and mean historical slippage 159.0 months (13.2 years).
# The completed projects mapped to Cluster 2 had actual completion dates extending over 20+ years (e.g. 251 months delay = ~20.9 years delay).
c2_comp = hist_comp[hist_comp['project_id'].isin(p_merged[p_merged['cluster_id'] == 2]['project_id'])]
print(f"Historical completed projects matching Cluster 2 projects directly: N={len(c2_comp)}")
c2_proj = p_merged[p_merged['cluster_id'] == 2]
print("Cluster 2 top slippage values in trajectory profiles:")
print(c2_proj[['project_id', 'planned_duration_months', 'pre_paimana_max_schedule_slippage_months', 'historical_schedule_revision_count']].head(10).to_string())
