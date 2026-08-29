"""Pydantic request/response models used across the API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TransactionPredictRequest(BaseModel):
    TransactionID: Optional[int] = Field(None, description="Optional dataset ID; generated if omitted")
    TransactionAmt: float = Field(..., gt=0)
    TransactionDT: int = Field(..., ge=0, description="Seconds relative to a reference point, per IEEE-CIS convention")
    ProductCD: str = Field(..., min_length=1)
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
        default=None, description="Additional raw dataset columns (C/D/M/V/id features)."
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


class DecisionRequest(BaseModel):
    transaction_id: str = Field(..., min_length=1)
    risk_score: int = Field(..., ge=0, le=100)
    override_decision: Optional[str] = None
    reason: Optional[str] = None
    actor: Optional[str] = Field("system", min_length=1, max_length=120)


class DecisionResponse(BaseModel):
    transaction_id: str
    risk_score: int
    risk_level: str
    recommended_decision: str
    final_decision: str
    decision_reason: str


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


class CopilotRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    transaction_id: Optional[str] = None
    merchant_id: Optional[str] = None


class CopilotResponse(BaseModel):
    answer: str
    risk_score: Optional[int] = None
    decision: Optional[str] = None
    key_findings: list[str]
    evidence: list[dict]
    recommended_action: str
    engine: str


class AuditLogCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1)
    previous_decision: Optional[str] = None
    new_decision: str
    risk_score: int = Field(..., ge=0, le=100)
    actor: str = Field("system", min_length=1, max_length=120)
    reason: str = Field(..., min_length=5, max_length=2000)


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


class CaseCreateRequest(BaseModel):
    transaction_id: Optional[str] = None
    merchant_id: Optional[str] = None
    title: str = Field(..., min_length=3, max_length=200)
    summary: Optional[str] = Field(None, max_length=4000)
    priority: str = "MEDIUM"
    assigned_to: Optional[str] = Field(None, max_length=120)
    actor: str = Field("system", min_length=1, max_length=120)


class CaseUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = Field(None, max_length=120)
    resolution: Optional[str] = Field(None, max_length=4000)
    actor: str = Field("system", min_length=1, max_length=120)
    note: str = Field("Case updated", min_length=3, max_length=2000)


class CaseEventResponse(BaseModel):
    id: int
    case_id: str
    timestamp: datetime
    actor: str
    event_type: str
    note: str

    class Config:
        from_attributes = True


class CaseResponse(BaseModel):
    case_id: str
    transaction_id: Optional[str]
    merchant_id: Optional[str]
    status: str
    priority: str
    assigned_to: Optional[str]
    title: str
    summary: Optional[str]
    resolution: Optional[str]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True
