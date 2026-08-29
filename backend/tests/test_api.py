"""Backend API tests including authentication and protected endpoints."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ALLOW_SYNTHETIC_FALLBACK", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("AUTH_SECRET_KEY", "test-only-secret-key-with-more-than-32-chars")
os.environ.setdefault("DEFAULT_ADMIN_USERNAME", "admin")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "TestPassword123!")

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def token():
    response = client.post("/api/auth/login", json={"username": "admin", "password": "TestPassword123!"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers():
    return {"Authorization": f"Bearer {token()}"}


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_protected_endpoint_requires_authentication():
    assert client.get("/api/analytics/overview").status_code == 401


def test_login_and_me():
    headers = auth_headers()
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "ADMINISTRATOR"


def test_predict_valid_transaction():
    payload = {"TransactionAmt": 125.50, "TransactionDT": 86400 * 10, "ProductCD": "W", "card4": "visa", "card6": "debit", "P_emaildomain": "gmail.com"}
    resp = client.post("/api/transactions/predict", json=payload, headers=auth_headers())
    if resp.status_code == 503:
        pytest.skip("Model not trained yet — run `python -m app.ml.train` first.")
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["risk_score"] <= 100
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert body["recommended_decision"] in ("ALLOW", "REVIEW", "HOLD")


def test_predict_missing_required_field():
    resp = client.post("/api/transactions/predict", json={"card4": "visa"}, headers=auth_headers())
    assert resp.status_code == 422


def test_get_unknown_transaction_returns_404():
    resp = client.get("/api/transactions/TXN-DOES-NOT-EXIST", headers=auth_headers())
    assert resp.status_code == 404


def test_get_unknown_merchant_returns_404():
    resp = client.get("/api/merchants/does-not-exist", headers=auth_headers())
    assert resp.status_code == 404


def test_copilot_with_no_matching_transaction():
    resp = client.post("/api/copilot", json={"message": "why was this flagged?", "transaction_id": "TXN-UNKNOWN"}, headers=auth_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body["engine"] in ("llm", "deterministic_template")
    assert "evidence" in body


def test_analytics_overview_ok_with_no_data():
    resp = client.get("/api/analytics/overview", headers=auth_headers())
    assert resp.status_code == 200
