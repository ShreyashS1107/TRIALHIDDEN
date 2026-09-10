import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score, adjusted_rand_score

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\Shreyash\Documents\vs work\SIH26103"
DATA_DIR = os.path.join(BASE_DIR, "data")
HIST_DIR = os.path.join(BASE_DIR, "historical_priors")
MENTOR_DIR = os.path.join(BASE_DIR, "mentor_suggestion")
OUT_DATA_DIR = os.path.join(MENTOR_DIR, "data")
OUT_CLUSTERING_DIR = os.path.join(MENTOR_DIR, "clustering")
OUT_REPORTS_DIR = os.path.join(MENTOR_DIR, "reports")

os.makedirs(OUT_DATA_DIR, exist_ok=True)
os.makedirs(OUT_CLUSTERING_DIR, exist_ok=True)
os.makedirs(OUT_REPORTS_DIR, exist_ok=True)

print("="*80)
print("PHASE 1: PROJECT-SIMILARITY CLUSTERING PIPELINE (SIH26103)")
print("="*80)

# 1. Load Data
paimana_master_path = os.path.join(DATA_DIR, "paimana_master_dataset.csv")
linked_hist_path = os.path.join(HIST_DIR, "linked_project_history.csv")
sector_priors_path = os.path.join(HIST_DIR, "sector_historical_priors.csv")

p_df = pd.read_csv(paimana_master_path, low_memory=False)
l_df = pd.read_csv(linked_hist_path, low_memory=False)

print(f"Loaded PAIMANA Master Dataset ({len(p_df):,} rows, {p_df['project_id'].nunique():,} unique projects)")
print(f"Loaded Linked Project History ({len(l_df):,} rows, {l_df['project_id'].nunique():,} unique projects)")

# 2. Overlap Population Audit & Reconciliation
total_pids = set(p_df['project_id'].unique())
legacy_pids = set(p_df[p_df['legacy_ocms_code'].notna()]['project_id'].unique())
unmatched_pids = total_pids - legacy_pids

# Pre-PAIMANA observation max per project
l_max_obs = l_df.groupby('project_id')['pre_paimana_observation_months'].max().reset_index()
linked_with_obs = set(l_max_obs[l_max_obs['pre_paimana_observation_months'] > 0]['project_id'].unique())
transition_only = set(l_max_obs[l_max_obs['pre_paimana_observation_months'] == 0]['project_id'].unique())

print("\n--- Overlap Population Reconciliation ---")
print(f"Total Unique PAIMANA Projects        : {len(total_pids)}")
print(f"Projects with legacy_ocms_code       : {len(legacy_pids)}")
print(f"Comprehensively Linked (Pre-Obs > 0) : {len(linked_with_obs)} (COHORT A)")
print(f"Transition-Boundary (Pre-Obs == 0)   : {len(transition_only)}")
print(f"Unmatched PAIMANA Inceptions         : {len(unmatched_pids)}")
print(f"Reconciliation Check: {len(linked_with_obs)} + {len(transition_only)} + {len(unmatched_pids)} = {len(linked_with_obs) + len(transition_only) + len(unmatched_pids)}")
assert len(linked_with_obs) == 1442, f"Expected 1,442 linked projects, got {len(linked_with_obs)}"
assert len(transition_only) == 294, f"Expected 294 transition projects, got {len(transition_only)}"
assert len(unmatched_pids) == 1005, f"Expected 1,005 unmatched projects, got {len(unmatched_pids)}"
assert len(total_pids) == 2741, f"Expected 2,741 total projects, got {len(total_pids)}"
print("100% POPULATION RECONCILIATION VERIFIED.")

# 3. Build Clustering Cohort (N = 1,442)
# Extract static metadata as of the first observation in PAIMANA
p_first = p_df.sort_values('report_month').groupby('project_id').first().reset_index()
cohort_meta = p_first[p_first['project_id'].isin(linked_with_obs)].copy()

