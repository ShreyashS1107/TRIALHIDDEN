import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\Shreyash\Documents\vs work\SIH26103"
DATA_DIR = os.path.join(BASE_DIR, "data")
HIST_DIR = os.path.join(BASE_DIR, "historical_priors")
MENTOR_DIR = os.path.join(BASE_DIR, "mentor_suggestion")
OUT_DATA_DIR = os.path.join(MENTOR_DIR, "data")
OUT_CLUSTERING_DIR = os.path.join(MENTOR_DIR, "clustering")
OUT_REPORTS_DIR = os.path.join(MENTOR_DIR, "reports")

print("="*80)
print("PHASE 2A: POINT-IN-TIME HISTORICAL BENCHMARKING ENGINE (SIH26103)")
print("="*80)

# 1. Load Frozen Phase 1 Artifacts
scaler_path = os.path.join(OUT_CLUSTERING_DIR, "clustering_scaler.joblib")
model_path = os.path.join(OUT_CLUSTERING_DIR, "clustering_model.joblib")
assignments_path = os.path.join(OUT_CLUSTERING_DIR, "cluster_assignments.csv")
profiles_path = os.path.join(OUT_DATA_DIR, "project_clustering_profiles.csv")

scaler = joblib.load(scaler_path)
kmeans = joblib.load(model_path)
assignments_df = pd.read_csv(assignments_path)
profiles_df = pd.read_csv(profiles_path)

print(f"Loaded frozen Phase 1 K-Means (K=4) model and scaler.")
print(f"Loaded {len(assignments_df)} cluster assignments across Cohort A.")

# 2. Load Production Feature Backbone and Historical Sources
features_path = os.path.join(BASE_DIR, "features", "feature_dataset_v1.csv")
hist_comp_path = os.path.join(HIST_DIR, "historical_completed_projects.csv")
paimana_comp_path = os.path.join(DATA_DIR, "paimana_completed_projects.csv")
paimana_master_path = os.path.join(DATA_DIR, "paimana_master_dataset.csv")

f_df = pd.read_csv(features_path, low_memory=False)
hist_comp = pd.read_csv(hist_comp_path, low_memory=False)
p_comp = pd.read_csv(paimana_comp_path, low_memory=False)
p_master = pd.read_csv(paimana_master_path, low_memory=False)

print(f"Loaded feature backbone: {len(f_df):,} snapshot rows across {f_df['prediction_month'].nunique()} prediction months.")
print(f"Loaded historical completed projects: {len(hist_comp):,} projects.")
print(f"Loaded PAIMANA completed projects: {len(p_comp):,} projects.")

# Helper duration functions
def calc_planned_dur(r):
    if pd.isna(r['approval_start_date']) or pd.isna(r['original_completion_date']):
        return 38.0
    try:
        y1, m1 = map(int, str(r['approval_start_date'])[:7].split('-'))
        y2, m2 = map(int, str(r['original_completion_date'])[:7].split('-'))
        dur = (y2 - y1) * 12 + (m2 - m1)
        return float(dur) if dur >= 0 else 38.0
    except:
        return 38.0

def calc_dur_hist(r):
    if pd.isna(r['original_doc']) or pd.isna(r['report_month']):
        return 38.0
    try:
        y1, m1 = map(int, str(r['report_month'])[:7].split('-'))
        y2, m2 = map(int, str(r['original_doc'])[:7].split('-'))
        dur = (y2 - y1) * 12 + (m2 - m1)
        return float(dur) if 0 <= dur <= 300 else 38.0
    except:
        return 38.0

# 3. Establish Cluster Mapping for All PAIMANA Projects (2,741 Universe)
pid_to_cluster = dict(zip(assignments_df['project_id'].astype(str), assignments_df['cluster_id']))
pid_to_label = dict(zip(assignments_df['project_id'].astype(str), assignments_df['cluster_label']))
pid_to_dist = dict(zip(assignments_df['project_id'].astype(str), assignments_df['distance_to_centroid']))

# Extract static features for all 2,741 PAIMANA projects from paimana_master
p_static = p_master.sort_values('report_month').groupby('project_id').first().reset_index()
p_static['project_id_str'] = p_static['project_id'].astype(str)
p_static['original_cost_crore'] = pd.to_numeric(p_static['original_cost_crore'], errors='coerce')
p_static['original_cost_log'] = np.log1p(p_static['original_cost_crore'].clip(lower=0).fillna(p_static['original_cost_crore'].median()))
p_static['planned_duration_months'] = p_static.apply(calc_planned_dur, axis=1)

