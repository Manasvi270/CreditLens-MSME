import os
import warnings
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt

from ml.config import CASHFLOW_DATA_PATH, MSME_DATA_PATH
from ml.dscr import calculate_emi, calculate_dscr_metrics

# Suppress statsmodels optimization convergence warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*Optimization failed to converge.*")

def forecast_series(series: np.ndarray, forecast_horizon: int = 6) -> tuple:
    """
    Forecasts a 1D time series using Holt's Linear Exponential Smoothing.
    Computes an approximate 80% uncertainty band (±1.28 * residual std dev).
    Returns (forecast_values, lower_bounds, upper_bounds).
    """
    series = np.array(series, dtype=float)
    if len(series) < 3:
        mean_val = np.mean(series) if len(series) > 0 else 100000.0
        fc = np.full(forecast_horizon, mean_val)
        std_val = np.std(series) if len(series) > 1 else abs(mean_val) * 0.15
        lb = fc - 1.28 * std_val
        ub = fc + 1.28 * std_val
        return fc, lb, ub

    try:
        model = Holt(series, initialization_method="estimated", suppress_warnings=True).fit(smoothing_level=0.3, smoothing_trend=0.1)
        fc = model.forecast(forecast_horizon)
        residuals = series - model.fittedvalues
        sigma = np.std(residuals)
        if sigma < 1.0:
            sigma = max(np.std(series) * 0.15, 1000.0)
    except Exception:
        try:
            model = SimpleExpSmoothing(series, initialization_method="estimated", suppress_warnings=True).fit(smoothing_level=0.3)
            fc = model.forecast(forecast_horizon)
            residuals = series - model.fittedvalues
            sigma = np.std(residuals)
        except Exception:
            fc = np.full(forecast_horizon, np.mean(series[-3:]))
            sigma = max(np.std(series), 1000.0)

    z_80 = 1.2815
    step_scales = np.sqrt(1.0 + 0.08 * np.arange(1, forecast_horizon + 1))
    half_width = z_80 * sigma * step_scales
    
    lb = fc - half_width
    ub = fc + half_width
    
    return np.round(fc, 2), np.round(lb, 2), np.round(ub, 2)

def forecast_cashflow(
    msme_id: str,
    loan_amount: float = None,
    interest_rate: float = 12.0,
    tenure_months: int = 36,
    cashflow_path: str = CASHFLOW_DATA_PATH,
    msme_path: str = MSME_DATA_PATH
) -> dict:
    """
    Main forecast entrypoint.
    Returns 12 historical months, 6 forecast months with 80% uncertainty bounds,
    EMI, DSCR metrics, downside month count, liquidity coverage, and repayment capacity assessment.
    """
    if not os.path.exists(cashflow_path) or not os.path.exists(msme_path):
        raise FileNotFoundError("Data files missing. Please run Phase 1 data generator first.")
        
    df_cf = pd.read_csv(cashflow_path)
    df_msme = pd.read_csv(msme_path)
    
    match_cf = df_cf[df_cf['msme_id'] == msme_id].sort_values('month')
    if match_cf.empty:
        raise ValueError(f"MSME ID '{msme_id}' not found in cashflow dataset.")
        
    match_msme = df_msme[df_msme['msme_id'] == msme_id]
    if match_msme.empty:
        raise ValueError(f"MSME ID '{msme_id}' not found in MSME profile dataset.")
        
    msme_profile = match_msme.iloc[0].to_dict()
    
    # Extract historical vectors
    hist_months = match_cf['month'].tolist()
    hist_inflows = match_cf['inflow'].tolist()
    hist_outflows = match_cf['outflow'].tolist()
    hist_net_cfs = match_cf['net_cash_flow'].tolist()
    avg_closing_balance = float(match_cf['closing_balance'].mean())
    
    # 6-Month Forecast Generation
    fc_inflow, _, _ = forecast_series(hist_inflows, forecast_horizon=6)
    fc_outflow, _, _ = forecast_series(hist_outflows, forecast_horizon=6)
    fc_net_cf, lb_net_cf, ub_net_cf = forecast_series(hist_net_cfs, forecast_horizon=6)
    
    # Enforce non-negative inflows and outflows
    fc_inflow = np.maximum(5000.0, fc_inflow)
    fc_outflow = np.maximum(4000.0, fc_outflow)
    
    fc_months = list(range(13, 19))
    
    if loan_amount is None:
        loan_amount = float(msme_profile.get('requested_loan_amount', 500000.0))
        
    emi = calculate_emi(loan_amount, interest_rate, tenure_months)
    
    repayment_metrics = calculate_dscr_metrics(
        forecast_net_cashflows=fc_net_cf.tolist(),
        lower_80_forecast_bounds=lb_net_cf.tolist(),
        forecast_outflows=fc_outflow.tolist(),
        avg_closing_balance=avg_closing_balance,
        emi=emi
    )
    
    return {
        "msme_id": msme_id,
        "historical": {
            "months": hist_months,
            "inflow": [round(float(x), 2) for x in hist_inflows],
            "outflow": [round(float(x), 2) for x in hist_outflows],
            "net_cashflow": [round(float(x), 2) for x in hist_net_cfs]
        },
        "forecast": {
            "months": fc_months,
            "inflow": [round(float(x), 2) for x in fc_inflow],
            "outflow": [round(float(x), 2) for x in fc_outflow],
            "net_cashflow": [round(float(x), 2) for x in fc_net_cf],
            "lower_bound": [round(float(x), 2) for x in lb_net_cf],
            "upper_bound": [round(float(x), 2) for x in ub_net_cf]
        },
        "loan": {
            "amount": round(float(loan_amount), 2),
            "interest_rate": float(interest_rate),
            "tenure_months": int(tenure_months),
            "emi": emi
        },
        "repayment_capacity": repayment_metrics
    }
