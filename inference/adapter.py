"""
Production PDF → Features Inference Adapter
SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform

Authoritative Production Bridge:
  New PAIMANA PDF + report_month + PostgreSQL project/history data
  ↓
  exact 75 production ML features (71 Numerical + 4 Categorical)
  +
  exact 12 ESI input features

Public Interface:
  extract_features_for_inference(pdf_path, report_month, db_session) -> tuple[pd.DataFrame, pd.DataFrame]
"""

import os
import re
import pandas as pd
import numpy as np

# This ensures the inference package is initialized and ai-ml/ is in sys.path
import inference

from inference.pdf_extractor import extract_monthly_paimana_pdf
from inference.data_access import fetch_historical_project_snapshots
from inference.feature_engine import (
    compute_point_in_time_features_for_month,
    PRODUCTION_75_FEATURES,
    NUMERICAL_FEATURE_NAMES,
    CATEGORICAL_FEATURE_NAMES,
    ESI_12_INPUT_FEATURES,
    RAW_DATE_STRINGS
)

# Prohibited Target & Metadata Columns
from ml.inference.contracts import KNOWN_TARGET_COLUMNS as BANNED_TARGET_COLUMNS

# Prohibited OCMS Historical Priors (Banned from Production ML Feature Matrix)
BANNED_OCMS_COLUMNS = [
    'historical_mean_cost_escalation_pct',
    'historical_mean_delay_months',
    'historical_completion_rate_pct',
    'agency_historical_delay_rate',
    'sector_historical_cost_escalation',
    'ocms_historical_observation_months'
]


class InferenceAdapter:
    """
    Production-grade AI/ML inference adapter for processing new monthly PAIMANA Flash Report PDFs.
    """

    def __init__(self, db_session=None):
        self.db_session = db_session

    def extract_features(
        self,
        pdf_path: str,
        report_month: str = None,
        db_session=None
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Executes end-to-end extraction from a PAIMANA PDF and historical DB records.

        Returns:
            tuple (features_df, esi_df, metadata_df):
                - features_df: DataFrame with exactly 75 production ML features
                - esi_df: DataFrame with exactly 12 ESI input features
                - metadata_df: DataFrame containing project identification & provenance
        """
        active_session = db_session if db_session is not None else self.db_session

        if report_month is not None:
            report_month = str(report_month).strip()[:7]
            if not re.match(r'^\d{4}-\d{2}$', report_month):
                raise ValueError(f"Invalid report_month format: '{report_month}'. Expected 'YYYY-MM'.")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")

        current_df, resolved_month = extract_monthly_paimana_pdf(pdf_path, report_month=report_month)
        
        if current_df is None or len(current_df) == 0:
            raise ValueError(f"No ongoing project records could be extracted from PDF: {pdf_path}")

        project_ids = current_df['project_id'].unique().tolist()
        historical_df = fetch_historical_project_snapshots(
            db_session=active_session,
            as_of_month=resolved_month,
            project_ids=project_ids
        )

        features_df, esi_df, metadata_df = compute_point_in_time_features_for_month(
            current_records_df=current_df,
            historical_records_df=historical_df,
            as_of_month=resolved_month
        )

        self.validate_feature_contracts(features_df, esi_df, metadata_df, resolved_month)

        return features_df, esi_df, metadata_df

    @staticmethod
    def validate_feature_contracts(
        features_df: pd.DataFrame,
        esi_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
        report_month: str
    ) -> None:
        """
        Validates that extracted DataFrames strictly satisfy the production contracts.
        """
        n_rows = len(features_df)
        if len(esi_df) != n_rows or len(metadata_df) != n_rows:
            raise ValueError(
                f"Row count mismatch between features_df ({len(features_df)}), "
                f"esi_df ({len(esi_df)}), and metadata_df ({len(metadata_df)})."
            )

        if len(features_df.columns) != 75:
            raise AssertionError(f"features_df must contain EXACTLY 75 columns, found {len(features_df.columns)}.")

        actual_features = list(features_df.columns)
        if actual_features != PRODUCTION_75_FEATURES:
            missing = set(PRODUCTION_75_FEATURES) - set(actual_features)
            extra = set(actual_features) - set(PRODUCTION_75_FEATURES)
            raise AssertionError(f"features_df columns do not match contract. Missing: {missing}, Extra: {extra}")

        actual_num_cols = [c for c in actual_features if c in NUMERICAL_FEATURE_NAMES]
        actual_cat_cols = [c for c in actual_features if c in CATEGORICAL_FEATURE_NAMES]
        if len(actual_num_cols) != 71:
            raise AssertionError(f"Expected 71 numerical features, found {len(actual_num_cols)}.")
        if len(actual_cat_cols) != 4:
            raise AssertionError(f"Expected 4 categorical features, found {len(actual_cat_cols)}.")

        if len(esi_df.columns) != 12:
            raise AssertionError(f"esi_df must contain EXACTLY 12 columns, found {len(esi_df.columns)}.")

        actual_esi = list(esi_df.columns)
        if actual_esi != ESI_12_INPUT_FEATURES:
            missing_esi = set(ESI_12_INPUT_FEATURES) - set(actual_esi)
            extra_esi = set(actual_esi) - set(ESI_12_INPUT_FEATURES)
            raise AssertionError(f"esi_df columns do not match contract. Missing: {missing_esi}, Extra: {extra_esi}")

        for b_col in BANNED_TARGET_COLUMNS:
            if b_col in features_df.columns or b_col in esi_df.columns:
                raise AssertionError(f"Target column '{b_col}' leaked into feature matrix!")

        for o_col in BANNED_OCMS_COLUMNS:
            if o_col in features_df.columns or o_col in esi_df.columns:
                raise AssertionError(f"Banned OCMS column '{o_col}' found in feature matrix!")

        for d_col in RAW_DATE_STRINGS:
            if d_col in features_df.columns:
                raise AssertionError(f"Raw date string '{d_col}' present in features_df (must remain in metadata only)!")

        if 'project_id' in metadata_df.columns:
            if metadata_df['project_id'].duplicated().any():
                dup_pids = metadata_df.loc[metadata_df['project_id'].duplicated(), 'project_id'].tolist()
                raise ValueError(f"Duplicate project IDs found in extracted batch: {dup_pids[:5]}")


def extract_features_for_inference(
    pdf_path: str,
    report_month: str,
    db_session=None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Authoritative AI/ML Public Interface for Production Inference.

    Parameters:
        pdf_path: Path to the PAIMANA Flash Report PDF file.
        report_month: The target reporting month epoch in 'YYYY-MM' format.
        db_session: Database session abstraction (SQLAlchemy session, DataFrame, or Callable).

    Returns:
        tuple (features_df, esi_df):
            - features_df: DataFrame with EXACTLY 75 production ML features (71 numerical + 4 categorical)
            - esi_df: DataFrame with EXACTLY 12 ESI input features
    """
    adapter = InferenceAdapter(db_session=db_session)
    features_df, esi_df, _ = adapter.extract_features(
        pdf_path=pdf_path,
        report_month=report_month,
        db_session=db_session
    )
    return features_df, esi_df