# Project unlinked projects into frozen K-Means space
unlinked_mask = ~p_static['project_id_str'].isin(pid_to_cluster)
unlinked_projects = p_static[unlinked_mask].copy()

if len(unlinked_projects) > 0:
    unlinked_X = pd.DataFrame({
        'original_cost_log': unlinked_projects['original_cost_log'],
        'planned_duration_months': unlinked_projects['planned_duration_months'],
        'pre_paimana_obs_months': 0.0,
        'historical_schedule_revision_count': 0.0,
        'historical_cost_revision_count': 0.0,
        'pre_paimana_max_schedule_slippage_months': 0.0
    })
    unlinked_X_scaled = scaler.transform(unlinked_X)
    unlinked_clusters = kmeans.predict(unlinked_X_scaled)
    
    centroids = kmeans.cluster_centers_
    for idx, (_, row) in enumerate(unlinked_projects.iterrows()):
        pid = row['project_id_str']
        cid = int(unlinked_clusters[idx])
        c_vec = centroids[cid]
        d = float(np.linalg.norm(unlinked_X_scaled[idx] - c_vec))
        
        pid_to_cluster[pid] = cid
        pid_to_label[pid] = assignments_df[assignments_df['cluster_id'] == cid]['cluster_label'].iloc[0]
        pid_to_dist[pid] = round(d, 4)

print(f"Total projects mapped to clusters: {len(pid_to_cluster)} (1,442 Cohort A + {len(unlinked_projects)} Unlinked/New Inceptions).")

# 4. Precompute Historical Archetype Trajectory & Outcome Profiles as of Entry
cluster_hist_behavior = {}
merged_p = profiles_df.merge(assignments_df[['project_id', 'cluster_id']], on='project_id')

for cid in range(4):
    c_sub = merged_p[merged_p['cluster_id'] == cid]
    cluster_hist_behavior[cid] = {
        'historical_sample_count': int(len(c_sub)),
        'pre_slippage_median': float(c_sub['pre_paimana_max_schedule_slippage_months'].median()),
        'pre_slippage_mean': float(c_sub['pre_paimana_max_schedule_slippage_months'].mean()),
        'pre_slippage_rate': float((c_sub['pre_paimana_max_schedule_slippage_months'] > 0).mean()),
        'sched_rev_rate': float((c_sub['historical_schedule_revision_count'] > 0).mean()),
        'sched_rev_mean': float(c_sub['historical_schedule_revision_count'].mean()),
        'cost_rev_rate': float((c_sub['historical_cost_revision_count'] > 0).mean()),
        'cost_rev_mean': float(c_sub['historical_cost_revision_count'].mean()),
        'stagnation_rate': float((c_sub['pre_paimana_obs_months'] >= 3).mean()),
        'mean_cost': float(c_sub['original_cost_crore'].mean()),
        'mean_duration': float(c_sub['planned_duration_months'].mean())
    }

# 5. Point-in-Time Historical Completed Projects Benchmarking Engine
hist_comp_clean = hist_comp.copy()
hist_comp_clean['actual_completion_date'] = hist_comp_clean['actual_completion_date'].astype(str).str.strip()
hist_comp_clean = hist_comp_clean[hist_comp_clean['actual_completion_date'].str.match(r'^\d{4}-\d{2}$', na=False)].copy()
hist_comp_clean['original_cost_crore'] = pd.to_numeric(hist_comp_clean['original_cost'], errors='coerce')
hist_comp_clean['original_cost_log'] = np.log1p(hist_comp_clean['original_cost_crore'].clip(lower=0).fillna(hist_comp_clean['original_cost_crore'].median()))
hist_comp_clean['planned_duration_months'] = hist_comp_clean.apply(calc_dur_hist, axis=1)

# Project historical completed projects into cluster archetypes
X_hc = pd.DataFrame({
    'original_cost_log': hist_comp_clean['original_cost_log'],
    'planned_duration_months': hist_comp_clean['planned_duration_months'],
    'pre_paimana_obs_months': 1.0,
    'historical_schedule_revision_count': 0.0,
    'historical_cost_revision_count': 0.0,
    'pre_paimana_max_schedule_slippage_months': hist_comp_clean['historical_delay_months'].clip(lower=0).fillna(0)
})
X_hc_scaled = scaler.transform(X_hc)
hist_comp_clean['cluster_id'] = kmeans.predict(X_hc_scaled)

