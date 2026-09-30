import numpy as np
import pandas as pd
from typing import Dict, Any, List

from ml.config import MSME_DATA_PATH, CASHFLOW_DATA_PATH
from ml.preprocess import load_and_prepare_dataset
from ml.predict import MSMERiskPredictor, get_risk_band
from ml.dscr import calculate_emi
from ml.forecasting import forecast_series

# Configurable Default LGD (Loss Given Default) Assumption for MSME loans
DEFAULT_LGD = 0.45

# Preset Scenario Definitions
SCENARIO_PRESETS = {
    "BASELINE": {
        "demand_change": 0.0,
        "input_cost_inflation": 0.0,
        "receivable_delay_days": 0,
        "interest_rate_change": 0.0,
        "description": "Baseline operating environment with zero macro shock."
    },
    "STRESS": {
        "demand_change": -0.10,
        "input_cost_inflation": 0.10,
        "receivable_delay_days": 15,
        "interest_rate_change": 1.0,
        "description": "Moderate economic downturn: 10% demand drop, 10% cost inflation, 15 days delay, +1% interest rate."
    },
    "SEVERE_STRESS": {
        "demand_change": -0.20,
        "input_cost_inflation": 0.20,
        "receivable_delay_days": 30,
        "interest_rate_change": 2.0,
        "description": "Severe recession shock: 20% demand drop, 20% cost inflation, 30 days delay, +2% interest rate."
    },
    "BOOM": {
        "demand_change": 0.10,
        "input_cost_inflation": -0.05,
        "receivable_delay_days": -10,
        "interest_rate_change": -1.0,
        "description": "Favorable economic expansion: +10% demand, -5% cost reduction, -10 days faster payment, -1% interest rate."
    }
}

