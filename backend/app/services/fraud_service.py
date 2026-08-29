"""
Fraud service: orchestrates model scoring -> risk scoring -> decision ->
explanation -> persistence for a single transaction (Explainable Fraud
Agent, STEP 9, plus /transactions and /risk endpoints).
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.database.models import ScoredTransaction
from app.ml.explain import build_explanation_text
from app.ml.predict import score_transaction, ModelNotTrainedError, get_model_bundle
from app.services.risk_service import build_risk_decision

logger = logging.getLogger(__name__)


def score_and_explain(raw_row: dict, db: Optional[Session] = None) -> dict:
    """
    Full pipeline for a single transaction: model score -> risk score ->
    decision -> explanation. Optionally persists the result to the DB cache.
    """
    txn_id = str(raw_row.get("TransactionID") or f"TXN-{uuid.uuid4().hex[:8].upper()}")

    try:
        result = score_transaction(raw_row)
    except ModelNotTrainedError as e:
        raise

    top_factor_desc = result["top_risk_factors"][0]["description"] if result["top_risk_factors"] else None
    risk_decision = build_risk_decision(result["fraud_probability"], top_factor_desc)

    explanation = build_explanation_text(
        risk_decision["risk_level"], risk_decision["recommended_decision"], result["top_risk_factors"]
    )

    bundle = get_model_bundle()
    response = {
        "transaction_id": txn_id,
        "fraud_probability": round(result["fraud_probability"], 4),
        **risk_decision,
        "risk_factors": result["top_risk_factors"],
        "explanation": explanation,
        "data_source": bundle.metadata.get("data_source"),
    }

    if db is not None:
        _persist_scored_transaction(db, response, raw_row)

    return response


def _persist_scored_transaction(db: Session, response: dict, raw_row: dict) -> None:
    existing = db.query(ScoredTransaction).filter_by(transaction_id=response["transaction_id"]).first()
    if existing:
        existing.fraud_probability = response["fraud_probability"]
        existing.risk_score = response["risk_score"]
        existing.risk_level = response["risk_level"]
        existing.recommended_decision = response["recommended_decision"]
        existing.explanation = response["explanation"]
        existing.raw_payload_json = json.dumps(raw_row, default=str)
    else:
        record = ScoredTransaction(
            transaction_id=response["transaction_id"],
            fraud_probability=response["fraud_probability"],
            risk_score=response["risk_score"],
            risk_level=response["risk_level"],
            recommended_decision=response["recommended_decision"],
            explanation=response["explanation"],
            raw_payload_json=json.dumps(raw_row, default=str),
        )
        db.add(record)
    db.commit()


def get_cached_transaction(db: Session, transaction_id: str) -> Optional[ScoredTransaction]:
    return db.query(ScoredTransaction).filter_by(transaction_id=transaction_id).first()


def list_cached_transactions(db: Session, limit: int = 50, offset: int = 0):
    return (
        db.query(ScoredTransaction)
        .order_by(ScoredTransaction.created_at.desc())
        .offset(offset).limit(limit).all()
    )
