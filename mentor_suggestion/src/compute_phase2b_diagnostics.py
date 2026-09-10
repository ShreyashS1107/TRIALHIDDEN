import os
import sys
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, log_loss

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\Shreyash\Documents\vs work\SIH26103"
DATA_DIR = os.path.join(BASE_DIR, "data")
TARGET_DIR = os.path.join(BASE_DIR, "target_labels_v2")
FEATURES_DIR = os.path.join(BASE_DIR, "features")
MENTOR_DIR = os.path.join(BASE_DIR, "mentor_suggestion")
OUT_DATA_DIR = os.path.join(MENTOR_DIR, "data")
OUT_REPORTS_DIR = os.path.join(MENTOR_DIR, "reports")

# Load datasets
f_df = pd.read_csv(os.path.join(FEATURES_DIR, "feature_dataset_v1.csv"), low_memory=False)
dict_df = pd.read_csv(os.path.join(FEATURES_DIR, "feature_dictionary_v1.csv"))
benchmarks_df = pd.read_csv(os.path.join(OUT_DATA_DIR, "point_in_time_cluster_benchmarks.csv"), low_memory=False)

f_df['project_id_str'] = f_df['project_id'].astype(str)
f_df['prediction_month_str'] = f_df['prediction_month'].astype(str)

benchmarks_df['project_id_str'] = benchmarks_df['project_id'].astype(str)
benchmarks_df['prediction_month_str'] = benchmarks_df['prediction_month'].astype(str)

# Join
merged = f_df.merge(
    benchmarks_df[[
        'project_id_str', 'prediction_month_str', 'cluster_id', 'cluster_label', 'is_legacy_linked',
        'cluster_distance_to_centroid_t', 'cluster_hist_delay_rate_smoothed_t',
        'cluster_hist_median_delay_months_t', 'cluster_hist_mean_delay_months_t',
        'cluster_hist_cost_escalation_rate_t', 'cluster_hist_median_cost_escalation_t',
        'cluster_hist_stagnation_rate_t', 'cluster_hist_schedule_revision_rate_t',
        'cluster_hist_cost_revision_rate_t', 'cluster_slippage_deviation_t',
        'cluster_cost_esc_deviation_t', 'cluster_stagnation_deviation_t'
    ]],
    on=['project_id_str', 'prediction_month_str'],
    how='inner'
)

paimana_cat_cols = ['project_size_category', 'current_schedule_status_as_of_t', 'reporting_structure_version_t', 'table_source_t']
paimana_num_cols = dict_df[dict_df['data_type'].isin(['float64', 'int64'])]['feature_name'].tolist()

merged['pred_dt'] = pd.to_datetime(merged['prediction_month_str'] + '-01')
df_train = merged[merged['pred_dt'] <= '2025-11-01'].copy()
df_val = merged[(merged['pred_dt'] >= '2025-12-01') & (merged['pred_dt'] <= '2026-01-01')].copy()
df_oot = merged[merged['pred_dt'] >= '2026-02-01'].copy()

# 1. Logistic Regression Coefficients for schedule_revision_3m
target_col = 'schedule_revision_3m'
valid_train = df_train[df_train[target_col].notna()]
valid_val = df_val[df_val[target_col].notna()]
valid_oot = df_oot[df_oot[target_col].notna()]

valid_benchmark_num = [
    'cluster_hist_delay_rate_smoothed_t',
    'cluster_hist_median_delay_months_t',
    'cluster_hist_cost_revision_rate_t',
    'cluster_distance_to_centroid_t',
    'cluster_slippage_deviation_t',
    'is_legacy_linked'
]

num_cols_b = paimana_num_cols + valid_benchmark_num

preprocessor_b = ColumnTransformer([
    ('num', Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ]), num_cols_b),
    ('cat', Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='UNKNOWN')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ]), paimana_cat_cols)
])

clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
pipe_b = Pipeline([('prep', preprocessor_b), ('clf', clf)])
pipe_b.fit(valid_train, valid_train[target_col].astype(int))

prep_step = pipe_b.named_steps['prep']
ohe_features = prep_step.named_transformers_['cat'].named_steps['encoder'].get_feature_names_out(paimana_cat_cols)
all_feat_names = list(num_cols_b) + list(ohe_features)
coefs = pipe_b.named_steps['clf'].coef_[0]

