"""Investigation case lifecycle service.

Cases are intentionally independent from the presentation layer so they can
be used by investigators, managers, automation, or future integrations.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import CaseEvent, InvestigationCase

VALID_STATUSES = {"OPEN", "INVESTIGATING", "REVIEW", "ESCALATED", "APPROVED", "REJECTED", "CLOSED"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def _case_id() -> str:
    return f"CASE-{uuid.uuid4().hex[:10].upper()}"


def get_case(db: Session, case_id: str) -> InvestigationCase | None:
    return db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()


def list_cases(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: str | None = None,
    transaction_id: str | None = None,
    merchant_id: str | None = None,
):
    query = db.query(InvestigationCase)
    if status:
        query = query.filter(InvestigationCase.status == status.upper())
    if priority:
        query = query.filter(InvestigationCase.priority == priority.upper())
    if assigned_to:
        query = query.filter(InvestigationCase.assigned_to == assigned_to)
    if transaction_id:
        query = query.filter(InvestigationCase.transaction_id == transaction_id)
    if merchant_id:
        query = query.filter(InvestigationCase.merchant_id == merchant_id)
    return query.order_by(InvestigationCase.updated_at.desc()).offset(offset).limit(limit).all()


def create_case(
    db: Session,
    *,
    transaction_id: str | None,
    merchant_id: str | None,
    title: str,
    summary: str | None,
    priority: str,
    actor: str,
    assigned_to: str | None = None,
) -> InvestigationCase:
    priority = priority.upper()
    if priority not in VALID_PRIORITIES:
        raise ValueError("priority must be LOW, MEDIUM, HIGH, or CRITICAL")
    if not transaction_id and not merchant_id:
        raise ValueError("A case must reference a transaction or merchant")

    case = InvestigationCase(
        case_id=_case_id(),
        transaction_id=transaction_id,
        merchant_id=merchant_id,
        title=title.strip(),
        summary=summary.strip() if summary else None,
        priority=priority,
        assigned_to=assigned_to,
        status="OPEN",
    )
    db.add(case)
    db.flush()
    add_event(db, case.case_id, actor, "CASE_CREATED", summary or "Investigation case created")
    db.commit()
    db.refresh(case)
    return case


def update_case(
    db: Session,
    case: InvestigationCase,
    *,
    status: str | None,
    priority: str | None,
    assigned_to: str | None,
    resolution: str | None,
    actor: str,
    note: str,
) -> InvestigationCase:
    if status:
        status = status.upper()
        if status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
        if status != case.status:
            case.status = status
            if status == "CLOSED":
                case.closed_at = datetime.utcnow()
    if priority:
        priority = priority.upper()
        if priority not in VALID_PRIORITIES:
            raise ValueError("priority must be LOW, MEDIUM, HIGH, or CRITICAL")
        case.priority = priority
    if assigned_to is not None:
        case.assigned_to = assigned_to or None
    if resolution is not None:
        case.resolution = resolution.strip() or None
    if note.strip():
        add_event(db, case.case_id, actor, "CASE_UPDATED", note.strip())
    db.commit()
    db.refresh(case)
    return case


def add_event(db: Session, case_id: str, actor: str, event_type: str, note: str) -> CaseEvent:
    event = CaseEvent(case_id=case_id, actor=actor or "system", event_type=event_type, note=note.strip())
    db.add(event)
    return event


def list_events(db: Session, case_id: str, limit: int = 200):
    return (
        db.query(CaseEvent)
        .filter(CaseEvent.case_id == case_id)
        .order_by(CaseEvent.timestamp.asc())
        .limit(limit)
        .all()
    )
