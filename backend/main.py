from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd

from ml.config import MSME_DATA_PATH
from ml.credit_optimizer import optimize_credit_structure

app = FastAPI(
    title="CreditLens-MSME API",
    description="Explainable, fairness-aware, and stress-testable credit-risk decision-support platform for MSMEs.",
    version="1.0.0"
)

# Enable CORS for local React development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptimizeRequest(BaseModel):
    msme_id: str
    requested_loan_amount: Optional[float] = None
    requested_tenure_months: Optional[int] = 36
    interest_rate: Optional[float] = 12.0
    config_overrides: Optional[Dict[str, Any]] = None

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "CreditLens-MSME",
        "message": "Welcome to CreditLens-MSME Decision Support API",
        "notice": "This system uses 100% synthetic data."
    }

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "creditlens-msme-backend",
        "data_mode": "synthetic"
    }

@app.get("/msme-list")
@app.get("/api/msme-list")
def get_msme_list():
    try:
        df = pd.read_csv(MSME_DATA_PATH)
        msme_list = []
        for _, row in df.head(25).iterrows():
            msme_list.append({
                "msme_id": str(row["msme_id"]),
                "business_name": str(row.get("business_name", f"MSME {row['msme_id']}")),
                "sector": str(row.get("sector", "General")),
                "annual_turnover": float(row.get("annual_turnover", 0.0)),
                "requested_loan_amount": float(row.get("requested_loan_amount", 500000.0)),
                "credit_score": int(row.get("credit_score", 650))
            })
        return {"msmes": msme_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load MSME list: {str(e)}")

@app.post("/optimize-credit")
@app.post("/api/optimize-credit")
def optimize_credit_endpoint(req: OptimizeRequest):
    try:
        res = optimize_credit_structure(
            msme_id=req.msme_id,
            requested_loan_amount=req.requested_loan_amount,
            requested_tenure_months=req.requested_tenure_months,
            interest_rate=req.interest_rate,
            config_overrides=req.config_overrides
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
