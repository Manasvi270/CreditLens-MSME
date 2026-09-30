import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from ml.config import CATEGORICAL_FEATURES, NUMERICAL_FEATURES

def extract_cashflow_features(df_cashflow: pd.DataFrame) -> pd.DataFrame:
    """
    Derives aggregated borrower-level cash flow features from 12-month historical data:
    - cf_volatility: Coefficient of variation of net cash flow
    - cf_downside_months: Number of months with negative net cash flow
    - avg_closing_balance: Mean closing bank balance across 12 months
    """
    def calc_borrower_cf_stats(group):
        net_cfs = group['net_cash_flow'].values
        mean_cf = np.mean(net_cfs)
        std_cf = np.std(net_cfs)
        cf_volatility = std_cf / (abs(mean_cf) + 1.0)
        downside_months = int(np.sum(net_cfs < 0))
        avg_balance = float(np.mean(group['closing_balance']))
        
        return pd.Series({
            'cf_volatility': cf_volatility,
            'cf_downside_months': downside_months,
            'avg_closing_balance': avg_balance
        })

    cf_stats = df_cashflow.groupby('msme_id').apply(calc_borrower_cf_stats, include_groups=False).reset_index()
    return cf_stats

def load_and_prepare_dataset(msme_path: str, cashflow_path: str) -> pd.DataFrame:
    """
    Loads raw MSME and cashflow CSV files, merges engineered cashflow features,
    and calculates baseline financial ratios.
    """
    df_msme = pd.read_csv(msme_path)
    df_cashflow = pd.read_csv(cashflow_path)
    
    # Extract cashflow features
    cf_features = extract_cashflow_features(df_cashflow)
    
    # Merge with MSME records
    df = pd.merge(df_msme, cf_features, on='msme_id', how='left')
    
    # Engineer financial ratios
    df['debt_to_turnover'] = df['existing_debt'] / (df['annual_turnover'] + 1.0)
    df['debt_to_revenue'] = df['existing_debt'] / ((df['monthly_revenue'] * 12.0) + 1.0)
    df['loan_to_turnover'] = df['requested_loan_amount'] / (df['annual_turnover'] + 1.0)
    df['expense_to_revenue'] = df['monthly_expenses'] / (df['monthly_revenue'] + 1.0)
    
    return df

def build_preprocessing_pipeline() -> ColumnTransformer:
    """
    Builds a scikit-learn ColumnTransformer for numerical scaling and categorical one-hot encoding.
    Prevents data leakage by encapsulating fit parameters within the transformer pipeline.
    """
    num_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    cat_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipeline, NUMERICAL_FEATURES),
            ('cat', cat_pipeline, CATEGORICAL_FEATURES)
        ]
    )
    
    return preprocessor
