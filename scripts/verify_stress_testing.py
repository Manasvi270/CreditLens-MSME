import pandas as pd
from ml.stress_testing import get_stress_engine, SCENARIO_PRESETS
from ml.config import MSME_DATA_PATH

def verify_stress_testing_scenarios():
    engine = get_stress_engine()
    df_msme = pd.read_csv(MSME_DATA_PATH)
    sample_ids = df_msme['msme_id'].head(5).tolist()
    
    scenarios_to_run = ["BASELINE", "STRESS", "SEVERE_STRESS"]
    
    print("=== PHASE 5 STRESS TESTING VERIFICATION (5 SAMPLE MSMEs) ===")
    
    for msme_id in sample_ids:
        print(f"\n------------------------------------------------------------")
        print(f"[*] MSME ID: {msme_id}")
        
        for sc_name in scenarios_to_run:
            p = SCENARIO_PRESETS[sc_name]
            res = engine.run_stress_test(
                msme_id,
                demand_change=p["demand_change"],
                input_cost_inflation=p["input_cost_inflation"],
                receivable_delay_days=p["receivable_delay_days"],
                interest_rate_change=p["interest_rate_change"]
            )
            
            r = res["risk"]
            l = res["loan"]
            d = res["dscr"]
            el = res["expected_loss"]
            
            print(f"   Scenario [{sc_name:<13}]: PD={r['stressed_pd']*100:5.2f}% ({r['stressed_band']:<18}) | EMI=INR {l['stressed_emi']:,.2f} | Avg DSCR={d['stressed_avg_dscr']:4.2f} (Worst={d['worst_dscr']:4.2f}) | Months<1: {d['months_below_1']} | EL=INR {el['stressed_el']:,.2f}")
            
        # Run Sensitivity Analysis
        sens = engine.run_sensitivity_analysis(msme_id)
        print(f"   --> Sensitivity Driver: '{sens['top_dscr_driver']}' has the largest impact on DSCR.")

    print("\n\n=== RUNNING FULL PORTFOLIO STRESS TEST ACROSS ALL 800 MSMEs ===")
    port_res = engine.run_portfolio_stress_test(
        demand_change=-0.10, input_cost_inflation=0.10,
        receivable_delay_days=15, interest_rate_change=1.0
    )
    
    pm = port_res["portfolio_metrics"]
    print(f"Total MSMEs Stress Tested: {port_res['total_msmes']}")
    print(f"Average Baseline Portfolio PD: {pm['avg_baseline_pd']*100:.2f}%  --> Stressed Portfolio PD: {pm['avg_stressed_pd']*100:.2f}%")
    print(f"Total Baseline Expected Loss:  INR {pm['total_baseline_el']:,.2f} --> Stressed Expected Loss: INR {pm['total_stressed_el']:,.2f}")
    print(f"Portfolio Risk Band Downgrade Rate: {pm['downgrade_percentage']*100:.2f}%")
    print(f"Borrowers with Stressed DSCR < 1.0: {pm['shortfall_percentage']*100:.2f}%")
    print(f"Stressed Risk Band Distribution: {port_res['risk_band_distribution']['stressed']}")

if __name__ == "__main__":
    verify_stress_testing_scenarios()
