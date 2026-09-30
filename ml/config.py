import os

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "ml", "models")

MSME_DATA_PATH = os.path.join(DATA_DIR, "msme_data.csv")
CASHFLOW_DATA_PATH = os.path.join(DATA_DIR, "monthly_cashflow.csv")

PRIMARY_MODEL_PATH = os.path.join(MODEL_DIR, "primary_model.joblib")
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, "preprocessor.joblib")
CHALLENGER_MODEL_PATH = os.path.join(MODEL_DIR, "challenger_model.joblib")
METRICS_REPORT_PATH = os.path.join(MODEL_DIR, "model_evaluation.json")

# Model Metadata
MODEL_VERSION = "v1.0.0-logistic-scorecard"
RANDOM_SEED = 42
DEFAULT_LGD = 0.45

# Feature Definitions
CATEGORICAL_FEATURES = ['sector', 'region', 'gender']

NUMERICAL_FEATURES = [
    'thin_file_status',
    'business_vintage_years',
    'annual_turnover',
    'monthly_revenue',
    'monthly_expenses',
    'existing_debt',
    'gst_regularity',
    'digital_payment_share',
    'bank_inflow',
    'utility_payment_timeliness',
    'requested_loan_amount',
    'debt_to_turnover',
    'debt_to_revenue',
    'loan_to_turnover',
    'expense_to_revenue',
    'cf_volatility',
    'cf_downside_months',
    'avg_closing_balance'
]

# Configurable Risk Band Cut-offs (Probability of Default)
RISK_BANDS = [
    {"name": "Prime", "max_pd": 0.05, "description": "Lowest risk profile, high repayment likelihood."},
    {"name": "Standard", "max_pd": 0.15, "description": "Low-to-moderate risk profile, acceptable standard lending."},
    {"name": "Watchlist", "max_pd": 0.30, "description": "Moderate risk, requires closer monitoring or enhanced collateral."},
    {"name": "Volatile Cash Flow", "max_pd": 0.50, "description": "High cash flow volatility or debt burden, requires caution."},
    {"name": "High Risk", "max_pd": 1.00, "description": "Very high risk of default under current requested terms."}
]

def get_risk_band(pd_value: float) -> str:
    """Map a Probability of Default (0.0 - 1.0) to a configurable risk band name."""
    pd_clamped = min(max(pd_value, 0.0), 1.0)
    for band in RISK_BANDS:
        if pd_clamped <= band["max_pd"]:
            return band["name"]
    return "High Risk"
