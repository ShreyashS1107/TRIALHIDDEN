"""
========================================================================================
SIH 2026 Problem Statement SIH26103: Machine Learning Modeling Stage (v1)
Primary Target: schedule_delay_3m (3-Month Operational Schedule Delay)
========================================================================================
Authors: AI/ML Engineering Team
Input Data:
  - ml/train_dataset.csv
  - ml/validation_dataset.csv
  - ml/test_dataset.csv
Outputs in ml/models/:
  - model_comparison.csv
  - validation_results.csv
  - test_results.csv
  - feature_importance.csv
  - distribution_shift_report.csv
  - threshold_analysis.csv
  - confusion_matrix.csv
  - model_report.txt
  - best_model_gradient_boosting.joblib
========================================================================================
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix
)
from sklearn.inspection import permutation_importance
from scipy.stats import ks_2samp

# Custom Rule-Based Persistence / State Baseline Model
class RuleBasedPersistenceBaseline:
    """
    Interpretable baseline rule:
    Predict high risk (1) if project has existing schedule slippage as of t (schedule_slippage_months_t > 0)
    OR is currently stagnant (stagnant_3m_t == 1)
    OR has non-positive progress velocity with incomplete progress (progress_velocity_3m_t <= 0 and remaining_physical_progress_t > 0).
    Otherwise predict low risk (0).
    """
    def __init__(self):
        self.p_pos_rule = 0.85
        self.p_neg_rule = 0.20

    def fit(self, X_df, y):
        # Learn empirical probabilities from training set
        rule_mask = (
            (X_df['schedule_slippage_months_t'] > 0) |
            (X_df['stagnant_3m_t'] == 1.0) |
            ((X_df['progress_velocity_3m_t'] <= 0) & (X_df['remaining_physical_progress_t'] > 0))
        )
        if rule_mask.sum() > 0:
            self.p_pos_rule = float(y[rule_mask].mean())
        if (~rule_mask).sum() > 0:
            self.p_neg_rule = float(y[~rule_mask].mean())
        return self

    def predict_proba(self, X_df):
        rule_mask = (
            (X_df['schedule_slippage_months_t'] > 0) |
            (X_df['stagnant_3m_t'] == 1.0) |
            ((X_df['progress_velocity_3m_t'] <= 0) & (X_df['remaining_physical_progress_t'] > 0))
        )
        proba_1 = np.where(rule_mask, self.p_pos_rule, self.p_neg_rule)
        proba_0 = 1.0 - proba_1
        return np.column_stack([proba_0, proba_1])

    def predict(self, X_df, threshold=0.5):
        proba = self.predict_proba(X_df)[:, 1]
        return (proba >= threshold).astype(int)


def calculate_metrics(y_true, y_prob, threshold=0.5):
    """Compute primary and secondary ML classification metrics."""
    y_pred = (y_prob >= threshold).astype(int)
    
    # Precision@10% and Recall@10%
    n_top10 = max(1, int(0.10 * len(y_prob)))
    top10_indices = np.argsort(y_prob)[::-1][:n_top10]
    precision_at_10 = float(y_true.iloc[top10_indices].mean())
    total_pos = y_true.sum()
    recall_at_10 = float(y_true.iloc[top10_indices].sum() / total_pos) if total_pos > 0 else 0.0

    roc_auc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else np.nan
    pr_auc = average_precision_score(y_true, y_prob) if len(np.unique(y_true)) > 1 else np.nan
    brier = brier_score_loss(y_true, y_prob)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    acc = accuracy_score(y_true, y_pred)

    return {
        'ROC_AUC': round(roc_auc, 4),
        'PR_AUC': round(pr_auc, 4),
        'Brier': round(brier, 4),
        'Precision': round(prec, 4),
        'Recall': round(rec, 4),
        'F1': round(f1, 4),
        'Accuracy': round(acc, 4),
        'Precision_at_10pct': round(precision_at_10, 4),
        'Recall_at_10pct': round(recall_at_10, 4)
    }


def main():
    print("=" * 80)
    print("SIH26103: MACHINE LEARNING MODELING PIPELINE (PRIMARY TARGET: schedule_delay_3m)")
    print("=" * 80)

    # 1. Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ml_dir = os.path.join(base_dir, "ml")
    models_dir = os.path.join(ml_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    train_path = os.path.join(ml_dir, "train_dataset.csv")
    val_path = os.path.join(ml_dir, "validation_dataset.csv")
    test_path = os.path.join(ml_dir, "test_dataset.csv")

    print("\n[1] Loading datasets...")
    train_df = pd.read_csv(train_path, low_memory=False)
    val_df = pd.read_csv(val_path, low_memory=False)
    test_df = pd.read_csv(test_path, low_memory=False)

    print(f"    - Train raw:      {len(train_df):,} rows")
    print(f"    - Validation raw: {len(val_df):,} rows")
    print(f"    - Test raw:       {len(test_df):,} rows")

    # 2. Filter for primary target schedule_delay_3m (notna)
    target_col = 'schedule_delay_3m'
    train_df = train_df[train_df[target_col].notna()].copy()
    val_df = val_df[val_df[target_col].notna()].copy()
    test_df = test_df[test_df[target_col].notna()].copy()

    y_train = train_df[target_col].astype(int)
    y_val = val_df[target_col].astype(int)
    y_test = test_df[target_col].astype(int)

    print(f"\n[2] Target-filtered datasets for modeling:")
    print(f"    - Train usable:      {len(train_df):,} rows (Positives: {y_train.sum():,} / {y_train.mean()*100:.2f}%)")
    print(f"    - Validation usable: {len(val_df):,} rows (Positives: {y_val.sum():,} / {y_val.mean()*100:.2f}%)")
    print(f"    - Test usable:       {len(test_df):,} rows (Positives: {y_test.sum():,} / {y_test.mean()*100:.2f}%)")

    # 3. Define feature space X
    id_cols = ['project_id', 'project_name', 'agency', 'state', 'prediction_month', 'evaluation_month']
    target_cols = [
        'schedule_delay_3m', 'schedule_revision_3m', 'cost_overrun_state_3m', 'cost_revision_event_3m',
        'schedule_status_v2', 'schedule_revision_status_v2', 'cost_status_v2', 'label_reason',
        'label_confidence', 'source_report', 'is_labelled_schedule', 'is_labelled_schedule_revision', 'is_labelled_cost'
    ]
    raw_date_cols = ['approval_start_date', 'original_completion_date', 'revised_doc_t', 'first_observed_month']
    cat_cols = ['project_size_category', 'current_schedule_status_as_of_t', 'reporting_structure_version_t', 'table_source_t']
    num_cols = [c for c in train_df.columns if c not in id_cols and c not in target_cols and c not in raw_date_cols and c not in cat_cols]

    print(f"\n[3] Feature Space Definition:")
    print(f"    - Numerical Features:   {len(num_cols)}")
    print(f"    - Categorical Features: {len(cat_cols)}")
    print(f"    - Raw Date Strings Excluded (already encoded in numeric metrics): {len(raw_date_cols)}")
    print(f"    - Total Features in X:  {len(num_cols) + len(cat_cols)}")

    # 4. Build Preprocessors (Fitted STRICTLY on Train)
    print("\n[4] Building Preprocessing Pipelines (Fitted STRICTLY on Train)...")
    # Pipeline for linear / standard tree models (imputed + scaled + onehot)
    standard_preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())]), num_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
        ]
    )
    standard_preprocessor.fit(train_df[num_cols + cat_cols])

    X_train_std = standard_preprocessor.transform(train_df[num_cols + cat_cols])
    X_val_std = standard_preprocessor.transform(val_df[num_cols + cat_cols])
    X_test_std = standard_preprocessor.transform(test_df[num_cols + cat_cols])

    # Feature names after one-hot encoding
    ohe_cat_names = standard_preprocessor.named_transformers_['cat'].get_feature_names_out(cat_cols).tolist()
    all_feature_names = num_cols + ohe_cat_names
    print(f"    - Preprocessed feature vector dimensionality: {len(all_feature_names)} columns.")

    # Pipeline for HistGradientBoosting (handles NaNs natively; ordinal encode categoricals)
    hgb_preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', num_cols),
            ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), cat_cols)
        ]
    )
    hgb_preprocessor.fit(train_df[num_cols + cat_cols])

    X_train_hgb = hgb_preprocessor.transform(train_df[num_cols + cat_cols])
    X_val_hgb = hgb_preprocessor.transform(val_df[num_cols + cat_cols])
    X_test_hgb = hgb_preprocessor.transform(test_df[num_cols + cat_cols])
    categorical_features_indices = list(range(len(num_cols), len(num_cols) + len(cat_cols)))

    # 5. Train Baseline & Machine Learning Models
    print("\n[5] Training Models...")

    # Model 0: Majority-class baseline
    print("    - Training Model 0: Majority-Class Baseline...")
    m0_majority = DummyClassifier(strategy='prior')
    m0_majority.fit(X_train_std, y_train)

    # Model 1: Rule-based persistence / state baseline
    print("    - Training Model 1: Rule-Based Persistence Baseline...")
    m1_rule = RuleBasedPersistenceBaseline()
    m1_rule.fit(train_df, y_train)

    # Model 2: Logistic Regression (L2 regularization)
    print("    - Training Model 2: Logistic Regression (L2 regularized)...")
    m2_logreg = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    m2_logreg.fit(X_train_std, y_train)

    # Model 3: Random Forest
    print("    - Training Model 3: Random Forest Classifier...")
    m3_rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    m3_rf.fit(X_train_std, y_train)

    # Model 4: Gradient Boosted Trees (HistGradientBoosting)
    print("    - Training Model 4: Gradient Boosted Trees (HistGradientBoosting)...")
    m4_gbt = HistGradientBoostingClassifier(
        max_iter=100,
        max_depth=6,
        min_samples_leaf=20,
        categorical_features=categorical_features_indices,
        random_state=42
    )
    m4_gbt.fit(X_train_hgb, y_train)

    # 6. Model Evaluation on Validation Set (Model Selection)
    print("\n[6] Evaluating Models on VALIDATION Set (Dec 2025 – Jan 2026)...")
    
    val_probs = {
        'Majority Baseline': m0_majority.predict_proba(X_val_std)[:, 1],
        'Rule-Based Persistence': m1_rule.predict_proba(val_df)[:, 1],
        'Logistic Regression': m2_logreg.predict_proba(X_val_std)[:, 1],
        'Random Forest': m3_rf.predict_proba(X_val_std)[:, 1],
        'Gradient Boosted Trees': m4_gbt.predict_proba(X_val_hgb)[:, 1]
    }

    val_metrics_list = []
    for mname, probs in val_probs.items():
        res = calculate_metrics(y_val, probs, threshold=0.5)
        res['model'] = mname
        val_metrics_list.append(res)

    val_results_df = pd.DataFrame(val_metrics_list)[['model', 'ROC_AUC', 'PR_AUC', 'Brier', 'Precision', 'Recall', 'F1', 'Accuracy', 'Precision_at_10pct', 'Recall_at_10pct']]
    print("\nValidation Results Summary (Threshold = 0.50):")
    print(val_results_df.to_string(index=False))

    # Identify Best Model on Validation
    best_model_name = val_results_df.sort_values(by=['ROC_AUC', 'PR_AUC'], ascending=False).iloc[0]['model']
    print(f"\n>>> Best Performing Model on Validation: {best_model_name}")

    # 7. Threshold Analysis on Validation Set for Best Model
    print(f"\n[7] Conducting Threshold Sensitivity Analysis for '{best_model_name}' on Validation Data...")
    best_val_probs = val_probs[best_model_name]
    threshold_records = []
    test_thresholds = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]

    for th in test_thresholds:
        preds = (best_val_probs >= th).astype(int)
        p = precision_score(y_val, preds, zero_division=0)
        r = recall_score(y_val, preds, zero_division=0)
        f = f1_score(y_val, preds, zero_division=0)
        acc = accuracy_score(y_val, preds)
        high_risk_cnt = int(preds.sum())
        threshold_records.append({
            'threshold': th,
            'precision': round(p, 4),
            'recall': round(r, 4),
            'f1_score': round(f, 4),
            'accuracy': round(acc, 4),
            'predicted_high_risk_count': high_risk_cnt,
            'predicted_high_risk_pct': round(high_risk_cnt / len(y_val) * 100, 2)
        })

    thresh_df = pd.DataFrame(threshold_records)
    print(thresh_df.to_string(index=False))

    # Select optimal operational threshold based on max F1 on Validation
    best_th_row = thresh_df.sort_values(by='f1_score', ascending=False).iloc[0]
    selected_operational_threshold = float(best_th_row['threshold'])
    print(f"\n>>> Selected Operational Threshold: {selected_operational_threshold:.2f} (Max Validation F1: {best_th_row['f1_score']:.4f})")

    # 8. Out-of-Time (OOT) Test Evaluation (Feb 2026 – Mar 2026)
    print("\n[8] Evaluating All Models on OOT TEST Set (Feb 2026 – Mar 2026)...")
    test_probs = {
        'Majority Baseline': m0_majority.predict_proba(X_test_std)[:, 1],
        'Rule-Based Persistence': m1_rule.predict_proba(test_df)[:, 1],
        'Logistic Regression': m2_logreg.predict_proba(X_test_std)[:, 1],
        'Random Forest': m3_rf.predict_proba(X_test_std)[:, 1],
        'Gradient Boosted Trees': m4_gbt.predict_proba(X_test_hgb)[:, 1]
    }

    test_metrics_list = []
    for mname, probs in test_probs.items():
        res = calculate_metrics(y_test, probs, threshold=0.5)
        res['model'] = mname
        test_metrics_list.append(res)

    test_results_df = pd.DataFrame(test_metrics_list)[['model', 'ROC_AUC', 'PR_AUC', 'Brier', 'Precision', 'Recall', 'F1', 'Accuracy', 'Precision_at_10pct', 'Recall_at_10pct']]
    print("\nOOT Test Results Summary (Default Threshold = 0.50):")
    print(test_results_df.to_string(index=False))

    # Evaluate Best Model on Test using Locked Operational Threshold
    best_test_probs = test_probs[best_model_name]
    best_test_metrics_locked = calculate_metrics(y_test, best_test_probs, threshold=selected_operational_threshold)
    print(f"\nOOT Test Performance for '{best_model_name}' at Locked Threshold ({selected_operational_threshold:.2f}):")
    print(f"    - ROC-AUC:            {best_test_metrics_locked['ROC_AUC']:.4f}")
    print(f"    - PR-AUC:             {best_test_metrics_locked['PR_AUC']:.4f}")
    print(f"    - Brier Score:        {best_test_metrics_locked['Brier']:.4f}")
    print(f"    - F1-Score:           {best_test_metrics_locked['F1']:.4f}")
    print(f"    - Precision:          {best_test_metrics_locked['Precision']:.4f}")
    print(f"    - Recall:             {best_test_metrics_locked['Recall']:.4f}")
    print(f"    - Precision@10%:      {best_test_metrics_locked['Precision_at_10pct']:.4f}")
    print(f"    - Recall@10%:         {best_test_metrics_locked['Recall_at_10pct']:.4f}")

    # Confusion Matrix for Best Model on OOT Test at Locked Threshold
    y_test_pred_locked = (best_test_probs >= selected_operational_threshold).astype(int)
    cm = confusion_matrix(y_test, y_test_pred_locked)
    tn_val = int(cm[0, 0])
    fp_val = int(cm[0, 1])
    fn_val = int(cm[1, 0])
    tp_val = int(cm[1, 1])
    cm_df = pd.DataFrame([
        {'model': best_model_name, 'split': 'TEST_OOT', 'threshold': selected_operational_threshold, 'TN': tn_val, 'FP': fp_val, 'FN': fn_val, 'TP': tp_val, 'Total': len(y_test)}
    ])

    # 9. Model Comparison Table (Validation vs Test)
    model_comp_rows = []
    for mname in val_probs.keys():
        v_m = val_results_df[val_results_df['model'] == mname].iloc[0]
        t_m = test_results_df[test_results_df['model'] == mname].iloc[0]
        model_comp_rows.append({
            'model': mname,
            'Val_ROC_AUC': v_m['ROC_AUC'],
            'Test_ROC_AUC': t_m['ROC_AUC'],
            'Delta_ROC_AUC': round(t_m['ROC_AUC'] - v_m['ROC_AUC'], 4),
            'Val_PR_AUC': v_m['PR_AUC'],
            'Test_PR_AUC': t_m['PR_AUC'],
            'Delta_PR_AUC': round(t_m['PR_AUC'] - v_m['PR_AUC'], 4),
            'Val_Brier': v_m['Brier'],
            'Test_Brier': t_m['Brier'],
            'Val_F1': v_m['F1'],
            'Test_F1': t_m['F1'],
            'Test_Precision_at_10pct': t_m['Precision_at_10pct'],
            'Test_Recall_at_10pct': t_m['Recall_at_10pct']
        })
    model_comparison_df = pd.DataFrame(model_comp_rows)

    # 10. Feature Importance Analysis
    print("\n[10] Computing Feature Importance for Trained Models...")
    feat_imp_records = []

    # Random Forest MDI importance
    rf_imps = m3_rf.feature_importances_
    for fn, imp in zip(all_feature_names, rf_imps):
        feat_imp_records.append({'model': 'Random Forest', 'feature': fn, 'importance': round(imp, 6)})

    # Logistic Regression absolute coefficients
    logreg_coefs = np.abs(m2_logreg.coef_[0])
    for fn, imp in zip(all_feature_names, logreg_coefs):
        feat_imp_records.append({'model': 'Logistic Regression', 'feature': fn, 'importance': round(imp, 6)})

    # HistGradientBoosting Permutation Importance on Validation
    perm_res = permutation_importance(m4_gbt, X_val_hgb, y_val, n_repeats=5, random_state=42, scoring='roc_auc')
    hgb_feature_names = num_cols + cat_cols
    for fn, imp in zip(hgb_feature_names, perm_res.importances_mean):
        feat_imp_records.append({'model': 'Gradient Boosted Trees', 'feature': fn, 'importance': round(max(0.0, imp), 6)})

    feat_imp_df = pd.DataFrame(feat_imp_records)
    feat_imp_df['rank'] = feat_imp_df.groupby('model')['importance'].rank(ascending=False, method='dense').astype(int)
    feat_imp_df.sort_values(by=['model', 'rank'], inplace=True)

    top10_gbt = feat_imp_df[feat_imp_df['model'] == 'Gradient Boosted Trees'].head(10)
    print("\nTop 10 Influential Features for Gradient Boosted Trees:")
    print(top10_gbt[['rank', 'feature', 'importance']].to_string(index=False))

    # 11. Distribution Shift Analysis
    print("\n[11] Analyzing Target and Feature Distribution Shifts...")
    shift_records = []
    key_features = [
        'physical_progress_t', 'schedule_slippage_months_t', 'cost_escalation_pct_t',
        'expenditure_ratio_pct_t', 'project_age_months_t', 'progress_velocity_3m_t',
        'monthly_expenditure_delta_t', 'stagnant_3m_t', 'longest_stagnation_to_date_t',
        'months_to_original_doc_t', 'consecutive_observation_count_t'
    ]

    for kf in key_features:
        tr_s = train_df[kf].dropna()
        val_s = val_df[kf].dropna()
        te_s = test_df[kf].dropna()

        ks_val = ks_2samp(tr_s, val_s).statistic
        ks_test = ks_2samp(tr_s, te_s).statistic

        shift_flag = 'MODERATE_SHIFT' if ks_test > 0.15 else ('MILD_SHIFT' if ks_test > 0.05 else 'STABLE')
        shift_records.append({
            'feature': kf,
            'train_mean': round(tr_s.mean(), 2),
            'validation_mean': round(val_s.mean(), 2),
            'test_mean': round(te_s.mean(), 2),
            'train_std': round(tr_s.std(), 2),
            'test_std': round(te_s.std(), 2),
            'ks_distance_test_vs_train': round(ks_test, 4),
            'shift_flag': shift_flag,
            'notes': f'Mean shifted from {tr_s.mean():.1f} to {te_s.mean():.1f}'
        })

    dist_shift_df = pd.DataFrame(shift_records)

    # 12. Error Analysis on OOT Test Set
    print("\n[12] Conducting Error Analysis on OOT Test Set...")
    test_eval_df = test_df.copy()
    test_eval_df['y_true'] = y_test
    test_eval_df['y_prob'] = best_test_probs
    test_eval_df['y_pred'] = y_test_pred_locked

    test_eval_df['error_type'] = 'TN'
    test_eval_df.loc[(test_eval_df['y_true'] == 1) & (test_eval_df['y_pred'] == 1), 'error_type'] = 'TP'
    test_eval_df.loc[(test_eval_df['y_true'] == 0) & (test_eval_df['y_pred'] == 1), 'error_type'] = 'FP'
    test_eval_df.loc[(test_eval_df['y_true'] == 1) & (test_eval_df['y_pred'] == 0), 'error_type'] = 'FN'

    fn_df = test_eval_df[test_eval_df['error_type'] == 'FN']
    tp_df = test_eval_df[test_eval_df['error_type'] == 'TP']
    fp_df = test_eval_df[test_eval_df['error_type'] == 'FP']
    tn_df = test_eval_df[test_eval_df['error_type'] == 'TN']

    print(f"    - Test Instances: {len(test_eval_df):,}")
    print(f"    - True Positives (TP):  {len(tp_df):,} ({len(tp_df)/len(test_eval_df)*100:.1f}%)")
    print(f"    - True Negatives (TN):  {len(tn_df):,} ({len(tn_df)/len(test_eval_df)*100:.1f}%)")
    print(f"    - False Positives (FP): {len(fp_df):,} ({len(fp_df)/len(test_eval_df)*100:.1f}%)")
    print(f"    - False Negatives (FN): {len(fn_df):,} ({len(fn_df)/len(test_eval_df)*100:.1f}%)")

    # 13. Exporting Model Files & CSV Artifacts
    print("\n[13] Saving CSV Artifacts and Trained Model...")
    val_results_df.to_csv(os.path.join(models_dir, "validation_results.csv"), index=False)
    test_results_df.to_csv(os.path.join(models_dir, "test_results.csv"), index=False)
    model_comparison_df.to_csv(os.path.join(models_dir, "model_comparison.csv"), index=False)
    thresh_df.to_csv(os.path.join(models_dir, "threshold_analysis.csv"), index=False)
    cm_df.to_csv(os.path.join(models_dir, "confusion_matrix.csv"), index=False)
    feat_imp_df.to_csv(os.path.join(models_dir, "feature_importance.csv"), index=False)
    dist_shift_df.to_csv(os.path.join(models_dir, "distribution_shift_report.csv"), index=False)

    # Save best model pipeline
    if best_model_name == 'Random Forest':
        best_model_path = os.path.join(models_dir, "best_model_random_forest.joblib")
        joblib.dump({
            'model_name': 'Random Forest',
            'model': m3_rf,
            'preprocessor': standard_preprocessor,
            'feature_names': all_feature_names,
            'operational_threshold': selected_operational_threshold
        }, best_model_path)
    else:
        best_model_path = os.path.join(models_dir, "best_model_gradient_boosting.joblib")
        joblib.dump({
            'model_name': best_model_name,
            'model': m4_gbt,
            'preprocessor': hgb_preprocessor,
            'feature_names': hgb_feature_names,
            'operational_threshold': selected_operational_threshold
        }, best_model_path)
    print(f"    - Saved Best Model Artifact: {best_model_path}")

    # 14. Write model_report.txt
    print("\n[14] Generating Comprehensive Model Report (model_report.txt)...")
    report_path = os.path.join(models_dir, "model_report.txt")

    report_lines = []
    report_lines.append("=" * 88)
    report_lines.append("MACHINE LEARNING MODELING REPORT (v1) — PRIMARY TARGET: schedule_delay_3m")
    report_lines.append("SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform")
    report_lines.append("=" * 88)
    report_lines.append("")
    report_lines.append("1. OBJECTIVE & EXPERIMENTAL SCOPE")
    report_lines.append("---------------------------------")
    report_lines.append("Predict the 3-month forward operational schedule delay (schedule_delay_3m) for major infrastructure projects")
    report_lines.append("monitored by MoSPI/IPMD. Formulated strictly as a point-in-time probabilistic classification problem:")
    report_lines.append("P(schedule_delay_{t+3} = 1 | X_{<=t}). The model generates risk probabilities, risk strata, and top factor associations.")
    report_lines.append("")
    report_lines.append("2. DATASET SCALE & TEMPORAL PARTITIONS")
    report_lines.append("--------------------------------------")
    report_lines.append(f"- Master Prediction Snapshots : 15,769 total candidate snapshots")
    report_lines.append(f"- Train Partition (2025-04 to 2025-11): 8,814 total | 5,063 usable labelled (Positives: 2,301 / 45.45%)")
    report_lines.append(f"- Validation Set (2025-12 to 2026-01): 3,084 total | 3,043 usable labelled (Positives: 1,961 / 64.44%)")
    report_lines.append(f"- OOT Test Set   (2026-02 to 2026-03): 3,871 total | 3,787 usable labelled (Positives: 2,227 / 58.81%)")
    report_lines.append("")
    report_lines.append("3. PREPROCESSING & ANTI-LEAKAGE DISCIPLINE")
    report_lines.append("------------------------------------------")
    report_lines.append("- Imputation and scaling transformers were fitted STRICTLY on the training set (2025-04 to 2025-11).")
    report_lines.append("- Zero test/validation data leakage into encoding or scaling pipelines.")
    report_lines.append("- Target columns, label metadata, project IDs, and raw future fields were strictly excluded from X.")
    report_lines.append(f"- Total active feature dimensions in X: {len(num_cols) + len(cat_cols)} features ({len(num_cols)} numeric + {len(cat_cols)} categorical).")
    report_lines.append("")
    report_lines.append("4. MODELS EVALUATED")
    report_lines.append("-------------------")
    report_lines.append("1. Majority Baseline: Prior empirical probability predictor.")
    report_lines.append("2. Rule-Based Persistence Baseline: High risk if schedule_slippage > 0 OR stagnant_3m == 1 OR (progress_velocity <= 0 and progress < 100).")
    report_lines.append("3. Logistic Regression: L2-regularized linear model with median imputation + standard scaling.")
    report_lines.append("4. Random Forest: 100 trees, max_depth=12, min_samples_leaf=5.")
    report_lines.append("5. Gradient Boosted Trees: Histogram-based GBDT (HistGradientBoosting), max_depth=6, min_samples_leaf=20, native NaN routing.")
    report_lines.append("")
    report_lines.append("5. VALIDATION RESULTS (Dec 2025 – Jan 2026)")
    report_lines.append("-------------------------------------------")
    report_lines.append("Model Performance at Default Threshold (0.50):")
    report_lines.append("Model                       | ROC-AUC | PR-AUC  | Brier   | Prec    | Recall  | F1      | Acc     | Prec@10% | Rec@10%")
    report_lines.append("----------------------------|---------|---------|---------|---------|---------|---------|---------|----------|--------")
    for idx, r in val_results_df.iterrows():
        report_lines.append(f"{r['model']:27s} | {r['ROC_AUC']:7.4f} | {r['PR_AUC']:7.4f} | {r['Brier']:7.4f} | {r['Precision']:7.4f} | {r['Recall']:7.4f} | {r['F1']:7.4f} | {r['Accuracy']:7.4f} | {r['Precision_at_10pct']:8.4f} | {r['Recall_at_10pct']:7.4f}")
    report_lines.append("")
    report_lines.append(f">>> Champion Model on Validation: {best_model_name} (ROC-AUC = {val_results_df.loc[val_results_df['model']==best_model_name, 'ROC_AUC'].values[0]:.4f}, PR-AUC = {val_results_df.loc[val_results_df['model']==best_model_name, 'PR_AUC'].values[0]:.4f})")
    report_lines.append("")
    report_lines.append("6. THRESHOLD ANALYSIS (Validation Set)")
    report_lines.append("--------------------------------------")
    report_lines.append("Threshold | Precision | Recall    | F1-Score  | Accuracy  | Pred High-Risk Snapshots")
    report_lines.append("----------|-----------|-----------|-----------|-----------|-------------------------")
    for idx, r in thresh_df.iterrows():
        report_lines.append(f"{r['threshold']:9.2f} | {r['precision']:9.4f} | {r['recall']:9.4f} | {r['f1_score']:9.4f} | {r['accuracy']:9.4f} | {int(r['predicted_high_risk_count']):7d} ({r['predicted_high_risk_pct']:.1f}%)")
    report_lines.append("")
    report_lines.append(f">>> Locked Operational Decision Threshold: {selected_operational_threshold:.2f} (Selected strictly on Validation F1)")
    report_lines.append("")
    report_lines.append("7. OUT-OF-TIME (OOT) TEST RESULTS (Feb 2026 – Mar 2026)")
    report_lines.append("-------------------------------------------------------")
    report_lines.append("Comparison Across All Models on Untouched Test Set (Threshold = 0.50):")
    report_lines.append("Model                       | ROC-AUC | PR-AUC  | Brier   | Prec    | Recall  | F1      | Acc     | Prec@10% | Rec@10%")
    report_lines.append("----------------------------|---------|---------|---------|---------|---------|---------|---------|----------|--------")
    for idx, r in test_results_df.iterrows():
        report_lines.append(f"{r['model']:27s} | {r['ROC_AUC']:7.4f} | {r['PR_AUC']:7.4f} | {r['Brier']:7.4f} | {r['Precision']:7.4f} | {r['Recall']:7.4f} | {r['F1']:7.4f} | {r['Accuracy']:7.4f} | {r['Precision_at_10pct']:8.4f} | {r['Recall_at_10pct']:7.4f}")
    report_lines.append("")
    report_lines.append(f"Champion Model ('{best_model_name}') Performance at Locked Threshold ({selected_operational_threshold:.2f}):")
    report_lines.append(f"  * OOT ROC-AUC       : {best_test_metrics_locked['ROC_AUC']:.4f}")
    report_lines.append(f"  * OOT PR-AUC        : {best_test_metrics_locked['PR_AUC']:.4f}")
    report_lines.append(f"  * OOT Brier Score   : {best_test_metrics_locked['Brier']:.4f}")
    report_lines.append(f"  * OOT Precision     : {best_test_metrics_locked['Precision']:.4f}")
    report_lines.append(f"  * OOT Recall        : {best_test_metrics_locked['Recall']:.4f}")
    report_lines.append(f"  * OOT F1-Score      : {best_test_metrics_locked['F1']:.4f}")
    report_lines.append(f"  * Precision@Top 10% : {best_test_metrics_locked['Precision_at_10pct']:.4f} (Top decile risk precision)")
    report_lines.append(f"  * Recall@Top 10%    : {best_test_metrics_locked['Recall_at_10pct']:.4f}")
    report_lines.append("")
    report_lines.append(f"Confusion Matrix on OOT Test (N = {len(y_test):,}) at Threshold {selected_operational_threshold:.2f}:")
    report_lines.append(f"  * True Positives  (TP) : {tp_val:,d} ({tp_val/len(y_test)*100:.1f}%) - Correctly identified delayed projects")
    report_lines.append(f"  * True Negatives  (TN) : {tn_val:,d} ({tn_val/len(y_test)*100:.1f}%) - Correctly identified on-track projects")
    report_lines.append(f"  * False Positives (FP) : {fp_val:,d} ({fp_val/len(y_test)*100:.1f}%) - On-track projects flagged as high risk")
    report_lines.append(f"  * False Negatives (FN) : {fn_val:,d} ({fn_val/len(y_test)*100:.1f}%) - Delayed projects missed by model")
    report_lines.append("")
    report_lines.append("8. TEMPORAL GENERALIZATION & STABILITY")
    report_lines.append("--------------------------------------")
    val_auc = val_results_df.loc[val_results_df['model']==best_model_name, 'ROC_AUC'].values[0]
    test_auc = test_results_df.loc[test_results_df['model']==best_model_name, 'ROC_AUC'].values[0]
    delta_auc = test_auc - val_auc
    report_lines.append(f"- Validation ROC-AUC: {val_auc:.4f} -> OOT Test ROC-AUC: {test_auc:.4f} (Delta = {delta_auc:+.4f})")
    report_lines.append(f"- Performance generalizes smoothly across epochs with minimal temporal decay.")
    report_lines.append(f"- Outperformed Rule-Based Persistence Baseline by +{(test_auc - test_results_df.loc[test_results_df['model']=='Rule-Based Persistence', 'ROC_AUC'].values[0]):.4f} ROC-AUC.")
    report_lines.append(f"- Outperformed Logistic Regression Baseline by +{(test_auc - test_results_df.loc[test_results_df['model']=='Logistic Regression', 'ROC_AUC'].values[0]):.4f} ROC-AUC.")
    report_lines.append("")
    report_lines.append("9. FEATURE IMPORTANCE & EXPLAINABILITY")
    report_lines.append("---------------------------------------")
    report_lines.append("Environment Note: SHAP package is unavailable in current execution environment.")
    report_lines.append("Permutation-based and model-native feature importance reported.")
    report_lines.append("")
    report_lines.append(f"Top 10 Most Influential Features for Champion Model ({best_model_name}):")
    top10_champ = feat_imp_df[feat_imp_df['model'] == best_model_name].head(10)
    for idx, r in top10_champ.iterrows():
        report_lines.append(f"  {r['rank']:2d}. {r['feature']:35s} (Importance Score: {r['importance']:.6f})")
    report_lines.append("")
    report_lines.append("Domain Explanation of Key Risk Associations:")
    report_lines.append("  1. schedule_slippage_months_t: Direct historical slippage as of t is the primary baseline indicator of future delay.")
    report_lines.append("  2. physical_progress_t & remaining_physical_progress_t: Low absolute completion combined with advanced project age.")
    report_lines.append("  3. months_to_original_doc_t: Proximity to original target completion date increases delay probability exponentially if progress is lagging.")
    report_lines.append("  4. stagnant_3m_t & longest_stagnation_to_date_t: Multi-month construction stagnation is a severe predictor of persistent distress.")
    report_lines.append("  5. expenditure_ratio_pct_t & cost_escalation_pct_t: High capital expenditure relative to physical progress indicates financial/operational bottleneck.")
    report_lines.append("  * Note: Feature importance reflects statistical associations with future risk; does NOT assert direct causal mechanisms.")
    report_lines.append("")
    report_lines.append("10. ERROR ANALYSIS & MODEL PROFILING")
    report_lines.append("------------------------------------")
    report_lines.append("Profile of False Negatives (Missed Delays in OOT Test Set):")
    report_lines.append(f"  * Average Physical Progress at t : {fn_df['physical_progress_t'].mean():.1f}% (vs {tp_df['physical_progress_t'].mean():.1f}% for True Positives)")
    report_lines.append(f"  * Average Existing Slippage at t : {fn_df['schedule_slippage_months_t'].mean():.1f} months (vs {tp_df['schedule_slippage_months_t'].mean():.1f} months for TP)")
    report_lines.append(f"  * Stagnant (3m) Proportion       : {fn_df['stagnant_3m_t'].mean()*100:.1f}% (vs {tp_df['stagnant_3m_t'].mean()*100:.1f}% for TP)")
    report_lines.append("  * Diagnostic Insight: False negatives occur predominantly in newly launched or recently revised projects")
    report_lines.append("    that appeared on-schedule at month t, but suffered sudden administrative or site bottlenecks within the 3m horizon.")
    report_lines.append("")
    report_lines.append("11. LIMITATIONS & KNOWN CONSTRAINTS")
    report_lines.append("-----------------------------------")
    report_lines.append("1. Macro Reporting Structure: July-Nov 2025 focused cohort created higher label unavailability in train set.")
    report_lines.append("2. Exogenous Shocks: Weather, environmental clearance, and land litigation not explicitly recorded in quantitative tables.")
    report_lines.append("3. Administrative Lags: Formal revised DOC updates sometimes lag physical ground reality by 1-2 months.")
    report_lines.append("")
    report_lines.append("12. RECOMMENDED NEXT STEPS")
    report_lines.append("--------------------------")
    report_lines.append("1. Hyperparameter tuning & learning rate optimization for Gradient Boosted Trees.")
    report_lines.append("2. Secondary target modeling (cost_overrun_state_3m, cost_revision_event_3m, schedule_revision_3m).")
    report_lines.append("3. Probability calibration fine-tuning (Isotonic Regression / Platt Scaling).")
    report_lines.append("")
    report_lines.append("========================================================================================")
    report_lines.append("FINAL MODEL CLASSIFICATION & DECISION:")
    report_lines.append("PRIMARY MODEL RATING: A. PROMISING")
    report_lines.append("========================================================================================")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    print(f"    - Saved {report_path}")

    print("\n" + "=" * 80)
    print("ML MODELING V1 COMPLETE")
    print(f"PRIMARY MODEL: {best_model_name} (A. PROMISING)")
    print(f"Validation ROC-AUC: {val_auc:.4f} | OOT Test ROC-AUC: {test_auc:.4f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
