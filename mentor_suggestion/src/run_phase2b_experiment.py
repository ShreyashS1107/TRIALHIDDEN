import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss, log_loss,
    precision_score, recall_score, f1_score, confusion_matrix
)

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\Shreyash\Documents\vs work\SIH26103"
DATA_DIR = os.path.join(BASE_DIR, "data")
TARGET_DIR = os.path.join(BASE_DIR, "target_labels_v2")
FEATURES_DIR = os.path.join(BASE_DIR, "features")
MENTOR_DIR = os.path.join(BASE_DIR, "mentor_suggestion")
OUT_DATA_DIR = os.path.join(MENTOR_DIR, "data")
OUT_REPORTS_DIR = os.path.join(MENTOR_DIR, "reports")

print("="*80)
print("PHASE 2B: CONTROLLED ML PREDICTIVE EXPERIMENT (SIH26103)")
print("="*80)

# 1. Load Data
features_v1_path = os.path.join(FEATURES_DIR, "feature_dataset_v1.csv")
dict_v1_path = os.path.join(FEATURES_DIR, "feature_dictionary_v1.csv")
target_v2_path = os.path.join(TARGET_DIR, "target_dataset_v2.csv")
benchmarks_path = os.path.join(OUT_DATA_DIR, "point_in_time_cluster_benchmarks.csv")

f_df = pd.read_csv(features_v1_path, low_memory=False)
dict_df = pd.read_csv(dict_v1_path)
t_df = pd.read_csv(target_v2_path, low_memory=False)
b_df = pd.read_csv(benchmarks_path, low_memory=False)

print(f"Loaded Feature Dataset V1: {len(f_df):,} rows")
print(f"Loaded Target Dataset V2: {len(t_df):,} rows")
print(f"Loaded Point-in-Time Benchmarks: {len(b_df):,} rows")

# 2. Reconcile and Merge Datasets by (project_id, prediction_month)
f_df['project_id_str'] = f_df['project_id'].astype(str)
f_df['prediction_month_str'] = f_df['prediction_month'].astype(str)

t_df['project_id_str'] = t_df['project_id'].astype(str)
t_df['prediction_month_str'] = t_df['prediction_month'].astype(str)

b_df['project_id_str'] = b_df['project_id'].astype(str)
b_df['prediction_month_str'] = b_df['prediction_month'].astype(str)

