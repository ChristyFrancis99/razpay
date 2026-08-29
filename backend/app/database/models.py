"""ORM models: audit log + a lightweight cache of scored transactions."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from app.database.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    transaction_id = Column(String, index=True, nullable=False)
    previous_decision = Column(String, nullable=True)
    new_decision = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    actor = Column(String, nullable=False, default="system")
    reason = Column(Text, nullable=False)


class ScoredTransaction(Base):
    """Cache of scored transactions so GET /transactions/{id} and the copilot
    can retrieve prior results without re-running the model."""
    __tablename__ = "scored_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)
    recommended_decision = Column(String, nullable=False)
    final_decision = Column(String, nullable=True)
    explanation = Column(Text, nullable=True)
    raw_payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
