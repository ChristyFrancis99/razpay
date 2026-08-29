from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db
from app.database.models import ScoredTransaction

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
DECISIONS = ("ALLOW", "REVIEW", "HOLD")


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    total = db.query(func.count(ScoredTransaction.id)).scalar() or 0
    fraud_like = db.query(func.count(ScoredTransaction.id)).filter(ScoredTransaction.risk_level.in_(["HIGH", "CRITICAL"])).scalar() or 0
    high_risk = db.query(func.count(ScoredTransaction.id)).filter(ScoredTransaction.risk_level == "HIGH").scalar() or 0
    critical = db.query(func.count(ScoredTransaction.id)).filter(ScoredTransaction.risk_level == "CRITICAL").scalar() or 0
    avg_score = db.query(func.avg(ScoredTransaction.risk_score)).scalar() or 0.0

    def decision_count(decision: str) -> int:
        return db.query(func.count(ScoredTransaction.id)).filter(
            func.coalesce(ScoredTransaction.final_decision, ScoredTransaction.recommended_decision) == decision
        ).scalar() or 0

    return {
        "total_transactions": total,
        "fraud_transactions": fraud_like,
        "fraud_rate": round((fraud_like / total) * 100, 2) if total else 0.0,
        "high_risk_transactions": high_risk,
        "critical_transactions": critical,
        "allow_count": decision_count("ALLOW"),
        "review_count": decision_count("REVIEW"),
        "hold_count": decision_count("HOLD"),
        "average_risk_score": round(float(avg_score), 2),
        "data_source": "scored_transaction_cache",
        "note": "Operational statistics cover transactions scored through this API, not the training dataset.",
    }


@router.get("/model-performance")
def model_performance():
    metadata_path = Path(settings.MODEL_DIR) / settings.METADATA_FILE
    metrics_path = Path(settings.REPORTS_DIR) / "metrics.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=503, detail="Model has not been trained yet. Run `python -m app.ml.train`.")
    try:
        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)
        metrics = {}
        if metrics_path.exists():
            with open(metrics_path, encoding="utf-8") as f:
                metrics = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="Model metadata is unavailable or invalid.") from exc

    return {
        "model_name": metadata.get("model_name"),
        "data_source": metadata.get("data_source"),
        "trained_at": metadata.get("trained_at"),
        "model_comparison": metadata.get("model_comparison"),
        "test_set_metrics": metadata.get("test_set_metrics", metrics),
        "feature_selection_report": metadata.get("feature_selection_report"),
    }


@router.get("/risk-distribution")
def risk_distribution(db: Session = Depends(get_db)):
    rows = db.query(ScoredTransaction.risk_level, func.count(ScoredTransaction.id)).group_by(ScoredTransaction.risk_level).all()
    distribution = {level: 0 for level in LEVELS}
    distribution.update({level: count for level, count in rows})
    return {"risk_distribution": distribution}


@router.get("/trend")
def risk_trend(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.date(ScoredTransaction.created_at).label("day"),
            func.count(ScoredTransaction.id).label("transactions"),
            func.avg(ScoredTransaction.risk_score).label("average_risk_score"),
        )
        .filter(ScoredTransaction.created_at >= since)
        .group_by(func.date(ScoredTransaction.created_at))
        .order_by(func.date(ScoredTransaction.created_at))
        .all()
    )
    return {
        "days": days,
        "points": [
            {"date": str(day), "transactions": int(count), "average_risk_score": round(float(avg), 2)}
            for day, count, avg in rows
        ],
    }


@router.get("/decision-distribution")
def decision_distribution(db: Session = Depends(get_db)):
    rows = db.query(
        func.coalesce(ScoredTransaction.final_decision, ScoredTransaction.recommended_decision),
        func.count(ScoredTransaction.id),
    ).group_by(func.coalesce(ScoredTransaction.final_decision, ScoredTransaction.recommended_decision)).all()
    distribution = {decision: 0 for decision in DECISIONS}
    distribution.update({decision: count for decision, count in rows})
    return {"decision_distribution": distribution}
