# CreditLens-MSME Credit Optimizer Methodology

## 📌 Overview

The **Credit Optimizer** is the core differentiating decision-support feature of CreditLens-MSME.

Instead of binary "Approve / Reject" decisions, when a requested loan structure creates excessive repayment risk, the engine performs an exhaustive grid search to discover safer, feasible financing options.

---

## 🛠️ Search Space & Variables

The optimizer explores candidate combinations of:
- **Loan Amount**: 50% to 100% of requested principal (in ₹10,000 increments).
- **Tenure**: `24`, `36`, `48`, `60` months.
- **Interest Rate**: Configurable variation around base interest rate ($\pm 1.0\%$).

---

## ⚖️ Feasibility Policy Constraints

A candidate structure is considered **feasible** only if it simultaneously satisfies:

1. **Base DSCR**: $\ge 1.20$ (Average operating cash flow covers EMI by at least $1.20\times$).
2. **Downside DSCR**: $\ge 1.00$ (Lower 80% forecast bound covers EMI by at least $1.00\times$).
3. **Downside Months Below 1.0**: $= 0$ (Zero deficit months in 6-month forecast).
4. **Probability of Default (PD)**: $\le 0.25$ ($25\%$).
5. **Principal Amount**: $\le$ Requested Loan Amount.

*Note: These are prototype underwriting policy thresholds, not regulatory requirements.*

---

## 🎯 Multi-Objective Scoring Function

Feasible candidates are ranked using a transparent multi-objective score balancing borrower funding need, repayment capacity, probability of default, and expected loss:

$$\text{Objective Score} = w_{\text{amount}} \cdot \left(\frac{\text{Amount}}{\text{Requested}}\right) + w_{\text{pd}} \cdot (1 - \text{PD}) + w_{\text{dscr}} \cdot \frac{\min(\text{Downside DSCR}, 3.0)}{3.0} + w_{\text{el}} \cdot \left(1 - \min\left(\frac{\text{EL}}{\text{Requested} \times \text{LGD}}, 1.0\right)\right)$$

### Objective Rationale & Balancing Mechanism:
- **Borrower Funding Need (40% Weight - `w_amount = 0.40`)**: Prioritizes preserving as much of the MSME's requested principal as possible, preventing excessive loan reduction when larger safe structures exist.
- **Borrower Repayment Capacity (25% Weight - `w_dscr = 0.25`)**: Rewards structures with higher downside DSCR coverage, ensuring business resilience under severe cash flow stress.
- **Lender Risk / Default Probability (25% Weight - `w_pd = 0.25`)**: Rewards candidate structures that reduce credit default risk.
- **Portfolio Loss Mitigation (10% Weight - `w_el = 0.10`)**: Rewards candidates that minimize absolute Expected Loss to protect lender capital.

- Configurable Default Weights: $w_{\text{amount}} = 0.40$, $w_{\text{pd}} = 0.25$, $w_{\text{dscr}} = 0.25$, $w_{\text{el}} = 0.10$.

---

## 🛡️ Protected Attribute Safety

- The optimizer **NEVER** mutates or uses protected demographic attributes (`gender`, `region`).
- Modifications are restricted strictly to legitimate commercial parameters (`loan_amount`, `tenure_months`, `interest_rate`).

---

## 📊 Pareto Trade-Off Frontier

The engine extracts non-dominated feasible candidates trading off:  
**Higher Loan Amount vs. Higher Downside DSCR / Lower Risk**.  
This provides underwriters with a menu of options rather than a single black-box output.

---

## ❌ Handling Cases with No Feasible Option

If no candidate satisfies all policy constraints:
- Status returned: `NO_FEASIBLE_STRUCTURE`.
- The system details the **top 3 closest rejected candidates** and explicitly reports which policy constraint was violated (e.g. `Worst Downside DSCR (0.92) < Minimum Required (1.00)`).
