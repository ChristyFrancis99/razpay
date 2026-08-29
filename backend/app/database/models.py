"""SQLAlchemy models for scored transactions, investigations, and audit events."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Index

from app.database.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    transaction_id = Column(String, index=True, nullable=False)
    previous_decision = Column(String, nullable=True)
    new_decision = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    actor = Column(String, nullable=False, default="system")
    reason = Column(Text, nullable=False)


class ScoredTransaction(Base):
    __tablename__ = "scored_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False, index=True)
    recommended_decision = Column(String, nullable=False)
    final_decision = Column(String, nullable=True, index=True)
    explanation = Column(Text, nullable=True)
    raw_payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True, nullable=False)
    transaction_id = Column(String, index=True, nullable=True)
    merchant_id = Column(String, index=True, nullable=True)
    status = Column(String, nullable=False, default="OPEN", index=True)
    priority = Column(String, nullable=False, default="MEDIUM", index=True)
    assigned_to = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("investigation_cases.case_id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    actor = Column(String, nullable=False, default="system")
    event_type = Column(String, nullable=False)
    note = Column(Text, nullable=False)


Index("ix_case_transaction_status", InvestigationCase.transaction_id, InvestigationCase.status)
Index("ix_case_merchant_status", InvestigationCase.merchant_id, InvestigationCase.status)
