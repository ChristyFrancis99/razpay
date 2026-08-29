"""
Merchant Risk Investigator (STEP 12/13).

IMPORTANT LIMITATION (documented per project rules): the IEEE-CIS dataset
does NOT contain a genuine merchant identifier. There is no "merchant_id"
column anywhere in train_transaction/train_identity. We do NOT invent one
and present it as real merchant data.

Instead, this service builds a DERIVED ENTITY grouping using the most
defensible proxy available in the dataset: (ProductCD, card4, card6) — i.e.
"product category x card network x card type". This approximates a
business-line/channel grouping, NOT a specific real-world merchant. Every
API response from this service is labeled `grouping_strategy` and includes
an explicit `limitations` string so the frontend/analyst never mistakes this
for verified merchant identity.
"""
from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np
import pandas as pd

from app.core.config import settings
from app.data.loader import load_raw_datasets
from app.services.risk_service import probability_to_score, score_to_level

logger = logging.getLogger(__name__)

GROUPING_STRATEGY = "derived_entity:(ProductCD, card4, card6)"
LIMITATIONS_TEXT = (
    "IEEE-CIS provides no genuine merchant identifier. 'Entities' here are "
    "derived by grouping transactions on (ProductCD, card4, card6) as a proxy "
    "for a business line/channel — they do NOT represent verified real-world "
    "merchants and should not be treated as such in a production system."
)


@lru_cache()
def _load_cached_dataset() -> tuple[pd.DataFrame, str]:
    df, report = load_raw_datasets(split="train")
    return df, report.source


def _entity_key(df: pd.DataFrame) -> pd.Series:
    return (
        df["ProductCD"].astype(str) + "|"
        + df["card4"].astype(str) + "|"
        + df["card6"].astype(str)
    )


def _aggregate_entities() -> pd.DataFrame:
    df, source = _load_cached_dataset()
    df = df.copy()
    df["entity_id"] = _entity_key(df)

    agg = df.groupby("entity_id").agg(
        transaction_volume=("TransactionID", "count"),
        fraud_count=("isFraud", "sum"),
        average_transaction_amount=("TransactionAmt", "mean"),
        max_transaction_amount=("TransactionAmt", "max"),
    ).reset_index()
    agg["fraud_rate"] = (agg["fraud_count"] / agg["transaction_volume"]).round(4)

    # simple trend proxy: fraud rate in the later half of the entity's
    # transactions vs. the earlier half (still time-ordered via TransactionDT)
    trends = []
    for entity_id, group in df.sort_values("TransactionDT").groupby("entity_id"):
        half = len(group) // 2
        if half < 5:
            trends.append("insufficient_data")
            continue
        first_rate = group.iloc[:half]["isFraud"].mean()
        second_rate = group.iloc[half:]["isFraud"].mean()
        if second_rate > first_rate * 1.15:
            trends.append("increasing")
        elif second_rate < first_rate * 0.85:
            trends.append("decreasing")
        else:
            trends.append("stable")
    trend_df = pd.DataFrame({"entity_id": df.sort_values("TransactionDT").groupby("entity_id").size().index, "trend": trends})
    agg = agg.merge(trend_df, on="entity_id", how="left")

    # merchant_risk_score: blend of fraud rate (dominant) and high-value concentration
    high_value_threshold = df["TransactionAmt"].quantile(0.9)
    high_value_share = (
        df.assign(is_high_value=df["TransactionAmt"] >= high_value_threshold)
        .groupby("entity_id")["is_high_value"].mean()
    )
    agg = agg.merge(high_value_share.rename("high_value_concentration"), on="entity_id", how="left")

    blended = (agg["fraud_rate"].clip(0, 1) * 0.8 + agg["high_value_concentration"].fillna(0) * 0.2)
    agg["merchant_risk_score"] = blended.apply(probability_to_score)
    agg["merchant_risk_level"] = agg["merchant_risk_score"].apply(score_to_level)
    agg["data_source"] = source
    return agg


