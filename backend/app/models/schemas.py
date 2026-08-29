"""Pydantic request/response models used across the API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------
class TransactionPredictRequest(BaseModel):
    TransactionID: Optional[int] = Field(None, description="Optional ID; generated if omitted")
    TransactionAmt: float
    TransactionDT: int = Field(..., description="Seconds relative to a reference point, per IEEE-CIS convention")
    ProductCD: str
    card1: Optional[float] = None
    card2: Optional[float] = None
    card3: Optional[float] = None
    card4: Optional[str] = None
    card5: Optional[float] = None
    card6: Optional[str] = None
    addr1: Optional[float] = None
    addr2: Optional[float] = None
    dist1: Optional[float] = None
    P_emaildomain: Optional[str] = None
    R_emaildomain: Optional[str] = None
    DeviceType: Optional[str] = None
    DeviceInfo: Optional[str] = None
    extra_fields: Optional[dict[str, Any]] = Field(
        default=None, description="Any additional raw dataset columns (C1-C14, D1-D15, M1-M9, V1-V339, id_01...)."
    )

    class Config:
        extra = "allow"


class RiskFactor(BaseModel):
    feature: str
    impact: float
    direction: str
    description: str


class TransactionRiskResponse(BaseModel):
    transaction_id: str
    fraud_probability: float
    risk_score: int
    risk_level: str
    recommended_decision: str
    decision_reason: str
    risk_factors: list[RiskFactor]
    explanation: str
    data_source: Optional[str] = None


# ---------------------------------------------------------------------------
# Risk / decision engine
# ---------------------------------------------------------------------------
class DecisionRequest(BaseModel):
    transaction_id: str
    risk_score: int
    override_decision: Optional[str] = None
    reason: Optional[str] = None
    actor: Optional[str] = "system"


class DecisionResponse(BaseModel):
    transaction_id: str
    risk_score: int
    risk_level: str
    recommended_decision: str
    final_decision: str
    decision_reason: str


# ---------------------------------------------------------------------------
# Merchants
# ---------------------------------------------------------------------------
class MerchantSummary(BaseModel):
    merchant_id: str
    grouping_strategy: str
    transaction_volume: int
    fraud_count: int
    fraud_rate: float
    average_transaction_amount: float
    merchant_risk_score: int
    merchant_risk_level: str


class MerchantInvestigation(BaseModel):
    merchant_id: str
    grouping_strategy: str
    profile: dict
    transaction_volume: int
    fraud_rate: float
    risk_score: int
    risk_level: str
    risk_signals: list[str]
    trend: str
    top_suspicious_transactions: list[dict]
    ai_investigation_summary: str
    limitations: str


# ---------------------------------------------------------------------------
# Copilot
# ---------------------------------------------------------------------------
class CopilotRequest(BaseModel):
    message: str
    transaction_id: Optional[str] = None
    merchant_id: Optional[str] = None


class CopilotResponse(BaseModel):
    answer: str
    risk_score: Optional[int] = None
    decision: Optional[str] = None
    key_findings: list[str]
    evidence: list[dict]
    recommended_action: str
    engine: str  # "llm" | "deterministic_template"


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
class AuditLogCreate(BaseModel):
    transaction_id: str
    previous_decision: Optional[str] = None
    new_decision: str
    risk_score: int
    actor: str = "system"
    reason: str


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    transaction_id: str
    previous_decision: Optional[str]
    new_decision: str
    risk_score: int
    actor: str
    reason: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class AnalyticsOverview(BaseModel):
    total_transactions: int
    fraud_transactions: int
    fraud_rate: float
    high_risk_transactions: int
    critical_transactions: int
    allow_count: int
    review_count: int
    hold_count: int
    average_risk_score: float
    data_source: str


class ModelPerformance(BaseModel):
    model_name: str
    metrics: dict
    trained_at: Optional[str] = None
    data_source: Optional[str] = None
