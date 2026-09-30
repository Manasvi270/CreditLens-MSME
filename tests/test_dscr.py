import pytest
from ml.dscr import calculate_emi, calculate_dscr_metrics

def test_standard_emi_calculation():
    # 10 Lakhs, 12% annual interest, 36 months tenure
    emi = calculate_emi(1000000.0, 12.0, 36)
    assert 33000.0 <= emi <= 33500.0, f"Expected ~33,214.31, got {emi}"

def test_zero_interest_emi():
    emi = calculate_emi(120000.0, 0.0, 12)
    assert emi == 10000.0

def test_invalid_loan_inputs():
    assert calculate_emi(-50000.0, 12.0, 36) == 0.0
    assert calculate_emi(500000.0, 12.0, 0) == 0.0

def test_dscr_metrics_calculation():
    net_cfs = [40000.0, 35000.0, 25000.0, 45000.0, 30000.0, 50000.0]
    lower_bounds = [20000.0, 15000.0, 5000.0, 25000.0, 10000.0, 30000.0]
    outflows = [100000.0] * 6
    avg_closing = 40000.0
    emi = 25000.0
    
    res = calculate_dscr_metrics(net_cfs, lower_bounds, outflows, avg_closing, emi)
    
    assert "base_dscr" in res
    assert "downside_dscr" in res
    assert "liquidity_reserve" in res
    assert "liquidity_coverage" in res
    assert len(res["base_dscr"]) == 6
    assert len(res["downside_dscr"]) == 6
    
    # Base DSCR month 1 = 40000 / 25000 = 1.6
    assert res["base_dscr"][0] == 1.6
    # Downside DSCR month 3 = 5000 / 25000 = 0.2 < 1.0
    assert res["downside_dscr"][2] == 0.2
    assert res["downside_months_below_1"] > 0
    # Liquidity reserve = 25% * 40000 = 10000
    assert res["liquidity_reserve"] == 10000.0
    # Liquidity coverage = 10000 / 25000 = 0.4
    assert res["liquidity_coverage"] == 0.4
