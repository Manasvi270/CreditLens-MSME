# CreditLens-MSME Cash Flow & Repayment Capacity Methodology

## 📌 Overview

The Cash-Flow Forecasting & Repayment Capacity module answers the fundamental underwriting question:  
> **"Can this MSME generate sufficient operating cash flow to service its proposed debt EMI?"**

To maintain clean underwriting rigor, **Operating Repayment Capacity** (pure operating cash flow) is separated from **Available Liquidity Reserves**.

---

## 📈 1. Historical Cash Flow & Forecasting Engine

- **Input**: 12 months of historical cash inflows, outflows, and net cash flow from verified transactions/bank statements.
- **Forecasting Model**: **Holt's Linear Exponential Smoothing** (trend-adjusted forecasting).
- **Horizon**: 6 future months (Months 13 to 18).
- **Lower 80% Forecast Bound**:  
  Calculated using scaled residual variance ($z_{0.80} \approx 1.2815$):
  $$\text{Lower 80\% Forecast Bound}_h = \text{Base Net Cash Flow}_h - \left( 1.2815 \cdot \sigma_{\text{residual}} \cdot \sqrt{1 + 0.08 \cdot h} \right)$$
- **Statistical Interval Disclaimer**: This is a statistical prediction interval representing forecast variance; it is not a macro-economic stress scenario.

---

## 💳 2. Loan EMI Calculation

Calculated using the standard financial Equated Monthly Installment formula:

$$\text{EMI} = \frac{P \cdot r \cdot (1+r)^n}{(1+r)^n - 1}$$

- $P$: Principal loan amount (INR)
- $r$: Monthly interest rate ($\text{Annual Rate} / 12 / 100$)
- $n$: Loan tenure in months

---

## 📊 3. Separated DSCR & Liquidity Metrics

### A. Operating Repayment Capacity
$$\text{Base DSCR}_t = \frac{\text{Forecast Net Cash Flow}_t}{\text{EMI}}$$

$$\text{Downside DSCR}_t = \frac{\text{Lower 80\% Forecast Bound}_t}{\text{EMI}}$$

### B. Liquidity Reserve & Coverage
$$\text{Liquidity Reserve} = 25\% \times \text{Average Historical Bank Closing Balance}$$

$$\text{Liquidity Coverage} = \frac{\text{Liquidity Reserve}}{\text{EMI}}$$
*(Measures how many months of EMI are backed by the liquidity reserve buffer).*

---

## ⚠️ 4. Downside Scenario & Assessment

- **Downside Months Below DSCR 1.0**: Counts the number of months in the 6-month forecast where $\text{Downside DSCR}_t < 1.0$.
- **Interpretation Guide**:
  - $\text{Avg Base DSCR} \ge 1.40$ & $0$ downside months below 1.0 $\rightarrow$ **Strong**
  - $\text{Avg Base DSCR} \ge 1.10$ & $\le 2$ downside months below 1.0 $\rightarrow$ **Moderate**
  - Otherwise $\rightarrow$ **Weak**