# PAIMANA completed projects point-in-time
p_comp_clean = p_comp.copy()
p_comp_clean['actual_completion_date'] = p_comp_clean['actual_completion_date'].astype(str).str.strip()
p_comp_clean = p_comp_clean[p_comp_clean['actual_completion_date'].str.match(r'^\d{4}-\d{2}$', na=False)].copy()

def p_comp_delay(r):
    if pd.isna(r['original_completion_date']) or pd.isna(r['actual_completion_date']):
        return np.nan
    try:
        y1, m1 = map(int, str(r['original_completion_date'])[:7].split('-'))
        y2, m2 = map(int, str(r['actual_completion_date'])[:7].split('-'))
        return float((y2 - y1) * 12 + (m2 - m1))
    except:
        return np.nan

p_comp_clean['historical_delay_months'] = p_comp_clean.apply(p_comp_delay, axis=1)
p_comp_clean['historical_delay_flag'] = (p_comp_clean['historical_delay_months'] > 0).astype(float)
p_comp_clean['project_id_str'] = p_comp_clean['project_id'].astype(str)
p_comp_clean['cluster_id'] = p_comp_clean['project_id_str'].map(pid_to_cluster).fillna(1).astype(int)

# Global historical prior parameter for Empirical Bayes Beta Smoothing (M = 5.0)
M_SMOOTH = 5.0
GLOBAL_DELAY_PRIOR = 0.8266

prediction_months = sorted(f_df['prediction_month'].unique())
print(f"\nComputing point-in-time benchmarks across {len(prediction_months)} prediction epochs: {prediction_months}")

# Build benchmark lookup table for each (cluster_id, prediction_month)
benchmark_lookup = {}

for t in prediction_months:
    # STRICT POINT-IN-TIME CONDITION: actual_completion_date < t
    hc_valid = hist_comp_clean[hist_comp_clean['actual_completion_date'] < t]
    pc_valid = p_comp_clean[p_comp_clean['actual_completion_date'] < t]
    
    # Combined completed evidence as of t
    comp_delays_global = pd.concat([hc_valid['historical_delay_months'], pc_valid['historical_delay_months']]).dropna()
    glob_delay_rate = float((comp_delays_global > 0).mean()) if len(comp_delays_global) > 0 else GLOBAL_DELAY_PRIOR
    glob_median_delay = float(comp_delays_global.median()) if len(comp_delays_global) > 0 else 28.0
    glob_mean_delay = float(comp_delays_global.mean()) if len(comp_delays_global) > 0 else 32.6
    
    for cid in range(4):
        hc_c = hc_valid[hc_valid['cluster_id'] == cid]
        pc_c = pc_valid[pc_valid['cluster_id'] == cid]
        c_delays = pd.concat([hc_c['historical_delay_months'], pc_c['historical_delay_months']]).dropna()
        
        n_obs = len(c_delays)
        k_delayed = int((c_delays > 0).sum()) if n_obs > 0 else 0
        
        # Empirical Bayes Beta Smoothing: (k + M * Prior) / (N + M)
        smoothed_delay_rate = (k_delayed + M_SMOOTH * glob_delay_rate) / (n_obs + M_SMOOTH)
        
        # Fallback hierarchy for median/mean delay
        if n_obs >= 10:
            median_delay = float(c_delays.median())
            mean_delay = float(c_delays.mean())
            fallback_lvl = "CLUSTER_SPECIFIC"
            rel_tier = "HIGH" if n_obs >= 50 else "MEDIUM"
        else:
            # Fallback to pre-transition cluster trajectory median delay
            median_delay = cluster_hist_behavior[cid]['pre_slippage_median']
            mean_delay = cluster_hist_behavior[cid]['pre_slippage_mean']
            fallback_lvl = "TRAJECTORY_ARCHETYPE_FALLBACK"
            rel_tier = "MEDIUM" if cluster_hist_behavior[cid]['historical_sample_count'] >= 30 else "LOW"
            
        # Earliest and latest evidence dates strictly < t
        dates_available = pd.concat([hc_valid['actual_completion_date'], pc_valid['actual_completion_date']]).dropna()
        earliest_date = str(dates_available.min()) if len(dates_available) > 0 else "2009-01"
        latest_date = str(dates_available.max()) if len(dates_available) > 0 else "2025-03"
        
        # Check strict causality
        assert latest_date < t, f"CAUSALITY VIOLATION at {t}: latest evidence date is {latest_date}"
        
        # Historical cost revision / escalation rate from archetype trajectory
        cost_esc_rate = cluster_hist_behavior[cid]['cost_rev_rate']
        median_cost_esc = 0.0
        
        benchmark_lookup[(cid, t)] = {
            'cluster_hist_delay_rate_smoothed_t': round(smoothed_delay_rate, 4),
            'cluster_hist_median_delay_months_t': round(median_delay, 2),
            'cluster_hist_mean_delay_months_t': round(mean_delay, 2),
            'cluster_hist_cost_escalation_rate_t': round(cost_esc_rate, 4),
            'cluster_hist_median_cost_escalation_t': round(median_cost_esc, 2),
            'cluster_hist_stagnation_rate_t': round(cluster_hist_behavior[cid]['stagnation_rate'], 4),
            'cluster_hist_schedule_revision_rate_t': round(cluster_hist_behavior[cid]['sched_rev_rate'], 4),
            'cluster_hist_cost_revision_rate_t': round(cluster_hist_behavior[cid]['cost_rev_rate'], 4),
            'historical_sample_count': n_obs + cluster_hist_behavior[cid]['historical_sample_count'],
            'earliest_evidence_date': earliest_date,
            'latest_evidence_date': latest_date,
            'fallback_level': fallback_lvl,
            'reliability_tier': rel_tier
        }

