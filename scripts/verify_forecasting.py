import pandas as pd
from ml.forecasting import forecast_cashflow
from ml.config import MSME_DATA_PATH

def verify_5_sample_forecasts_updated():
    df_msme = pd.read_csv(MSME_DATA_PATH)
    sample_ids = df_msme['msme_id'].head(5).tolist()
    
    print("=== UPDATED PHASE 4 CASH-FLOW FORECASTING & DSCR VERIFICATION ===")
    
    for msme_id in sample_ids:
        res = forecast_cashflow(msme_id, interest_rate=12.0, tenure_months=36)
        repay = res['repayment_capacity']
        loan = res['loan']
        
        print(f"\n------------------------------------------------------------")
        print(f"[*] MSME ID: {res['msme_id']}")
        print(f"   Requested Loan: INR {loan['amount']:,.2f} | Tenure: {loan['tenure_months']} months @ {loan['interest_rate']}%")
        print(f"   Calculated Monthly EMI: INR {loan['emi']:,.2f}")
        print(f"   Liquidity Reserve (25% Avg Closing): INR {repay['liquidity_reserve']:,.2f}")
        print(f"   Liquidity Coverage: {repay['liquidity_coverage']} months of EMI")
        print(f"   Forecast Net Cash Flows (Months 13-18): {res['forecast']['net_cashflow']}")
        print(f"   Lower 80% Forecast Bound:               {res['forecast']['lower_bound']}")
        print(f"   Pure Operating Base DSCR per Month:     {repay['base_dscr']}")
        print(f"   Downside DSCR per Month:                {repay['downside_dscr']}")
        print(f"   Downside Months Below DSCR 1.0:         {repay['downside_months_below_1']} of 6 months")
        print(f"   Repayment Capacity Assessment:          {repay['assessment']}")
        print(f"   Summary Statement:                      \"{repay['summary_statement']}\"")

if __name__ == "__main__":
    verify_5_sample_forecasts_updated()
