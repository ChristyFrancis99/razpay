"""
Risk scoring (STEP 10) + decision engine (STEP 11).

Converts a model probability (0-1) into a 0-100 risk score and a risk level,
then maps the risk level to a recommended ALLOW/REVIEW/HOLD decision via a
configurable table (app.core.config.settings.DECISION_MAP). Thresholds are
NOT hardcoded in logic — they live in settings so they can be tuned without
code changes.

We explicitly do NOT assume the model's probability equals real-world risk;
the score is documented as "model-estimated risk on a 0-100 scale", not an
objective probability of fraud in the wild.
"""
from __future__ import annotations

from app.core.config import settings


def probability_to_score(fraud_probability: float) -> int:
    """Linear 0-1 -> 0-100 mapping, clipped to bounds."""
    score = round(max(0.0, min(1.0, fraud_probability)) * 100)
    return int(score)


def score_to_level(risk_score: int) -> str:
    if risk_score <= settings.RISK_LOW_MAX:
        return "LOW"
    if risk_score <= settings.RISK_MEDIUM_MAX:
        return "MEDIUM"
    if risk_score <= settings.RISK_HIGH_MAX:
        return "HIGH"
    return "CRITICAL"


def decision_for_level(risk_level: str) -> str:
    return settings.DECISION_MAP.get(risk_level, "REVIEW")


def decision_reason(risk_level: str, decision: str, top_factor_desc: str | None) -> str:
    base = f"Risk level classified as {risk_level}, mapped to {decision} per current policy thresholds."
    if top_factor_desc:
        base += f" Primary driver: {top_factor_desc}"
    return base


def build_risk_decision(fraud_probability: float, top_factor_desc: str | None = None) -> dict:
    risk_score = probability_to_score(fraud_probability)
    risk_level = score_to_level(risk_score)
    decision = decision_for_level(risk_level)
    reason = decision_reason(risk_level, decision, top_factor_desc)
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommended_decision": decision,
        "decision_reason": reason,
    }
