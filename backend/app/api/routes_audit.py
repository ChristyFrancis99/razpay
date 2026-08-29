from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database.database import get_db
from app.models.schemas import AuditLogCreate, AuditLogResponse
from app.services import audit_service, fraud_service

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

@router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), transaction_id: str | None = None, actor: str | None = Query(None, max_length=120), new_decision: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if new_decision and new_decision.upper() not in {"ALLOW", "REVIEW", "HOLD"}: raise HTTPException(status_code=422, detail="new_decision must be ALLOW, REVIEW, or HOLD.")
    return audit_service.list_audit_logs(db, limit=limit, offset=offset, transaction_id=transaction_id, actor=actor, new_decision=new_decision.upper() if new_decision else None)

@router.post("", response_model=AuditLogResponse, status_code=201)
def create_audit_log(payload: AuditLogCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.get("role") not in {"MANAGER", "ADMINISTRATOR"}: raise HTTPException(status_code=403, detail="Only managers and administrators can create manual audit events.")
    transaction = fraud_service.get_cached_transaction(db, payload.transaction_id)
    if not transaction: raise HTTPException(status_code=404, detail=f"Transaction '{payload.transaction_id}' not found.")
    if payload.new_decision.upper() not in {"ALLOW", "REVIEW", "HOLD"}: raise HTTPException(status_code=422, detail="new_decision must be ALLOW, REVIEW, or HOLD.")
    if payload.risk_score != transaction.risk_score: raise HTTPException(status_code=409, detail="risk_score does not match the persisted transaction score.")
    return audit_service.create_audit_log(db, transaction_id=payload.transaction_id, previous_decision=payload.previous_decision, new_decision=payload.new_decision.upper(), risk_score=transaction.risk_score, actor=user.get("username", "system"), reason=payload.reason.strip())
