import os
import pytest
import pandas as pd
import numpy as np

MSME_DATA_PATH = os.path.join("data", "msme_data.csv")
CASHFLOW_DATA_PATH = os.path.join("data", "monthly_cashflow.csv")

def test_files_exist_and_loadable():
    assert os.path.exists(MSME_DATA_PATH), f"File {MSME_DATA_PATH} does not exist."
    assert os.path.exists(CASHFLOW_DATA_PATH), f"File {CASHFLOW_DATA_PATH} does not exist."
    
    df_msme = pd.read_csv(MSME_DATA_PATH)
    df_cashflow = pd.read_csv(CASHFLOW_DATA_PATH)
    
    assert not df_msme.empty, "MSME dataset is empty."
    assert not df_cashflow.empty, "Cash flow dataset is empty."

def test_msme_count_and_uniqueness():
    df_msme = pd.read_csv(MSME_DATA_PATH)
    assert 750 <= len(df_msme) <= 850, f"Expected ~800 MSMEs, found {len(df_msme)}"
    assert df_msme['msme_id'].nunique() == len(df_msme), "MSME IDs are not unique."

def test_cashflow_12_months_per_msme():
    df_msme = pd.read_csv(MSME_DATA_PATH)
    df_cashflow = pd.read_csv(CASHFLOW_DATA_PATH)
    
    # Check total cashflow record count
    expected_total_records = len(df_msme) * 12
    assert len(df_cashflow) == expected_total_records, f"Expected {expected_total_records} cashflow rows, found {len(df_cashflow)}"
    
    # Verify each MSME has exactly 12 months (1 through 12)
    counts = df_cashflow.groupby('msme_id')['month'].nunique()
    assert (counts == 12).all(), "Some MSMEs do not have exactly 12 months of cash flow records."
    
    months_per_msme = df_cashflow.groupby('msme_id')['month'].apply(set)
    expected_months = set(range(1, 13))
    for msme_id, month_set in months_per_msme.items():
        assert month_set == expected_months, f"{msme_id} missing months in cash flow series."

def test_required_columns_exist():
    df_msme = pd.read_csv(MSME_DATA_PATH)
    required_msme_cols = [
        'msme_id', 'sector', 'region', 'gender', 'thin_file_status',
        'business_vintage_years', 'annual_turnover', 'monthly_revenue',
        'monthly_expenses', 'existing_debt', 'gst_regularity',
        'digital_payment_share', 'bank_inflow', 'utility_payment_timeliness',
        'requested_loan_amount', 'default_label'
    ]
    for col in required_msme_cols:
        assert col in df_msme.columns, f"Missing required column '{col}' in msme_data.csv"
        
    df_cashflow = pd.read_csv(CASHFLOW_DATA_PATH)
    required_cf_cols = ['msme_id', 'month', 'inflow', 'outflow', 'net_cash_flow', 'closing_balance']
    for col in required_cf_cols:
        assert col in df_cashflow.columns, f"Missing required column '{col}' in monthly_cashflow.csv"

def test_no_impossible_negative_values():
    df_msme = pd.read_csv(MSME_DATA_PATH)
    non_negative_cols = [
        'business_vintage_years', 'annual_turnover', 'monthly_revenue',
        'monthly_expenses', 'existing_debt', 'gst_regularity',
        'digital_payment_share', 'bank_inflow', 'utility_payment_timeliness',
        'requested_loan_amount'
    ]
    for col in non_negative_cols:
        assert (df_msme[col] >= 0).all(), f"Column '{col}' contains negative values."

def test_class_imbalance():
    df_msme = pd.read_csv(MSME_DATA_PATH)
    default_rate = df_msme['default_label'].mean()
    assert 0.10 <= default_rate <= 0.30, f"Default rate ({default_rate:.2%}) is outside acceptable 10%-30% range."

def test_sector_and_region_variation():
    df_msme = pd.read_csv(MSME_DATA_PATH)
    assert df_msme['sector'].nunique() >= 4, "Too few sectors represented."
    assert df_msme['region'].nunique() >= 3, "Too few regions represented."
    
    region_counts = df_msme['region'].value_counts()
    for reg in ['Rural', 'Semi-Urban', 'Urban']:
        assert reg in region_counts, f"Region {reg} missing from dataset."
        assert region_counts[reg] > 50, f"Region {reg} sample size too small."

def test_proxy_relationship_exists():
    """
    Verifies controlled relationship between region and digital_payment_share
    (Rural mean digital_payment_share < Urban mean digital_payment_share)
    to enable proxy bias demonstration in Phase 7.
    """
    df_msme = pd.read_csv(MSME_DATA_PATH)
    rural_digital_mean = df_msme[df_msme['region'] == 'Rural']['digital_payment_share'].mean()
    urban_digital_mean = df_msme[df_msme['region'] == 'Urban']['digital_payment_share'].mean()
    
    assert urban_digital_mean > rural_digital_mean + 0.25, (
        f"Expected Urban digital share ({urban_digital_mean:.2f}) to be significantly higher "
        f"than Rural ({rural_digital_mean:.2f}) to act as a proxy metric."
    )
