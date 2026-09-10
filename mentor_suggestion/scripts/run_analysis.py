import os
import sys
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA

paimana_master_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\data\paimana_master_dataset.csv"
features_v1_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\features\feature_dataset_v1.csv"
target_v2_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\target_labels_v2\target_dataset_v2.csv"
linked_hist_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\linked_project_history.csv"
hist_completed_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\historical_priors\historical_completed_projects.csv"

# Load datasets
p_df = pd.read_csv(paimana_master_path, low_memory=False)
f_df = pd.read_csv(features_v1_path, low_memory=False)
t_df = pd.read_csv(target_v2_path, low_memory=False)
l_df = pd.read_csv(linked_hist_path, low_memory=False)
c_df = pd.read_csv(hist_completed_path, low_memory=False)

print("="*80)
print("1. COMPREHENSIVE OVERLAP AUDIT")
print("="*80)

# Total PAIMANA projects
all_pids = set(p_df['project_id'].unique())
print(f"Total PAIMANA projects: {len(all_pids)}")

# Legacy tagged
legacy_df = p_df[p_df['legacy_ocms_code'].notna()].drop_duplicates('project_id')
legacy_pids = set(legacy_df['project_id'].unique())
print(f"Projects with legacy OCMS code: {len(legacy_pids)}")
print(f"Unique legacy OCMS code strings: {legacy_df['legacy_ocms_code'].nunique()}")

# Unmatched PAIMANA projects
unmatched_pids = all_pids - legacy_pids
print(f"Unmatched PAIMANA projects (no legacy code): {len(unmatched_pids)}")

# Linked history observations
# Get max pre_paimana_observation_months per project across all prediction months
l_max_obs = l_df.groupby('project_id')['pre_paimana_observation_months'].max().reset_index()
linked_with_obs = set(l_max_obs[l_max_obs['pre_paimana_observation_months'] > 0]['project_id'].unique())
transition_only = set(l_max_obs[l_max_obs['pre_paimana_observation_months'] == 0]['project_id'].unique())

print(f"Comprehensively linked projects with pre-PAIMANA monthly trajectories (>0 obs): {len(linked_with_obs)}")
print(f"Transition-boundary projects (0 pre-PAIMANA obs): {len(transition_only)}")
print(f"Check sum: {len(linked_with_obs)} + {len(transition_only)} = {len(linked_with_obs) + len(transition_only)} (Matches {len(legacy_pids)})")

# Historical completed overlap
comp_codes = set(c_df['ocms_code'].dropna().unique())
comp_names = set(c_df['project_name'].dropna().str.strip().str.upper().unique())
print(f"\nHistorical Completed Projects in OCMS: {len(c_df)} rows, {c_df['project_id'].nunique()} unique completed projects")

# Start year analysis across groups
p_summary = p_df.sort_values('report_month').groupby('project_id').first().reset_index()
p_summary['start_year'] = pd.to_datetime(p_summary['approval_start_date'], errors='coerce').dt.year
p_summary['orig_doc_year'] = pd.to_datetime(p_summary['original_completion_date'], errors='coerce').dt.year

print("\n" + "="*80)
print("2. COHORT INVESTIGATION")
print("="*80)

# Merge pre_paimana_observation_months and PAIMANA months count
paimana_counts = p_df.groupby('project_id')['report_month'].nunique().reset_index(name='paimana_months_count')
p_summary = p_summary.merge(paimana_counts, on='project_id', how='left')
p_summary = p_summary.merge(l_max_obs, on='project_id', how='left')
p_summary['pre_paimana_observation_months'] = p_summary['pre_paimana_observation_months'].fillna(0)

# Define cohorts:
# Cohort A: All projects with reliable OCMS history (pre_paimana_obs > 0) + PAIMANA continuation
cohort_A = p_summary[p_summary['pre_paimana_observation_months'] > 0]

# Cohort B: Mentor suggestion: Projects started around 2025 (e.g. 2024-2025 or 2025) with OCMS history + PAIMANA continuation
cohort_B_2025 = p_summary[(p_summary['pre_paimana_observation_months'] > 0) & (p_summary['start_year'] == 2025)]
cohort_B_2024_2025 = p_summary[(p_summary['pre_paimana_observation_months'] > 0) & (p_summary['start_year'].isin([2024, 2025]))]
cohort_B_all_2025 = p_summary[p_summary['start_year'] == 2025]