# Extract pre-PAIMANA trajectory features strictly as-of 2025-04 (entry boundary)
l_entry = l_df[l_df['as_of_date'] == '2025-04'].copy()
cohort_df = cohort_meta.merge(l_entry, on='project_id', how='inner', suffixes=('', '_hist'))

# Sector mapping: clean sector from state string or agency if available
def clean_state_str(st):
    if pd.isna(st):
        return 'UNKNOWN'
    s = str(st).strip().upper()
    tokens = s.split()
    clean_tokens = [t for t in tokens if not any(c.isdigit() for c in t) and t not in [',', '.']]
    cleaned = ' '.join(clean_tokens)
    return cleaned if cleaned else s

cohort_df['clean_state'] = cohort_df['state'].apply(clean_state_str)

# Map high-level sector
agency_to_sector = {
    'NHAI': 'ROAD TRANSPORT & HIGHWAYS',
    'MORTH': 'ROAD TRANSPORT & HIGHWAYS',
    'MoRTH': 'ROAD TRANSPORT & HIGHWAYS',
    'NHIDCL': 'ROAD TRANSPORT & HIGHWAYS',
    'BRO': 'ROAD TRANSPORT & HIGHWAYS',
    'RVNL': 'RAILWAYS',
    'ECR': 'RAILWAYS',
    'NR': 'RAILWAYS',
    'WR': 'RAILWAYS',
    'SCR': 'RAILWAYS',
    'SER': 'RAILWAYS',
    'NFR': 'RAILWAYS',
    'SR': 'RAILWAYS',
    'CR': 'RAILWAYS',
    'ER': 'RAILWAYS',
    'NCR': 'RAILWAYS',
    'NER': 'RAILWAYS',
    'NWR': 'RAILWAYS',
    'SECR': 'RAILWAYS',
    'SWR': 'RAILWAYS',
    'WCR': 'RAILWAYS',
    'ECOR': 'RAILWAYS',
    'MRVC': 'RAILWAYS',
    'DFCCIL': 'RAILWAYS',
    'CORE': 'RAILWAYS',
    'IOCL': 'PETROLEUM & NATURAL GAS',
    'ONGC': 'PETROLEUM & NATURAL GAS',
    'BPCL': 'PETROLEUM & NATURAL GAS',
    'HPCL': 'PETROLEUM & NATURAL GAS',
    'GAIL': 'PETROLEUM & NATURAL GAS',
    'NRL': 'PETROLEUM & NATURAL GAS',
    'OIL': 'PETROLEUM & NATURAL GAS',
    'PGCIL': 'POWER',
    'NTPC': 'POWER',
    'NHPC': 'POWER',
    'SJVN': 'POWER',
    'NEEPCO': 'POWER',
    'THDC': 'POWER',
    'SECL': 'COAL',
    'NCL': 'COAL',
    'MCL': 'COAL',
    'WCL': 'COAL',
    'BCCL': 'COAL',
    'ECL': 'COAL',
    'CCL': 'COAL',
    'AAI': 'CIVIL AVIATION'
}

def assign_sector(row):
    ag = str(row['agency']).strip().upper() if pd.notna(row['agency']) else ''
    if ag in agency_to_sector:
        return agency_to_sector[ag]
    st = str(row['state']).strip().upper() if pd.notna(row['state']) else ''
    for s_k in ['ROAD', 'HIGHWAY', 'RAIL', 'PETROLEUM', 'POWER', 'COAL', 'AVIATION', 'STEEL', 'URBAN', 'HEALTH', 'MINES']:
        if s_k in st:
            if s_k in ['ROAD', 'HIGHWAY']: return 'ROAD TRANSPORT & HIGHWAYS'
            if s_k in ['RAIL']: return 'RAILWAYS'
            if s_k in ['PETROLEUM']: return 'PETROLEUM & NATURAL GAS'
            if s_k in ['POWER']: return 'POWER'
            if s_k in ['COAL']: return 'COAL'
            if s_k in ['AVIATION']: return 'CIVIL AVIATION'
            return s_k
    return 'OTHER CENTRAL SECTOR'

