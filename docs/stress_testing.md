# CreditLens-MSME Stress Testing Methodology

## 📌 Overview

The Stress Testing Module simulates macro-economic and business shock scenarios across MSME credit profiles to answer:  
> **"What happens to an MSME's credit risk (PD), operating cash flows, EMI affordability, and DSCR if economic conditions deteriorate?"**

It unifies the **Risk Model**, **Cash-Flow Forecast**, and **DSCR Framework** into an integrated scenario analysis engine.

---

## 🛠️ Stress Variables & Ranges

| Stress Variable | Configurable Range | Description |
| :--- | :--- | :--- |
| `demand_change` | `-30%` to `+20%` | Revenue/demand shock altering sales volume. |
| `input_cost_inflation` | `0%` to `+30%` | Inflationary operating cost increase. |
| `receivable_delay_days` | `0` to `60` days | Commercial payment collection delay (working capital drag). |
| `interest_rate_change` | `-2%` to `+5%` (pts) | Benchmark interest rate hike impacting loan EMI. |

---

## ⚙️ Configurable Scenario Presets

1. **`BASELINE`**: Demand `0%`, Cost Inflation `0%`, Delay `0 days`, Rate `0%`.
2. **`STRESS`**: Demand `-10%`, Cost Inflation `+10%`, Delay `15 days`, Rate `+1.0%`.
3. **`SEVERE_STRESS`**: Demand `-20%`, Cost Inflation `+20%`, Delay `30 days`, Rate `+2.0%`.
4. **`BOOM`**: Demand `+10%`, Cost Inflation `-5%`, Delay `-10 days`, Rate `-1.0%`.

---

## 🧮 Cash Flow & Risk Model Mechanics

### 1. Stressed Inflows & Outflows
$$\text{Stressed Inflow}_t = \text{Base Inflow}_t \times (1 + \text{demand\_change}) \times \left(1 - \frac{\text{receivable\_delay\_days}}{90}\right)$$

$$\text{Stressed Outflow}_t = \text{Base Outflow}_t \times (1 + \text{input\_cost\_inflation})$$

$$\text{Stressed Net Cash Flow}_t = \text{Stressed Inflow}_t - \text{Stressed Outflow}_t$$

### 2. Stressed EMI Calculation
$$\text{Stressed Rate} = \text{Base Rate} + \text{interest\_rate\_change}$$
$$\text{Stressed EMI} = \text{EMI}(P, \text{Stressed Rate}, n)$$

### 3. Risk Model Re-Scoring
Borrower features (`monthly_revenue`, `monthly_expenses`, `debt_to_turnover`, `cf_volatility`, `expense_to_revenue`) are recomputed under stress and passed through the primary Calibrated Scorecard model to generate **Stressed PD** and **Stressed Risk Band**.

### 4. Expected Loss (EL)
$$\text{Expected Loss} = \text{PD} \times \text{LGD} \times \text{Exposure}$$
- $\text{LGD} = 0.45$ (Default prototype Loss Given Default assumption).
- $\text{Exposure} = \text{Requested Loan Amount}$.

---

## ⚠️ Important Disclosure
- **Scenario Output Disclaimer**: Stress testing outputs represent hypothetical model simulations. They are not predictions of real-world macro default rates or guaranteed economic forecasts.
