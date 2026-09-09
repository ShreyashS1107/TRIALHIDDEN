"""
Inference Adapter Package
SIH 2026 Problem Statement SIH26103: MoSPI / IPMD Integrated Project-Monitoring Platform

Public API:
  - extract_features_for_inference
  - InferenceAdapter
  - ProductionScorer
  - compute_execution_stress_index
  - PRODUCTION_75_FEATURES
  - ESI_12_INPUT_FEATURES
"""

from inference.adapter import extract_features_for_inference, InferenceAdapter
from inference.feature_engine import (
    compute_point_in_time_features_for_month,
    PRODUCTION_75_FEATURES,
    NUMERICAL_FEATURE_NAMES,
    CATEGORICAL_FEATURE_NAMES,
    ESI_12_INPUT_FEATURES
)
from inference.pdf_extractor import extract_monthly_paimana_pdf
from inference.data_access import fetch_historical_project_snapshots
from inference.scorer import ProductionScorer, compute_execution_stress_index

__all__ = [
    "extract_features_for_inference",
    "InferenceAdapter",
    "ProductionScorer",
    "compute_execution_stress_index",
    "compute_point_in_time_features_for_month",
    "extract_monthly_paimana_pdf",
    "fetch_historical_project_snapshots",
    "PRODUCTION_75_FEATURES",
    "NUMERICAL_FEATURE_NAMES",
    "CATEGORICAL_FEATURE_NAMES",
    "ESI_12_INPUT_FEATURES"
]
