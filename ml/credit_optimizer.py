import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List

from ml.config import MSME_DATA_PATH, CASHFLOW_DATA_PATH, DEFAULT_LGD, get_risk_band
from ml.preprocess import load_and_prepare_dataset
from ml.predict import MSMERiskPredictor
from ml.dscr import calculate_emi, calculate_dscr_metrics
from ml.forecasting import forecast_series

# Prototype Feasibility Policy Defaults
DEFAULT_OPTIMIZER_CONFIG = {
    "min_base_dscr": 1.20,
    "min_downside_dscr": 1.00,
    "max_downside_months_below_1": 0,
    "max_pd": 0.25,
    "lgd": DEFAULT_LGD,
    "loan_amount_steps": 11,  # 50% to 100% in 5% increments
    "tenures": [24, 36, 48, 60], # Allowed loan tenures in months
    "rate_variations": [-1.0, 0.0, 1.0], # Interest rate variations around base rate (%)
    
    # Objective weights for ranking feasible candidates
    # Objective = w_amount * (Amount / Requested) + w_pd * (1 - PD) + w_dscr * min(Downside_DSCR, 3.0)/3.0 + w_el * (1 - min(EL / Max_EL, 1.0))
    "weight_amount": 0.40,
    "weight_pd": 0.25,
    "weight_dscr": 0.25,
    "weight_el": 0.10
}