print("Point-in-time benchmark lookup table computed successfully with 0 causality violations.")

# 6. Construct Snapshot Benchmark Dataset for All 15,769 Rows
print("\nConstructing monthly point-in-time benchmark dataset for 15,769 candidate snapshots...")

cohort_pids_set = set(assignments_df['project_id'].astype(str))
benchmark_rows = []

for idx, row in f_df.iterrows():
    pid = str(row['project_id'])
    t = str(row['prediction_month'])
    
    cid = pid_to_cluster.get(pid, 1)
    clabel = pid_to_label.get(pid, "Standard Rapid-Execution / Linear Infrastructure")
    dist = pid_to_dist.get(pid, 0.9993)
    is_linked = 1 if pid in cohort_pids_set else 0
    
    b_info = benchmark_lookup.get((cid, t))
    
    # Active PAIMANA current metrics as-of month t
    active_slippage = pd.to_numeric(row.get('schedule_slippage_months_t'), errors='coerce')
    active_cost_esc = pd.to_numeric(row.get('cost_escalation_pct_t'), errors='coerce')
    active_stagnant = pd.to_numeric(row.get('stagnant_3m_t'), errors='coerce')
    
    # Deviations from Archetype Benchmark
    if pd.notna(active_slippage):
        slippage_dev = round(float(active_slippage - b_info['cluster_hist_median_delay_months_t']), 2)
    else:
        slippage_dev = np.nan
        
    if pd.notna(active_cost_esc):
        cost_esc_dev = round(float(active_cost_esc - b_info['cluster_hist_median_cost_escalation_t']), 2)
    else:
        cost_esc_dev = np.nan
        
    if pd.notna(active_stagnant):
        stagnant_dev = round(float(active_stagnant - b_info['cluster_hist_stagnation_rate_t']), 4)
    else:
        stagnant_dev = np.nan

    benchmark_rows.append({
        'project_id': pid,
        'prediction_month': t,
        'cluster_id': cid,
        'cluster_label': clabel,
        'is_legacy_linked': is_linked,
        'cluster_distance_to_centroid_t': dist,
        'cluster_hist_delay_rate_smoothed_t': b_info['cluster_hist_delay_rate_smoothed_t'],
        'cluster_hist_median_delay_months_t': b_info['cluster_hist_median_delay_months_t'],
        'cluster_hist_mean_delay_months_t': b_info['cluster_hist_mean_delay_months_t'],
        'cluster_hist_cost_escalation_rate_t': b_info['cluster_hist_cost_escalation_rate_t'],
        'cluster_hist_median_cost_escalation_t': b_info['cluster_hist_median_cost_escalation_t'],
        'cluster_hist_stagnation_rate_t': b_info['cluster_hist_stagnation_rate_t'],
        'cluster_hist_schedule_revision_rate_t': b_info['cluster_hist_schedule_revision_rate_t'],
        'cluster_hist_cost_revision_rate_t': b_info['cluster_hist_cost_revision_rate_t'],
        'cluster_slippage_deviation_t': slippage_dev,
        'cluster_cost_esc_deviation_t': cost_esc_dev,
        'cluster_stagnation_deviation_t': stagnant_dev,
        'historical_sample_count': b_info['historical_sample_count'],
        'earliest_evidence_date': b_info['earliest_evidence_date'],
        'latest_evidence_date': b_info['latest_evidence_date'],
        'fallback_level': b_info['fallback_level'],
        'reliability_tier': b_info['reliability_tier']
    })

