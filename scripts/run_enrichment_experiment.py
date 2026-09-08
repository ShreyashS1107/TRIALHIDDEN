import os
import sys
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_score,
    recall_score,
    f1_score
)
from scipy.stats import ks_2samp

sys.stdout.reconfigure(encoding='utf-8')

# 1. Setup paths
exp_dir = r"c:\Users\Shreyash\Documents\vs work\SIH26103\experiments\ocms_enrichment"
dataset_ocms_path = os.path.join(exp_dir, "feature_dataset_paimana_ocms.csv")
target_path = r"c:\Users\Shreyash\Documents\vs work\SIH26103\target_labels_v2\target_dataset_v2.csv"

df = pd.read_csv(dataset_ocms_path, low_memory=False)
df_target = pd.read_csv(target_path, low_memory=False)

print(f"Loaded Enriched Dataset: {df.shape[0]} rows, {df.shape[1]} columns.")

# Define temporal splits
train_mask = df['prediction_month'] <= '2025-11'
val_mask = df['prediction_month'].isin(['2025-12', '2026-01'])
test_mask = df['prediction_month'].isin(['2026-02', '2026-03'])

print(f"Train split: {train_mask.sum()} rows")
print(f"Validation split: {val_mask.sum()} rows")
print(f"OOT Test split: {test_mask.sum()} rows")

# Identify feature columns
id_cols = ['project_id', 'project_name', 'agency', 'state', 'prediction_month', 'evaluation_month', 'approval_start_date', 'original_completion_date', 'original_cost_crore']
target_cols = [
    'schedule_delay_3m', 'schedule_revision_3m', 'cost_overrun_state_3m', 'cost_revision_event_3m',
    'schedule_status_v2', 'schedule_revision_status_v2', 'cost_status_v2', 'label_reason',
    'label_confidence', 'source_report', 'source_table', 'is_labelled_schedule', 'is_labelled_schedule_revision', 'is_labelled_cost'
]

# Baseline 75 PAIMANA features
paimana_features = [c for c in df.columns if c not in id_cols and c not in target_cols and not c.startswith('hist_')]
print(f"Baseline PAIMANA Features: {len(paimana_features)}")

# OCMS Feature Families
agency_features = [c for c in df.columns if c.startswith('hist_agency_')]
sector_features = [c for c in df.columns if c.startswith('hist_sector_')]
linked_features = [c for c in df.columns if c.startswith('hist_linked_')]
all_ocms_features = [c for c in df.columns if c.startswith('hist_')]

print(f"OCMS Agency Features: {len(agency_features)}")
print(f"OCMS Sector Features: {len(sector_features)}")
print(f"OCMS Linked Project Features: {len(linked_features)}")
print(f"Total OCMS Enriched Features: {len(all_ocms_features)}")

# Define Ablation Feature Subsets
ablation_configs = {
    'Model A (PAIMANA-Only)': paimana_features,
    'Model B (PAIMANA + Agency Priors)': paimana_features + agency_features,
    'Model C (PAIMANA + Sector Priors)': paimana_features + sector_features,
    'Model D (PAIMANA + Linked Project History)': paimana_features + linked_features,
    'Model E (PAIMANA + Agency + Sector)': paimana_features + agency_features + sector_features,
    'Model F (PAIMANA + All OCMS Priors)': paimana_features + all_ocms_features
}

def calculate_all_metrics(y_true, y_prob):
    # Filter out NaNs if any
    valid_idx = (~np.isnan(y_true)) & (~np.isnan(y_prob))
    y_t = y_true[valid_idx]
    y_p = y_prob[valid_idx]
    
    if len(y_t) == 0 or len(np.unique(y_t)) < 2:
        return {
            'PR-AUC': np.nan, 'ROC-AUC': np.nan, 'Brier': np.nan, 'LogLoss': np.nan,
            'Precision@Top10': np.nan, 'Recall@Top10': np.nan
        }
        
    pr_auc = average_precision_score(y_t, y_p)
    roc_auc = roc_auc_score(y_t, y_p)
    brier = brier_score_loss(y_t, y_p)
    ll = log_loss(y_t, np.clip(y_p, 1e-6, 1.0 - 1e-6))
    
    # Precision and Recall at Top 10%
    n_top10 = max(1, int(0.10 * len(y_p)))
    top10_indices = np.argsort(y_p)[::-1][:n_top10]
    prec_top10 = float(np.mean(y_t.iloc[top10_indices])) if hasattr(y_t, 'iloc') else float(np.mean(y_t[top10_indices]))
    total_pos = np.sum(y_t)
    rec_top10 = float(np.sum(y_t.iloc[top10_indices]) / total_pos) if hasattr(y_t, 'iloc') else float(np.sum(y_t[top10_indices]) / total_pos)
    
    return {
        'PR-AUC': round(pr_auc, 4),
        'ROC-AUC': round(roc_auc, 4),
        'Brier': round(brier, 4),
        'LogLoss': round(ll, 4),
        'Precision@Top10': round(prec_top10, 4),
        'Recall@Top10': round(rec_top10, 4)
    }

