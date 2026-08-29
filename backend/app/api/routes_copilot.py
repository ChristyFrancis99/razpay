from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.schemas import CopilotRequest, CopilotResponse
from app.services import copilot_service

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.post("", response_model=CopilotResponse)
def copilot(payload: CopilotRequest, db: Session = Depends(get_db)):
    result = copilot_service.answer_question(
        db, message=payload.message, transaction_id=payload.transaction_id, merchant_id=payload.merchant_id
    )
    return result
