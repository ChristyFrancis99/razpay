from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.schemas import DecisionRequest, DecisionResponse
from app.services import fraud_service, audit_service
from app.services.risk_service import score_to_level, decision_for_level

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/{transaction_id}")
def get_risk(transaction_id: str, db: Session = Depends(get_db)):
    record = fraud_service.get_cached_transaction(db, transaction_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
    return {
        "transaction_id": record.transaction_id,
        "risk_score": record.risk_score,
        "risk_level": record.risk_level,
        "recommended_decision": record.recommended_decision,
        "final_decision": record.final_decision or record.recommended_decision,
    }


@router.post("/decision", response_model=DecisionResponse)
def make_decision(payload: DecisionRequest, db: Session = Depends(get_db)):
    record = fraud_service.get_cached_transaction(db, payload.transaction_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Transaction '{payload.transaction_id}' not found.")

    risk_level = score_to_level(payload.risk_score)
    recommended = decision_for_level(risk_level)
    final_decision = payload.override_decision or recommended

    previous_decision = record.final_decision or record.recommended_decision
    record.final_decision = final_decision
    db.commit()

    audit_service.create_audit_log(
        db,
        transaction_id=payload.transaction_id,
        previous_decision=previous_decision,
        new_decision=final_decision,
        risk_score=payload.risk_score,
        actor=payload.actor or "system",
        reason=payload.reason or "Decision recorded via /api/risk/decision.",
    )

    return DecisionResponse(
        transaction_id=payload.transaction_id,
        risk_score=payload.risk_score,
        risk_level=risk_level,
        recommended_decision=recommended,
        final_decision=final_decision,
        decision_reason=payload.reason or f"Decision set to {final_decision} (recommended: {recommended}).",
    )
