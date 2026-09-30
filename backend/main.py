from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "CreditLens-MSME",
        "message": "Welcome to CreditLens-MSME Decision Support API",
        "notice": "This system uses 100% synthetic data."
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "creditlens-msme-backend",
        "data_mode": "synthetic"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