# Join benchmarks
df_all = f_df.merge(
    b_df[[
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

print(f"Merged Modeling Matrix: {len(df_all):,} snapshot rows.")

# 3. Extract Authoritative Production 75 Features (71 numerical + 4 categorical)
paimana_cat_cols = ['project_size_category', 'current_schedule_status_as_of_t', 'reporting_structure_version_t', 'table_source_t']
paimana_num_cols = dict_df[dict_df['data_type'].isin(['float64', 'int64'])]['feature_name'].tolist()

print(f"\nProduction Feature Universe: {len(paimana_num_cols)} numerical + {len(paimana_cat_cols)} categorical = {len(paimana_num_cols) + len(paimana_cat_cols)} total features.")
assert len(paimana_num_cols) == 71, f"Expected 71 numerical features, got {len(paimana_num_cols)}"
assert len(paimana_cat_cols) == 4, f"Expected 4 categorical features, got {len(paimana_cat_cols)}"

# Ensure numerical features are numeric
for col in paimana_num_cols:
    df_all[col] = pd.to_numeric(df_all[col], errors='coerce')

# 4. Define Feature Configurations for Experiment & Ablations
valid_benchmark_num = [
    'cluster_hist_delay_rate_smoothed_t',
    'cluster_hist_median_delay_months_t',
    'cluster_distance_to_centroid_t',
    'cluster_slippage_deviation_t',
    'cluster_hist_cost_revision_rate_t',
    'is_legacy_linked'
]
for col in valid_benchmark_num:
    df_all[col] = pd.to_numeric(df_all[col], errors='coerce')

# Additional ablation feature sets
df_all['cluster_cost_esc_deviation_t'] = pd.to_numeric(df_all['cluster_cost_esc_deviation_t'], errors='coerce')
df_all['cluster_hist_mean_delay_months_t'] = pd.to_numeric(df_all['cluster_hist_mean_delay_months_t'], errors='coerce')
df_all['cluster_id_str'] = df_all['cluster_id'].astype(str)

# Feature Set B: All Valid Benchmarks (6 features)
feat_B_num = paimana_num_cols + valid_benchmark_num
feat_B_cat = paimana_cat_cols

# Feature Set C: Benchmark Outcome Stats Only (3 features)
feat_C_num = paimana_num_cols + ['cluster_hist_delay_rate_smoothed_t', 'cluster_hist_median_delay_months_t', 'cluster_hist_mean_delay_months_t']
feat_C_cat = paimana_cat_cols

# Feature Set D: Benchmark Deviations Only (2 features)
feat_D_num = paimana_num_cols + ['cluster_slippage_deviation_t', 'cluster_cost_esc_deviation_t']
feat_D_cat = paimana_cat_cols

# Feature Set E: Distance & Continuity Only (2 features)
feat_E_num = paimana_num_cols + ['cluster_distance_to_centroid_t', 'is_legacy_linked']
feat_E_cat = paimana_cat_cols

# Feature Set F: Research Diagnostic (One-Hot Cluster ID)
feat_F_num = paimana_num_cols
feat_F_cat = paimana_cat_cols + ['cluster_id_str']

configurations = {
    'Model A (PAIMANA-Only) [CHAMPION]': (paimana_num_cols, paimana_cat_cols),
    'Model B (PAIMANA + Valid Benchmarks)': (feat_B_num, feat_B_cat),
    'Model C (PAIMANA + Outcome Stats Only)': (feat_C_num, feat_C_cat),
    'Model D (PAIMANA + Deviations Only)': (feat_D_num, feat_D_cat),
    'Model E (PAIMANA + Distance & Continuity)': (feat_E_num, feat_E_cat),
    'Model F (Research: PAIMANA + Cluster ID)': (feat_F_num, feat_F_cat)
}

# 5. Temporal Splits (Strictly Chronological)
train_mask = df_all['prediction_month'].between('2025-04', '2025-11')
val_mask = df_all['prediction_month'].between('2025-12', '2026-01')
oot_mask = df_all['prediction_month'].between('2026-02', '2026-03')

df_train_raw = df_all[train_mask].copy()
df_val_raw = df_all[val_mask].copy()
df_oot_raw = df_all[oot_mask].copy()

print(f"\n--- Chronological Split Verification ---")
print(f"Train Raw     : {len(df_train_raw):,} rows (Apr 2025 – Nov 2025)")
print(f"Validation Raw: {len(df_val_raw):,} rows (Dec 2025 – Jan 2026)")
print(f"OOT Test Raw  : {len(df_oot_raw):,} rows (Feb 2026 – Mar 2026)")

# 6. Evaluation Function for Expected Calibration Error (ECE)
def calc_ece(y_true, y_prob, n_bins=10):
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_prob, bins) - 1
    ece = 0.0
    n = len(y_true)
    for b in range(n_bins):
        mask = bin_indices == b
        if np.sum(mask) > 0:
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += (np.sum(mask) / n) * np.abs(bin_acc - bin_conf)
    return float(ece)

# 7. Experiment Execution across Targets & Configurations
targets_to_evaluate = [
    ('schedule_delay_3m', 'RandomForest_Calibrated'),
    ('cost_overrun_state_3m', 'BalancedRandomForest'),
    ('schedule_revision_3m', 'LogisticRegression_L2')
]

results = []
feature_importances_dict = {}

for target_col, model_family in targets_to_evaluate:
    print("\n" + "="*80)
    print(f"EVALUATING TARGET: {target_col} (Model Family: {model_family})")
    print("="*80)
    
    # Filter non-null target rows strictly
    df_train = df_train_raw[df_train_raw[target_col].notna()].copy()
    df_val = df_val_raw[df_val_raw[target_col].notna()].copy()
    df_oot = df_oot_raw[df_oot_raw[target_col].notna()].copy()
    
    y_train = df_train[target_col].astype(float).values
    y_val = df_val[target_col].astype(float).values
    y_oot = df_oot[target_col].astype(float).values
    
    pos_train = float(np.mean(y_train))
    pos_val = float(np.mean(y_val))
    pos_oot = float(np.mean(y_oot))
    print(f"Labelled rows: Train = {len(df_train):,} ({pos_train*100:.2f}% pos), Val = {len(df_val):,} ({pos_val*100:.2f}% pos), OOT = {len(df_oot):,} ({pos_oot*100:.2f}% pos)")
    
    baseline_metrics = {}
    
    for cfg_name, (num_cols, cat_cols) in configurations.items():
        num_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        cat_transformer = Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='UNKNOWN')),
            ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])
        
        preprocessor = ColumnTransformer([
            ('num', num_transformer, num_cols),
            ('cat', cat_transformer, cat_cols)
        ])
        
        if model_family == 'RandomForest_Calibrated':
            base_estimator = RandomForestClassifier(
                n_estimators=200, max_depth=12, min_samples_leaf=5, max_features='sqrt',
                random_state=42, n_jobs=-1
            )
            pipe = Pipeline([
                ('prep', preprocessor),
                ('clf', base_estimator)
            ])
            pipe.fit(df_train, y_train)
            
            calibrator = CalibratedClassifierCV(estimator=FrozenEstimator(pipe), method='sigmoid')
            calibrator.fit(df_val, y_val)
            model_evaluator = calibrator
            
            if cfg_name == 'Model B (PAIMANA + Valid Benchmarks)':
                fitted_clf = pipe.named_steps['clf']
                prep_step = pipe.named_steps['prep']
                ohe_features = prep_step.named_transformers_['cat'].named_steps['encoder'].get_feature_names_out(cat_cols)
                all_feature_names = list(num_cols) + list(ohe_features)
                importances = fitted_clf.feature_importances_
                feature_importances_dict[target_col] = pd.DataFrame({
                    'feature': all_feature_names,
                    'importance': importances
                }).sort_values('importance', ascending=False)
                
        elif model_family == 'BalancedRandomForest':
            base_estimator = RandomForestClassifier(
                n_estimators=200, max_depth=12, min_samples_leaf=5, max_features='sqrt',
                class_weight='balanced', random_state=42, n_jobs=-1
            )
            pipe = Pipeline([
                ('prep', preprocessor),
                ('clf', base_estimator)
            ])
            pipe.fit(df_train, y_train)
            model_evaluator = pipe
            
            if cfg_name == 'Model B (PAIMANA + Valid Benchmarks)':
                fitted_clf = pipe.named_steps['clf']
                prep_step = pipe.named_steps['prep']
                ohe_features = prep_step.named_transformers_['cat'].named_steps['encoder'].get_feature_names_out(cat_cols)
                all_feature_names = list(num_cols) + list(ohe_features)
                feature_importances_dict[target_col] = pd.DataFrame({
                    'feature': all_feature_names,
                    'importance': fitted_clf.feature_importances_
                }).sort_values('importance', ascending=False)
                
        elif model_family == 'LogisticRegression_L2':
            base_estimator = LogisticRegression(
                C=1.0, max_iter=1000, solver='lbfgs', random_state=42
            )
            pipe = Pipeline([
                ('prep', preprocessor),
                ('clf', base_estimator)
            ])
            pipe.fit(df_train, y_train)
            model_evaluator = pipe
        
        # Predictions
        val_probs = model_evaluator.predict_proba(df_val)[:, 1]
        oot_probs = model_evaluator.predict_proba(df_oot)[:, 1]
        
        # Metrics
        val_roc = roc_auc_score(y_val, val_probs)
        val_pr = average_precision_score(y_val, val_probs)
        val_brier = brier_score_loss(y_val, val_probs)
        val_ece = calc_ece(y_val, val_probs)
        
        oot_roc = roc_auc_score(y_oot, oot_probs)
        oot_pr = average_precision_score(y_oot, oot_probs)
        oot_brier = brier_score_loss(y_oot, oot_probs)
        oot_logloss = log_loss(y_oot, oot_probs)
        oot_ece = calc_ece(y_oot, oot_probs)
        
        # Top Decile Precision (Top 10% highest predicted risk)
        top10_idx = np.argsort(oot_probs)[-int(0.10 * len(oot_probs)):]
        p_at_10 = float(np.mean(y_oot[top10_idx]))
        
        # Operational Threshold metrics (Threshold = 0.50)
        thresh = 0.50
        oot_preds = (oot_probs >= thresh).astype(int)
        prec = precision_score(y_oot, oot_preds, zero_division=0)
        rec = recall_score(y_oot, oot_preds, zero_division=0)
        f1 = f1_score(y_oot, oot_preds, zero_division=0)
        
        # Store baseline for delta calculation
        if 'Model A' in cfg_name:
            baseline_metrics[target_col] = {
                'oot_pr': oot_pr,
                'oot_roc': oot_roc,
                'oot_brier': oot_brier,
                'oot_logloss': oot_logloss,
                'oot_ece': oot_ece
            }
            delta_pr = 0.0
            delta_roc = 0.0
            delta_brier = 0.0
        else:
            delta_pr = oot_pr - baseline_metrics[target_col]['oot_pr']
            delta_roc = oot_roc - baseline_metrics[target_col]['oot_roc']
            delta_brier = oot_brier - baseline_metrics[target_col]['oot_brier']
            
        print(f"  {cfg_name:<42} | Val PR: {val_pr:.4f} | OOT PR: {oot_pr:.4f} (Δ={delta_pr:+.4f}) | OOT ROC: {oot_roc:.4f} (Δ={delta_roc:+.4f}) | OOT Brier: {oot_brier:.4f}")
        
        results.append({
            'target': target_col,
            'model_family': model_family,
            'configuration': cfg_name,
            'num_features': len(num_cols) + len(cat_cols),
            'val_pr_auc': round(val_pr, 4),
            'val_roc_auc': round(val_roc, 4),
            'val_brier': round(val_brier, 4),
            'val_ece': round(val_ece, 4),
            'oot_pr_auc': round(oot_pr, 4),
            'oot_roc_auc': round(oot_roc, 4),
            'oot_brier': round(oot_brier, 4),
            'oot_logloss': round(oot_logloss, 4),
            'oot_ece': round(oot_ece, 4),
            'delta_oot_pr_auc': round(delta_pr, 4),
            'delta_oot_roc_auc': round(delta_roc, 4),
            'delta_oot_brier': round(delta_brier, 4),
            'precision_at_top_decile': round(p_at_10, 4),
            'oot_precision': round(prec, 4),
            'oot_recall': round(rec, 4),
            'oot_f1': round(f1, 4)
        })