# Cohort C: Projects with substantial pre-PAIMANA history (e.g. >= 3 historical snapshots)
cohort_C_3plus = p_summary[p_summary['pre_paimana_observation_months'] >= 3]
cohort_C_6plus = p_summary[p_summary['pre_paimana_observation_months'] >= 6]

# Cohort D: Comprehensively linked with adequate trajectories (pre_paimana_obs >= 2 AND paimana_months >= 6)
cohort_D = p_summary[(p_summary['pre_paimana_observation_months'] >= 2) & (p_summary['paimana_months_count'] >= 6)]

print(f"Cohort A (All Linked with OCMS History >0): N = {len(cohort_A)}")
print(f"Cohort B (Mentor 2025 Start + OCMS History): N = {len(cohort_B_2025)} (If 2024-2025: N = {len(cohort_B_2024_2025)})")
print(f"Total PAIMANA projects started in 2025: N = {len(cohort_B_all_2025)} (Notice: only {len(cohort_B_2025)} have OCMS history because projects started in 2025 were brand new when PAIMANA launched in April 2025!)")
print(f"Cohort C (Substantial History >= 3 obs): N = {len(cohort_C_3plus)}")
print(f"Cohort C (Deep History >= 6 obs): N = {len(cohort_C_6plus)}")
print(f"Cohort D (Adequate pre >= 2 & PAIMANA >= 6): N = {len(cohort_D)}")

print("\nDetailed Cohort Comparison:")
cohorts = {
    "A: All Linked (pre_obs > 0)": cohort_A,
    "B: 2025 Starts with OCMS": cohort_B_2025,
    "B2: 2024-2025 Starts with OCMS": cohort_B_2024_2025,
    "C1: Substantial (pre_obs >= 3)": cohort_C_3plus,
    "C2: Deep (pre_obs >= 6)": cohort_C_6plus,
    "D: Robust Trajectory (pre >= 2, paimana >= 6)": cohort_D,
    "All PAIMANA Projects": p_summary
}

cohort_metrics = []
for name, c_sub in cohorts.items():
    pids = set(c_sub['project_id'])
    # Coverage in feature_dataset_v1 across splits
    f_sub = f_df[f_df['project_id'].isin(pids)]
    train_f = f_sub[f_sub['prediction_month'].between('2025-04', '2025-11')]
    val_f = f_sub[f_sub['prediction_month'].between('2025-12', '2026-01')]
    oot_f = f_sub[f_sub['prediction_month'].between('2026-02', '2026-03')]
    
    # Missingness of original cost
    cost_miss = c_sub['original_cost_crore'].isna().mean() * 100
    
    cohort_metrics.append({
        'Cohort': name,
        'Projects (N)': len(c_sub),
        'Mean Pre-Obs': round(c_sub['pre_paimana_observation_months'].mean(), 2),
        'Median Pre-Obs': round(c_sub['pre_paimana_observation_months'].median(), 1),
        'Mean PAIMANA Mos': round(c_sub['paimana_months_count'].mean(), 1),
        'Portfolio %': round(len(c_sub) / len(p_summary) * 100, 1),
        'Train Snapshots': len(train_f),
        'Val Snapshots': len(val_f),
        'OOT Snapshots': len(oot_f),
        'Cost Missing %': round(cost_miss, 1)
    })

df_cohort_comp = pd.DataFrame(cohort_metrics)
print(df_cohort_comp.to_string(index=False))

print("\n" + "="*80)
print("3. CLUSTERING FEASIBILITY & TRAJECTORY REPRESENTATION")
print("="*80)

# Build a static + point-in-time trajectory feature set for Cohort A (N=1,442) as of 2025-04 (entry into PAIMANA)
l_2025_04 = l_df[l_df['as_of_date'] == '2025-04'].copy()
c_a_pids = set(cohort_A['project_id'])
c_a_meta = p_summary[p_summary['project_id'].isin(c_a_pids)].copy()

# Merge static & trajectory features
c_a_df = c_a_meta.merge(l_2025_04, on='project_id', how='left')

# Add engineered static features: planned_duration_months, original_cost_log
def calc_planned_dur(row):
    if pd.isna(row['approval_start_date']) or pd.isna(row['original_completion_date']):
        return np.nan
    try:
        y1, m1 = map(int, str(row['approval_start_date'])[:7].split('-'))
        y2, m2 = map(int, str(row['original_completion_date'])[:7].split('-'))
        return (y2 - y1) * 12 + (m2 - m1)
    except:
        return np.nan