cohort_df['sector'] = cohort_df.apply(assign_sector, axis=1)

# Planned duration calculation
def calc_planned_duration(row):
    if pd.isna(row['approval_start_date']) or pd.isna(row['original_completion_date']):
        return np.nan
    try:
        y1, m1 = map(int, str(row['approval_start_date'])[:7].split('-'))
        y2, m2 = map(int, str(row['original_completion_date'])[:7].split('-'))
        dur = (y2 - y1) * 12 + (m2 - m1)
        return float(dur) if dur >= 0 else np.nan
    except:
        return np.nan

cohort_df['planned_duration_months'] = cohort_df.apply(calc_planned_duration, axis=1)
cohort_df['project_size_category'] = cohort_df['original_cost_crore'].apply(lambda c: 'Mega' if c >= 1000.0 else 'Major')

# Save clustering cohort dataset
cohort_export_cols = [
    'project_id', 'legacy_ocms_code', 'project_name', 'agency', 'sector', 'clean_state',
    'approval_start_date', 'original_completion_date', 'original_cost_crore', 'project_size_category',
    'pre_paimana_observation_months', 'pre_paimana_schedule_revision_count', 'pre_paimana_cost_revision_count',
    'pre_paimana_max_schedule_slippage_months', 'pre_paimana_max_cost_escalation_pct', 'max_source_date'
]
cohort_export_path = os.path.join(OUT_DATA_DIR, "clustering_cohort.csv")
cohort_df[cohort_export_cols].to_csv(cohort_export_path, index=False)
print(f"Saved clustering cohort dataset ({len(cohort_df)} rows) to: {cohort_export_path}")

# 4. Construct Project-Level Clustering Profiles
# Selected clustering features
profile_df = pd.DataFrame()
profile_df['project_id'] = cohort_df['project_id']
profile_df['legacy_ocms_code'] = cohort_df['legacy_ocms_code']
profile_df['agency'] = cohort_df['agency']
profile_df['sector'] = cohort_df['sector']
profile_df['project_size_category'] = cohort_df['project_size_category']

# Numerical features
profile_df['original_cost_crore'] = pd.to_numeric(cohort_df['original_cost_crore'], errors='coerce')
profile_df['original_cost_log'] = np.log1p(profile_df['original_cost_crore'].clip(lower=0))
profile_df['planned_duration_months'] = cohort_df['planned_duration_months']
profile_df['pre_paimana_obs_months'] = cohort_df['pre_paimana_observation_months']
profile_df['historical_schedule_revision_count'] = cohort_df['pre_paimana_schedule_revision_count']
profile_df['historical_cost_revision_count'] = cohort_df['pre_paimana_cost_revision_count']
profile_df['pre_paimana_max_schedule_slippage_months'] = cohort_df['pre_paimana_max_schedule_slippage_months']
profile_df['pre_paimana_max_cost_escalation_pct'] = cohort_df['pre_paimana_max_cost_escalation_pct']

# Handle missing data
missing_counts = profile_df.isnull().sum()
print("\n--- Clustering Variable Missingness Audit ---")
print(missing_counts[missing_counts > 0])

# Impute median planned duration for the 5 projects missing start/completion dates
median_dur = profile_df['planned_duration_months'].median()
profile_df['planned_duration_months'] = profile_df['planned_duration_months'].fillna(median_dur)
print(f"Imputed {missing_counts['planned_duration_months']} missing planned_duration_months values with cohort median: {median_dur} months.")

profiles_export_path = os.path.join(OUT_DATA_DIR, "project_clustering_profiles.csv")
profile_df.to_csv(profiles_export_path, index=False)
print(f"Saved project clustering profiles dataset ({len(profile_df)} rows) to: {profiles_export_path}")

# 5. Numerical Feature Scaling for Clustering
clustering_feature_cols = [
    'original_cost_log',
    'planned_duration_months',
    'pre_paimana_obs_months',
    'historical_schedule_revision_count',
    'historical_cost_revision_count',
    'pre_paimana_max_schedule_slippage_months'
]

