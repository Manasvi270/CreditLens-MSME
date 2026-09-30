import pandas as pd

df_msme = pd.read_csv("data/msme_data.csv")
df_cashflow = pd.read_csv("data/monthly_cashflow.csv")

print("=== DATASET SUMMARY STATISTICS ===")
print(f"Total Unique MSMEs: {len(df_msme)}")
print(f"Total Cashflow Rows: {len(df_cashflow)} (12 months per MSME)")
print(f"Default Rate: {df_msme['default_label'].mean():.2%} ({df_msme['default_label'].sum()} Defaults / {len(df_msme) - df_msme['default_label'].sum()} Non-Defaults)")
print(f"Thin-File Borrower Rate: {df_msme['thin_file_status'].mean():.2%}")
print(f"Average Annual Turnover: INR {df_msme['annual_turnover'].mean():,.2f}")
print(f"Average Requested Loan: INR {df_msme['requested_loan_amount'].mean():,.2f}")

print("\n=== DIGITAL PAYMENT SHARE BY REGION (PROXY FEATURE) ===")
print(df_msme.groupby('region')['digital_payment_share'].agg(['mean', 'std', 'min', 'max']))

print("\n=== SECTOR DISTRIBUTION ===")
print(df_msme['sector'].value_counts())

print("\n=== 5 SAMPLE MSME RECORDS ===")
cols = ['msme_id', 'sector', 'region', 'gender', 'thin_file_status', 'annual_turnover', 'existing_debt', 'requested_loan_amount', 'default_label']
print(df_msme[cols].head(5).to_string(index=False))
