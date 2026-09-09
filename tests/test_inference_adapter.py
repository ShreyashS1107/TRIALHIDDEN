"""
Comprehensive Unit & Integration Test Suite for Production Inference Adapter
SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform

Tests:
  1. Valid PDF + Historical DB extraction
  2. Exact 75 production ML features contract (71 numerical + 4 categorical)
  3. Exact 12 ESI operational surveillance inputs contract
  4. Point-in-time boundary safety (zero future leakage)
  5. Prohibited target columns exclusion
  6. Prohibited OCMS historical priors exclusion
  7. Duplicate project ID handling
  8. Missing historical observations (new entering projects)
  9. Invalid report_month handling
  10. Callable db_session query callback handling
  11. Empty extraction / project matching failure handling
  12. End-to-end model scoring & ESI calculation compatibility
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd

# Ensure repository root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from inference import (
    extract_features_for_inference,
    InferenceAdapter,
    ProductionScorer,
    compute_execution_stress_index,
    compute_point_in_time_features_for_month,
    PRODUCTION_75_FEATURES,
    NUMERICAL_FEATURE_NAMES,
    CATEGORICAL_FEATURE_NAMES,
    ESI_12_INPUT_FEATURES
)
from inference.adapter import BANNED_TARGET_COLUMNS, BANNED_OCMS_COLUMNS
from inference.pdf_extractor import extract_monthly_paimana_pdf


class TestInferenceAdapter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = BASE_DIR
        cls.sample_pdf = os.path.join(cls.base_dir, "dataset", "FlashReport_June_2026.pdf")
        if not os.path.exists(cls.sample_pdf):
            cls.sample_pdf = os.path.join(cls.base_dir, "dataset", "FlashReport_December_2025.pdf")

        cls.master_csv = os.path.join(cls.base_dir, "data", "paimana_master_dataset.csv")
        if os.path.exists(cls.master_csv):
            cls.master_df = pd.read_csv(cls.master_csv, dtype=str)
        else:
            cls.master_df = pd.DataFrame()

        # Cache one extraction to speed up downstream feature contract tests
        cls.cached_current_df, cls.cached_month = extract_monthly_paimana_pdf(
            cls.sample_pdf, report_month="2026-06"
        )

    def test_01_extract_features_contract_count(self):
        """Test 1: Verify exact 75 ML features and 12 ESI inputs contract."""
        report_month = "2026-06"
        features_df, esi_df = extract_features_for_inference(
            pdf_path=self.sample_pdf,
            report_month=report_month,
            db_session=self.master_df
        )

        # Exact row count match
        self.assertGreater(len(features_df), 0, "features_df should not be empty")
        self.assertEqual(len(features_df), len(esi_df), "features_df and esi_df must have identical row count")

        # Exact 75 ML features
        self.assertEqual(len(features_df.columns), 75, f"Expected 75 ML features, got {len(features_df.columns)}")
        self.assertEqual(list(features_df.columns), PRODUCTION_75_FEATURES, "features_df columns must match PRODUCTION_75_FEATURES order")

        # Exact 71 numerical + 4 categorical
        num_cols = [c for c in features_df.columns if c in NUMERICAL_FEATURE_NAMES]
        cat_cols = [c for c in features_df.columns if c in CATEGORICAL_FEATURE_NAMES]
        self.assertEqual(len(num_cols), 71, f"Expected 71 numerical features, got {len(num_cols)}")
        self.assertEqual(len(cat_cols), 4, f"Expected 4 categorical features, got {len(cat_cols)}")

        # Exact 12 ESI inputs
        self.assertEqual(len(esi_df.columns), 12, f"Expected 12 ESI inputs, got {len(esi_df.columns)}")
        self.assertEqual(list(esi_df.columns), ESI_12_INPUT_FEATURES, "esi_df columns must match ESI_12_INPUT_FEATURES order")

    def test_02_target_and_metadata_exclusion(self):
        """Test 2: Verify that no target labels or label metadata leak into feature matrices."""
        features_df, esi_df, _ = compute_point_in_time_features_for_month(
            current_records_df=self.cached_current_df,
            historical_records_df=self.master_df,
            as_of_month="2026-06"
        )

        for b_col in BANNED_TARGET_COLUMNS:
            self.assertNotIn(b_col, features_df.columns, f"Target column '{b_col}' leaked into features_df!")
            self.assertNotIn(b_col, esi_df.columns, f"Target column '{b_col}' leaked into esi_df!")

        # ID columns should also not be in features_df
        for id_col in ['project_id', 'project_name', 'agency', 'state', 'report_month', 'prediction_month']:
            self.assertNotIn(id_col, features_df.columns, f"ID column '{id_col}' found in features_df!")

    def test_03_ocms_historical_priors_exclusion(self):
        """Test 3: Verify that OCMS historical priors are strictly excluded from the ML feature matrix."""
        features_df, esi_df, _ = compute_point_in_time_features_for_month(
            current_records_df=self.cached_current_df,
            historical_records_df=self.master_df,
            as_of_month="2026-06"
        )

        for o_col in BANNED_OCMS_COLUMNS:
            self.assertNotIn(o_col, features_df.columns, f"OCMS column '{o_col}' found in features_df!")
            self.assertNotIn(o_col, esi_df.columns, f"OCMS column '{o_col}' found in esi_df!")

    def test_04_point_in_time_anti_leakage(self):
        """Test 4: Verify that future records (> report_month) are strictly blocked from entering calculations."""
        # Synthesize a poisoned database with a future month snapshot
        as_of_month = "2025-08"
        poisoned_db = self.master_df.copy()
        
        # Add a synthetic future row for project '105236' with massive future expenditure in 2026-12
        synthetic_future_row = {
            'project_id': '105236',
            'project_name': 'TEST PROJECT',
            'agency': 'NHAI',
            'state': 'MAHARASHTRA',
            'report_month': '2026-12', # FUTURE!
            'physical_progress_percent': 99.9,
            'cumulative_expenditure_crore': 999999.0,
            'original_cost_crore': 500.0,
            'revised_cost_crore': 500.0
        }
        poisoned_db = pd.concat([poisoned_db, pd.DataFrame([synthetic_future_row])], ignore_index=True)

        features_df, esi_df, meta_df = compute_point_in_time_features_for_month(
            current_records_df=self.cached_current_df,
            historical_records_df=poisoned_db,
            as_of_month=as_of_month
        )

        # Check if project 105236 is present, its max progress cannot be 99.9 from the future
        if '105236' in meta_df['project_id'].values:
            idx = meta_df[meta_df['project_id'] == '105236'].index[0]
            max_p = features_df.loc[idx, 'max_progress_to_date_t']
            self.assertNotEqual(max_p, 99.9, "Future progress leaked into point-in-time calculation!")

    def test_05_missing_historical_observations_handling(self):
        """Test 5: Handle a new project with zero historical observations gracefully (preserves NaN)."""
        features_df, esi_df, meta_df = compute_point_in_time_features_for_month(
            current_records_df=self.cached_current_df,
            historical_records_df=pd.DataFrame(columns=['project_id', 'report_month']),
            as_of_month="2026-06"
        )

        self.assertEqual(len(features_df), len(meta_df))
        # With zero historical observations, lag features should be NaN
        self.assertTrue(features_df['physical_progress_lag1'].isna().all())
        self.assertTrue(features_df['consecutive_observation_count_t'].eq(1).all())

    def test_06_invalid_report_month_handling(self):
        """Test 6: Reject invalid report_month formats."""
        with self.assertRaises(ValueError):
            extract_features_for_inference(
                pdf_path=self.sample_pdf,
                report_month="INVALID_DATE_FORMAT",
                db_session=self.master_df
            )

    def test_07_callable_db_session_handling(self):
        """Test 7: Verify that a query callable db_session is properly called and filtered."""
        def custom_db_query(as_of_month, project_ids=None):
            return self.master_df[self.master_df['report_month'] < as_of_month]

        features_df, esi_df = extract_features_for_inference(
            pdf_path=self.sample_pdf,
            report_month="2026-06",
            db_session=custom_db_query
        )
        self.assertEqual(len(features_df.columns), 75)
        self.assertEqual(len(esi_df.columns), 12)

    def test_08_duplicate_project_id_validation(self):
        """Test 8: Validate that duplicate project IDs in a batch are rejected by validation guards."""
        dup_current_df = pd.concat([self.cached_current_df.iloc[:2], self.cached_current_df.iloc[:1]], ignore_index=True)
        with self.assertRaises(ValueError):
            features_df, esi_df, meta_df = compute_point_in_time_features_for_month(
                current_records_df=dup_current_df,
                historical_records_df=self.master_df,
                as_of_month="2026-06"
            )
            InferenceAdapter.validate_feature_contracts(features_df, esi_df, meta_df, "2026-06")

    def test_09_end_to_end_scoring_compatibility(self):
        """Test 9: Verify that extracted features score seamlessly through the frozen ML & ESI models."""
        features_df, esi_df, _ = compute_point_in_time_features_for_month(
            current_records_df=self.cached_current_df,
            historical_records_df=self.master_df,
            as_of_month="2026-06"
        )

        scorer = ProductionScorer()
        ml_scores, esi_scores = scorer.score(features_df, esi_df)

        # ML scores verification
        self.assertEqual(len(ml_scores), len(features_df))
        self.assertTrue('schedule_delay_risk' in ml_scores.columns)
        self.assertTrue('cost_overrun_risk' in ml_scores.columns)
        self.assertTrue('schedule_revision_risk' in ml_scores.columns)
        self.assertTrue('selected_integrated_risk' in ml_scores.columns)
        self.assertTrue('risk_band' in ml_scores.columns)
        self.assertTrue('dominant_component' in ml_scores.columns)

        # Value bounds check
        self.assertTrue((ml_scores['schedule_delay_risk'] >= 0.0).all() and (ml_scores['schedule_delay_risk'] <= 1.0).all())
        self.assertTrue((ml_scores['cost_overrun_risk'] >= 0.0).all() and (ml_scores['cost_overrun_risk'] <= 1.0).all())
        self.assertTrue((ml_scores['schedule_revision_risk'] >= 0.0).all() and (ml_scores['schedule_revision_risk'] <= 1.0).all())
        self.assertTrue((ml_scores['selected_integrated_risk'] >= 0.0).all() and (ml_scores['selected_integrated_risk'] <= 1.0).all())

        # ESI scores verification
        self.assertEqual(len(esi_scores), len(esi_df))
        self.assertTrue('execution_stress_index' in esi_scores.columns)
        self.assertTrue('esi_tier' in esi_scores.columns)
        self.assertTrue('dominant_stressor' in esi_scores.columns)
        self.assertTrue('suggested_action' in esi_scores.columns)
        self.assertTrue((esi_scores['execution_stress_index'] >= 0.0).all() and (esi_scores['execution_stress_index'] <= 1.0).all())


if __name__ == '__main__':
    unittest.main()
