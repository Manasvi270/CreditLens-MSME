import pytest
from ml.stress_testing import run_stress_test, get_stress_engine, SCENARIO_PRESETS
from ml.config import RISK_BANDS

@pytest.fixture
def sample_msme_id():
    return "MSME_001"

@pytest.fixture
def stress_engine():
    return get_stress_engine()

def test_baseline_scenario_preserves_values(sample_msme_id):
    res = run_stress_test(sample_msme_id, 0.0, 0.0, 0, 0.0)
    
    assert res["risk"]["pd_change"] == 0.0
    assert res["risk"]["baseline_pd"] == res["risk"]["stressed_pd"]
    assert res["loan"]["baseline_emi"] == res["loan"]["stressed_emi"]
    assert res["expected_loss"]["baseline_el"] == res["expected_loss"]["stressed_el"]

def test_input_cost_inflation_reduces_net_cashflow(sample_msme_id):
    base_res = run_stress_test(sample_msme_id, 0.0, 0.0, 0, 0.0)
    cost_res = run_stress_test(sample_msme_id, 0.0, 0.15, 0, 0.0)
    
    assert cost_res["cashflow"]["stressed_avg_net_cashflow"] < base_res["cashflow"]["baseline_avg_net_cashflow"]

def test_demand_reduction_reduces_net_cashflow(sample_msme_id):
    base_res = run_stress_test(sample_msme_id, 0.0, 0.0, 0, 0.0)
    dem_res = run_stress_test(sample_msme_id, -0.15, 0.0, 0, 0.0)
    
    assert dem_res["cashflow"]["stressed_avg_net_cashflow"] < base_res["cashflow"]["baseline_avg_net_cashflow"]

def test_receivable_delay_reduces_cashflow(sample_msme_id):
    base_res = run_stress_test(sample_msme_id, 0.0, 0.0, 0, 0.0)
    del_res = run_stress_test(sample_msme_id, 0.0, 0.0, 30, 0.0)
    
    assert del_res["cashflow"]["stressed_avg_net_cashflow"] <= base_res["cashflow"]["baseline_avg_net_cashflow"]

def test_interest_rate_hike_increases_emi(sample_msme_id):
    base_res = run_stress_test(sample_msme_id, 0.0, 0.0, 0, 0.0)
    rate_res = run_stress_test(sample_msme_id, 0.0, 0.0, 0, 2.0)
    
    assert rate_res["loan"]["stressed_emi"] > base_res["loan"]["baseline_emi"]

def test_pd_and_band_validity(sample_msme_id):
    res = run_stress_test(sample_msme_id, -0.20, 0.20, 30, 2.0)
    
    assert 0.0 <= res["risk"]["stressed_pd"] <= 1.0
    valid_bands = [b["name"] for b in RISK_BANDS]
    assert res["risk"]["stressed_band"] in valid_bands

def test_expected_loss_non_negative(sample_msme_id):
    res = run_stress_test(sample_msme_id, -0.10, 0.10, 15, 1.0)
    assert res["expected_loss"]["stressed_el"] >= 0.0
    assert res["expected_loss"]["baseline_el"] >= 0.0

def test_invalid_parameters_rejected(sample_msme_id):
    with pytest.raises(ValueError):
        run_stress_test(sample_msme_id, demand_change=-0.90)  # Invalid demand < -0.50
        
    with pytest.raises(ValueError):
        run_stress_test(sample_msme_id, input_cost_inflation=1.5)  # Invalid inflation > 0.60

def test_sensitivity_analysis(stress_engine, sample_msme_id):
    sens = stress_engine.run_sensitivity_analysis(sample_msme_id)
    assert "top_dscr_driver" in sens
    assert len(sens["rankings"]) == 4

def test_full_portfolio_stress_test(stress_engine):
    """Verify all ~800 MSMEs can be stress tested cleanly in a portfolio batch run."""
    port_res = stress_engine.run_portfolio_stress_test(
        demand_change=-0.10, input_cost_inflation=0.10,
        receivable_delay_days=15, interest_rate_change=1.0
    )
    
    assert port_res["total_msmes"] >= 750
    assert 0.0 <= port_res["portfolio_metrics"]["avg_stressed_pd"] <= 1.0
    assert port_res["portfolio_metrics"]["total_stressed_el"] > 0.0
    assert "baseline" in port_res["risk_band_distribution"]
    assert "stressed" in port_res["risk_band_distribution"]
