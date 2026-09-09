import pandas as pd
from typing import Tuple, List
import importlib.util
import os
import logging

logger = logging.getLogger(__name__)

class MLIntegrationAdapter:
    """
    Validates feature sets returned by the ML pipeline to ensure strict contract adherence
    before passing them to the existing ML scoring engines.
    """
    
    REQUIRED_METADATA = ["project_id", "report_month"]
    
    @classmethod
    def _load_contract_module(cls, module_name: str, file_path: str):
        """
        Safely loads a Python module from a file path without relying on standard imports.
        
        Because `ai-ml` contains a hyphen, it is not a valid Python package identifier.
        Furthermore, the directory lacks a setup.py/pyproject.toml, meaning it cannot be 
        installed as a package natively in the backend environment. 
        
        To avoid polluting sys.path (a path hack) or crashing on heavy ML dependencies 
        (like joblib/scikit-learn) imported by ai-ml's __init__.py files, this uses 
        importlib to securely and directly execute the isolated contracts.py file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Canonical contract file not found at {file_path}")
            
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {file_path}")
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @classmethod
    def get_risk_features(cls) -> List[str]:
        mod = cls._load_contract_module('risk_contracts', 'ai-ml/ml/inference/contracts.py')
        return getattr(mod, 'ALL_MODEL_FEATURES')

    @classmethod
    def get_risk_forbidden_targets(cls) -> List[str]:
        mod = cls._load_contract_module('risk_contracts', 'ai-ml/ml/inference/contracts.py')
        return getattr(mod, 'KNOWN_TARGET_COLUMNS')

    @classmethod
    def get_esi_features(cls) -> List[str]:
        mod = cls._load_contract_module('esi_contracts', 'ai-ml/ml/surveillance/contracts.py')
        return getattr(mod, 'REQUIRED_SURVEILLANCE_FEATURES')

    @classmethod
    def get_esi_forbidden_targets(cls) -> List[str]:
        mod = cls._load_contract_module('esi_contracts', 'ai-ml/ml/surveillance/contracts.py')
        return getattr(mod, 'KNOWN_TARGET_COLUMNS')

    @classmethod
    def validate_risk_features(cls, df: pd.DataFrame) -> None:
        if df.empty:
            return
            
        missing_metadata = [m for m in cls.REQUIRED_METADATA if m not in df.columns]
        if missing_metadata:
            raise ValueError(f"Risk features missing required metadata: {missing_metadata}")

        required_features = cls.get_risk_features()
        missing_features = [f for f in required_features if f not in df.columns]
        if missing_features:
            raise ValueError(f"Risk features missing strictly required columns: {missing_features}")
            
        forbidden_targets = cls.get_risk_forbidden_targets()
        leaked_targets = [f for f in forbidden_targets if f in df.columns]
        if leaked_targets:
            raise ValueError(f"Risk features contain forbidden target columns: {leaked_targets}")

    @classmethod
    def validate_esi_features(cls, df: pd.DataFrame) -> None:
        if df.empty:
            return
            
        missing_metadata = [m for m in cls.REQUIRED_METADATA if m not in df.columns]
        if missing_metadata:
            raise ValueError(f"ESI features missing required metadata: {missing_metadata}")

        required_features = cls.get_esi_features()
        missing_features = [f for f in required_features if f not in df.columns]
        if missing_features:
            raise ValueError(f"ESI features missing strictly required columns: {missing_features}")

        forbidden_targets = cls.get_esi_forbidden_targets()
        leaked_targets = [f for f in forbidden_targets if f in df.columns]
        if leaked_targets:
            raise ValueError(f"ESI features contain forbidden target columns: {leaked_targets}")
