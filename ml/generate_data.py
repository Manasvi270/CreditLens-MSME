import os
import numpy as np
import pandas as pd

def generate_synthetic_msme_data(num_msmes: int = 800, seed: int = 42):
    """
    Generates synthetic MSME dataset (~800 records) and 12-month historical cash flow dataset.
    Strictly uses synthetic data for decision support, risk scoring, fairness analysis, and stress testing.
    """
    np.random.seed(seed)
    
    sectors = [
        'Retail Trade', 
        'Light Manufacturing', 
        'Services', 
        'Textile & Apparel', 
        'Agri-Processing', 
        'Handicrafts & Artisan'
    ]
    sector_props = [0.30, 0.20, 0.25, 0.10, 0.10, 0.05]
    
    regions = ['Rural', 'Semi-Urban', 'Urban']
    region_props = [0.35, 0.40, 0.25]
    
    genders = ['Female', 'Male']
    gender_props = [0.35, 0.65]

    msme_records = []
    cashflow_records = []

    for i in range(1, num_msmes + 1):
        msme_id = f"MSME_{i:03d}"
        sector = np.random.choice(sectors, p=sector_props)
        region = np.random.choice(regions, p=region_props)
        gender = np.random.choice(genders, p=gender_props)
        thin_file_status = int(np.random.rand() < 0.28) # 28% thin-file borrowers
        
        # Vintage: 1 to 22 years
        business_vintage_years = int(np.clip(np.random.exponential(scale=5.5) + 1, 1, 25))
        
        # Annual Turnover (in INR): Log-normal distribution between ~₹6 Lakhs and ₹2.5 Crores
        annual_turnover = float(np.round(np.random.lognormal(mean=14.8, sigma=0.65), -3))
        annual_turnover = max(500000.0, annual_turnover)
        
        # Monthly Base Revenue & Expenses
        base_monthly_revenue = annual_turnover / 12.0
        profit_margin = np.random.uniform(0.10, 0.32)
        base_monthly_expenses = base_monthly_revenue * (1.0 - profit_margin)
        
        # Existing Debt & Requested Loan Amount
        debt_to_turnover_ratio = np.random.beta(a=2, b=5) * 0.7  # typically 0.05 to 0.45
        existing_debt = float(np.round(annual_turnover * debt_to_turnover_ratio, -3))
        
        loan_ratio = np.random.uniform(0.12, 0.38)
        requested_loan_amount = float(np.round(annual_turnover * loan_ratio, -3))
        
        # Payment behavior features
        if thin_file_status == 1:
            gst_regularity = float(np.round(np.random.beta(a=3.5, b=2.5), 2))
            utility_payment_timeliness = float(np.round(np.random.beta(a=4.0, b=2.5), 2))
        else:
            gst_regularity = float(np.round(np.random.beta(a=6.0, b=2.0), 2))
            utility_payment_timeliness = float(np.round(np.random.beta(a=6.5, b=2.0), 2))

        # Controlled Proxy Relationship for Fairness Demo:
        # Region strongly drives digital_payment_share (Rural lower, Urban higher)
        if region == 'Rural':
            digital_payment_share = float(np.round(np.random.beta(a=2.0, b=5.0), 2)) # mean ~0.28
        elif region == 'Semi-Urban':
            digital_payment_share = float(np.round(np.random.beta(a=4.0, b=4.0), 2)) # mean ~0.50
        else: # Urban
            digital_payment_share = float(np.round(np.random.beta(a=6.5, b=2.0), 2)) # mean ~0.76
            
        # Generate 12 Months Cash-Flow History
        monthly_inflows = []
        monthly_outflows = []
        
        for m in range(1, 13):
            # Sector seasonality
            season_factor = 1.0
            if sector == 'Retail Trade' and m in [9, 10, 11]:  # Festive peak
                season_factor = 1.25 + np.random.uniform(-0.05, 0.10)
            elif sector == 'Agri-Processing' and m in [3, 4, 10, 11]: # Harvest season
                season_factor = 1.30 + np.random.uniform(-0.05, 0.10)
            elif sector == 'Textile & Apparel' and m in [8, 9, 10]:
                season_factor = 1.20 + np.random.uniform(-0.05, 0.08)
            else:
                season_factor = 1.0 + np.random.uniform(-0.12, 0.12)
                
            volatility_factor = np.random.normal(loc=1.0, scale=0.15)
            month_inflow = max(10000.0, float(np.round(base_monthly_revenue * season_factor * volatility_factor, -2)))
            month_outflow = max(8000.0, float(np.round(base_monthly_expenses * np.random.normal(loc=1.0, scale=0.10), -2)))
            
            monthly_inflows.append(month_inflow)
            monthly_outflows.append(month_outflow)
            
            cashflow_records.append({
                'msme_id': msme_id,
                'month': m,
                'inflow': month_inflow,
                'outflow': month_outflow,
                'net_cash_flow': month_inflow - month_outflow,
                'closing_balance': float(np.round((month_inflow - month_outflow) * np.random.uniform(0.5, 1.8), -2))
            })

        avg_monthly_revenue = float(np.round(np.mean(monthly_inflows), -2))
        avg_monthly_expenses = float(np.round(np.mean(monthly_outflows), -2))
        bank_inflow = float(np.round(avg_monthly_revenue * np.random.uniform(0.92, 1.05), -2))

        # Calculate cash flow volatility metric (coefficient of variation of net cash flow)
        net_cfs = np.array(monthly_inflows) - np.array(monthly_outflows)
        cf_volatility = np.std(net_cfs) / (abs(np.mean(net_cfs)) + 1.0)

        # Risk Factors & Non-Deterministic Logistic Formula for Default Label
        # Positive risk factors: high debt/turnover, high cashflow volatility, thin file
        # Negative risk factors: high GST regularity, high utility timeliness, longer vintage
        debt_turnover_ratio = existing_debt / annual_turnover
        
        logit = (
            -0.85  # Intercept tuned for ~18% target default rate
            + 3.2 * debt_turnover_ratio
            + 1.6 * np.clip(cf_volatility, 0, 2)
            - 2.4 * gst_regularity
            - 1.8 * utility_payment_timeliness
            - 0.06 * business_vintage_years
            + 0.55 * thin_file_status
            + np.random.normal(0, 0.4)  # Controlled unobserved noise
        )
        
        prob_default = 1.0 / (1.0 + np.exp(-logit))
        default_label = int(np.random.rand() < prob_default)

        msme_records.append({
            'msme_id': msme_id,
            'sector': sector,
            'region': region,
            'gender': gender,
            'thin_file_status': thin_file_status,
            'business_vintage_years': business_vintage_years,
            'annual_turnover': annual_turnover,
            'monthly_revenue': avg_monthly_revenue,
            'monthly_expenses': avg_monthly_expenses,
            'existing_debt': existing_debt,
            'gst_regularity': gst_regularity,
            'digital_payment_share': digital_payment_share,
            'bank_inflow': bank_inflow,
            'utility_payment_timeliness': utility_payment_timeliness,
            'requested_loan_amount': requested_loan_amount,
            'default_label': default_label
        })

    df_msme = pd.DataFrame(msme_records)
    df_cashflow = pd.DataFrame(cashflow_records)

    return df_msme, df_cashflow

def save_synthetic_data(data_dir: str = "data"):
    os.makedirs(data_dir, exist_ok=True)
    df_msme, df_cashflow = generate_synthetic_msme_data(num_msmes=800, seed=42)
    
    msme_path = os.path.join(data_dir, "msme_data.csv")
    cashflow_path = os.path.join(data_dir, "monthly_cashflow.csv")
    
    df_msme.to_csv(msme_path, index=False)
    df_cashflow.to_csv(cashflow_path, index=False)
    
    print(f"[OK] Generated {len(df_msme)} synthetic MSME records saved to {msme_path}")
    print(f"[OK] Generated {len(df_cashflow)} monthly cash flow records saved to {cashflow_path}")
    print(f"   Default rate: {df_msme['default_label'].mean():.2%}")
    print(f"   Thin-file rate: {df_msme['thin_file_status'].mean():.2%}")
    
    return df_msme, df_cashflow

if __name__ == "__main__":
    save_synthetic_data()
