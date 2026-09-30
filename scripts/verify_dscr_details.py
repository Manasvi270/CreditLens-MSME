import pandas as pd
import numpy as np
from ml.forecasting import forecast_cashflow, forecast_series
from ml.dscr import calculate_emi, calculate_dscr_metrics
from ml.config import CASHFLOW_DATA_PATH, MSME_DATA_PATH

def inspect_msme_001_details():
    df_cf = pd.read_csv(CASHFLOW_DATA_PATH)
    msme_001_cf = df_cf[df_cf['msme_id'] == 'MSME_001'].sort_values('month')
    
    hist_net_cfs = msme_001_cf['net_cash_flow'].values
    avg_closing_bal = float(msme_001_cf['closing_balance'].mean())
    
    print("=== MSME_001 HISTORICAL NET CASH FLOW (MONTHS 1-12) ===")
    for m, val in zip(msme_001_cf['month'], hist_net_cfs):
        print(f"  Month {m:02d}: INR {val:,.2f}")
        
    print(f"\nAverage Historical Closing Balance: INR {avg_closing_bal:,.2f}")
    print(f"Operating Liquidity Buffer (25% of Closing Bal): INR {avg_closing_bal * 0.25:,.2f}")

    # Forecast series inspection
    fc_net, lb_net, ub_net = forecast_series(hist_net_cfs, forecast_horizon=6)
    
    # Let's inspect step-by-step forecast calculations
    # Fit Holt model manually to show exact residuals and sigma
    from statsmodels.tsa.holtwinters import Holt
    model = Holt(hist_net_cfs, initialization_method="estimated").fit(smoothing_level=0.3, smoothing_trend=0.1)
    fitted = model.fittedvalues
    residuals = hist_net_cfs - fitted
    sigma = np.std(residuals)
    z_80 = 1.2815
    
    print("\n=== STATISTICAL FORECAST & 80% UNCERTAINTY BAND FORMULA VERIFICATION ===")
    print(f"Model: Holt's Linear Exponential Smoothing (level_alpha=0.3, trend_beta=0.1)")
    print(f"Residual Std Dev (sigma): INR {sigma:,.2f}")
    print(f"z-score for 80% Two-Sided Confidence Interval: {z_80}")
    
    print("\nStep-by-Step Forecast Month Calculation (Months 13 to 18):")
    for h in range(1, 7):
        step_scale = np.sqrt(1.0 + 0.08 * h)
        half_width = z_80 * sigma * step_scale
        fc_val = fc_net[h-1]
        lb_val = lb_net[h-1]
        ub_val = ub_net[h-1]
        print(f"  Month {12+h}: Forecast=INR {fc_val:,.2f} | Step Scale=sqrt(1 + 0.08*{h})={step_scale:.4f} | Margin=+-INR {half_width:,.2f} | Lower Bound=INR {lb_val:,.2f} | Upper Bound=INR {ub_val:,.2f}")

    # EMI calculation for MSME_001
    loan_amount = 639000.0
    interest_rate = 12.0
    tenure_months = 36
    emi = calculate_emi(loan_amount, interest_rate, tenure_months)
    
    print("\n=== LOAN EMI CALCULATION FOR MSME_001 ===")
    print(f"Loan Principal (P): INR {loan_amount:,.2f}")
    print(f"Annual Interest Rate: {interest_rate}%  -> Monthly Rate (r): {interest_rate/12/100:.4f}")
    print(f"Tenure (n): {tenure_months} months")
    print(f"Formula: EMI = [P * r * (1+r)^n] / [(1+r)^n - 1]")
    print(f"Calculated Monthly EMI: INR {emi:,.2f}")

    # DSCR Step-by-Step Manual Calculation
    liquidity_buffer = avg_closing_bal * 0.25
    print("\n=== DSCR MANUAL STEP-BY-STEP CALCULATION FOR MSME_001 ===")
    print(f"Cash Available for Debt Service (CADS) Formula:")
    print(f"  Base CADS_h = Base Net Cash Flow_h + Liquidity Buffer (INR {liquidity_buffer:,.2f})")
    print(f"  Downside CADS_h = Lower Bound Net Cash Flow_h + Liquidity Buffer (INR {liquidity_buffer:,.2f})")
    print(f"  Base DSCR_h = Base CADS_h / EMI")
    print(f"  Downside DSCR_h = Downside CADS_h / EMI\n")
    
    for h in range(6):
        m = 13 + h
        b_cf = fc_net[h]
        d_cf = lb_net[h]
        
        cads_b = b_cf + liquidity_buffer
        cads_d = d_cf + liquidity_buffer
        
        b_dscr = round(cads_b / emi, 2)
        d_dscr = round(cads_d / emi, 2)
        
        print(f"  Month {m}:")
        print(f"    Base:     Net CF = INR {b_cf:,.2f} + Buffer = CADS INR {cads_b:,.2f} / EMI {emi:,.2f} -> Base DSCR = {b_dscr:.2f}")
        print(f"    Downside: Net CF = INR {d_cf:,.2f} + Buffer = CADS INR {cads_d:,.2f} / EMI {emi:,.2f} -> Downside DSCR = {d_dscr:.2f} (Below 1.0? {'YES' if d_dscr < 1.0 else 'NO'})")

if __name__ == "__main__":
    inspect_msme_001_details()
