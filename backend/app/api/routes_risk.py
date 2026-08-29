from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database.database import get_db
from app.models.schemas import DecisionRequest, DecisionResponse
from app.services import audit_service, fraud_service
from app.services.risk_service import decision_for_level, score_to_level

router = APIRouter(prefix="/api/risk", tags=["risk"])
VALID_DECISIONS = {"ALLOW", "REVIEW", "HOLD"}

@router.get("/{transaction_id}")
def get_risk(transaction_id: str, db: Session = Depends(get_db)):
    record = fraud_service.get_cached_transaction(db, transaction_id)
    if not record: raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
    return {"transaction_id": record.transaction_id, "risk_score": record.risk_score, "risk_level": record.risk_level, "recommended_decision": record.recommended_decision, "final_decision": record.final_decision or record.recommended_decision}

@router.post("/decision", response_model=DecisionResponse)
def make_decision(payload: DecisionRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    record = fraud_service.get_cached_transaction(db, payload.transaction_id)
    if not record: raise HTTPException(status_code=404, detail=f"Transaction '{payload.transaction_id}' not found.")
    risk_score = int(record.risk_score)
    if payload.risk_score != risk_score: raise HTTPException(status_code=409, detail="Risk score is stale. Refresh the transaction before recording a decision.")
    risk_level = score_to_level(risk_score); recommended = decision_for_level(risk_level)
    override = payload.override_decision.upper() if payload.override_decision else None
    if override and override not in VALID_DECISIONS: raise HTTPException(status_code=422, detail="override_decision must be ALLOW, REVIEW, or HOLD.")
    if not payload.reason or len(payload.reason.strip()) < 5: raise HTTPException(status_code=422, detail="A decision reason of at least 5 characters is required.")
    final_decision = override or recommended; previous_decision = record.final_decision or record.recommended_decision
    actor = user.get("username", "system")
    try:
        record.final_decision = final_decision
        audit_service.create_audit_log(db, transaction_id=payload.transaction_id, previous_decision=previous_decision, new_decision=final_decision, risk_score=risk_score, actor=actor, reason=payload.reason.strip(), commit=False)
        db.commit()
    except (SQLAlchemyError, ValueError) as exc:
        db.rollback(); raise HTTPException(status_code=500, detail="Could not persist the risk decision and audit event.") from exc
    return DecisionResponse(transaction_id=payload.transaction_id, risk_score=risk_score, risk_level=risk_level, recommended_decision=recommended, final_decision=final_decision, decision_reason=payload.reason.strip())
