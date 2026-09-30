import pytest
import pandas as pd
from ml.explain import explain_borrower, MSMEExplainer, get_explainer
from ml.config import MSME_DATA_PATH

@pytest.fixture
def sample_msme_id():
    return "MSME_001"

@pytest.fixture
def sample_record():
    return {
        "msme_id": "MSME_TEST_XAI",
        "sector": "Retail Trade",
        "region": "Rural",
        "gender": "Female",
        "thin_file_status": 1,
        "business_vintage_years": 3,
        "annual_turnover": 2000000.0,
        "monthly_revenue": 160000.0,
        "monthly_expenses": 140000.0,
        "existing_debt": 800000.0,
        "gst_regularity": 0.50,
        "digital_payment_share": 0.25,
        "bank_inflow": 150000.0,
        "utility_payment_timeliness": 0.60,
        "requested_loan_amount": 600000.0
    }

def test_explain_borrower_output_contract(sample_record):
    res = explain_borrower(sample_record)
    
    assert "msme_id" in res
    assert "pd" in res
    assert "risk_band" in res
    assert "decision_policy" in res
    assert res["decision_policy"]["threshold"] == 0.20
    
    assert "risk_increasing_factors" in res
    assert "risk_reducing_factors" in res
    assert "borrower_guidance" in res
    assert "counterfactual" in res
    assert "explanation_stability" in res

def test_risk_increasing_and_reducing_separation(sample_record):
    res = explain_borrower(sample_record)
    
    for inc in res["risk_increasing_factors"]:
        assert inc["direction"] == "risk_increasing"
        assert inc["contribution"] > 0
        assert "reason_code" in inc
        
    for red in res["risk_reducing_factors"]:
        assert red["direction"] == "risk_reducing"
        assert red["contribution"] < 0
        assert "reason_code" in red

def test_protected_attributes_unaltered_by_counterfactual(sample_record):
    res = explain_borrower(sample_record)
    cf = res["counterfactual"]
    
    assert cf["available"] is True
    # Ensure no change modified gender or region
    for change in cf["changes"]:
        assert change["feature"] not in ["gender", "region"], "Illegal modification of protected attribute!"

def test_no_unsupported_causal_promises(sample_record):
    res = explain_borrower(sample_record)
    cf_disclaimer = res["counterfactual"]["disclaimer"].lower()
    
    assert "guarantee" in cf_disclaimer or "does not guarantee" in cf_disclaimer
    assert "causes" not in cf_disclaimer

def test_global_feature_importance():
    explainer = get_explainer()
    global_factors = explainer.get_global_feature_importance()
    
    assert len(global_factors) > 0
    for factor in global_factors:
        assert "feature" in factor
        assert "coefficient" in factor
        assert "direction" in factor
        assert "statement" in factor

def test_explanation_handles_missing_data():
    minimal_record = {
        "msme_id": "MSME_PARTIAL",
        "sector": "Services",
        "region": "Urban",
        "annual_turnover": 1500000.0
    }
    res = explain_borrower(minimal_record)
    assert "pd" in res
    assert "risk_increasing_factors" in res
    assert "counterfactual" in res