def build_preprocessing_pipeline(feature_cols, df_sample):
    num_cols = [c for c in feature_cols if df_sample[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    cat_cols = [c for c in feature_cols if c not in num_cols]
    
    transformers = []
    if num_cols:
        num_pipe = Pipeline([
            ('imputer', SimpleImputer(strategy='median'))
        ])
        transformers.append(('num', num_pipe, num_cols))
        
    if cat_cols:
        cat_pipe = Pipeline([
            ('imputer', SimpleImputer(strategy='constant', fill_value='UNKNOWN')),
            ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])
        transformers.append(('cat', cat_pipe, cat_cols))
        
    preprocessor = ColumnTransformer(transformers=transformers, remainder='drop')
    return preprocessor, num_cols, cat_cols

# Operational Target Model Mapping
targets_config = {
    'schedule_delay_3m': {
        'model_type': 'RandomForest_RF02',
        'estimator': RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=5, max_features='sqrt', random_state=42, n_jobs=-1
        ),
        'scale_for_linear': False
    },
    'cost_overrun_state_3m': {
        'model_type': 'RandomForest_Balanced',
        'estimator': RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=5, class_weight='balanced', max_features='sqrt', random_state=42, n_jobs=-1
        ),
        'scale_for_linear': False
    },
    'schedule_revision_3m': {
        'model_type': 'LogisticRegression',
        'estimator': LogisticRegression(
            penalty='l2', C=1.0, max_iter=1000, random_state=42
        ),
        'scale_for_linear': True
    }
}

ablation_results = []
feature_importances_list = []

print("\n" + "="*80)
print("STARTING CONTROLLED ENRICHMENT EXPERIMENTATION ACROSS 3 TARGETS")
print("="*80)

for target_name, t_cfg in targets_config.items():
    print(f"\n>>> EVALUATING TARGET: {target_name} ({t_cfg['model_type']})")
    
    # Filter rows where target is not null
    valid_target_mask = df[target_name].notna()
    
    train_sub_mask = train_mask & valid_target_mask
    val_sub_mask = val_mask & valid_target_mask
    test_sub_mask = test_mask & valid_target_mask
    
    y_train = df.loc[train_sub_mask, target_name]
    y_val = df.loc[val_sub_mask, target_name]
    y_test = df.loc[test_sub_mask, target_name]
    
    print(f"    Train size: {len(y_train)} (Pos: {y_train.mean():.3f}) | Val size: {len(y_val)} (Pos: {y_val.mean():.3f}) | Test size: {len(y_test)} (Pos: {y_test.mean():.3f})")
    
    baseline_val_metrics = None
    baseline_oot_metrics = None
    
    for model_name, f_cols in ablation_configs.items():
        preproc, num_cols, cat_cols = build_preprocessing_pipeline(f_cols, df)
        
        # Pipeline
        if t_cfg['scale_for_linear']:
            # For linear models, add standard scaler
            full_pipeline = Pipeline([
                ('preproc', preproc),
                ('scaler', StandardScaler(with_mean=False)),
                ('clf', t_cfg['estimator'])
            ])
        else:
            full_pipeline = Pipeline([
                ('preproc', preproc),
                ('clf', t_cfg['estimator'])
            ])
            
        # Fit on Train
        X_train = df.loc[train_sub_mask, f_cols]
        full_pipeline.fit(X_train, y_train)
        
        # Predict on Validation
        X_val = df.loc[val_sub_mask, f_cols]
        y_val_prob = full_pipeline.predict_proba(X_val)[:, 1]
        val_m = calculate_all_metrics(y_val, y_val_prob)
        
        # Predict on Test (OOT)
        X_test = df.loc[test_sub_mask, f_cols]
        y_test_prob = full_pipeline.predict_proba(X_test)[:, 1]
        oot_m = calculate_all_metrics(y_test, y_test_prob)
        
        if model_name == 'Model A (PAIMANA-Only)':
            baseline_val_metrics = val_m
            baseline_oot_metrics = oot_m
            
        delta_val_pr = round(val_m['PR-AUC'] - baseline_val_metrics['PR-AUC'], 4)
        delta_val_roc = round(val_m['ROC-AUC'] - baseline_val_metrics['ROC-AUC'], 4)
        delta_oot_pr = round(oot_m['PR-AUC'] - baseline_oot_metrics['PR-AUC'], 4)
        delta_oot_roc = round(oot_m['ROC-AUC'] - baseline_oot_metrics['ROC-AUC'], 4)
        delta_oot_brier = round(oot_m['Brier'] - baseline_oot_metrics['Brier'], 4)
        
        print(f"    - {model_name:42s} | Val PR: {val_m['PR-AUC']:.4f} (Δ {delta_val_pr:+.4f}) | OOT PR: {oot_m['PR-AUC']:.4f} (Δ {delta_oot_pr:+.4f}) | OOT ROC: {oot_m['ROC-AUC']:.4f} (Δ {delta_oot_roc:+.4f})")
        
        ablation_results.append({
            'target': target_name,
            'model_name': model_name,
            'model_family': t_cfg['model_type'],
            'feature_count': len(f_cols),
            'val_pr_auc': val_m['PR-AUC'],
            'val_roc_auc': val_m['ROC-AUC'],
            'val_brier': val_m['Brier'],
            'val_logloss': val_m['LogLoss'],
            'val_precision_top10': val_m['Precision@Top10'],
            'val_recall_top10': val_m['Recall@Top10'],
            'oot_pr_auc': oot_m['PR-AUC'],
            'oot_roc_auc': oot_m['ROC-AUC'],
            'oot_brier': oot_m['Brier'],
            'oot_logloss': oot_m['LogLoss'],
            'oot_precision_top10': oot_m['Precision@Top10'],
            'oot_recall_top10': oot_m['Recall@Top10'],
            'delta_val_pr_auc': delta_val_pr,
            'delta_val_roc_auc': delta_val_roc,
            'delta_oot_pr_auc': delta_oot_pr,
            'delta_oot_roc_auc': delta_oot_roc,
            'delta_oot_brier': delta_oot_brier
        })
        
        # If Model F, extract feature importances
        if model_name == 'Model F (PAIMANA + All OCMS Priors)' and hasattr(full_pipeline.named_steps['clf'], 'feature_importances_'):
            importances = full_pipeline.named_steps['clf'].feature_importances_
            # Approximate feature names
            feat_names = num_cols.copy()
            if cat_cols:
                ohe = full_pipeline.named_steps['preproc'].named_transformers_['cat'].named_steps['ohe']
                feat_names.extend(ohe.get_feature_names_out(cat_cols))
            
            for fn, imp in zip(feat_names[:len(importances)], importances):
                feature_importances_list.append({
                    'target': target_name,
                    'feature_name': fn,
                    'feature_family': 'OCMS Historical Prior' if fn.startswith('hist_') else 'PAIMANA Core',
                    'importance_score': round(float(imp), 6)
                })

