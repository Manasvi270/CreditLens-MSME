import numpy as np

def calculate_emi(loan_amount: float, annual_interest_rate: float, tenure_months: int) -> float:
    """
    Calculates standard Equated Monthly Installment (EMI) for a loan.
    EMI = [P x r x (1+r)^n] / [(1+r)^n - 1]
    
    Handles zero interest, zero loan, or invalid inputs safely.
    """
    if loan_amount <= 0 or tenure_months <= 0:
        return 0.0
        
    if annual_interest_rate <= 0:
        return round(float(loan_amount / tenure_months), 2)
        
    monthly_rate = (annual_interest_rate / 100.0) / 12.0
    numerator = loan_amount * monthly_rate * ((1 + monthly_rate) ** tenure_months)
    denominator = ((1 + monthly_rate) ** tenure_months) - 1.0
    
    if denominator == 0:
        return 0.0
        
    emi = numerator / denominator
    return round(float(emi), 2)

def calculate_dscr_metrics(
    forecast_net_cashflows: list,
    lower_80_forecast_bounds: list,
    forecast_outflows: list,
    avg_closing_balance: float,
    emi: float
) -> dict:
    """
    Calculates pure operating DSCR metrics, separating operating cash flow from liquidity reserves:
    1. Base DSCR = Forecast Net Cash Flow / EMI
    2. Downside DSCR = Lower 80% Forecast Bound / EMI
    3. Liquidity Reserve = 25% * Average Historical Bank Closing Balance
    4. Liquidity Coverage = Liquidity Reserve / EMI
    5. Downside Months Below 1.0 (where Downside DSCR < 1.0)
    6. Cash Runway = Average Closing Balance / Average Monthly Operating Outflow
    """
    liquidity_reserve = round(max(0.0, float(avg_closing_balance * 0.25)), 2)

    if emi <= 0:
        base_dscr = [99.0] * len(forecast_net_cashflows)
        downside_dscr = [99.0] * len(lower_80_forecast_bounds)
        liquidity_coverage = 99.0
        downside_months_below_1 = 0
        assessment = "Strong"
        summary_statement = "No active loan EMI requested; operating cash flow coverage is unconstrained."
    else:
        liquidity_coverage = round(float(liquidity_reserve / emi), 2)
        
        base_dscr = []
        downside_dscr = []
        
        for net_cf, lower_bound_cf in zip(forecast_net_cashflows, lower_80_forecast_bounds):
            # Pure operating cash flow coverage
            b_dscr = round(float(net_cf / emi), 2)
            d_dscr = round(float(lower_bound_cf / emi), 2)
            
            # Clamp negative DSCR to 0.0 for clean metrics reporting
            base_dscr.append(max(0.0, b_dscr))
            downside_dscr.append(max(0.0, d_dscr))
            
        downside_months_below_1 = sum(1 for d in downside_dscr if d < 1.0)
        avg_base_dscr = round(float(np.mean(base_dscr)), 2)
        
        # Determine Repayment Capacity Assessment based on operating coverage & liquidity cushion
        if avg_base_dscr >= 1.4 and downside_months_below_1 == 0:
            assessment = "Strong"
            summary_statement = f"Operating cash flow comfortably covers the proposed EMI (avg Base DSCR {avg_base_dscr:.2f}) with zero downside shortfall months."
        elif avg_base_dscr >= 1.1 and downside_months_below_1 <= 2:
            assessment = "Moderate"
            summary_statement = f"Operating cash flow covers proposed EMI in base case (avg Base DSCR {avg_base_dscr:.2f}), but lower 80% forecast bound shows pressure in {downside_months_below_1} of the next 6 months (Liquidity Coverage: {liquidity_coverage:.1f} months of EMI)."
        else:
            assessment = "Weak"
            summary_statement = f"Operating cash flow indicates significant debt service pressure with lower 80% forecast bound below DSCR 1.0 in {downside_months_below_1} of the next 6 months."

    avg_outflow = np.mean(forecast_outflows) if len(forecast_outflows) > 0 and np.mean(forecast_outflows) > 0 else 1.0
    cash_runway_months = round(float(avg_closing_balance / avg_outflow), 1)

    return {
        "base_dscr": base_dscr,
        "downside_dscr": downside_dscr,
        "liquidity_reserve": liquidity_reserve,
        "liquidity_coverage": liquidity_coverage,
        "downside_months_below_1": int(downside_months_below_1),
        "average_base_dscr": round(float(np.mean(base_dscr)), 2),
        "worst_downside_dscr": round(float(min(downside_dscr)), 2),
        "cash_runway_months": cash_runway_months,
        "assessment": assessment,
        "summary_statement": summary_statement
    }
