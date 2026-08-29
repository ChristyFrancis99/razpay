from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import merchant_service

router = APIRouter(prefix="/api/merchants", tags=["merchants"])


@router.get("")
def list_merchants(limit: int = Query(50, le=200), offset: int = 0):
    try:
        merchants = merchant_service.list_merchants(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Merchant data unavailable: {e}")
    return {
        "count": len(merchants),
        "grouping_strategy": merchant_service.GROUPING_STRATEGY,
        "limitations": merchant_service.LIMITATIONS_TEXT,
        "merchants": merchants,
    }


@router.get("/{merchant_id}")
def get_merchant(merchant_id: str):
    investigation = merchant_service.investigate_merchant(merchant_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail=f"Merchant/entity '{merchant_id}' not found.")
    return investigation


@router.get("/{merchant_id}/risk")
def get_merchant_risk(merchant_id: str):
    risk = merchant_service.get_merchant_risk(merchant_id)
    if risk is None:
        raise HTTPException(status_code=404, detail=f"Merchant/entity '{merchant_id}' not found.")
    return risk