c_a_df['planned_duration_months'] = c_a_df.apply(calc_planned_dur, axis=1)
c_a_df['original_cost_log'] = np.log1p(c_a_df['original_cost_crore'].clip(lower=0))

# Select numeric clustering candidates
clustering_cols = [
    'original_cost_log',
    'planned_duration_months',
    'pre_paimana_observation_months_y',
    'pre_paimana_schedule_revision_count',
    'pre_paimana_cost_revision_count',
    'pre_paimana_max_cost_escalation_pct',
    'pre_paimana_max_schedule_slippage_months'
]

print("\nCandidate Numeric Clustering Features summary across Cohort A (N=1,442):")
print(c_a_df[clustering_cols].describe().round(2).to_string())

# Impute median for missing in clustering test
X_raw = c_a_df[clustering_cols].copy()
X_imputed = X_raw.fillna(X_raw.median())

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_imputed)

print("\nEvaluating K-Means with k = 2 to 8:")
k_results = []
for k in range(2, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels)
    ch = calinski_harabasz_score(X_scaled, labels)
    db = davies_bouldin_score(X_scaled, labels)
    counts = pd.Series(labels).value_counts().to_dict()
    min_size = min(counts.values())
    k_results.append({
        'k': k,
        'Inertia': round(km.inertia_, 1),
        'Silhouette': round(sil, 4),
        'Calinski-Harabasz': round(ch, 1),
        'Davies-Bouldin': round(db, 4),
        'Min Cluster Size': min_size,
        'Cluster Sizes': counts
    })

df_k_results = pd.DataFrame(k_results)
print(df_k_results[['k', 'Inertia', 'Silhouette', 'Calinski-Harabasz', 'Davies-Bouldin', 'Min Cluster Size']].to_string(index=False))

# Test Agglomerative / Hierarchical
print("\nEvaluating Agglomerative Clustering with Ward linkage:")
for k in [3, 4, 5, 6]:
    agg = AgglomerativeClustering(n_clusters=k, linkage='ward')
    labels = agg.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels)
    db = davies_bouldin_score(X_scaled, labels)
    counts = pd.Series(labels).value_counts().to_dict()
    print(f"k={k}: Silhouette = {sil:.4f}, DB = {db:.4f}, Sizes = {counts}")

# Test k=4 K-Means cluster profiling
km4 = KMeans(n_clusters=4, random_state=42, n_init=10)
c_a_df['cluster_k4'] = km4.fit_predict(X_scaled)

print("\nCluster Profiles (k=4 K-Means centroids in original scale):")
cluster_profiles = c_a_df.groupby('cluster_k4')[clustering_cols].mean().round(2)
cluster_profiles['count'] = c_a_df['cluster_k4'].value_counts()
print(cluster_profiles.to_string())

# Top agencies / sectors in each cluster
print("\nTop Agencies per Cluster (k=4):")
for cl in range(4):
    top_ag = c_a_df[c_a_df['cluster_k4'] == cl]['agency'].value_counts().head(3).to_dict()
    print(f"Cluster {cl} (N={len(c_a_df[c_a_df['cluster_k4'] == cl])}): Top Agencies = {top_ag}")

print("\n" + "="*80)
print("4. HISTORICAL OUTCOMES & BENCHMARK STATISTICS PER CLUSTER")
print("="*80)

# Check PAIMANA outcomes for each cluster
# Merge target labels as of 2025-04 or across train
f_train = f_df[f_df['prediction_month'] == '2025-04'][['project_id', 'schedule_delay_3m', 'cost_overrun_state_3m', 'schedule_revision_3m', 'schedule_slippage_months_t', 'stagnant_3m_t']]
c_a_outcomes = c_a_df[['project_id', 'cluster_k4']].merge(f_train, on='project_id', how='left')

print("Cluster Outcomes in PAIMANA (as of 2025-04):")
outcome_summary = c_a_outcomes.groupby('cluster_k4').agg(
    count=('project_id', 'count'),
    delay_rate_3m=('schedule_delay_3m', 'mean'),
    cost_overrun_rate_3m=('cost_overrun_state_3m', 'mean'),
    sched_rev_rate_3m=('schedule_revision_3m', 'mean'),
    mean_slippage_months=('schedule_slippage_months_t', 'mean'),
    stagnant_rate=('stagnant_3m_t', 'mean')
).round(3)
print(outcome_summary.to_string())