df_ablation = pd.DataFrame(ablation_results)
ablation_csv_path = os.path.join(exp_dir, "ablation_results.csv")
df_ablation.to_csv(ablation_csv_path, index=False)
print(f"\nSaved {ablation_csv_path}")

df_fi = pd.DataFrame(feature_importances_list)
if len(df_fi) > 0:
    df_fi.sort_values(by=['target', 'importance_score'], ascending=[True, False], inplace=True)
    fi_csv_path = os.path.join(exp_dir, "feature_importances.csv")
    df_fi.to_csv(fi_csv_path, index=False)
    print(f"Saved {fi_csv_path}")

# 2. Data Drift Analysis across Train vs Val vs OOT for OCMS Features
print("\n" + "="*80)
print("COMPUTING DATA DRIFT (TRAIN VS VAL VS OOT)")
print("="*80)

drift_records = []
for f in all_ocms_features:
    train_s = df.loc[train_mask, f].dropna()
    val_s = df.loc[val_mask, f].dropna()
    oot_s = df.loc[test_mask, f].dropna()
    
    ks_stat_val, ks_pval_val = ks_2samp(train_s, val_s) if len(train_s) > 0 and len(val_s) > 0 else (np.nan, np.nan)
    ks_stat_oot, ks_pval_oot = ks_2samp(train_s, oot_s) if len(train_s) > 0 and len(oot_s) > 0 else (np.nan, np.nan)
    
    drift_records.append({
        'feature_name': f,
        'feature_family': 'Agency' if 'agency' in f else ('Sector' if 'sector' in f else 'Linked Project'),
        'train_mean': round(train_s.mean(), 4) if len(train_s) > 0 else np.nan,
        'val_mean': round(val_s.mean(), 4) if len(val_s) > 0 else np.nan,
        'oot_mean': round(oot_s.mean(), 4) if len(oot_s) > 0 else np.nan,
        'train_missing_pct': round((df.loc[train_mask, f].isna().mean()) * 100, 2),
        'val_missing_pct': round((df.loc[val_mask, f].isna().mean()) * 100, 2),
        'oot_missing_pct': round((df.loc[test_mask, f].isna().mean()) * 100, 2),
        'ks_stat_train_vs_oot': round(ks_stat_oot, 4) if pd.notna(ks_stat_oot) else np.nan,
        'ks_pval_train_vs_oot': round(ks_pval_oot, 4) if pd.notna(ks_pval_oot) else np.nan,
        'drift_verdict': 'Significant Shift' if (pd.notna(ks_pval_oot) and ks_pval_oot < 0.01) else 'Stable Distribution'
    })

df_drift = pd.DataFrame(drift_records)
drift_csv_path = os.path.join(exp_dir, "data_drift_summary.csv")
df_drift.to_csv(drift_csv_path, index=False)
print(f"Saved {drift_csv_path}")

print("Component 2 complete.")
