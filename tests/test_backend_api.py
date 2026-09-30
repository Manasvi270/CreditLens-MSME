import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_msme_list_endpoint():
    response = client.get("/api/msme-list")
    assert response.status_code == 200
    data = response.json()
    assert "msmes" in data
    assert len(data["msmes"]) > 0
    first_msme = data["msmes"][0]
    assert "msme_id" in first_msme
    assert "business_name" in first_msme
    assert "sector" in first_msme

def test_optimize_credit_endpoint_success():
    payload = {
        "msme_id": "MSME_001",
        "requested_loan_amount": 639000.0,
        "requested_tenure_months": 36,
        "interest_rate": 12.0
    }
    response = client.post("/api/optimize-credit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["msme_id"] == "MSME_001"
    assert "status" in data
    assert "requested" in data
    assert "recommended" in data
    assert "borrower_explanation" in data

def test_optimize_credit_endpoint_invalid_id():
    payload = {
        "msme_id": "NON_EXISTENT_MSME_99999"
    }
    response = client.post("/api/optimize-credit", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
