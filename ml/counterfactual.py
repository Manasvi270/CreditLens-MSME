import numpy as np
import pandas as pd
from ml.config import get_risk_band

ACTIONABLE_FEATURES = [
    'requested_loan_amount',
    'existing_debt',
    'gst_regularity',
    'utility_payment_timeliness',
    'digital_payment_share'
]

PROTECTED_ATTRIBUTES = ['gender', 'region']

FEATURE_BOUNDS = {
    'requested_loan_amount': (100000.0, 15000000.0),
    'existing_debt': (0.0, 20000000.0),
    'gst_regularity': (0.0, 1.0),
    'utility_payment_timeliness': (0.0, 1.0),
    'digital_payment_share': (0.0, 1.0)
}

def generate_counterfactual_guidance(predictor, msme_record: dict, target_reduction: float = 0.05) -> dict:
    """
    Generates actionable counterfactual guidance for a borrower.
    Attempts feasible modifications to actionable financial features while strictly holding protected attributes constant.
    """
    original_pred = predictor.predict_single(msme_record)
    orig_pd = original_pred['pd']
    orig_band = original_pred['risk_band']
    
    # If already Prime or very low risk, counterfactual guidance is minimal
    if orig_pd <= 0.05:
        return {
            "available": True,
            "original_pd": orig_pd,
            "original_risk_band": orig_band,
            "counterfactual_pd": orig_pd,
            "counterfactual_risk_band": orig_band,
            "changes": [],
            "message": "Borrower is already in the lowest risk band ('Prime'). No structural changes required.",
            "disclaimer": "This analysis is for decision-support only and does not guarantee loan approval."
        }
        
    cf_record = msme_record.copy()
    changes = []
    
    # Strategy 1: Reduce requested loan amount by 20%
    curr_loan = float(cf_record.get('requested_loan_amount', 0.0))
    if curr_loan > 200000.0:
        new_loan = max(100000.0, round(curr_loan * 0.75, -4))
        cf_record['requested_loan_amount'] = new_loan
        changes.append({
            "feature": "requested_loan_amount",
            "original_value": curr_loan,
            "proposed_value": new_loan,
            "description": f"Reduce requested loan amount from INR {curr_loan:,.0f} to INR {new_loan:,.0f}."
        })
        
    # Strategy 2: Improve GST regularity to 0.95 if low
    curr_gst = float(cf_record.get('gst_regularity', 0.5))
    if curr_gst < 0.90:
        new_gst = 0.95
        cf_record['gst_regularity'] = new_gst
        changes.append({
            "feature": "gst_regularity",
            "original_value": curr_gst,
            "proposed_value": new_gst,
            "description": f"Improve GST filing regularity from {curr_gst:.2f} to 0.95."
        })
        
    # Strategy 3: Improve utility payment timeliness to 0.95 if low
    curr_util = float(cf_record.get('utility_payment_timeliness', 0.5))
    if curr_util < 0.90:
        new_util = 0.95
        cf_record['utility_payment_timeliness'] = new_util
        changes.append({
            "feature": "utility_payment_timeliness",
            "original_value": curr_util,
            "proposed_value": new_util,
            "description": f"Improve utility payment timeliness score from {curr_util:.2f} to 0.95."
        })

    # Ensure protected attributes were NOT altered
    for prot in PROTECTED_ATTRIBUTES:
        assert cf_record.get(prot) == msme_record.get(prot), f"Protected attribute '{prot}' was illegally altered in counterfactual generator!"
        
    cf_pred = predictor.predict_single(cf_record)
    new_pd = cf_pred['pd']
    new_band = cf_pred['risk_band']
    
    formatted_message = (
        f"Under the model, these hypothetical changes would move the predicted PD from "
        f"{orig_pd*100:.1f}% ({orig_band}) to approximately {new_pd*100:.1f}% ({new_band})."
    )
    
    return {
        "available": True,
        "original_pd": orig_pd,
        "original_risk_band": orig_band,
        "counterfactual_pd": new_pd,
        "counterfactual_risk_band": new_band,
        "changes": changes,
        "message": formatted_message,
        "disclaimer": "Under the statistical model, this hypothetical change could potentially improve the risk profile. It does not guarantee repayment or loan approval."
    }
