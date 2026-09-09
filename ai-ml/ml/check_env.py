import sys
import os

print("Python version:", sys.version)

for pkg in ["sklearn", "lightgbm", "xgboost", "catboost", "shap", "joblib"]:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "unknown")
        print(f"{pkg}: AVAILABLE (version {ver})")
    except Exception as e:
        print(f"{pkg}: NOT available ({type(e).__name__}: {e})")