coef_df = pd.DataFrame({
    'feature': all_feat_names,
    'coefficient': coefs,
    'abs_coefficient': np.abs(coefs)
}).sort_values('abs_coefficient', ascending=False)

coef_df.to_csv(os.path.join(OUT_REPORTS_DIR, "feature_coefficients_schedule_revision_3m.csv"), index=False)
print("Top 15 Coefficients for schedule_revision_3m in Model B:")
print(coef_df.head(15).to_string(index=False))

# 2. Coverage Analysis by Feature, Split, and Cluster
coverage_records = []
all_candidate_benchmarks = [
    'cluster_hist_delay_rate_smoothed_t',
    'cluster_hist_median_delay_months_t',
    'cluster_hist_mean_delay_months_t',
    'cluster_hist_cost_escalation_rate_t',
    'cluster_hist_median_cost_escalation_t',
    'cluster_hist_stagnation_rate_t',
    'cluster_hist_schedule_revision_rate_t',
    'cluster_hist_cost_revision_rate_t',
    'cluster_distance_to_centroid_t',
    'cluster_slippage_deviation_t',
    'is_legacy_linked',
    'cluster_id'
]

for feat in all_candidate_benchmarks:
    total_cnt = len(merged)
    avail_cnt = merged[feat].notna().sum()
    miss_cnt = total_cnt - avail_cnt
    pct = avail_cnt / total_cnt * 100
    
    train_pct = df_train[feat].notna().sum() / len(df_train) * 100
    val_pct = df_val[feat].notna().sum() / len(df_val) * 100
    oot_pct = df_oot[feat].notna().sum() / len(df_oot) * 100
    
    c0_pct = merged[merged['cluster_id'] == 0][feat].notna().sum() / (merged['cluster_id'] == 0).sum() * 100 if (merged['cluster_id'] == 0).sum() > 0 else 0
    c1_pct = merged[merged['cluster_id'] == 1][feat].notna().sum() / (merged['cluster_id'] == 1).sum() * 100 if (merged['cluster_id'] == 1).sum() > 0 else 0
    c2_pct = merged[merged['cluster_id'] == 2][feat].notna().sum() / (merged['cluster_id'] == 2).sum() * 100 if (merged['cluster_id'] == 2).sum() > 0 else 0
    c3_pct = merged[merged['cluster_id'] == 3][feat].notna().sum() / (merged['cluster_id'] == 3).sum() * 100 if (merged['cluster_id'] == 3).sum() > 0 else 0
    
    coverage_records.append({
        'feature': feat,
        'total_rows': total_cnt,
        'available_rows': avail_cnt,
        'missing_rows': miss_cnt,
        'coverage_pct': round(pct, 2),
        'train_cov_pct': round(train_pct, 2),
        'val_cov_pct': round(val_pct, 2),
        'oot_cov_pct': round(oot_pct, 2),
        'c0_cov_pct': round(c0_pct, 2),
        'c1_cov_pct': round(c1_pct, 2),
        'c2_cov_pct': round(c2_pct, 2),
        'c3_cov_pct': round(c3_pct, 2),
    })

cov_df = pd.DataFrame(coverage_records)
cov_df.to_csv(os.path.join(OUT_REPORTS_DIR, "benchmark_coverage_analysis.csv"), index=False)
print("\nBenchmark Coverage Analysis:")
print(cov_df[['feature', 'coverage_pct', 'train_cov_pct', 'val_cov_pct', 'oot_cov_pct']].to_string(index=False))

# 3. Bootstrap Confidence Intervals for OOT Delta (Model B - Model A)
np.random.seed(42)
N_BOOT = 1000

targets_info = [
    ('schedule_delay_3m', 'RandomForest_Calibrated'),
    ('cost_overrun_state_3m', 'BalancedRandomForest'),
    ('schedule_revision_3m', 'LogisticRegression_L2')
]

print("\n" + "="*80)
print("1,000-ITERATION BOOTSTRAP 95% CONFIDENCE INTERVALS (OOT DELTA: MODEL B - MODEL A)")
print("="*80)

