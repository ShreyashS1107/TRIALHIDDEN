import pytest
import pandas as pd
from app.services.ml_integration import MLIntegrationAdapter

def test_ml_integration_adapter_valid_risk_features():
    cols = MLIntegrationAdapter.REQUIRED_METADATA + MLIntegrationAdapter.get_risk_features()
    df = pd.DataFrame([["dummy"] * len(cols)], columns=cols)
    MLIntegrationAdapter.validate_risk_features(df)

def test_ml_integration_adapter_missing_risk_features():
    cols = MLIntegrationAdapter.REQUIRED_METADATA + MLIntegrationAdapter.get_risk_features()
    df = pd.DataFrame([["dummy"] * (len(cols)-1)], columns=cols[:-1])
    
    with pytest.raises(ValueError) as exc:
        MLIntegrationAdapter.validate_risk_features(df)
    assert "missing strictly required columns" in str(exc.value)

def test_ml_integration_adapter_forbidden_target_leakage():
    cols = MLIntegrationAdapter.REQUIRED_METADATA + MLIntegrationAdapter.get_risk_features() + ["schedule_delay_3m"]
    df = pd.DataFrame([["dummy"] * len(cols)], columns=cols)
    
    with pytest.raises(ValueError) as exc:
        MLIntegrationAdapter.validate_risk_features(df)
    assert "forbidden target columns" in str(exc.value)

def test_ml_integration_adapter_valid_esi_features():
    cols = MLIntegrationAdapter.REQUIRED_METADATA + MLIntegrationAdapter.get_esi_features()
    df = pd.DataFrame([["dummy"] * len(cols)], columns=cols)
    MLIntegrationAdapter.validate_esi_features(df)

def test_ml_integration_adapter_missing_esi_features():
    df = pd.DataFrame([["P1", "2026-07", 1]], columns=["project_id", "report_month", "stagnant_3m_t"])
    with pytest.raises(ValueError) as exc:
        MLIntegrationAdapter.validate_esi_features(df)
    assert "missing strictly required columns" in str(exc.value)

def test_ml_integration_adapter_contract_alignment():
    """
    Proves the adapter's expected feature list is directly aligned with the canonical ML contract
    without modifying ai-ml, and verifies no hardcoded duplicates exist.
    """
    risk_features = MLIntegrationAdapter.get_risk_features()
    assert len(risk_features) == 75
    assert "project_age_months_t" in risk_features
    assert "project_size_category" in risk_features
    
    esi_features = MLIntegrationAdapter.get_esi_features()
    assert len(esi_features) == 12
    assert "months_since_last_progress_increase_t" in esi_features
    
    # Prove they didn't come from a hardcoded list on the class:
    assert not hasattr(MLIntegrationAdapter, "REQUIRED_RISK_FEATURES")
    assert not hasattr(MLIntegrationAdapter, "REQUIRED_ESI_FEATURES")
