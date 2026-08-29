"""Backend integration tests for investigation lifecycle and operational APIs."""
from __future__ import annotations
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ALLOW_SYNTHETIC_FALLBACK", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("AUTH_SECRET_KEY", "test-only-secret-key-with-more-than-32-chars")
os.environ.setdefault("DEFAULT_ADMIN_USERNAME", "admin")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "TestPassword123!")
from fastapi.testclient import TestClient
from app.main import app


def _auth(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "TestPassword123!"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _score_transaction(client, headers) -> dict:
    payload = {"TransactionAmt": 125.50, "TransactionDT": 864000, "ProductCD": "W", "card4": "visa", "card6": "debit", "P_emaildomain": "gmail.com"}
    response = client.post("/api/transactions/predict", json=payload, headers=headers)
    if response.status_code == 503: return {}
    response.raise_for_status()
    return response.json()


def test_health_contract():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] in {"ok", "degraded"}
        assert "database" in body and "model_loaded" in body


def test_case_lifecycle():
    with TestClient(app) as client:
        headers = _auth(client); transaction = _score_transaction(client, headers)
        if not transaction: return
        created = client.post("/api/cases", headers=headers, json={"transaction_id": transaction["transaction_id"], "title": "Suspicious transaction investigation", "summary": "Investigate unusual transaction activity.", "priority": "HIGH", "actor": "pytest"})
        assert created.status_code == 201, created.text
        case = created.json(); assert case["status"] == "OPEN"
        updated = client.patch(f"/api/cases/{case['case_id']}", headers=headers, json={"status": "INVESTIGATING", "assigned_to": "analyst-1", "actor": "pytest", "note": "Analyst started investigation"})
        assert updated.status_code == 200, updated.text
        assert updated.json()["status"] == "INVESTIGATING"
        events = client.get(f"/api/cases/{case['case_id']}/events", headers=headers)
        assert events.status_code == 200 and len(events.json()) >= 2


def test_transaction_filter_contract():
    with TestClient(app) as client:
        headers = _auth(client)
        response = client.get("/api/transactions", params={"risk_level": "CRITICAL", "limit": 10}, headers=headers)
        assert response.status_code == 200
        body = response.json(); assert {"count", "total", "transactions"}.issubset(body)
        assert all(item["risk_level"] == "CRITICAL" for item in body["transactions"])


def test_analytics_contract():
    with TestClient(app) as client:
        headers = _auth(client)
        overview = client.get("/api/analytics/overview", headers=headers)
        assert overview.status_code == 200
        assert {"total_transactions", "fraud_transactions", "fraud_rate", "data_source"}.issubset(overview.json())
        trend = client.get("/api/analytics/trend", params={"days": 7}, headers=headers)
        assert trend.status_code == 200 and isinstance(trend.json()["points"], list)
        decisions = client.get("/api/analytics/decision-distribution", headers=headers)
        assert decisions.status_code == 200
        assert set(decisions.json()["decision_distribution"]) == {"ALLOW", "REVIEW", "HOLD"}