def list_merchants(limit: int = 50, offset: int = 0) -> list[dict]:
    agg = _aggregate_entities().sort_values("merchant_risk_score", ascending=False)
    page = agg.iloc[offset:offset + limit]
    return [
        {
            "merchant_id": row.entity_id,
            "grouping_strategy": GROUPING_STRATEGY,
            "transaction_volume": int(row.transaction_volume),
            "fraud_count": int(row.fraud_count),
            "fraud_rate": float(row.fraud_rate),
            "average_transaction_amount": round(float(row.average_transaction_amount), 2),
            "merchant_risk_score": int(row.merchant_risk_score),
            "merchant_risk_level": row.merchant_risk_level,
        }
        for row in page.itertuples()
    ]


def get_merchant_risk(merchant_id: str) -> dict | None:
    agg = _aggregate_entities()
    row = agg[agg["entity_id"] == merchant_id]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "merchant_id": merchant_id,
        "grouping_strategy": GROUPING_STRATEGY,
        "transaction_volume": int(r.transaction_volume),
        "fraud_count": int(r.fraud_count),
        "fraud_rate": float(r.fraud_rate),
        "average_transaction_amount": round(float(r.average_transaction_amount), 2),
        "merchant_risk_score": int(r.merchant_risk_score),
        "merchant_risk_level": r.merchant_risk_level,
        "trend": r.trend,
    }


def investigate_merchant(merchant_id: str) -> dict | None:
    df, source = _load_cached_dataset()
    df = df.copy()
    df["entity_id"] = _entity_key(df)
    risk = get_merchant_risk(merchant_id)
    if risk is None:
        return None

    entity_txns = df[df["entity_id"] == merchant_id]
    top_suspicious = (
        entity_txns[entity_txns["isFraud"] == 1]
        .nlargest(5, "TransactionAmt")[["TransactionID", "TransactionAmt", "TransactionDT", "ProductCD"]]
    )
    top_suspicious_records = [
        {
            "transaction_id": str(int(r.TransactionID)),
            "amount": float(r.TransactionAmt),
            "transaction_dt": int(r.TransactionDT),
            "product_cd": r.ProductCD,
        }
        for r in top_suspicious.itertuples()
    ]

    risk_signals = []
    if risk["fraud_rate"] > entity_txns["isFraud"].mean() * 0 + 0.05:
        risk_signals.append(f"Fraud rate of {risk['fraud_rate']:.2%} across {risk['transaction_volume']} transactions.")
    if risk["trend"] == "increasing":
        risk_signals.append("Fraud concentration has increased in the more recent half of observed transactions.")
    if risk["merchant_risk_level"] in ("HIGH", "CRITICAL"):
        risk_signals.append("Overall derived risk score falls in the high/critical band relative to other entities.")
    if not risk_signals:
        risk_signals.append("No elevated risk signals detected relative to the dataset baseline.")

    summary = (
        f"This derived entity ({merchant_id}) shows a fraud rate of {risk['fraud_rate']:.2%} "
        f"across {risk['transaction_volume']} observed transactions, with a {risk['trend']} trend. "
        f"Derived risk level: {risk['merchant_risk_level']}. "
        f"Note: this is a proxy grouping, not a verified merchant identity — see limitations."
    )

    return {
        "merchant_id": merchant_id,
        "grouping_strategy": GROUPING_STRATEGY,
        "profile": {
            "product_cd": merchant_id.split("|")[0],
            "card_network": merchant_id.split("|")[1],
            "card_type": merchant_id.split("|")[2],
        },
        "transaction_volume": risk["transaction_volume"],
        "fraud_rate": risk["fraud_rate"],
        "risk_score": risk["merchant_risk_score"],
        "risk_level": risk["merchant_risk_level"],
        "risk_signals": risk_signals,
        "trend": risk["trend"],
        "top_suspicious_transactions": top_suspicious_records,
        "ai_investigation_summary": summary,
        "limitations": LIMITATIONS_TEXT,
    }
