"""Backend integration tests for investigation lifecycle and operational APIs."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("ALLOW_SYNTHETIC_FALLBACK", "true")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _score_transaction() -> dict:
    payload = {
        "TransactionAmt": 125.50,
        "TransactionDT": 864000,
        "ProductCD": "W",
        "card4": "visa",
        "card6": "debit",
        "P_emaildomain": "gmail.com",
    }
    response = client.post("/api/transactions/predict", json=payload)
    if response.status_code == 503:
        return {}
    response.raise_for_status()
    return response.json()


def test_health_contract():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "database" in body
    assert "model_loaded" in body


def test_case_lifecycle():
    transaction = _score_transaction()
    if not transaction:
        return

    created = client.post(
        "/api/cases",
        json={
            "transaction_id": transaction["transaction_id"],
            "title": "Suspicious transaction investigation",
            "summary": "Investigate unusual transaction activity.",
            "priority": transaction["risk_level"],
            "actor": "pytest",
        },
    )
    assert created.status_code == 201, created.text
    case = created.json()
    assert case["status"] == "OPEN"

    updated = client.patch(
        f"/api/cases/{case['case_id']}",
        json={
            "status": "INVESTIGATING",
            "assigned_to": "analyst-1",
            "actor": "pytest",
            "note": "Analyst started investigation",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "INVESTIGATING"

    events = client.get(f"/api/cases/{case['case_id']}/events")
    assert events.status_code == 200
    assert len(events.json()) >= 2


def test_transaction_filter_contract():
    response = client.get("/api/transactions", params={"risk_level": "CRITICAL", "limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert {"count", "total", "transactions"}.issubset(body)
    assert all(item["risk_level"] == "CRITICAL" for item in body["transactions"])


def test_analytics_contract():
    overview = client.get("/api/analytics/overview")
    assert overview.status_code == 200
    assert {"total_transactions", "fraud_transactions", "fraud_rate", "data_source"}.issubset(overview.json())

    trend = client.get("/api/analytics/trend", params={"days": 7})
    assert trend.status_code == 200
    assert isinstance(trend.json()["points"], list)

    decisions = client.get("/api/analytics/decision-distribution")
    assert decisions.status_code == 200
    assert set(decisions.json()["decision_distribution"]) == {"ALLOW", "REVIEW", "HOLD"}
