# CreditLens-MSME Explainability Architecture

## 🎯 Overview

CreditLens-MSME enforces **Explainable AI (XAI)** at both global and borrower levels. Because credit decisions directly impact businesses and livelihoods, black-box predictions are unacceptable.

Our primary risk engine uses a **Calibrated Logistic Scorecard**, which provides exact mathematical transparency without relying on complex approximations.

---

## 🏛️ Explainability Layers

### 1. Global Scorecard Feature Importance
- Extracts log-odds coefficients ($\beta_i$) from the scorecard.
- Categorizes features by direction:
  - **Risk-Increasing Factors**: Positive coefficients ($\beta_i > 0$), where higher feature values are associated with higher predicted PD.
  - **Risk-Reducing Factors**: Negative coefficients ($\beta_i < 0$), where higher feature values are associated with lower predicted PD.
- Uses strict non-causal language ("associated with higher/lower predicted risk").

### 2. Individual Borrower Explanations
For any given borrower application:
- Computes exact contribution: $\text{Contribution}_i = x_i \cdot \beta_i$.
- Ranks top 3–5 risk-increasing and risk-reducing drivers.
- Maps contributions to standardized **Reason Codes** (e.g. `RC01` to `RC16`).

### 3. Borrower-Friendly Guidance
- Translates technical scorecard metrics into clear natural language.
- Eliminates technical jargon (e.g. "log-odds", "z-scores", "coefficients").
- Example: *"Your existing debt is high compared to your business turnover."*

### 4. Actionable Counterfactual Guidance
- Identifies smallest feasible modifications to actionable metrics (`requested_loan_amount`, `gst_regularity`, `utility_payment_timeliness`).
- **Strict Constraint**: Protected demographic attributes (`gender`, `region`) are **NEVER** modified in counterfactual generation.
- Quantifies hypothetical PD impact:  
  *"Under the model, this hypothetical change would move the predicted PD from 20.7% to approximately 14.2%."*
- Includes non-causal disclaimers ("Hypothetical guidance only; does not guarantee loan approval").

---

## 🏷️ Standardized Reason Code Registry

| Reason Code | Category / Feature | Direction | Standard Message |
| :--- | :--- | :--- | :--- |
| **`RC01`** | Debt to Turnover | Risk Increasing | High debt relative to annual turnover is associated with higher predicted risk. |
| **`RC02`** | Cash Flow Volatility | Risk Increasing | High cash flow volatility is associated with higher predicted risk. |
| **`RC03`** | Utility Timeliness | Risk Increasing | Delays in utility bill payments are associated with higher predicted risk. |
| **`RC04`** | Business Vintage | Risk Increasing | Shorter business vintage is associated with higher predicted risk. |
| **`RC05`** | GST Regularity | Risk Increasing | Irregular GST filing history is associated with higher predicted risk. |
| **`RC06`** | Utility Timeliness | Risk Reducing | Timely utility bill payment history is associated with lower predicted risk. |
| **`RC07`** | Debt to Turnover | Risk Reducing | Low debt relative to annual turnover is associated with lower predicted risk. |
| **`RC08`** | Cash Flow Volatility | Risk Reducing | Consistent and stable net cash flow is associated with lower predicted risk. |
| **`RC09`** | Business Vintage | Risk Reducing | Longer business vintage is associated with lower predicted risk. |
| **`RC10`** | GST Regularity | Risk Reducing | Regular and on-time GST filing history is associated with lower predicted risk. |
