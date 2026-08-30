"""
Real-time Transaction Copilot (STEP 14).

Answers natural-language questions about a transaction or merchant using
ONLY facts actually available from the fraud model / risk engine / merchant
service — it never invents transaction facts.

Two modes:
 - LLM mode: if settings.LLM_API_KEY + LLM_PROVIDER are configured, an LLM is
   used to phrase the answer, but it is given ONLY the structured evidence
   gathered below as context (so it can't fabricate facts not in evidence).
 - Deterministic template mode (default / fallback): builds the answer with
   plain Python string templates from the same structured evidence, so the
   system works fully with zero external dependencies.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.fraud_service import get_cached_transaction, list_cached_transactions
from app.services.merchant_service import investigate_merchant

logger = logging.getLogger(__name__)


def _resolve_transaction_context(db: Session, message: str, transaction_id: Optional[str]) -> Optional[str]:
    """Resolve transaction context without requiring the UI to know an ID.

    Priority:
    1. Explicit transaction_id supplied by the frontend.
    2. A TXN-* identifier mentioned in the user's message.
    3. The most recently scored transaction, which is the natural context for
       questions such as "why was this transaction flagged?" from the Copilot.

    We never fabricate an ID. If an explicit TXN-* ID is mentioned but is not
    cached, it is returned unchanged so the normal evidence-missing response
    is shown instead of silently answering about a different transaction.
    """
    if transaction_id:
        return transaction_id

    match = re.search(r"\bTXN-[A-Z0-9_-]+\b", message.upper())
    if match:
        return match.group(0)

    latest = list_cached_transactions(db, limit=1)
    return latest[0].transaction_id if latest else None


def _gather_evidence(db: Session, transaction_id: Optional[str], merchant_id: Optional[str]) -> dict:
    evidence = {"transaction": None, "merchant": None}

    if transaction_id:
        record = get_cached_transaction(db, transaction_id)
        if record:
            evidence["transaction"] = {
                "transaction_id": record.transaction_id,
                "fraud_probability": record.fraud_probability,
                "risk_score": record.risk_score,
                "risk_level": record.risk_level,
                "recommended_decision": record.recommended_decision,
                "explanation": record.explanation,
            }

    if merchant_id:
        investigation = investigate_merchant(merchant_id)
        if investigation:
            evidence["merchant"] = investigation

    return evidence


def _deterministic_answer(message: str, evidence: dict) -> dict:
    txn = evidence.get("transaction")
    merchant = evidence.get("merchant")

    if txn:
        answer = (
            f"Transaction {txn['transaction_id']} was scored at risk level {txn['risk_level']} "
            f"(risk score {txn['risk_score']}/100, model fraud probability "
            f"{txn['fraud_probability']:.2%}), leading to a recommended decision of "
            f"{txn['recommended_decision']}. {txn['explanation']}"
        )
        key_findings = [
            f"Risk level: {txn['risk_level']}",
            f"Recommended decision: {txn['recommended_decision']}",
            f"Model fraud probability: {txn['fraud_probability']:.2%}",
        ]
        evidence_list = [{"type": "model_score", "detail": txn}]
        recommended_action = {
            "ALLOW": "No action required; continue standard processing.",
            "REVIEW": "Route to an analyst for manual review before settlement.",
            "HOLD": "Hold the transaction and escalate to fraud operations immediately.",
        }.get(txn["recommended_decision"], "Route to an analyst for manual review.")
        return {
            "answer": answer,
            "risk_score": txn["risk_score"],
            "decision": txn["recommended_decision"],
            "key_findings": key_findings,
            "evidence": evidence_list,
            "recommended_action": recommended_action,
        }

    if merchant:
        answer = merchant["ai_investigation_summary"] + " " + merchant["limitations"]
        return {
            "answer": answer,
            "risk_score": merchant["risk_score"],
            "decision": None,
            "key_findings": merchant["risk_signals"],
            "evidence": [{"type": "merchant_aggregation", "detail": {
                "transaction_volume": merchant["transaction_volume"],
                "fraud_rate": merchant["fraud_rate"],
                "trend": merchant["trend"],
            }}],
            "recommended_action": "Review top suspicious transactions listed for this entity before making a merchant-level decision.",
        }

    return {
        "answer": (
            "I don't have a scored transaction or investigated entity matching what you asked for. "
            "Please score a transaction first via /api/transactions/predict, then ask again."
        ),
        "risk_score": None,
        "decision": None,
        "key_findings": [],
        "evidence": [],
        "recommended_action": "Score at least one transaction or provide a valid merchant_id and try again.",
    }


def _llm_answer(message: str, evidence: dict) -> Optional[dict]:
    """Best-effort LLM-backed phrasing. Returns None on any failure so the
    caller falls back to the deterministic engine. The LLM is only allowed to
    phrase/summarize the evidence dict — it is instructed not to add facts."""
    if not settings.LLM_API_KEY or not settings.LLM_PROVIDER:
        return None
    try:
        # Abstraction layer: only anthropic is wired up as an example; add
        # other providers here following the same interface.
        if settings.LLM_PROVIDER == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.LLM_API_KEY)
            system_prompt = (
                "You are a fraud-risk copilot. Answer the user's question using ONLY the "
                "JSON evidence provided. Never invent transaction facts not present in the "
                "evidence. If evidence is empty, say so plainly."
            )
            resp = client.messages.create(
                model=settings.LLM_MODEL or "claude-sonnet-4-6",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Question: {message}\n\nEvidence: {evidence}"}],
            )
            text = "".join(b.text for b in resp.content if hasattr(b, "text"))
            base = _deterministic_answer(message, evidence)
            base["answer"] = text
            return base
    except Exception as e:
        logger.warning("LLM copilot call failed, falling back to deterministic engine: %s", e)
    return None


def answer_question(db: Session, message: str, transaction_id: Optional[str], merchant_id: Optional[str]) -> dict:
    resolved_transaction_id = _resolve_transaction_context(db, message, transaction_id)
    evidence = _gather_evidence(db, resolved_transaction_id, merchant_id)

    llm_result = _llm_answer(message, evidence)
    if llm_result is not None:
        llm_result["engine"] = "llm"
        return llm_result

    result = _deterministic_answer(message, evidence)
    result["engine"] = "deterministic_template"
    return result
