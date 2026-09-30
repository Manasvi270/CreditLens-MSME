# CreditLens-MSME

> **From Credit Risk Prediction to Safer MSME Lending**
> 
> *Explainable, Fairness-Aware, and Stress-Testable Credit-Risk Decision-Support Platform for Micro, Small, and Medium Enterprises (MSMEs).*

---

> [!IMPORTANT]
> **SYNTHETIC DATA NOTICE**  
> This prototype strictly uses **100% synthetic data** for all MSME profiles, financial transactions, and cash flow simulations. It does **NOT** connect to or consume real borrower data, real GST APIs, real bank APIs, real UPI APIs, or real Account Aggregator data.

---

## 🎯 Overview

CreditLens-MSME is a decision-support system designed for credit officers, risk managers, banks/NBFCs, and compliance teams. It provides a multi-dimensional view of MSME creditworthiness beyond traditional credit bureau scoring by utilizing alternative financial metrics, explainable AI, fairness audits, stress testing, and structured loan optimization.

### Key Capabilities
1. **Portfolio Overview**: Macro-level dashboard tracking Portfolio Probability of Default (PD), Expected Loss, and risk distribution with adjustable PD cut-offs.
2. **Explainable AI (XAI)**: Borrower-level breakdown of positive & negative risk drivers, reason codes, and actionable counterfactual guidance.
3. **Cash-Flow Analysis**: 12-month historical trends + 6-month forecasts, DSCR, cash runway, and coverage analysis.
4. **Borrower Segmentation**: Categorization into Prime, Standard, Watchlist, Volatile Cash Flow, and High Risk segments with suggested actions.
5. **Fairness & Bias Audit**: Demographic disparity metrics (Disparate Impact Ratio, 4/5ths Rule) with proxy bias detection and mitigation sliders.
6. **Stress Testing**: Scenario simulation for interest rate hikes, demand slumps, inflation shocks, and payment delays.
7. **Credit Optimizer ⭐**: Grid-search recommendation engine finding safer, feasible loan structures (tenure, amount, EMI) for high-risk requests.
8. **Model Monitoring**: Population Stability Index (PSI), calibration drift, and explanation stability over time.

---

## 🛠️ Tech Stack

- **Frontend**: React, Tailwind CSS, Recharts, Lucide Icons, Vite
- **Backend**: Python, FastAPI, Uvicorn
- **ML & Analytics**: pandas, numpy, scikit-learn, XGBoost, SHAP, Fairlearn, statsmodels
- **Testing**: pytest

---

## 🚀 Getting Started

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run backend API server
python -m backend.main
# Or: uvicorn backend.main:app --reload --port 8000
```
API docs will be available at `http://localhost:8000/docs`.

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Dashboard will be available at `http://localhost:5173`.

---

## 📁 Repository Structure

```
creditlens-msme/
├── frontend/        # Vite + React + Tailwind CSS dashboard
├── backend/         # FastAPI REST service
├── ml/              # Machine learning, scoring, optimization & fairness modules
├── data/            # Synthetic dataset storage & schemas
├── tests/           # Unit & API test suite
├── docs/            # Architecture & domain documentation
├── scripts/         # Data generation & pipeline execution scripts
├── requirements.txt # Python dependencies
└── README.md        # Project documentation
```
