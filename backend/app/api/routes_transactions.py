from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import ScoredTransaction
from app.models.schemas import TransactionPredictRequest, TransactionRiskResponse
from app.services import fraud_service
from app.ml.predict import ModelNotTrainedError

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def list_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    risk_level: str | None = Query(None),
    decision: str | None = Query(None),
    search: str | None = Query(None, min_length=1, max_length=100),
    min_risk: int | None = Query(None, ge=0, le=100),
    max_risk: int | None = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    if min_risk is not None and max_risk is not None and min_risk > max_risk:
        raise HTTPException(status_code=422, detail="min_risk cannot be greater than max_risk.")

    query = db.query(ScoredTransaction)
    if risk_level:
        level = risk_level.upper()
        if level not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise HTTPException(status_code=422, detail="risk_level must be LOW, MEDIUM, HIGH, or CRITICAL.")
        query = query.filter(ScoredTransaction.risk_level == level)
    if decision:
        decision = decision.upper()
        if decision not in {"ALLOW", "REVIEW", "HOLD"}:
            raise HTTPException(status_code=422, detail="decision must be ALLOW, REVIEW, or HOLD.")
        query = query.filter(func.coalesce(ScoredTransaction.final_decision, ScoredTransaction.recommended_decision) == decision)
    if search:
        query = query.filter(ScoredTransaction.transaction_id.ilike(f"%{search}%"))
    if min_risk is not None:
        query = query.filter(ScoredTransaction.risk_score >= min_risk)
    if max_risk is not None:
        query = query.filter(ScoredTransaction.risk_score <= max_risk)

    total = query.count()
    records = query.order_by(ScoredTransaction.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "count": len(records),
        "total": total,
        "offset": offset,
        "limit": limit,
        "transactions": [
            {
                "transaction_id": r.transaction_id,
                "fraud_probability": r.fraud_probability,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level,
                "recommended_decision": r.recommended_decision,
                "final_decision": r.final_decision,
                "created_at": r.created_at,
            }
            for r in records
        ],
    }


@router.get("/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    record = fraud_service.get_cached_transaction(db, transaction_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found. Score it first via POST /api/transactions/predict.")

    raw_payload = None
    if record.raw_payload_json:
        try:
            raw_payload = json.loads(record.raw_payload_json)
        except json.JSONDecodeError:
            raw_payload = None

    return {
        "transaction_id": record.transaction_id,
        "fraud_probability": record.fraud_probability,
        "risk_score": record.risk_score,
        "risk_level": record.risk_level,
        "recommended_decision": record.recommended_decision,
        "final_decision": record.final_decision,
        "explanation": record.explanation,
        "created_at": record.created_at,
        "raw_payload": raw_payload,
    }


@router.post("/predict", response_model=TransactionRiskResponse)
def predict_transaction(payload: TransactionPredictRequest, db: Session = Depends(get_db)):
    raw_row = payload.model_dump(exclude={"extra_fields"}, exclude_none=True) if hasattr(payload, "model_dump") else payload.dict(exclude={"extra_fields"}, exclude_none=True)
    if payload.extra_fields:
        raw_row.update(payload.extra_fields)
    try:
        return fraud_service.score_and_explain(raw_row, db=db)
    except ModelNotTrainedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Transaction scoring failed.") from exc
