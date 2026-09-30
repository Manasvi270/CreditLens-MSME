# CreditLens-MSME Data Dictionary

> **Disclaimer**: This project utilizes 100% synthetic data generated for decision support system prototyping. No real borrower identity or sensitive banking API data is used.

---

## 📊 Dataset 1: `msme_data.csv` (800 Unique MSME Records)

| Field Name | Type | Description | Values / Range |
| :--- | :--- | :--- | :--- |
| `msme_id` | String (PK) | Unique borrower identifier | `MSME_001` to `MSME_800` |
| `sector` | Categorical | MSME business operating sector | Retail Trade, Light Manufacturing, Services, Textile & Apparel, Agri-Processing, Handicrafts & Artisan |
| `region` | Categorical | Geographic region category | Rural, Semi-Urban, Urban |
| `gender` | Categorical | Business owner gender | Female, Male |
| `thin_file_status` | Binary | Indicator if borrower has limited credit bureau history | `0` (Established history), `1` (Thin file) |
| `business_vintage_years` | Integer | Number of years the enterprise has been operational | 1 to 25 years |
| `annual_turnover` | Float (INR) | Total annual revenue/sales turnover in INR | ₹5,000,000 to ₹25,000,000+ |
| `monthly_revenue` | Float (INR) | Average monthly gross inflow/sales revenue | Computed from cash flow & turnover |
| `monthly_expenses` | Float (INR) | Average monthly operating costs & expenses | Computed from cash flow & margin |
| `existing_debt` | Float (INR) | Total outstanding debt/loans prior to request | ₹50,000 to ₹10,000,000+ |
| `gst_regularity` | Float (0-1) | Score measuring proportion of on-time GST filing | `0.00` (Irregular) to `1.00` (Perfect) |
| `digital_payment_share` | Float (0-1) | Percentage of business transactions via digital modes (UPI/POS/Cards) | `0.00` to `1.00` (Controlled proxy metric) |
| `bank_inflow` | Float (INR) | Average monthly bank statement verified inflows | INR currency |
| `utility_payment_timeliness`| Float (0-1) | Score measuring electricity/water/telco bill payment timeliness | `0.00` (Frequent delays) to `1.00` (On-time) |
| `requested_loan_amount` | Float (INR) | Principal amount requested by MSME | ₹100,000 to ₹8,000,000+ |
| `default_label` | Binary (Target) | Observed credit default outcome over 12-month horizon | `0` (Non-default / Healthy), `1` (Default / Distressed) |

---

## 📈 Dataset 2: `monthly_cashflow.csv` (9,600 Historical Monthly Records)

Each of the 800 MSMEs has exactly 12 months of consecutive historical cash flow records.

| Field Name | Type | Description | Values / Range |
| :--- | :--- | :--- | :--- |
| `msme_id` | String (FK) | Foreign key referencing `msme_data.csv` | `MSME_001` to `MSME_800` |
| `month` | Integer | Historical month index | `1` (Oldest) to `12` (Most recent) |
| `inflow` | Float (INR) | Total cash receipts/inflows during the month | Seasonally adjusted cash inflow |
| `outflow` | Float (INR) | Total operating expenses & debt payments during the month | Monthly operating cash outflow |
| `net_cash_flow` | Float (INR) | Monthly net cash surplus/deficit (`inflow - outflow`) | Positive or Negative INR amount |
| `closing_balance` | Float (INR) | End-of-month bank account closing balance | Operating liquidity buffer |
