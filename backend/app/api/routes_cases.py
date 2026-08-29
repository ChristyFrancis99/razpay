from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database.database import get_db
from app.models.schemas import CaseCreateRequest, CaseEventResponse, CaseResponse, CaseUpdateRequest
from app.services import case_service, fraud_service

router = APIRouter(prefix="/api/cases", tags=["investigations"])

def _validate_reference(db: Session, transaction_id: str | None, merchant_id: str | None) -> None:
    if transaction_id and not fraud_service.get_cached_transaction(db, transaction_id): raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found.")
    if not transaction_id and not merchant_id: raise HTTPException(status_code=422, detail="transaction_id or merchant_id is required.")

def _write_role(user: dict):
    if user.get("role") not in {"INVESTIGATOR", "MANAGER", "ADMINISTRATOR"}: raise HTTPException(status_code=403, detail="Insufficient permissions")

@router.get("", response_model=list[CaseResponse])
def list_cases(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), status: str | None = None, priority: str | None = None, assigned_to: str | None = None, transaction_id: str | None = None, merchant_id: str | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return case_service.list_cases(db, limit=limit, offset=offset, status=status, priority=priority, assigned_to=assigned_to, transaction_id=transaction_id, merchant_id=merchant_id)

@router.post("", response_model=CaseResponse, status_code=201)
def create_case(payload: CaseCreateRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _write_role(user); _validate_reference(db, payload.transaction_id, payload.merchant_id)
    try:
        return case_service.create_case(db, transaction_id=payload.transaction_id, merchant_id=payload.merchant_id, title=payload.title, summary=payload.summary, priority=payload.priority, actor=user.get("username", "system"), assigned_to=payload.assigned_to)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    case = case_service.get_case(db, case_id)
    if not case: raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case

@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(case_id: str, payload: CaseUpdateRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _write_role(user); case = case_service.get_case(db, case_id)
    if not case: raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    if payload.status in {"APPROVED", "REJECTED", "CLOSED", "ESCALATED"} and user.get("role") not in {"MANAGER", "ADMINISTRATOR"}:
        raise HTTPException(status_code=403, detail="Manager or administrator approval is required for final/escalation case states.")
    try:
        return case_service.update_case(db, case, status=payload.status, priority=payload.priority, assigned_to=payload.assigned_to, resolution=payload.resolution, actor=user.get("username", "system"), note=payload.note)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/{case_id}/events", response_model=list[CaseEventResponse])
def get_case_events(case_id: str, limit: int = Query(200, ge=1, le=500), db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not case_service.get_case(db, case_id): raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    return case_service.list_events(db, case_id, limit=limit)
