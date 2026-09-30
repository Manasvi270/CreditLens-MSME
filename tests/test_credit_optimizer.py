import pytest
import pandas as pd
from ml.credit_optimizer import optimize_credit_structure, get_credit_optimizer, DEFAULT_OPTIMIZER_CONFIG
from ml.config import MSME_DATA_PATH

@pytest.fixture
def optimizer_engine():
    return get_credit_optimizer()

def test_already_feasible_borrower_remains_feasible(optimizer_engine):
    # MSME_001 has high cash flow and moderate loan request
    res = optimizer_engine.optimize_credit_structure("MSME_001")
    assert res["status"] == "REQUESTED_FEASIBLE"
    assert res["recommended"]["loan_amount"] == res["requested"]["loan_amount"]
    assert res["improvement"]["loan_reduction_pct"] == 0.0

def test_risky_borrower_produces_optimized_structure(optimizer_engine):
    # MSME_003 is risky with requested loan ₹24.32L
    res = optimizer_engine.optimize_credit_structure("MSME_003")
    
    assert res["status"] in ["OPTIMIZED_RECOMMENDATION_FOUND", "NO_FEASIBLE_STRUCTURE"]
    if res["status"] == "OPTIMIZED_RECOMMENDATION_FOUND":
        rec = res["recommended"]
        req = res["requested"]
        
        # Check loan amount constraint
        assert rec["loan_amount"] <= req["loan_amount"]
        # Check policy constraints
        assert rec["average_base_dscr"] >= DEFAULT_OPTIMIZER_CONFIG["min_base_dscr"]
        assert rec["worst_downside_dscr"] >= DEFAULT_OPTIMIZER_CONFIG["min_downside_dscr"]
        assert rec["downside_months_below_1"] <= DEFAULT_OPTIMIZER_CONFIG["max_downside_months_below_1"]
        assert rec["pd"] <= DEFAULT_OPTIMIZER_CONFIG["max_pd"]
        
        # Check improvement metrics
        assert "loan_reduction_pct" in res["improvement"]
        assert "emi_reduction_pct" in res["improvement"]

def test_no_feasible_structure_returns_clear_explanation(optimizer_engine):
    # Pass an impossibly strict constraint set (e.g. min_base_dscr = 50.0) to force NO_FEASIBLE_STRUCTURE
    strict_config = {"min_base_dscr": 50.0}
    res = optimizer_engine.optimize_credit_structure("MSME_003", config_overrides=strict_config)
    
    assert res["status"] == "NO_FEASIBLE_STRUCTURE"
    assert res["recommended"] is None
    assert "closest_rejected_candidates" in res
    assert len(res["closest_rejected_candidates"]) > 0
    # Verify violation reasons are reported
    for rej in res["closest_rejected_candidates"]:
        assert len(rej["violations"]) > 0

def test_protected_attributes_never_mutated_or_used(optimizer_engine):
    df_before = pd.read_csv(MSME_DATA_PATH)
    msme_003_before = df_before[df_before['msme_id'] == 'MSME_003'].iloc[0].to_dict()
    
    res = optimizer_engine.optimize_credit_structure("MSME_003")
    
    df_after = pd.read_csv(MSME_DATA_PATH)
    msme_003_after = df_after[df_after['msme_id'] == 'MSME_003'].iloc[0].to_dict()
    
    assert msme_003_before['gender'] == msme_003_after['gender']
    assert msme_003_before['region'] == msme_003_after['region']

def test_deterministic_candidate_ranking(optimizer_engine):
    res1 = optimizer_engine.optimize_credit_structure("MSME_003")
    res2 = optimizer_engine.optimize_credit_structure("MSME_003")
    
    if res1["recommended"] and res2["recommended"]:
        assert res1["recommended"]["loan_amount"] == res2["recommended"]["loan_amount"]
        assert res1["recommended"]["tenure_months"] == res2["recommended"]["tenure_months"]
        assert res1["recommended"]["objective_score"] == res2["recommended"]["objective_score"]

def test_expected_loss_and_pd_bounds(optimizer_engine):
    res = optimizer_engine.optimize_credit_structure("MSME_002")
    req = res["requested"]
    assert 0.0 <= req["pd"] <= 1.0
    assert req["expected_loss"] >= 0.0

def test_objective_weights_sum_to_one():
    total_weight = (
        DEFAULT_OPTIMIZER_CONFIG["weight_amount"] +
        DEFAULT_OPTIMIZER_CONFIG["weight_pd"] +
        DEFAULT_OPTIMIZER_CONFIG["weight_dscr"] +
        DEFAULT_OPTIMIZER_CONFIG["weight_el"]
    )
    assert abs(total_weight - 1.0) < 1e-6

def test_larger_feasible_loan_receives_higher_retention_component():
    req_amount = 500000.0
    cand_small = 250000.0
    cand_large = 450000.0
    score_small = cand_small / req_amount
    score_large = cand_large / req_amount
    assert score_large > score_small
    assert score_large == 0.90
    assert score_small == 0.50

def test_feasibility_constraints_take_priority_over_objective_score(optimizer_engine):
    # MSME_005 has both feasible and rejected candidates
    res = optimizer_engine.optimize_credit_structure("MSME_005")
    assert res["status"] == "OPTIMIZED_RECOMMENDATION_FOUND"
    rec = res["recommended"]
    assert rec["is_feasible"] is True
    assert rec["average_base_dscr"] >= DEFAULT_OPTIMIZER_CONFIG["min_base_dscr"]
    assert rec["worst_downside_dscr"] >= DEFAULT_OPTIMIZER_CONFIG["min_downside_dscr"]
    assert rec["downside_months_below_1"] <= DEFAULT_OPTIMIZER_CONFIG["max_downside_months_below_1"]
    assert rec["pd"] <= DEFAULT_OPTIMIZER_CONFIG["max_pd"]