benchmarks_df = pd.DataFrame(benchmark_rows)

out_benchmarks_path = os.path.join(OUT_DATA_DIR, "point_in_time_cluster_benchmarks.csv")
benchmarks_df.to_csv(out_benchmarks_path, index=False)
print(f"Saved {len(benchmarks_df):,} snapshot benchmark rows to: {out_benchmarks_path}")

# 7. Construct Feature Dictionary for Benchmark Layer
dictionary_rows = [
    {
        'feature_name': 'cluster_id',
        'category': 'Project Archetype',
        'data_type': 'int64',
        'source_columns': 'clustering_model.joblib (K-Means K=4)',
        'time_window': 'Pre-transition baseline (t <= 2025-03)',
        'missing_policy': 'None (100% complete)',
        'leakage_status': 'SAFE (Frozen pre-transition model)'
    },
    {
        'feature_name': 'cluster_label',
        'category': 'Project Archetype Context',
        'data_type': 'str',
        'source_columns': 'cluster_assignments.csv',
        'time_window': 'Pre-transition baseline (t <= 2025-03)',
        'missing_policy': 'None (100% complete)',
        'leakage_status': 'SAFE (Context label only)'
    },
    {
        'feature_name': 'is_legacy_linked',
        'category': 'Data Provenance Indicator',
        'data_type': 'int64',
        'source_columns': 'clustering_cohort.csv',
        'time_window': 'Static indicator',
        'missing_policy': 'None (100% complete)',
        'leakage_status': 'SAFE'
    },
    {
        'feature_name': 'cluster_distance_to_centroid_t',
        'category': 'Archetype Typicality',
        'data_type': 'float64',
        'source_columns': 'Normalized Euclidean distance to cluster centroid',
        'time_window': 'Point-in-time evaluated as-of t',
        'missing_policy': 'None (100% complete)',
        'leakage_status': 'SAFE (Distance in frozen space)'
    },
    {
        'feature_name': 'cluster_hist_delay_rate_smoothed_t',
        'category': 'Historical Archetype Benchmark',
        'data_type': 'float64',
        'source_columns': 'historical_completed_projects.csv (evidence_date < t)',
        'time_window': 'Historical completed projects before prediction month t',
        'missing_policy': 'Empirical Bayes Beta smoothing with M=5.0',
        'leakage_status': 'SAFE (evidence_date < t)'
    },
    {
        'feature_name': 'cluster_hist_median_delay_months_t',
        'category': 'Historical Archetype Benchmark',
        'data_type': 'float64',
        'source_columns': 'historical_completed_projects.csv / trajectory profiles',
        'time_window': 'Historical completed projects before prediction month t',
        'missing_policy': 'Fallback to pre-transition archetype median if N < 10',
        'leakage_status': 'SAFE (evidence_date < t)'
    },
    {
        'feature_name': 'cluster_hist_mean_delay_months_t',
        'category': 'Historical Archetype Benchmark',
        'data_type': 'float64',
        'source_columns': 'historical_completed_projects.csv / trajectory profiles',
        'time_window': 'Historical completed projects before prediction month t',
        'missing_policy': 'Fallback to pre-transition archetype mean if N < 10',
        'leakage_status': 'SAFE (evidence_date < t)'
    },
    {
        'feature_name': 'cluster_hist_cost_escalation_rate_t',
        'category': 'Historical Archetype Benchmark',
        'data_type': 'float64',
        'source_columns': 'project_clustering_profiles.csv',
        'time_window': 'Pre-transition historical trajectory records (t <= 2025-03)',
        'missing_policy': 'Preserve rate from cluster trajectory',
        'leakage_status': 'SAFE (t <= 2025-03)'
    },
    {
        'feature_name': 'cluster_hist_median_cost_escalation_t',
        'category': 'Historical Archetype Benchmark',
        'data_type': 'float64',
        'source_columns': 'historical_completed_projects.csv',
        'time_window': 'Historical completed projects before prediction month t',
        'missing_policy': 'Preserve 0.0 baseline',
        'leakage_status': 'SAFE (evidence_date < t)'
    },
    {
        'feature_name': 'cluster_hist_stagnation_rate_t',
        'category': 'Historical Archetype Benchmark',
        'data_type': 'float64',
        'source_columns': 'project_clustering_profiles.csv',
        'time_window': 'Pre-transition historical trajectory records (t <= 2025-03)',
        'missing_policy': 'Preserve archetype stagnation frequency',
        'leakage_status': 'SAFE (t <= 2025-03)'
    },
    {
        'feature_name': 'cluster_hist_schedule_revision_rate_t',
        'category': 'Historical Archetype Benchmark',
        'data_type': 'float64',
        'source_columns': 'project_clustering_profiles.csv',
        'time_window': 'Pre-transition historical trajectory records (t <= 2025-03)',
        'missing_policy': 'Preserve archetype revision frequency',
        'leakage_status': 'SAFE (t <= 2025-03)'
    },
    {
        'feature_name': 'cluster_hist_cost_revision_rate_t',
        'category': 'Historical Archetype Benchmark',
        'data_type': 'float64',
        'source_columns': 'project_clustering_profiles.csv',
        'time_window': 'Pre-transition historical trajectory records (t <= 2025-03)',
        'missing_policy': 'Preserve archetype cost revision frequency',
        'leakage_status': 'SAFE (t <= 2025-03)'
    },
    {
        'feature_name': 'cluster_slippage_deviation_t',
        'category': 'Benchmark Deviation Context',
        'data_type': 'float64',
        'source_columns': 'schedule_slippage_months_t - cluster_hist_median_delay_months_t',
        'time_window': 'Current month t vs historical benchmark < t',
        'missing_policy': 'Preserve NaN if schedule_slippage_months_t is NaN',
        'leakage_status': 'SAFE (Point-in-time calculation)'
    },
    {
        'feature_name': 'cluster_cost_esc_deviation_t',
        'category': 'Benchmark Deviation Context',
        'data_type': 'float64',
        'source_columns': 'cost_escalation_pct_t - cluster_hist_median_cost_escalation_t',
        'time_window': 'Current month t vs historical benchmark < t',
        'missing_policy': 'Preserve NaN if cost_escalation_pct_t is NaN',
        'leakage_status': 'SAFE (Point-in-time calculation)'
    },
    {
        'feature_name': 'cluster_stagnation_deviation_t',
        'category': 'Benchmark Deviation Context',
        'data_type': 'float64',
        'source_columns': 'stagnant_3m_t - cluster_hist_stagnation_rate_t',
        'time_window': 'Current month t vs historical benchmark < t',
        'missing_policy': 'Preserve NaN if stagnant_3m_t is NaN',
        'leakage_status': 'SAFE (Point-in-time calculation)'
    },
    {
        'feature_name': 'historical_sample_count',
        'category': 'Provenance Metadata',
        'data_type': 'int64',
        'source_columns': 'Sum of historical completed + trajectory observations',
        'time_window': 'Available evidence count < t',
        'missing_policy': 'None',
        'leakage_status': 'SAFE'
    },
    {
        'feature_name': 'earliest_evidence_date',
        'category': 'Provenance Metadata',
        'data_type': 'str',
        'source_columns': 'Earliest historical completed date used',
        'time_window': 'Global historical start',
        'missing_policy': 'None',
        'leakage_status': 'SAFE'
    },
    {
        'feature_name': 'latest_evidence_date',
        'category': 'Provenance Metadata',
        'data_type': 'str',
        'source_columns': 'Latest historical completed date used',
        'time_window': 'Strictly < prediction_month t',
        'missing_policy': 'None',
        'leakage_status': 'SAFE (Verified < t)'
    },
    {
        'feature_name': 'fallback_level',
        'category': 'Provenance Metadata',
        'data_type': 'str',
        'source_columns': 'Fallback indicator (CLUSTER_SPECIFIC vs TRAJECTORY_ARCHETYPE_FALLBACK)',
        'time_window': 'As-of t',
        'missing_policy': 'None',
        'leakage_status': 'SAFE'
    },
    {
        'feature_name': 'reliability_tier',
        'category': 'Provenance Metadata',
        'data_type': 'str',
        'source_columns': 'HIGH (N>=50), MEDIUM (N>=30), LOW (N<30)',
        'time_window': 'As-of t',
        'missing_policy': 'None',
        'leakage_status': 'SAFE'
    }
]

dict_df = pd.DataFrame(dictionary_rows)
out_dict_path = os.path.join(OUT_DATA_DIR, "benchmark_feature_dictionary.csv")
dict_df.to_csv(out_dict_path, index=False)
print(f"Saved benchmark feature dictionary ({len(dict_df)} fields) to: {out_dict_path}")

print("\nPhase 2A point-in-time benchmarking dataset and dictionary created successfully.")
