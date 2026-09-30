import pytest
import pandas as pd
from ml.predict import MSMERiskPredictor, predict_msme_risk
from ml.config import RISK_BANDS, MSME_DATA_PATH

@pytest.fixture
def predictor():
    return MSMERiskPredictor()

@pytest.fixture
def sample_msme_record():
    return {
        "msme_id": "MSME_TEST_001",
        "sector": "Retail Trade",
        "region": "Urban",
        "gender": "Female",
        "thin_file_status": 0,
        "business_vintage_years": 8,
        "annual_turnover": 4500000.0,
        "monthly_revenue": 375000.0,
        "monthly_expenses": 280000.0,
        "existing_debt": 500000.0,
        "gst_regularity": 0.92,
        "digital_payment_share": 0.85,
        "bank_inflow": 380000.0,
        "utility_payment_timeliness": 0.95,
        "requested_loan_amount": 1000000.0
    }

def test_prediction_output_structure_and_bounds(predictor, sample_msme_record):
    res = predictor.predict_single(sample_msme_record)
    
    assert "msme_id" in res
    assert res["msme_id"] == "MSME_TEST_001"
    assert "pd" in res
    assert "risk_band" in res
    assert "model_version" in res
    
    # Check PD bounds
    assert 0.0 <= res["pd"] <= 1.0, f"PD output {res['pd']} is out of [0, 1] range."

def test_prediction_valid_risk_band(predictor, sample_msme_record):
    res = predictor.predict_single(sample_msme_record)
    valid_bands = [b["name"] for b in RISK_BANDS]
    assert res["risk_band"] in valid_bands, f"Risk band '{res['risk_band']}' is not a valid configurable band."

def test_missing_or_partial_input_handled_gracefully(predictor):
    minimal_record = {
        "msme_id": "MSME_MINIMAL_01",
        "sector": "Services",
        "region": "Rural",
        "annual_turnover": 1000000.0
    }
    res = predictor.predict_single(minimal_record)
    assert "pd" in res
    assert 0.0 <= res["pd"] <= 1.0
    assert "risk_band" in res

def test_convenience_predict_function(sample_msme_record):
    res = predict_msme_risk(sample_msme_record)
    assert res["msme_id"] == "MSME_TEST_001"
    assert 0.0 <= res["pd"] <= 1.0

def test_batch_prediction(predictor):
    df_sample = pd.read_csv(MSME_DATA_PATH).head(10)
    df_res = predictor.predict_batch(df_sample)
    
    assert 'pd' in df_res.columns
    assert 'risk_band' in df_res.columns
    assert (df_res['pd'] >= 0.0).all() and (df_res['pd'] <= 1.0).all()
    assert len(df_res) == 10
