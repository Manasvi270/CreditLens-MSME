import pandas as pd
import numpy as np
from ml.stress_testing import get_stress_engine
from ml.config import MSME_DATA_PATH, CASHFLOW_DATA_PATH
from ml.forecasting import forecast_cashflow

def audit_stress_math():
    engine = get_stress_engine()
    df_msme = pd.read_csv(MSME_DATA_PATH)
    sample_ids = df_msme['msme_id'].head(5).tolist()
    
    print("=== READ-ONLY AUDIT 1: INDEPENDENT STRESS VARIABLE SENSITIVITY ===")
    print("Comparing independent impacts on 5 sample MSMEs:\n")
    
    factors = [
        ("Demand Shock (-15%)", -0.15, 0.0, 0, 0.0),
        ("Cost Inflation (+15%)", 0.0, 0.15, 0, 0.0),
        ("Receivable Delay (+30 Days)", 0.0, 0.0, 30, 0.0),
        ("Interest Rate Hike (+2%)", 0.0, 0.0, 0, 2.0)
    ]
    
    for msme_id in sample_ids:
        base = engine.run_stress_test(msme_id, 0.0, 0.0, 0, 0.0)
        b_pd = base['risk']['baseline_pd']
        b_dscr = base['dscr']['baseline_avg_dscr']
        b_el = base['expected_loss']['baseline_el']
        b_emi = base['loan']['baseline_emi']
        
        print(f"[*] {msme_id} (Base PD: {b_pd*100:.2f}%, Base DSCR: {b_dscr:.2f}, Base EMI: INR {b_emi:,.2f}, Base EL: INR {b_el:,.2f}):")
        
        for label, d_chg, c_inf, r_del, i_chg in factors:
            res = engine.run_stress_test(msme_id, d_chg, c_inf, r_del, i_chg)
            s_pd = res['risk']['stressed_pd']
            s_dscr = res['dscr']['stressed_avg_dscr']
            s_el = res['expected_loss']['stressed_el']
            s_emi = res['loan']['stressed_emi']
            
            pd_delta = s_pd - b_pd
            dscr_delta = s_dscr - b_dscr
            el_delta = s_el - b_el
            
            print(f"  - {label:<28}: PD={s_pd*100:5.2f}% (d {pd_delta*100:+5.2f}%) | Avg DSCR={s_dscr:4.2f} (d {dscr_delta:+4.2f}) | EMI=INR {s_emi:,.2f} | EL=INR {s_el:,.2f} (d INR {el_delta:+,.2f})")
            
        print()

    print("=== READ-ONLY AUDIT 2: BASELINE PRESERVATION VS PHASE 2-4 ===")
    for msme_id in sample_ids:
        base_st = engine.run_stress_test(msme_id, 0.0, 0.0, 0, 0.0)
        p4_res = forecast_cashflow(msme_id, interest_rate=12.0, tenure_months=36)
        
        pd_match = (base_st['risk']['baseline_pd'] == base_st['risk']['stressed_pd'])
        emi_match = (base_st['loan']['baseline_emi'] == p4_res['loan']['emi'])
        dscr_match = (base_st['dscr']['baseline_avg_dscr'] == p4_res['repayment_capacity']['average_base_dscr'])
        
        print(f"{msme_id}: PD Preserved={pd_match} ({base_st['risk']['baseline_pd']:.4f}) | EMI Preserved={emi_match} ({base_st['loan']['baseline_emi']:,.2f}) | Base DSCR Preserved={dscr_match} ({base_st['dscr']['baseline_avg_dscr']:.2f})")

    print("\n=== READ-ONLY AUDIT 3: EXPECTED LOSS FORMULA VERIFICATION ===")
    for msme_id in sample_ids:
        res = engine.run_stress_test(msme_id, -0.10, 0.10, 15, 1.0, lgd=0.45)
        pd_val = res['risk']['stressed_pd']
        lgd_val = res['expected_loss']['lgd_assumed']
        exp_val = res['expected_loss']['exposure']
        reported_el = res['expected_loss']['stressed_el']
        
        computed_el = round(pd_val * lgd_val * exp_val, 2)
        diff = abs(reported_el - computed_el)
        print(f"{msme_id}: PD={pd_val:.4f} * LGD={lgd_val} * Exp={exp_val:,.0f} -> Calc EL={computed_el:,.2f} | Reported EL={reported_el:,.2f} (Diff={diff:.2f})")

if __name__ == "__main__":
    audit_stress_math()
