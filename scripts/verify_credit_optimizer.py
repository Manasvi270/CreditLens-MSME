import pandas as pd
from ml.credit_optimizer import optimize_credit_structure, get_credit_optimizer
from ml.config import MSME_DATA_PATH

def verify_credit_optimizer_demo():
    optimizer = get_credit_optimizer()
    df_msme = pd.read_csv(MSME_DATA_PATH)
    
    sample_ids = ["MSME_003", "MSME_001", "MSME_002", "MSME_004", "MSME_005"]
    
    print("=== PHASE 6 CREDIT OPTIMIZER DEMO VERIFICATION ===")
    
    for msme_id in sample_ids:
        res = optimizer.optimize_credit_structure(msme_id)
        req = res["requested"]
        rec = res["recommended"]
        
        print(f"\n------------------------------------------------------------")
        print(f"[*] MSME ID: {res['msme_id']} | Status: {res['status']}")
        print(f"   REQUESTED STRUCTURE:   INR {req['loan_amount']:,.2f} / {req['tenure_months']} mos @ {req['interest_rate']}% | EMI=INR {req['emi']:,.2f} | Base DSCR={req['average_base_dscr']:.2f} | Downside DSCR={req['worst_downside_dscr']:.2f} | PD={req['pd']*100:.1f}% ({req['risk_band']})")
        
        if rec:
            imp = res["improvement"]
            obj_score = res.get('objective_score', rec.get('objective_score', 1.0))
            print(f"   RECOMMENDED STRUCTURE: INR {rec['loan_amount']:,.2f} / {rec['tenure_months']} mos @ {rec['interest_rate']}% | EMI=INR {rec['emi']:,.2f} | Base DSCR={rec['average_base_dscr']:.2f} | Downside DSCR={rec['worst_downside_dscr']:.2f} | PD={rec['pd']*100:.1f}% ({rec['risk_band']}) | Obj Score={obj_score:.4f}")
            print(f"   IMPROVEMENTS: Loan Red={imp['loan_reduction_pct']}% | EMI Red={imp['emi_reduction_pct']}% | Base DSCR Change={imp['dscr_change']:+.2f} | PD Change={imp['pd_change']*100:+.1f}% | EL Change=INR {imp['expected_loss_change']:+,.2f}")
            print(f"   GRID SEARCH SUMMARY: Evaluated {res['feasible_candidates_count'] + res['rejected_candidates_count']} candidates ({res['feasible_candidates_count']} feasible, {res['rejected_candidates_count']} rejected)")
            print(f"   BORROWER EXPLANATION: \"{res['borrower_explanation']}\"")
        else:
            print(f"   REASON: {res['reason']}")
            print(f"   CLOSEST REJECTED CANDIDATE: INR {res['closest_rejected_candidates'][0]['loan_amount']:,.2f} / {res['closest_rejected_candidates'][0]['tenure_months']} mos | Violations: {res['closest_rejected_candidates'][0]['violations']}")

    print("\n\n=== RUNNING CREDIT OPTIMIZER SAMPLE BENCHMARK (25 PORTFOLIO MSMEs) ===")
    sample_25 = df_msme['msme_id'].head(25).tolist()
    
    already_feasible_cnt = 0
    optimized_cnt = 0
    no_feasible_cnt = 0
    total_evaluations = 0
    
    for msme_id in sample_25:
        r = optimizer.optimize_credit_structure(msme_id)
        status = r["status"]
        if status == "REQUESTED_FEASIBLE":
            already_feasible_cnt += 1
        elif status == "OPTIMIZED_RECOMMENDATION_FOUND":
            optimized_cnt += 1
            total_evaluations += (r["feasible_candidates_count"] + r["rejected_candidates_count"])
        elif status == "NO_FEASIBLE_STRUCTURE":
            no_feasible_cnt += 1
            total_evaluations += r["rejected_candidates_count"]
            
    print(f"Portfolio Sample MSMEs Evaluated: {len(sample_25)}")
    print(f"  - Requested Structure Already Feasible: {already_feasible_cnt} ({already_feasible_cnt/len(sample_25):.1%})")
    print(f"  - Successfully Optimized Safer Structure: {optimized_cnt} ({optimized_cnt/len(sample_25):.1%})")
    print(f"  - No Feasible Option Under Policy Limits: {no_feasible_cnt} ({no_feasible_cnt/len(sample_25):.1%})")
    print(f"Total Candidate Loan Structures Evaluated: {total_evaluations:,}")

if __name__ == "__main__":
    verify_credit_optimizer_demo()