class CreditOptimizerEngine:
    def __init__(self, msme_path: str = MSME_DATA_PATH, cashflow_path: str = CASHFLOW_DATA_PATH):
        self.predictor = MSMERiskPredictor()
        self.df_msme = pd.read_csv(msme_path)
        self.df_cashflow = pd.read_csv(cashflow_path)
        self.df_prepared = load_and_prepare_dataset(msme_path, cashflow_path)

    def _evaluate_structure(
        self,
        borrower_row: dict,
        hist_net_cfs: np.ndarray,
        avg_closing_bal: float,
        loan_amount: float,
        tenure_months: int,
        interest_rate: float,
        config: dict
    ) -> dict:
        """
        Evaluates a single candidate loan structure (amount, tenure, interest_rate):
        - Calculates EMI
        - Generates 6-month forecast & 80% lower bound
        - Calculates Base DSCR, Downside DSCR, and Downside Months < 1
        - Re-scores risk model under new loan burden
        - Calculates Expected Loss
        - Assesses policy feasibility
        """
        # 1. Calculate EMI
        emi = calculate_emi(loan_amount, interest_rate, tenure_months)
        
        # 2. 6-Month Forecast & DSCR Metrics
        fc_net, lb_net, _ = forecast_series(hist_net_cfs, 6)
        fc_outflows = [float(borrower_row['monthly_expenses'])] * 6
        
        dscr_res = calculate_dscr_metrics(
            forecast_net_cashflows=fc_net.tolist(),
            lower_80_forecast_bounds=lb_net.tolist(),
            forecast_outflows=fc_outflows,
            avg_closing_balance=avg_closing_bal,
            emi=emi
        )
        
        # 3. Re-score Risk Model under candidate loan structure
        row_cand = borrower_row.copy()
        annual_turnover = float(borrower_row['annual_turnover'])
        row_cand['requested_loan_amount'] = loan_amount
        row_cand['loan_to_turnover'] = float(loan_amount / (annual_turnover + 1.0))
        
        pred = self.predictor.predict_single(row_cand)
        pd_val = pred['pd']
        risk_band = pred['risk_band']
        
        # 4. Expected Loss
        lgd = config.get('lgd', DEFAULT_LGD)
        el = round(float(pd_val * lgd * loan_amount), 2)
        
        # 5. Check Feasibility
        min_base_dscr = config['min_base_dscr']
        min_downside_dscr = config['min_downside_dscr']
        max_downside_months = config['max_downside_months_below_1']
        max_pd = config['max_pd']
        
        avg_base_dscr = dscr_res['average_base_dscr']
        worst_downside_dscr = dscr_res['worst_downside_dscr']
        downside_months = dscr_res['downside_months_below_1']
        
        violations = []
        if avg_base_dscr < min_base_dscr:
            violations.append(f"Average Base DSCR ({avg_base_dscr:.2f}) < Minimum Required ({min_base_dscr:.2f})")
        if worst_downside_dscr < min_downside_dscr:
            violations.append(f"Worst Downside DSCR ({worst_downside_dscr:.2f}) < Minimum Required ({min_downside_dscr:.2f})")
        if downside_months > max_downside_months:
            violations.append(f"Downside Months Below 1.0 ({downside_months}) > Maximum Allowed ({max_downside_months})")
        if pd_val > max_pd:
            violations.append(f"Predicted Probability of Default ({pd_val*100:.1f}%) > Maximum Allowed ({max_pd*100:.1f}%)")
            
        is_feasible = (len(violations) == 0)
        
        return {
            "loan_amount": round(float(loan_amount), 2),
            "tenure_months": int(tenure_months),
            "interest_rate": round(float(interest_rate), 2),
            "emi": emi,
            "pd": pd_val,
            "risk_band": risk_band,
            "average_base_dscr": avg_base_dscr,
            "worst_downside_dscr": worst_downside_dscr,
            "downside_months_below_1": downside_months,
            "expected_loss": el,
            "is_feasible": is_feasible,
            "violations": violations
        }

    def optimize_credit_structure(
        self,
        msme_id: str,
        requested_loan_amount: float = None,
        requested_tenure_months: int = 36,
        interest_rate: float = 12.0,
        config_overrides: dict = None
    ) -> Dict[str, Any]:
        """
        Main Credit Optimization entrypoint.
        Performs an exhaustive grid search over loan amounts, tenures, and interest rates.
        Returns requested structure, recommended structure, feasibility candidates, trade-off frontier,
        and structured borrower explanations.
        """
        config = DEFAULT_OPTIMIZER_CONFIG.copy()
        if config_overrides:
            config.update(config_overrides)
            
        match = self.df_prepared[self.df_prepared['msme_id'] == msme_id]
        if match.empty:
            raise ValueError(f"MSME ID '{msme_id}' not found.")
            
        borrower_row = match.iloc[0].to_dict()
        
        # Preserve protected attributes strictly (ensure unmutated)
        gender_orig = borrower_row.get('gender')
        region_orig = borrower_row.get('region')
        
        if requested_loan_amount is None:
            requested_loan_amount = float(borrower_row.get('requested_loan_amount', 500000.0))
            
        cf_match = self.df_cashflow[self.df_cashflow['msme_id'] == msme_id].sort_values('month')
        hist_net_cfs = cf_match['net_cash_flow'].values
        avg_closing_bal = float(cf_match['closing_balance'].mean())
        
        # 1. Evaluate Requested Loan Structure
        requested_eval = self._evaluate_structure(
            borrower_row, hist_net_cfs, avg_closing_bal,
            requested_loan_amount, requested_tenure_months, interest_rate, config
        )
        
        # Check if requested loan is already fully feasible
        if requested_eval["is_feasible"]:
            return {
                "msme_id": msme_id,
                "requested": requested_eval,
                "recommended": requested_eval,
                "status": "REQUESTED_FEASIBLE",
                "improvement": {
                    "loan_reduction_pct": 0.0,
                    "emi_reduction_pct": 0.0,
                    "pd_change": 0.0,
                    "dscr_change": 0.0,
                    "expected_loss_change": 0.0
                },
                "feasible_candidates_count": 1,
                "rejected_candidates_count": 0,
                "reason": "Requested loan structure already satisfies all repayment feasibility and policy risk constraints.",
                "borrower_explanation": f"Your requested loan of INR {requested_loan_amount:,.0f} for {requested_tenure_months} months is fully feasible under policy risk guidelines.",
                "tradeoff_frontier": [requested_eval]
            }

        # 2. Grid Search Space Setup & Pre-computed Forecasts
        fc_net, lb_net, _ = forecast_series(hist_net_cfs, 6)
        fc_outflows = [float(borrower_row['monthly_expenses'])] * 6

        amount_steps = config["loan_amount_steps"]
        min_amount = max(50000.0, requested_loan_amount * 0.50)
        max_amount = requested_loan_amount
        amounts = np.linspace(min_amount, max_amount, amount_steps)
        amounts = sorted(list(set([round(float(a), -4) for a in amounts if a > 0])))
        
        tenures = config["tenures"]
        rates = sorted(list(set([max(8.0, round(float(interest_rate + delta), 2)) for delta in config["rate_variations"]])))

        # Pre-compute base borrower feature array and base prediction
        base_pred = self.predictor.predict_single(borrower_row)
        base_pd = base_pred['pd']
        
        # 3. Ultra-Fast Vectorized Grid Search Execution
        all_evals = []
        feasible_candidates = []
        rejected_candidates = []
        
        for amt in amounts:
            # Re-score borrower risk for candidate loan amount
            row_cand = borrower_row.copy()
            annual_turnover = float(borrower_row['annual_turnover'])
            row_cand['requested_loan_amount'] = amt
            row_cand['loan_to_turnover'] = float(amt / (annual_turnover + 1.0))
            
            pred = self.predictor.predict_single(row_cand)
            pd_val = pred['pd']
            risk_band = pred['risk_band']
            lgd = config.get('lgd', DEFAULT_LGD)
            el = round(float(pd_val * lgd * amt), 2)
            
            for ten in tenures:
                for r in rates:
                    emi = calculate_emi(amt, r, ten)
                    
                    dscr_res = calculate_dscr_metrics(
                        forecast_net_cashflows=fc_net.tolist(),
                        lower_80_forecast_bounds=lb_net.tolist(),
                        forecast_outflows=fc_outflows,
                        avg_closing_balance=avg_closing_bal,
                        emi=emi
                    )
                    
                    avg_base_dscr = dscr_res['average_base_dscr']
                    worst_downside_dscr = dscr_res['worst_downside_dscr']
                    downside_months = dscr_res['downside_months_below_1']
                    
                    violations = []
                    if avg_base_dscr < config['min_base_dscr']:
                        violations.append(f"Average Base DSCR ({avg_base_dscr:.2f}) < Minimum Required ({config['min_base_dscr']:.2f})")
                    if worst_downside_dscr < config['min_downside_dscr']:
                        violations.append(f"Worst Downside DSCR ({worst_downside_dscr:.2f}) < Minimum Required ({config['min_downside_dscr']:.2f})")
                    if downside_months > config['max_downside_months_below_1']:
                        violations.append(f"Downside Months Below 1.0 ({downside_months}) > Maximum Allowed ({config['max_downside_months_below_1']})")
                    if pd_val > config['max_pd']:
                        violations.append(f"Predicted Probability of Default ({pd_val*100:.1f}%) > Maximum Allowed ({config['max_pd']*100:.1f}%)")
                        
                    is_feasible = (len(violations) == 0)
                    
                    cand_eval = {
                        "loan_amount": round(float(amt), 2),
                        "tenure_months": int(ten),
                        "interest_rate": round(float(r), 2),
                        "emi": emi,
                        "pd": pd_val,
                        "risk_band": risk_band,
                        "average_base_dscr": avg_base_dscr,
                        "worst_downside_dscr": worst_downside_dscr,
                        "downside_months_below_1": downside_months,
                        "expected_loss": el,
                        "is_feasible": is_feasible,
                        "violations": violations
                    }
                    
                    # Ensure protected attributes were NOT altered
                    assert borrower_row['gender'] == gender_orig
                    assert borrower_row['region'] == region_orig
                    
                    all_evals.append(cand_eval)
                    
                    if is_feasible:
                        pd_score = (1.0 - pd_val)
                        dscr_score = min(worst_downside_dscr, 3.0) / 3.0
                        amt_score = amt / requested_loan_amount
                        el_score = 1.0 - min(el / (requested_loan_amount * lgd), 1.0)
                        
                        obj_score = (
                            config["weight_pd"] * pd_score +
                            config["weight_dscr"] * dscr_score +
                            config["weight_amount"] * amt_score +
                            config["weight_el"] * el_score
                        )
                        cand_eval["objective_score"] = round(float(obj_score), 4)
                        feasible_candidates.append(cand_eval)
                    else:
                        rejected_candidates.append(cand_eval)

        # Sort candidates deterministically
        feasible_candidates.sort(key=lambda x: (x["objective_score"], x["loan_amount"], -x["pd"]), reverse=True)
        rejected_candidates.sort(key=lambda x: (x["worst_downside_dscr"], -x["pd"]), reverse=True)

        # 4. Handle Case: NO Feasible Solution Exists
        if not feasible_candidates:
            closest_rejected = rejected_candidates[:3]
            return {
                "msme_id": msme_id,
                "requested": requested_eval,
                "recommended": None,
                "status": "NO_FEASIBLE_STRUCTURE",
                "improvement": None,
                "feasible_candidates_count": 0,
                "rejected_candidates_count": len(rejected_candidates),
                "closest_rejected_candidates": closest_rejected,
                "reason": "No feasible loan structure found within the configured policy risk constraints.",
                "borrower_explanation": f"No feasible loan structure could be identified for requested loan of INR {requested_loan_amount:,.0f} within current risk policy limits. Consider providing additional collateral or lowering requested amount further.",
                "tradeoff_frontier": []
            }

        # 5. Best Feasible Recommendation & Improvement Calculation
        recommended = feasible_candidates[0]
        
        loan_red_pct = round(float((requested_loan_amount - recommended["loan_amount"]) / requested_loan_amount * 100.0), 2)
        emi_red_pct = round(float((requested_eval["emi"] - recommended["emi"]) / requested_eval["emi"] * 100.0), 2) if requested_eval["emi"] > 0 else 0.0
        pd_change = round(float(recommended["pd"] - requested_eval["pd"]), 4)
        dscr_change = round(float(recommended["average_base_dscr"] - requested_eval["average_base_dscr"]), 2)
        el_change = round(float(recommended["expected_loss"] - requested_eval["expected_loss"]), 2)
        
        improvement = {
            "loan_reduction_pct": loan_red_pct,
            "emi_reduction_pct": emi_red_pct,
            "pd_change": pd_change,
            "dscr_change": dscr_change,
            "expected_loss_change": el_change
        }

        # 6. Extract Pareto Trade-Off Frontier (Non-dominated feasible candidates)
        # Trade-off: Higher Loan Amount vs. Higher Downside DSCR / Lower PD
        tradeoff_frontier = []
        sorted_by_amount = sorted(feasible_candidates, key=lambda x: x["loan_amount"], reverse=True)
        max_seen_dscr = -1.0
        for cand in sorted_by_amount:
            if cand["worst_downside_dscr"] > max_seen_dscr:
                tradeoff_frontier.append(cand)
                max_seen_dscr = cand["worst_downside_dscr"]

        # 7. Generate Borrower-Friendly Explanation
        explanation_msg = (
            f"Your requested loan of INR {requested_loan_amount:,.0f} for {requested_tenure_months} months creates repayment pressure under policy guidelines. "
            f"The system identified a safer structure of INR {recommended['loan_amount']:,.0f} for {recommended['tenure_months']} months @ {recommended['interest_rate']}%. "
            f"Estimated Base DSCR improves from {requested_eval['average_base_dscr']:.2f} to {recommended['average_base_dscr']:.2f}, "
            f"and predicted PD changes from {requested_eval['pd']*100:.1f}% to {recommended['pd']*100:.1f}%."
        )

        return {
            "msme_id": msme_id,
            "requested": requested_eval,
            "recommended": recommended,
            "status": "OPTIMIZED_RECOMMENDATION_FOUND",
            "improvement": improvement,
            "feasible_candidates_count": len(feasible_candidates),
            "rejected_candidates_count": len(rejected_candidates),
            "reason": "Found safer feasible loan structure balancing borrower affordability and lender risk.",
            "borrower_explanation": explanation_msg,
            "tradeoff_frontier": tradeoff_frontier[:5],
            "objective_score": recommended["objective_score"]
        }

# Global singleton loader helper
_credit_optimizer_instance = None

def get_credit_optimizer():
    global _credit_optimizer_instance
    if _credit_optimizer_instance is None:
        _credit_optimizer_instance = CreditOptimizerEngine()
    return _credit_optimizer_instance

def optimize_credit_structure(
    msme_id: str,
    requested_loan_amount: float = None,
    requested_tenure_months: int = 36,
    interest_rate: float = 12.0,
    config_overrides: dict = None
) -> dict:
    optimizer = get_credit_optimizer()
    return optimizer.optimize_credit_structure(
        msme_id, requested_loan_amount, requested_tenure_months, interest_rate, config_overrides
    )
