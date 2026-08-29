"""
API tests (STEP 20): valid transaction, invalid transaction, missing fields,
404s, and health check. Requires a trained model — run
`python -m app.ml.train` (with synthetic fallback is fine) before these
tests, or run `pytest` after `python -m app.ml.train`.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ALLOW_SYNTHETIC_FALLBACK", "true")

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_predict_valid_transaction():
    payload = {
        "TransactionAmt": 125.50,
        "TransactionDT": 86400 * 10,
        "ProductCD": "W",
        "card4": "visa",
        "card6": "debit",
        "P_emaildomain": "gmail.com",
    }
    resp = client.post("/api/transactions/predict", json=payload)
    if resp.status_code == 503:
        pytest.skip("Model not trained yet — run `python -m app.ml.train` first.")
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["risk_score"] <= 100
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert body["recommended_decision"] in ("ALLOW", "REVIEW", "HOLD")
    return body["transaction_id"]


def test_predict_missing_required_field():
    # missing TransactionAmt / TransactionDT / ProductCD
    resp = client.post("/api/transactions/predict", json={"card4": "visa"})
    assert resp.status_code == 422  # pydantic validation error


def test_get_unknown_transaction_returns_404():
    resp = client.get("/api/transactions/TXN-DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_get_unknown_merchant_returns_404():
    resp = client.get("/api/merchants/does-not-exist")
    assert resp.status_code == 404


def test_copilot_with_no_matching_transaction():
    resp = client.post("/api/copilot", json={"message": "why was this flagged?", "transaction_id": "TXN-UNKNOWN"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["engine"] in ("llm", "deterministic_template")
    assert "evidence" in body


def test_analytics_overview_ok_with_no_data():
    resp = client.get("/api/analytics/overview")
    assert resp.status_code == 200
