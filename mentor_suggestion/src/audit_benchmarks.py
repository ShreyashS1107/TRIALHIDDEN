import os
import sys
import pandas as pd
import numpy as np

features_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\features\feature_dataset_v1.csv"
assignments_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\clustering\cluster_assignments.csv"
profiles_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\mentor_suggestion\data\project_clustering_profiles.csv"

f_df = pd.read_csv(features_path, low_memory=False)
assignments = pd.read_csv(assignments_path)
profiles = pd.read_csv(profiles_path)

merged_profiles = profiles.merge(assignments[['project_id', 'cluster_id', 'cluster_label', 'distance_to_centroid', 'is_outlier']], on='project_id')

print("="*80)
print("AUDITING PRE-TRANSITION BENCHMARK STATISTICS PER CLUSTER")
print("="*80)

# Pre-transition historical statistics for the 4 clusters from profiles (N=1,442)
print("Cluster Profiles Summary across 1,442 Linked Projects:")
for cid in range(4):
    sub = merged_profiles[merged_profiles['cluster_id'] == cid]
    print(f"\nCluster {cid}: {sub['cluster_label'].iloc[0]} (N={len(sub)})")
    print(f"  Mean Original Cost: Rs. {sub['original_cost_crore'].mean():.1f} Cr (Median: Rs. {sub['original_cost_crore'].median():.1f} Cr)")
    print(f"  Planned Duration: {sub['planned_duration_months'].mean():.1f} mos (Median: {sub['planned_duration_months'].median():.1f} mos)")
    print(f"  Pre-PAIMANA Obs: {sub['pre_paimana_obs_months'].mean():.2f} mos (Median: {sub['pre_paimana_obs_months'].median():.1f} mos)")
    print(f"  Pre-PAIMANA Sched Revisions: {sub['historical_schedule_revision_count'].mean():.2f} revs (Rate > 0: {(sub['historical_schedule_revision_count'] > 0).mean()*100:.1f}%)")
    print(f"  Pre-PAIMANA Cost Revisions: {sub['historical_cost_revision_count'].mean():.2f} revs (Rate > 0: {(sub['historical_cost_revision_count'] > 0).mean()*100:.1f}%)")
    print(f"  Pre-PAIMANA Max Slippage: {sub['pre_paimana_max_schedule_slippage_months'].mean():.1f} mos (Median: {sub['pre_paimana_max_schedule_slippage_months'].median():.1f} mos, Rate > 0: {(sub['pre_paimana_max_schedule_slippage_months'] > 0).mean()*100:.1f}%)")
    print(f"  Mean Distance to Centroid: {sub['distance_to_centroid'].mean():.4f}")

# Cross-reference with active PAIMANA snapshots in feature_dataset_v1 (15,769 rows)
print(f"\nFeature Dataset V1: {len(f_df)} snapshot rows across 12 prediction months.")
f_linked = f_df[f_df['project_id'].isin(assignments['project_id'])]
print(f"Linked Project Snapshots in V1: {len(f_linked)} / {len(f_df)} ({len(f_linked)/len(f_df)*100:.1f}%)")