X_raw = profile_df[clustering_feature_cols].copy()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

# 6. Evaluate K-Means across K = 2 to 8
k_metrics = []
for k in range(2, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=20)
    labels = km.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels)
    ch = calinski_harabasz_score(X_scaled, labels)
    db = davies_bouldin_score(X_scaled, labels)
    counts = pd.Series(labels).value_counts().to_dict()
    min_size = min(counts.values())
    max_size = max(counts.values())
    
    k_metrics.append({
        'k': k,
        'inertia': float(round(km.inertia_, 2)),
        'silhouette': float(round(sil, 4)),
        'calinski_harabasz': float(round(ch, 2)),
        'davies_bouldin': float(round(db, 4)),
        'min_cluster_size': int(min_size),
        'max_cluster_size': int(max_size),
        'cluster_sizes': {str(c): int(cnt) for c, cnt in counts.items()}
    })

df_k_eval = pd.DataFrame(k_metrics)
print("\n--- Clustering Evaluation across K=2 to 8 ---")
print(df_k_eval[['k', 'inertia', 'silhouette', 'calinski_harabasz', 'davies_bouldin', 'min_cluster_size', 'max_cluster_size']].to_string(index=False))

# 7. Select Final K = 4 and Fit Champion Clustering Model
SELECTED_K = 4
final_kmeans = KMeans(n_clusters=SELECTED_K, random_state=42, n_init=20)
final_labels = final_kmeans.fit_predict(X_scaled)
profile_df['cluster_id'] = final_labels

# Calculate distance to assigned centroid in standardized space
centroids = final_kmeans.cluster_centers_
distances = []
for i in range(len(X_scaled)):
    cid = final_labels[i]
    c_vec = centroids[cid]
    dist = np.linalg.norm(X_scaled[i] - c_vec)
    distances.append(dist)

profile_df['distance_to_centroid'] = np.round(distances, 4)

# Define Neutral Physical Archetype Labels based on empirical centroid characteristics
# Centroid profiling
raw_profiles = profile_df.groupby('cluster_id')[clustering_feature_cols + ['original_cost_crore', 'distance_to_centroid']].agg({
    'original_cost_crore': ['count', 'mean', 'median'],
    'planned_duration_months': ['mean', 'median'],
    'pre_paimana_obs_months': ['mean', 'median'],
    'historical_schedule_revision_count': ['mean', 'median'],
    'historical_cost_revision_count': ['mean', 'median'],
    'pre_paimana_max_schedule_slippage_months': ['mean', 'median'],
    'distance_to_centroid': ['mean', 'max']
})

print("\n--- Empirical Centroid Summary Table ---")
print(raw_profiles.to_string())

# Map Cluster Labels neutrally based on observed features:
# Let's inspect which cluster ID corresponds to which archetype dynamically
cluster_summary = profile_df.groupby('cluster_id').agg(
    count=('project_id', 'count'),
    mean_cost=('original_cost_crore', 'mean'),
    median_cost=('original_cost_crore', 'median'),
    mean_duration=('planned_duration_months', 'mean'),
    mean_obs=('pre_paimana_obs_months', 'mean'),
    mean_sched_rev=('historical_schedule_revision_count', 'mean'),
    mean_cost_rev=('historical_cost_revision_count', 'mean'),
    mean_slippage=('pre_paimana_max_schedule_slippage_months', 'mean'),
    mean_dist=('distance_to_centroid', 'mean')
).reset_index()

def assign_archetype_label(row):
    # Cluster with extreme slippage (> 100m) and long duration (> 120m)
    if row['mean_slippage'] > 50.0:
        return "Severe Legacy Stagnation & Chronic Slippage"
    # Cluster with highest cost (> 2000 Cr) and high planned duration (> 80m)
    elif row['mean_cost'] > 2500.0:
        return "Mega Capital High-Value Infrastructure"
    # Cluster with highest cost revision frequency (> 1.5)
    elif row['mean_cost_rev'] > 1.5:
        return "High Administrative Cost-Revision Volatility"
    # Standard modular projects
    else:
        return "Standard Rapid-Execution / Linear Infrastructure"

