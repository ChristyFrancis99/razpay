from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.schemas import AuditLogCreate, AuditLogResponse
from app.services import audit_service

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(100, le=500),
    offset: int = 0,
    transaction_id: str | None = None,
    db: Session = Depends(get_db),
):
    return audit_service.list_audit_logs(db, limit=limit, offset=offset, transaction_id=transaction_id)


@router.post("", response_model=AuditLogResponse)
def create_audit_log(payload: AuditLogCreate, db: Session = Depends(get_db)):
    return audit_service.create_audit_log(
        db,
        transaction_id=payload.transaction_id,
        previous_decision=payload.previous_decision,
        new_decision=payload.new_decision,
        risk_score=payload.risk_score,
        actor=payload.actor,
        reason=payload.reason,
    )
