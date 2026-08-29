"""Audit log service (STEP 16). Every risk decision / override is recorded."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import AuditLog


def create_audit_log(db: Session, *, transaction_id: str, previous_decision: str | None,
                      new_decision: str, risk_score: int, actor: str, reason: str) -> AuditLog:
    record = AuditLog(
        transaction_id=transaction_id,
        previous_decision=previous_decision,
        new_decision=new_decision,
        risk_score=risk_score,
        actor=actor,
        reason=reason,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_audit_logs(db: Session, limit: int = 100, offset: int = 0, transaction_id: str | None = None):
    q = db.query(AuditLog)
    if transaction_id:
        q = q.filter(AuditLog.transaction_id == transaction_id)
    return q.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
