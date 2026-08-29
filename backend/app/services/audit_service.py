"""Audit log service. Risk decisions and overrides are persisted as immutable events."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import AuditLog

VALID_DECISIONS = {"ALLOW", "REVIEW", "HOLD"}


def create_audit_log(
    db: Session,
    *,
    transaction_id: str,
    previous_decision: str | None,
    new_decision: str,
    risk_score: int,
    actor: str,
    reason: str,
    commit: bool = True,
) -> AuditLog:
    new_decision = new_decision.upper()
    if new_decision not in VALID_DECISIONS:
        raise ValueError("new_decision must be ALLOW, REVIEW, or HOLD")
    if not reason or len(reason.strip()) < 5:
        raise ValueError("reason must contain at least 5 characters")

    record = AuditLog(
        transaction_id=transaction_id,
        previous_decision=previous_decision.upper() if previous_decision else None,
        new_decision=new_decision,
        risk_score=int(risk_score),
        actor=(actor or "system").strip(),
        reason=reason.strip(),
    )
    db.add(record)
    db.flush()
    if commit:
        db.commit()
        db.refresh(record)
    return record


def list_audit_logs(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    transaction_id: str | None = None,
    actor: str | None = None,
    new_decision: str | None = None,
):
    q = db.query(AuditLog)
    if transaction_id:
        q = q.filter(AuditLog.transaction_id == transaction_id)
    if actor:
        q = q.filter(AuditLog.actor == actor)
    if new_decision:
        q = q.filter(AuditLog.new_decision == new_decision.upper())
    return q.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
