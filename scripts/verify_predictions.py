import pandas as pd
from ml.predict import predict_msme_risk, MSMERiskPredictor
from ml.config import MSME_DATA_PATH, CASHFLOW_DATA_PATH
from ml.preprocess import load_and_prepare_dataset

def verify_sample_predictions():
    df = load_and_prepare_dataset(MSME_DATA_PATH, CASHFLOW_DATA_PATH)
    sample_5 = df.head(5).to_dict(orient='records')
    
    print("=== SAMPLE MSME PREDICTIONS VERIFICATION ===")
    for msme in sample_5:
        res = predict_msme_risk(msme)
        actual_default = msme.get('default_label', 'N/A')
        print(f"MSME ID: {res['msme_id']} | Sector: {msme['sector']:<20} | PD: {res['pd']:.4f} ({res['pd']*100:.2f}%) | Risk Band: {res['risk_band']:<18} | Actual Default: {actual_default}")

if __name__ == "__main__":
    verify_sample_predictions()
