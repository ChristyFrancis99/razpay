from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.database import get_db
from app.database.models import ScoredTransaction

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    total = db.query(func.count(ScoredTransaction.id)).scalar() or 0
    if total == 0:
        return {
            "total_transactions": 0,
            "fraud_transactions": 0,
            "fraud_rate": 0.0,
            "high_risk_transactions": 0,
            "critical_transactions": 0,
            "allow_count": 0,
            "review_count": 0,
            "hold_count": 0,
            "average_risk_score": 0.0,
            "note": "No transactions have been scored yet. Call POST /api/transactions/predict first.",
        }

    high_risk = db.query(func.count(ScoredTransaction.id)).filter(ScoredTransaction.risk_level == "HIGH").scalar() or 0
    critical = db.query(func.count(ScoredTransaction.id)).filter(ScoredTransaction.risk_level == "CRITICAL").scalar() or 0
    avg_score = db.query(func.avg(ScoredTransaction.risk_score)).scalar() or 0.0

    def decision_count(decision: str) -> int:
        return db.query(func.count(ScoredTransaction.id)).filter(
            func.coalesce(ScoredTransaction.final_decision, ScoredTransaction.recommended_decision) == decision
        ).scalar() or 0

    fraud_like = db.query(func.count(ScoredTransaction.id)).filter(ScoredTransaction.risk_level.in_(["HIGH", "CRITICAL"])).scalar() or 0

    return {
        "total_transactions": total,
        "high_risk_transactions": high_risk,
        "critical_transactions": critical,
        "allow_count": decision_count("ALLOW"),
        "review_count": decision_count("REVIEW"),
        "hold_count": decision_count("HOLD"),
        "average_risk_score": round(float(avg_score), 2),
        "note": "These stats cover transactions scored through this API session/DB, not the full training dataset.",
    }


@router.get("/model-performance")
def model_performance():
    metadata_path = Path(settings.MODEL_DIR) / settings.METADATA_FILE
    metrics_path = Path(settings.REPORTS_DIR) / "metrics.json"
    if not metadata_path.exists():
        raise HTTPException(status_code=503, detail="Model has not been trained yet. Run `python -m app.ml.train`.")

    with open(metadata_path) as f:
        metadata = json.load(f)
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

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
    rows = (
        db.query(ScoredTransaction.risk_level, func.count(ScoredTransaction.id))
        .group_by(ScoredTransaction.risk_level).all()
    )
    distribution = {level: count for level, count in rows}
    for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        distribution.setdefault(level, 0)
    return {"risk_distribution": distribution}
