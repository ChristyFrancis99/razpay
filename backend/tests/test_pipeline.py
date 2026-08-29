"""
Core pipeline tests (STEP 20). Uses the synthetic-data fallback so tests run
without requiring the real Kaggle dataset to be present.

Run with: pytest -v
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SYNTHETIC_ROWS", "3000")
os.environ.setdefault("ALLOW_SYNTHETIC_FALLBACK", "true")

import pytest

from app.data.loader import load_raw_datasets, dataset_report
from app.ml.feature_engineering import engineer_features
from app.services.risk_service import probability_to_score, score_to_level, decision_for_level, build_risk_decision


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------
def test_dataset_loads_and_joins():
    df, report = load_raw_datasets(split="train", use_synthetic=True)
    assert report.source == "synthetic"
    assert df.shape[0] > 0
    assert "isFraud" in df.columns
    assert report.shape_after_join[0] == report.transaction_shape_before_join[0]


def test_dataset_report_has_required_fields():
    df, _ = load_raw_datasets(split="train", use_synthetic=True)
    report = dataset_report(df)
    for key in ("total_transactions", "total_fraud", "fraud_percentage",
                "missing_value_percentage_overall", "number_of_features"):
        assert key in report


def test_no_duplicate_transaction_ids():
    df, _ = load_raw_datasets(split="train", use_synthetic=True)
    assert df["TransactionID"].duplicated().sum() == 0


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
def test_feature_engineering_adds_expected_columns():
    df, _ = load_raw_datasets(split="train", use_synthetic=True)
    out = engineer_features(df.head(500))
    for col in ("amount_log", "amount_percentile", "hour", "day_of_week",
                "time_period", "card_txn_count", "email_is_missing"):
        assert col in out.columns
    assert out["hour"].between(0, 23).all()


def test_feature_engineering_no_target_leakage():
    df, _ = load_raw_datasets(split="train", use_synthetic=True)
    out = engineer_features(df.head(500))
    # none of the engineered feature names should be derived directly from isFraud
    engineered_cols = set(out.columns) - set(df.columns)
    assert "isFraud" not in engineered_cols
    assert not any("fraud" in c.lower() for c in engineered_cols)


# ---------------------------------------------------------------------------
# Risk scoring boundaries
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("proba,expected_score", [(0.0, 0), (1.0, 100), (0.5, 50)])
def test_probability_to_score(proba, expected_score):
    assert probability_to_score(proba) == expected_score


@pytest.mark.parametrize("score,expected_level", [
    (0, "LOW"), (30, "LOW"), (31, "MEDIUM"), (60, "MEDIUM"),
    (61, "HIGH"), (80, "HIGH"), (81, "CRITICAL"), (100, "CRITICAL"),
])
def test_score_to_level_boundaries(score, expected_level):
    assert score_to_level(score) == expected_level


@pytest.mark.parametrize("level,expected_decision", [
    ("LOW", "ALLOW"), ("MEDIUM", "REVIEW"), ("HIGH", "REVIEW"), ("CRITICAL", "HOLD"),
])
def test_decision_thresholds(level, expected_decision):
    assert decision_for_level(level) == expected_decision


def test_build_risk_decision_end_to_end():
    result = build_risk_decision(0.92, top_factor_desc="High transaction amount")
    assert result["risk_score"] == 92
    assert result["risk_level"] == "CRITICAL"
    assert result["recommended_decision"] == "HOLD"
    assert "High transaction amount" in result["decision_reason"]


# ---------------------------------------------------------------------------
# Merchant aggregation
# ---------------------------------------------------------------------------
def test_merchant_aggregation_runs():
    from app.services import merchant_service
    merchant_service._load_cached_dataset.cache_clear()
    merchants = merchant_service.list_merchants(limit=5)
    assert len(merchants) > 0
    for m in merchants:
        assert 0 <= m["merchant_risk_score"] <= 100
        assert m["grouping_strategy"] == merchant_service.GROUPING_STRATEGY
