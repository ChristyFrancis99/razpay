from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.schemas import TransactionPredictRequest, TransactionRiskResponse
from app.services import fraud_service
from app.ml.predict import ModelNotTrainedError

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("")
def list_transactions(limit: int = Query(50, le=200), offset: int = 0, db: Session = Depends(get_db)):
    records = fraud_service.list_cached_transactions(db, limit=limit, offset=offset)
    return {
        "count": len(records),
        "transactions": [
            {
                "transaction_id": r.transaction_id,
                "fraud_probability": r.fraud_probability,
                "risk_score": r.risk_score,
                "risk_level": r.risk_level,
                "recommended_decision": r.recommended_decision,
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
    return {
        "transaction_id": record.transaction_id,
        "fraud_probability": record.fraud_probability,
        "risk_score": record.risk_score,
        "risk_level": record.risk_level,
        "recommended_decision": record.recommended_decision,
        "final_decision": record.final_decision,
        "explanation": record.explanation,
        "created_at": record.created_at,
    }


@router.post("/predict", response_model=TransactionRiskResponse)
def predict_transaction(payload: TransactionPredictRequest, db: Session = Depends(get_db)):
    raw_row = payload.dict(exclude={"extra_fields"}, exclude_none=True)
    if payload.extra_fields:
        raw_row.update(payload.extra_fields)
    try:
        result = fraud_service.score_and_explain(raw_row, db=db)
    except ModelNotTrainedError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not score transaction: {e}")
    return result