for tgt, family in targets_info:
    v_tr = df_train[df_train[tgt].notna()]
    v_v = df_val[df_val[tgt].notna()]
    v_ot = df_oot[df_oot[tgt].notna()]
    
    y_tr = v_tr[tgt].astype(int).values
    y_v = v_v[tgt].astype(int).values
    y_ot = v_ot[tgt].astype(int).values
    
    # Model A pipeline
    prep_a = ColumnTransformer([
        ('num', Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())]), paimana_num_cols),
        ('cat', Pipeline([('imputer', SimpleImputer(strategy='constant', fill_value='UNKNOWN')), ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), paimana_cat_cols)
    ])
    
    prep_b = ColumnTransformer([
        ('num', Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())]), num_cols_b),
        ('cat', Pipeline([('imputer', SimpleImputer(strategy='constant', fill_value='UNKNOWN')), ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), paimana_cat_cols)
    ])
    
    if family == 'RandomForest_Calibrated':
        pipe_a = Pipeline([('prep', prep_a), ('clf', RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=5, max_features='sqrt', random_state=42, n_jobs=-1))])
        pipe_a.fit(v_tr, y_tr)
        cal_a = CalibratedClassifierCV(estimator=FrozenEstimator(pipe_a), method='sigmoid')
        cal_a.fit(v_v, y_v)
        p_a = cal_a.predict_proba(v_ot)[:, 1]
        
        pipe_b = Pipeline([('prep', prep_b), ('clf', RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=5, max_features='sqrt', random_state=42, n_jobs=-1))])
        pipe_b.fit(v_tr, y_tr)
        cal_b = CalibratedClassifierCV(estimator=FrozenEstimator(pipe_b), method='sigmoid')
        cal_b.fit(v_v, y_v)
        p_b = cal_b.predict_proba(v_ot)[:, 1]
        
    elif family == 'BalancedRandomForest':
        pipe_a = Pipeline([('prep', prep_a), ('clf', RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=5, max_features='sqrt', class_weight='balanced', random_state=42, n_jobs=-1))])
        pipe_a.fit(v_tr, y_tr)
        p_a = pipe_a.predict_proba(v_ot)[:, 1]
        
        pipe_b = Pipeline([('prep', prep_b), ('clf', RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=5, max_features='sqrt', class_weight='balanced', random_state=42, n_jobs=-1))])
        pipe_b.fit(v_tr, y_tr)
        p_b = pipe_b.predict_proba(v_ot)[:, 1]
        
    elif family == 'LogisticRegression_L2':
        pipe_a = Pipeline([('prep', prep_a), ('clf', LogisticRegression(C=1.0, max_iter=1000, random_state=42))])
        pipe_a.fit(v_tr, y_tr)
        p_a = pipe_a.predict_proba(v_ot)[:, 1]
        
        pipe_b = Pipeline([('prep', prep_b), ('clf', LogisticRegression(C=1.0, max_iter=1000, random_state=42))])
        pipe_b.fit(v_tr, y_tr)
        p_b = pipe_b.predict_proba(v_ot)[:, 1]
        
    n_ot = len(y_ot)
    delta_pr_list = []
    delta_roc_list = []
    
    for _ in range(N_BOOT):
        boot_idx = np.random.choice(n_ot, size=n_ot, replace=True)
        y_boot = y_ot[boot_idx]
        if len(np.unique(y_boot)) < 2:
            continue
        p_a_boot = p_a[boot_idx]
        p_b_boot = p_b[boot_idx]
        
        pr_a = average_precision_score(y_boot, p_a_boot)
        pr_b = average_precision_score(y_boot, p_b_boot)
        roc_a = roc_auc_score(y_boot, p_a_boot)
        roc_b = roc_auc_score(y_boot, p_b_boot)
        
        delta_pr_list.append(pr_b - pr_a)
        delta_roc_list.append(roc_b - roc_a)
        
    d_pr_mean = np.mean(delta_pr_list)
    d_pr_ci_low, d_pr_ci_high = np.percentile(delta_pr_list, [2.5, 97.5])
    d_roc_mean = np.mean(delta_roc_list)
    d_roc_ci_low, d_roc_ci_high = np.percentile(delta_roc_list, [2.5, 97.5])
    
    print(f"Target: {tgt}")
    print(f"  Δ OOT PR-AUC : {d_pr_mean:+.4f} (95% CI: [{d_pr_ci_low:+.4f}, {d_pr_ci_high:+.4f}])")
    print(f"  Δ OOT ROC-AUC: {d_roc_mean:+.4f} (95% CI: [{d_roc_ci_low:+.4f}, {d_roc_ci_high:+.4f}])")
