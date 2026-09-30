import os
import joblib
import pandas as pd
import numpy as np

from ml.config import (
    PRIMARY_MODEL_PATH, PREPROCESSOR_PATH, MODEL_VERSION,
    CATEGORICAL_FEATURES, NUMERICAL_FEATURES, get_risk_band
)

class MSMERiskPredictor:
    def __init__(self, model_path: str = PRIMARY_MODEL_PATH, preprocessor_path: str = PREPROCESSOR_PATH):
        if not os.path.exists(model_path) or not os.path.exists(preprocessor_path):
            raise FileNotFoundError("Model artifacts not found. Please run 'python -m ml.train_model' first.")
            
        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preprocessor_path)
        self.feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES

    def _prepare_record(self, msme_record: dict) -> pd.DataFrame:
        """Helper to ensure derived financial ratios exist in input record dictionary."""
        record = msme_record.copy()
        
        # Fill missing categorical features
        for cat_col in CATEGORICAL_FEATURES:
            if cat_col not in record or pd.isna(record[cat_col]):
                record[cat_col] = 'Unknown'
                
        # Fill missing numerical features
        for num_col in NUMERICAL_FEATURES:
            if num_col not in record or pd.isna(record[num_col]):
                record[num_col] = 0.0
        
        annual_turnover = float(record.get('annual_turnover', 1.0))
        monthly_revenue = float(record.get('monthly_revenue', 1.0))
        existing_debt = float(record.get('existing_debt', 0.0))
        monthly_expenses = float(record.get('monthly_expenses', 0.0))
        requested_loan = float(record.get('requested_loan_amount', 0.0))
        
        record['debt_to_turnover'] = existing_debt / (annual_turnover + 1.0)
        record['debt_to_revenue'] = existing_debt / ((monthly_revenue * 12.0) + 1.0)
        record['loan_to_turnover'] = requested_loan / (annual_turnover + 1.0)
        record['expense_to_revenue'] = monthly_expenses / (monthly_revenue + 1.0)
            
        if 'cf_volatility' not in record or record['cf_volatility'] == 0.0:
            record['cf_volatility'] = 0.20  # Default neutral fallback if no cashflow history provided
        if 'cf_downside_months' not in record:
            record['cf_downside_months'] = 0
        if 'avg_closing_balance' not in record or record['avg_closing_balance'] == 0.0:
            record['avg_closing_balance'] = monthly_revenue * 0.15
            
        df_single = pd.DataFrame([record])
        return df_single[self.feature_cols]

    def predict_single(self, msme_record: dict) -> dict:
        """
        Predicts Probability of Default (PD) and Risk Band for a single MSME borrower.
        """
        msme_id = str(msme_record.get('msme_id', 'UNKNOWN'))
        X_df = self._prepare_record(msme_record)
        
        X_proc = self.preprocessor.transform(X_df)
        pd_val = float(self.model.predict_proba(X_proc)[0, 1])
        pd_val = float(np.round(pd_val, 4))
        
        risk_band = get_risk_band(pd_val)
        
        return {
            "msme_id": msme_id,
            "pd": pd_val,
            "risk_band": risk_band,
            "model_version": MODEL_VERSION
        }

    def predict_batch(self, df_input: pd.DataFrame) -> pd.DataFrame:
        """
        Predicts PD and Risk Band for a batch DataFrame of MSME records.
        """
        df_calc = df_input.copy()
        
        if 'debt_to_turnover' not in df_calc:
            df_calc['debt_to_turnover'] = df_calc['existing_debt'] / (df_calc['annual_turnover'] + 1.0)
        if 'debt_to_revenue' not in df_calc:
            df_calc['debt_to_revenue'] = df_calc['existing_debt'] / ((df_calc['monthly_revenue'] * 12.0) + 1.0)
        if 'loan_to_turnover' not in df_calc:
            df_calc['loan_to_turnover'] = df_calc['requested_loan_amount'] / (df_calc['annual_turnover'] + 1.0)
        if 'expense_to_revenue' not in df_calc:
            df_calc['expense_to_revenue'] = df_calc['monthly_expenses'] / (df_calc['monthly_revenue'] + 1.0)
            
        for col in ['cf_volatility', 'cf_downside_months', 'avg_closing_balance']:
            if col not in df_calc:
                df_calc[col] = 0.0
                
        X_proc = self.preprocessor.transform(df_calc[self.feature_cols])
        pds = self.model.predict_proba(X_proc)[:, 1]
        
        res = df_input.copy()
        res['pd'] = np.round(pds, 4)
        res['risk_band'] = res['pd'].apply(get_risk_band)
        return res

# Global instance lazy-loader helper
_predictor_instance = None

def predict_msme_risk(msme_record: dict) -> dict:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = MSMERiskPredictor()
    return _predictor_instance.predict_single(msme_record)