df_results = pd.DataFrame(results)

# 8. Save Experiment Results
results_csv_path = os.path.join(OUT_REPORTS_DIR, "PHASE_2B_EXPERIMENT_RESULTS.csv")
df_results.to_csv(results_csv_path, index=False)
print(f"\nSaved Phase 2B experiment results to: {results_csv_path}")

# 9. Save Top Feature Importances for Schedule Delay and Cost Overrun
for tgt, imp_df in feature_importances_dict.items():
    imp_csv_path = os.path.join(OUT_REPORTS_DIR, f"feature_importances_{tgt}.csv")
    imp_df.to_csv(imp_csv_path, index=False)
    print(f"\nTop 15 Features for {tgt} in Model B:")
    print(imp_df.head(15).to_string(index=False))

# 10. Redundancy Correlation Matrix between Benchmark Features and Top PAIMANA Features
top_paimana_features = [
    'schedule_slippage_months_t', 'months_to_original_doc_t', 'physical_progress_t',
    'project_age_months_t', 'original_cost_log', 'planned_duration_months', 'expenditure_ratio_pct_t'
]
benchmark_eval_features = [
    'cluster_hist_delay_rate_smoothed_t', 'cluster_hist_median_delay_months_t',
    'cluster_distance_to_centroid_t', 'cluster_slippage_deviation_t',
    'cluster_hist_cost_revision_rate_t', 'is_legacy_linked'
]

corr_sub = df_all[top_paimana_features + benchmark_eval_features].apply(pd.to_numeric, errors='coerce')
corr_mat = corr_sub.corr().loc[top_paimana_features, benchmark_eval_features].round(3)
corr_csv_path = os.path.join(OUT_REPORTS_DIR, "benchmark_redundancy_correlation.csv")
corr_mat.to_csv(corr_csv_path)
print("\n--- Correlation Matrix: PAIMANA Core vs Benchmark Layer ---")
print(corr_mat.to_string())

print("\nPhase 2B execution completed successfully.")
