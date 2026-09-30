import pytest
from ml.forecasting import forecast_cashflow, forecast_series

def test_forecast_series_numeric_and_bounds():
    series = [100000, 110000, 105000, 120000, 115000, 130000, 125000, 140000, 135000, 150000, 145000, 160000]
    fc, lb, ub = forecast_series(series, forecast_horizon=6)
    
    assert len(fc) == 6
    assert len(lb) == 6
    assert len(ub) == 6
    
    for i in range(6):
        assert lb[i] <= fc[i] <= ub[i], f"Bound ordering error at index {i}: {lb[i]} <= {fc[i]} <= {ub[i]}"

def test_forecast_cashflow_output_contract():
    res = forecast_cashflow("MSME_001", loan_amount=600000.0, interest_rate=12.0, tenure_months=36)
    
    assert res["msme_id"] == "MSME_001"
    
    # Historical check
    assert len(res["historical"]["months"]) == 12
    assert len(res["historical"]["inflow"]) == 12
    assert len(res["historical"]["outflow"]) == 12
    assert len(res["historical"]["net_cashflow"]) == 12
    
    # Forecast check
    assert len(res["forecast"]["months"]) == 6
    assert len(res["forecast"]["inflow"]) == 6
    assert len(res["forecast"]["outflow"]) == 6
    assert len(res["forecast"]["net_cashflow"]) == 6
    assert len(res["forecast"]["lower_bound"]) == 6
    assert len(res["forecast"]["upper_bound"]) == 6
    
    # Check numeric bounds ordering
    for i in range(6):
        assert res["forecast"]["lower_bound"][i] <= res["forecast"]["net_cashflow"][i] <= res["forecast"]["upper_bound"][i]
        
    # Loan & DSCR check
    assert res["loan"]["emi"] > 0
    rc = res["repayment_capacity"]
    assert "base_dscr" in rc
    assert "downside_dscr" in rc
    assert "liquidity_reserve" in rc
    assert "liquidity_coverage" in rc
    assert "downside_months_below_1" in rc

def test_missing_msme_id_raises_error():
    with pytest.raises(ValueError):
        forecast_cashflow("MSME_NON_EXISTENT_999")
