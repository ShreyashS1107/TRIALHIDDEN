import os
import sys

# Crucial architectural bridge: ai-ml/ contains hyphens and isn't natively importable.
# By inserting the ai-ml directory itself into sys.path, we enable Python to cleanly
# import its sub-packages like `ml` and `scripts` natively without hacky importlib logic.
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ai_ml_dir = os.path.join(base_dir, "ai-ml")
if ai_ml_dir not in sys.path:
    sys.path.insert(0, ai_ml_dir)

from inference.adapter import extract_features_for_inference, InferenceAdapter

__all__ = ["extract_features_for_inference", "InferenceAdapter"]
