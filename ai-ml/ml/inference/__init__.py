"""
ML Batch Inference Package for SIH26103.

Provides modular offline batch inference capabilities around frozen ML artifacts.
"""

from .contracts import (
    ALL_MODEL_FEATURES,
    BAND_HIGH,
    BAND_LOW,
    BAND_MODERATE,
    BAND_VERY_HIGH,
    DOMINANT_COST_OVERRUN,
    DOMINANT_SCHEDULE_DELAY,
    DOMINANT_SCHEDULE_REVISION,
    KNOWN_TARGET_COLUMNS,
    MODEL_VERSION,
    OUTPUT_COLUMNS,
    REQUIRED_CATEGORICAL_FEATURES,
    REQUIRED_NUMERICAL_FEATURES,
    WEIGHT_COST_OVERRUN,
    WEIGHT_SCHEDULE_DELAY,
    WEIGHT_SCHEDULE_REVISION,
    InferenceError,
    InvalidInputError,
    MissingFeatureError,
    ModelArtifactNotFoundError,
)
from .batch_scorer import BatchScorer

__all__ = [
    "BatchScorer",
    "MODEL_VERSION",
    "REQUIRED_NUMERICAL_FEATURES",
    "REQUIRED_CATEGORICAL_FEATURES",
    "ALL_MODEL_FEATURES",
    "KNOWN_TARGET_COLUMNS",
    "OUTPUT_COLUMNS",
    "WEIGHT_SCHEDULE_DELAY",
    "WEIGHT_COST_OVERRUN",
    "WEIGHT_SCHEDULE_REVISION",
    "BAND_LOW",
    "BAND_MODERATE",
    "BAND_HIGH",
    "BAND_VERY_HIGH",
    "DOMINANT_SCHEDULE_DELAY",
    "DOMINANT_COST_OVERRUN",
    "DOMINANT_SCHEDULE_REVISION",
    "InferenceError",
    "MissingFeatureError",
    "ModelArtifactNotFoundError",
    "InvalidInputError",
]