cluster_summary['cluster_label'] = cluster_summary.apply(assign_archetype_label, axis=1)
label_dict = dict(zip(cluster_summary['cluster_id'], cluster_summary['cluster_label']))
profile_df['cluster_label'] = profile_df['cluster_id'].map(label_dict)

print("\n--- Assigned Neutral Archetype Labels ---")
for _, r in cluster_summary.iterrows():
    print(f"Cluster {int(r['cluster_id'])} (N={int(r['count'])}, {r['count']/len(profile_df)*100:.1f}%): {r['cluster_label']}")
    print(f"   Mean Cost: Rs. {r['mean_cost']:.1f} Cr | Planned Duration: {r['mean_duration']:.1f}m | Pre-Slippage: {r['mean_slippage']:.1f}m | Cost Revs: {r['mean_cost_rev']:.2f}")

# Outlier threshold: distance > (mean + 3*std) within cluster
outlier_flags = []
for cid in range(SELECTED_K):
    sub_dists = profile_df[profile_df['cluster_id'] == cid]['distance_to_centroid']
    thresh = sub_dists.mean() + 3.0 * sub_dists.std()
    for idx, row in profile_df[profile_df['cluster_id'] == cid].iterrows():
        outlier_flags.append((idx, int(row['distance_to_centroid'] > thresh)))

outlier_df = pd.DataFrame(outlier_flags, columns=['index', 'is_outlier']).set_index('index')
profile_df['is_outlier'] = outlier_df['is_outlier']

# Save Cluster Assignments
assignments_path = os.path.join(OUT_CLUSTERING_DIR, "cluster_assignments.csv")
profile_df[['project_id', 'legacy_ocms_code', 'agency', 'sector', 'cluster_id', 'cluster_label', 'distance_to_centroid', 'is_outlier']].to_csv(assignments_path, index=False)
print(f"\nSaved cluster assignments to: {assignments_path}")

# 8. Stability Analysis
print("\n--- Running Cluster Stability Analysis ---")
# A. Random seed stability (10 seeds)
seeds = [42, 100, 2026, 777, 999, 1234, 4321, 555, 888, 9999]
ari_seeds = []
for s in seeds:
    if s == 42:
        continue
    km_s = KMeans(n_clusters=SELECTED_K, random_state=s, n_init=20)
    labels_s = km_s.fit_predict(X_scaled)
    ari = adjusted_rand_score(final_labels, labels_s)
    ari_seeds.append(ari)

mean_ari_seeds = float(np.mean(ari_seeds))
min_ari_seeds = float(np.min(ari_seeds))
print(f"Seed Invariance ARI (across 10 seeds): Mean ARI = {mean_ari_seeds:.4f}, Min ARI = {min_ari_seeds:.4f}")

# B. Bootstrap Subsampling Stability (100 iterations with 80% subsample)
np.random.seed(42)
ari_bootstraps = []
n_samples = len(X_scaled)
sub_size = int(0.80 * n_samples)

for b in range(100):
    sub_idx = np.random.choice(n_samples, size=sub_size, replace=False)
    X_sub = X_scaled[sub_idx]
    km_sub = KMeans(n_clusters=SELECTED_K, random_state=42 + b, n_init=10)
    labels_sub = km_sub.fit_predict(X_sub)
    ari_b = adjusted_rand_score(final_labels[sub_idx], labels_sub)
    ari_bootstraps.append(ari_b)

mean_ari_boot = float(np.mean(ari_bootstraps))
std_ari_boot = float(np.std(ari_bootstraps))
ci_low_boot = float(np.percentile(ari_bootstraps, 2.5))
ci_high_boot = float(np.percentile(ari_bootstraps, 97.5))
print(f"Bootstrap Subsample ARI (100 iterations, 80% sub): Mean = {mean_ari_boot:.4f} ± {std_ari_boot:.4f} (95% CI: [{ci_low_boot:.4f}, {ci_high_boot:.4f}])")

