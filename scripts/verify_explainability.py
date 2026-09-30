import json
import pandas as pd
from ml.explain import explain_borrower
from ml.config import MSME_DATA_PATH, CASHFLOW_DATA_PATH
from ml.preprocess import load_and_prepare_dataset

def verify_5_sample_explanations():
    df = load_and_prepare_dataset(MSME_DATA_PATH, CASHFLOW_DATA_PATH)
    sample_ids = df['msme_id'].head(5).tolist()
    
    print("=== PHASE 3 EXPLAINABILITY VERIFICATION (5 SAMPLE MSMEs) ===")
    
    for msme_id in sample_ids:
        exp = explain_borrower(msme_id)
        
        print(f"\n------------------------------------------------------------")
        print(f"[*] MSME ID: {exp['msme_id']}")
        print(f"   Predicted PD: {exp['pd']:.4f} ({exp['pd']*100:.2f}%)")
        print(f"   Risk Band: {exp['risk_band']}")
        print(f"   Decision Policy (Thresh 0.20): {exp['decision_policy']['policy_flag']}")
        
        print("\n   [+] Top Risk-Increasing Factors:")
        for factor in exp['risk_increasing_factors'][:3]:
            print(f"      - [{factor['reason_code']}] {factor['feature']} (contrib: +{factor['contribution']:.4f}): {factor['message']}")
            
        print("\n   [-] Top Risk-Reducing Factors:")
        for factor in exp['risk_reducing_factors'][:3]:
            print(f"      - [{factor['reason_code']}] {factor['feature']} (contrib: {factor['contribution']:.4f}): {factor['message']}")
            
        print("\n   [>] Borrower-Friendly Guidance:")
        for msg in exp['borrower_guidance'][:3]:
            print(f"      - \"{msg}\"")
            
        cf = exp['counterfactual']
        print(f"\n   [~] Actionable Counterfactual Guidance:")
        if cf['changes']:
            print(f"      Original PD: {cf['original_pd']*100:.2f}% ({cf['original_risk_band']}) -> Hypothetical New PD: {cf['counterfactual_pd']*100:.2f}% ({cf['counterfactual_risk_band']})")
            for chg in cf['changes']:
                print(f"      - {chg['description']}")
            print(f"      Disclaimer: {cf['disclaimer']}")
        else:
            print(f"      {cf['message']}")

if __name__ == "__main__":
    verify_5_sample_explanations()