class MSMEStressEngine:
    def __init__(self, msme_path: str = MSME_DATA_PATH, cashflow_path: str = CASHFLOW_DATA_PATH):
        self.predictor = MSMERiskPredictor()
        self.df_msme = pd.read_csv(msme_path)
        self.df_cashflow = pd.read_csv(cashflow_path)
        self.df_prepared = load_and_prepare_dataset(msme_path, cashflow_path)

    def _apply_cashflow_stress(
        self,
        inflow: float,
        outflow: float,
        demand_change: float,
        input_cost_inflation: float,
        receivable_delay_days: float
    ) -> tuple:
        """
        Applies cash flow stress mechanics:
        - Inflow adjusted for demand change and receivable delay:
          Stressed Inflow = Inflow * (1 + demand_change) * max(0.2, (1.0 - receivable_delay_days / 90.0))
        - Outflow adjusted for input cost inflation:
          Stressed Outflow = Outflow * (1 + input_cost_inflation)
        """
        delay_factor = max(0.20, 1.0 - (receivable_delay_days / 90.0))
        stressed_inflow = max(0.0, float(inflow * (1.0 + demand_change) * delay_factor))
        stressed_outflow = max(0.0, float(outflow * (1.0 + input_cost_inflation)))
        stressed_net = stressed_inflow - stressed_outflow
        return round(stressed_inflow, 2), round(stressed_outflow, 2), round(stressed_net, 2)

    def run_stress_test(
        self,
        msme_id: str,
        demand_change: float = 0.0,
        input_cost_inflation: float = 0.0,
        receivable_delay_days: int = 0,
        interest_rate_change: float = 0.0,
        base_interest_rate: float = 12.0,
        tenure_months: int = 36,
        lgd: float = DEFAULT_LGD
    ) -> Dict[str, Any]:
        """
        Executes scenario stress test on a single MSME borrower:
        1. Recalculates stressed cash flows and 6-month forecast.
        2. Recalculates stressed EMI under interest rate shock.
        3. Re-scores risk model under stressed metrics (Stressed PD & Risk Band).
        4. Calculates Stressed DSCR & downside months below 1.0.
        5. Computes Expected Loss (PD * LGD * Exposure).
        """
        # Validate parameter bounds
        if not (-0.50 <= demand_change <= 0.50):
            raise ValueError(f"demand_change {demand_change} is outside valid range [-0.50, 0.50].")
        if not (-0.20 <= input_cost_inflation <= 0.60):
            raise ValueError(f"input_cost_inflation {input_cost_inflation} is outside valid range [-0.20, 0.60].")
        if not (-30 <= receivable_delay_days <= 120):
            raise ValueError(f"receivable_delay_days {receivable_delay_days} is outside valid range [-30, 120].")
        if not (-5.0 <= interest_rate_change <= 10.0):
            raise ValueError(f"interest_rate_change {interest_rate_change} is outside valid range [-5.0, 10.0].")

        match = self.df_prepared[self.df_prepared['msme_id'] == msme_id]
        if match.empty:
            raise ValueError(f"MSME ID '{msme_id}' not found.")
            
        row = match.iloc[0].to_dict()
        
        # 1. Baseline Risk & Loan Details
        base_pred = self.predictor.predict_single(row)
        base_pd = base_pred['pd']
        base_band = base_pred['risk_band']
        
        loan_amount = float(row['requested_loan_amount'])
        base_emi = calculate_emi(loan_amount, base_interest_rate, tenure_months)
        
        # 2. Interest Rate Stress & EMI
        stressed_rate = max(0.0, base_interest_rate + interest_rate_change)
        stressed_emi = calculate_emi(loan_amount, stressed_rate, tenure_months)
        
        # 3. Cash Flow Stress Analysis (12 historical + 6 forecast months)
        cf_match = self.df_cashflow[self.df_cashflow['msme_id'] == msme_id].sort_values('month')
        hist_inflows = cf_match['inflow'].values
        hist_outflows = cf_match['outflow'].values
        
        # Stressed forecast series
        fc_in, _, _ = forecast_series(hist_inflows, 6)
        fc_out, _, _ = forecast_series(hist_outflows, 6)
        
        base_net_cfs = []
        stressed_net_cfs = []
        
        for bi, bo in zip(fc_in, fc_out):
            base_net_cfs.append(bi - bo)
            _, _, str_net = self._apply_cashflow_stress(bi, bo, demand_change, input_cost_inflation, receivable_delay_days)
            stressed_net_cfs.append(str_net)

        # Base vs Stressed DSCR
        base_dscrs = [round(float(net / base_emi), 2) if base_emi > 0 else 99.0 for net in base_net_cfs]
        stressed_dscrs = [round(float(net / stressed_emi), 2) if stressed_emi > 0 else 99.0 for net in stressed_net_cfs]
        
        # Clamp negative DSCRs to 0.0 for report readability
        stressed_dscrs_clamped = [max(0.0, d) for d in stressed_dscrs]
        months_below_1 = sum(1 for d in stressed_dscrs_clamped if d < 1.0)
        worst_dscr = round(float(min(stressed_dscrs_clamped)), 2)
        avg_stressed_dscr = round(float(np.mean(stressed_dscrs_clamped)), 2)

        # 4. Re-scoring Risk Model under Stressed Borrower Features
        stressed_row = row.copy()
        if demand_change != 0.0 or input_cost_inflation != 0.0 or receivable_delay_days != 0:
            str_inflow, str_outflow, _ = self._apply_cashflow_stress(
                row['monthly_revenue'], row['monthly_expenses'],
                demand_change, input_cost_inflation, receivable_delay_days
            )
            stressed_row['monthly_revenue'] = str_inflow
            stressed_row['monthly_expenses'] = str_outflow
            
            annual_rev_str = str_inflow * 12.0
            stressed_row['annual_turnover'] = annual_rev_str
            stressed_row['debt_to_turnover'] = float(row['existing_debt'] / (annual_rev_str + 1.0))
            stressed_row['expense_to_revenue'] = float(str_outflow / (str_inflow + 1.0))
            stressed_row['cf_volatility'] = float(row['cf_volatility'] * (1.0 + abs(demand_change) + input_cost_inflation))
        
        stressed_pred = self.predictor.predict_single(stressed_row)
        stressed_pd = stressed_pred['pd']
        stressed_band = stressed_pred['risk_band']
        pd_change = round(float(stressed_pd - base_pd), 4)

        # 5. Expected Loss Calculation: EL = PD * LGD * Exposure
        exposure = loan_amount
        baseline_el = round(float(base_pd * lgd * exposure), 2)
        stressed_el = round(float(stressed_pd * lgd * exposure), 2)
        el_change = round(float(stressed_el - baseline_el), 2)

        return {
            "msme_id": msme_id,
            "scenario": {
                "demand_change": demand_change,
                "input_cost_inflation": input_cost_inflation,
                "receivable_delay_days": receivable_delay_days,
                "interest_rate_change": interest_rate_change,
                "disclaimer": "Scenario-based model output; not an actual prediction of macroeconomic default."
            },
            "risk": {
                "baseline_pd": base_pd,
                "stressed_pd": stressed_pd,
                "pd_change": pd_change,
                "baseline_band": base_band,
                "stressed_band": stressed_band
            },
            "cashflow": {
                "baseline_avg_net_cashflow": round(float(np.mean(base_net_cfs)), 2),
                "stressed_avg_net_cashflow": round(float(np.mean(stressed_net_cfs)), 2)
            },
            "loan": {
                "baseline_emi": base_emi,
                "stressed_emi": stressed_emi
            },
            "dscr": {
                "baseline_avg_dscr": round(float(np.mean(base_dscrs)), 2),
                "stressed_avg_dscr": avg_stressed_dscr,
                "worst_dscr": worst_dscr,
                "months_below_1": int(months_below_1)
            },
            "expected_loss": {
                "baseline_el": baseline_el,
                "stressed_el": stressed_el,
                "el_change": el_change,
                "lgd_assumed": lgd,
                "exposure": exposure
            }
        }

    def run_sensitivity_analysis(self, msme_id: str) -> dict:
        """
        Identifies which individual stress variable has the largest impact on PD, DSCR, and Expected Loss.
        """
        factors = [
            ("demand_change", -0.15, 0.0, 0, 0.0, "Demand Reduction (-15%)"),
            ("input_cost_inflation", 0.0, 0.15, 0, 0.0, "Cost Inflation (+15%)"),
            ("receivable_delay_days", 0.0, 0.0, 30, 0.0, "Payment Delay (+30 days)"),
            ("interest_rate_change", 0.0, 0.0, 0, 2.0, "Rate Hike (+2%)")
        ]
        
        base_res = self.run_stress_test(msme_id, 0.0, 0.0, 0, 0.0)
        base_pd = base_res['risk']['baseline_pd']
        base_dscr = base_res['dscr']['baseline_avg_dscr']
        base_el = base_res['expected_loss']['baseline_el']
        
        rankings = []
        for name, d_chg, c_inf, r_del, i_chg, label in factors:
            res = self.run_stress_test(msme_id, d_chg, c_inf, r_del, i_chg)
            pd_impact = abs(res['risk']['stressed_pd'] - base_pd)
            dscr_impact = abs(res['dscr']['stressed_avg_dscr'] - base_dscr)
            el_impact = abs(res['expected_loss']['stressed_el'] - base_el)
            
            rankings.append({
                "factor": label,
                "variable": name,
                "pd_impact": round(pd_impact, 4),
                "dscr_impact": round(dscr_impact, 2),
                "el_impact": round(el_impact, 2)
            })
            
        rankings_by_dscr = sorted(rankings, key=lambda x: x["dscr_impact"], reverse=True)
        top_driver = rankings_by_dscr[0]["factor"]
        
        return {
            "msme_id": msme_id,
            "rankings": rankings_by_dscr,
            "top_dscr_driver": top_driver,
            "summary": f"Sensitivity analysis identifies '{top_driver}' as having the largest impact on repayment capacity (DSCR)."
        }

    def run_portfolio_stress_test(
        self,
        demand_change: float = -0.10,
        input_cost_inflation: float = 0.10,
        receivable_delay_days: int = 15,
        interest_rate_change: float = 1.0,
        lgd: float = DEFAULT_LGD
    ) -> dict:
        """
        Executes a macro stress test scenario across ALL ~800 MSMEs in the portfolio.
        Returns portfolio PD distribution, total expected loss, risk band migrations, and DSCR shortfall rates.
        """
        msme_ids = self.df_prepared['msme_id'].tolist()
        
        base_pds = []
        stressed_pds = []
        base_els = []
        stressed_els = []
        shortfall_counts = 0
        band_downgrades = 0
        
        band_distribution_base = {}
        band_distribution_stressed = {}
        
        for msme_id in msme_ids:
            res = self.run_stress_test(
                msme_id, demand_change, input_cost_inflation,
                receivable_delay_days, interest_rate_change, lgd=lgd
            )
            
            r = res['risk']
            d = res['dscr']
            el = res['expected_loss']
            
            base_pds.append(r['baseline_pd'])
            stressed_pds.append(r['stressed_pd'])
            base_els.append(el['baseline_el'])
            stressed_els.append(el['stressed_el'])
            
            if d['months_below_1'] > 0:
                shortfall_counts += 1
                
            b_band = r['baseline_band']
            s_band = r['stressed_band']
            
            band_distribution_base[b_band] = band_distribution_base.get(b_band, 0) + 1
            band_distribution_stressed[s_band] = band_distribution_stressed.get(s_band, 0) + 1
            
            # Count downgrade if risk band worsened
            band_order = ["Prime", "Standard", "Watchlist", "Volatile Cash Flow", "High Risk"]
            if band_order.index(s_band) > band_order.index(b_band):
                band_downgrades += 1
                
        total_count = len(msme_ids)
        
        return {
            "total_msmes": total_count,
            "scenario": {
                "demand_change": demand_change,
                "input_cost_inflation": input_cost_inflation,
                "receivable_delay_days": receivable_delay_days,
                "interest_rate_change": interest_rate_change
            },
            "portfolio_metrics": {
                "avg_baseline_pd": round(float(np.mean(base_pds)), 4),
                "avg_stressed_pd": round(float(np.mean(stressed_pds)), 4),
                "median_stressed_pd": round(float(np.median(stressed_pds)), 4),
                "total_baseline_el": round(float(np.sum(base_els)), 2),
                "total_stressed_el": round(float(np.sum(stressed_els)), 2),
                "downgrade_percentage": round(float(band_downgrades / total_count), 4),
                "shortfall_percentage": round(float(shortfall_counts / total_count), 4)
            },
            "risk_band_distribution": {
                "baseline": band_distribution_base,
                "stressed": band_distribution_stressed
            }
        }

# Global singleton helper
_stress_engine_instance = None

def get_stress_engine():
    global _stress_engine_instance
    if _stress_engine_instance is None:
        _stress_engine_instance = MSMEStressEngine()
    return _stress_engine_instance

def run_stress_test(
    msme_id: str,
    demand_change: float = 0.0,
    input_cost_inflation: float = 0.0,
    receivable_delay_days: int = 0,
    interest_rate_change: float = 0.0
) -> dict:
    engine = get_stress_engine()
    return engine.run_stress_test(
        msme_id, demand_change, input_cost_inflation, receivable_delay_days, interest_rate_change
    )