# C. Perturbation Stability (Gaussian noise sigma = 0.05)
ari_noise = []
for b in range(50):
    noise = np.random.normal(0, 0.05, size=X_scaled.shape)
    X_perturbed = X_scaled + noise
    km_p = KMeans(n_clusters=SELECTED_K, random_state=42 + b, n_init=10)
    labels_p = km_p.fit_predict(X_perturbed)
    ari_p = adjusted_rand_score(final_labels, labels_p)
    ari_noise.append(ari_p)

mean_ari_noise = float(np.mean(ari_noise))
print(f"Noise Perturbation ARI (sigma=0.05, 50 trials): Mean = {mean_ari_noise:.4f}")

# 9. Save Models and Metadata
model_joblib_path = os.path.join(OUT_CLUSTERING_DIR, "clustering_model.joblib")
scaler_joblib_path = os.path.join(OUT_CLUSTERING_DIR, "clustering_scaler.joblib")
model_pkl_path = os.path.join(OUT_CLUSTERING_DIR, "clustering_model.pkl")
scaler_pkl_path = os.path.join(OUT_CLUSTERING_DIR, "clustering_scaler.pkl")

joblib.dump(final_kmeans, model_joblib_path)
joblib.dump(scaler, scaler_joblib_path)
joblib.dump(final_kmeans, model_pkl_path)
joblib.dump(scaler, scaler_pkl_path)

metadata = {
    'experiment_name': 'SIH26103_Phase1_Project_Similarity_Clustering',
    'status': 'PHASE_1_COMPLETE',
    'date_created': 'September 2026',
    'cohort_size_N': int(len(cohort_df)),
    'selected_k': SELECTED_K,
    'clustering_algorithm': 'KMeans(n_clusters=4, random_state=42, n_init=20)',
    'scaler': 'StandardScaler()',
    'features_selected': clustering_feature_cols,
    'evaluation_metrics_k4': {
        'silhouette_score': float(round(silhouette_score(X_scaled, final_labels), 4)),
        'calinski_harabasz_score': float(round(calinski_harabasz_score(X_scaled, final_labels), 2)),
        'davies_bouldin_score': float(round(davies_bouldin_score(X_scaled, final_labels), 4)),
        'inertia': float(round(final_kmeans.inertia_, 2))
    },
    'stability_analysis': {
        'seed_invariance_mean_ari': mean_ari_seeds,
        'bootstrap_subsample_mean_ari_80pct': mean_ari_boot,
        'bootstrap_subsample_95ci': [ci_low_boot, ci_high_boot],
        'noise_perturbation_mean_ari': mean_ari_noise
    },
    'k_evaluation_table': k_metrics,
    'cluster_archetypes': {
        int(r['cluster_id']): {
            'label': r['cluster_label'],
            'project_count': int(r['count']),
            'percentage': float(round(r['count']/len(profile_df)*100, 2)),
            'mean_original_cost_crore': float(round(r['mean_cost'], 2)),
            'median_original_cost_crore': float(round(r['median_cost'], 2)),
            'mean_planned_duration_months': float(round(r['mean_duration'], 2)),
            'mean_pre_paimana_obs_months': float(round(r['mean_obs'], 2)),
            'mean_historical_schedule_revisions': float(round(r['mean_sched_rev'], 2)),
            'mean_historical_cost_revisions': float(round(r['mean_cost_rev'], 2)),
            'mean_pre_paimana_max_slippage_months': float(round(r['mean_slippage'], 2)),
            'mean_distance_to_centroid': float(round(r['mean_dist'], 4))
        }
        for _, r in cluster_summary.iterrows()
    }
}

metadata_path = os.path.join(OUT_CLUSTERING_DIR, "clustering_metadata.json")
with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=2)
print(f"Saved clustering metadata to: {metadata_path}")
print("\nPhase 1 clustering execution finished successfully.")
