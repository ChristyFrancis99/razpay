"""
Feature engineering for the fraud model.

Every engineered feature is documented below (name -> what it represents ->
why it may carry fraud signal). None of these features use isFraud or any
post-outcome information, so none of them leak the target.

IMPORTANT: many IEEE-CIS columns (V1-V339, most C/D columns) are provided by
Kaggle in ANONYMIZED form with no disclosed real-world meaning. We do not
claim specific real-world semantics for those columns anywhere in this code
or in any explanation text — we only describe them generically (e.g.
"anonymized engineered signal V45") per the project's implementation rules.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Human-readable documentation of every engineered feature, exposed to the
# explainability layer so descriptions shown to users are consistent.
FEATURE_DOCS: dict[str, str] = {
    "amount_log": "Log1p of TransactionAmt — compresses the heavy right tail of amounts.",
    "amount_percentile": "Percentile rank (0-1) of this transaction's amount within the full dataset.",
    "amount_vs_product_avg": "Ratio of this transaction's amount to the mean amount for its ProductCD group.",
    "hour": "Hour of day (0-23) derived from TransactionDT (seconds from a reference point).",
    "day_of_week": "Day index (0-6) derived from TransactionDT.",
    "time_period": "Coarse bucket of the day: night / morning / afternoon / evening.",
    "card_txn_count": "Number of transactions seen for this card1 value in the dataset (frequency/velocity proxy).",
    "card_amount_mean": "Mean TransactionAmt historically associated with this card1 value.",
    "amount_dev_from_card_mean": "How many standard deviations this transaction's amount is from its card's average amount.",
    "email_is_missing": "1 if P_emaildomain is missing, else 0 — missing email can correlate with risk.",
    "email_domain_freq": "How frequently this P_emaildomain appears in the dataset (rarer domains can be riskier).",
    "addr_is_missing": "1 if addr1 is missing, else 0.",
    "has_identity_info": "1 if this transaction has a matching row in the identity dataset, else 0.",
    "device_type_missing": "1 if DeviceType is missing (only meaningful when identity info is present).",
    "c_features_sum": "Sum of the C1-C14 count-style anonymized features (aggregate activity signal).",
    "d_features_missing_count": "Count of missing values across the D1-D15 anonymized time-delta features.",
    "m_match_true_count": "Count of M1-M9 match flags equal to 'T' (more matches can indicate lower risk).",
    "m_match_false_count": "Count of M1-M9 match flags equal to 'F' (more mismatches can indicate higher risk).",
}


def _time_period(hour: pd.Series) -> pd.Series:
    bins = [-1, 5, 11, 17, 21, 24]
    labels = ["night", "morning", "afternoon", "evening", "night"]
    period = pd.cut(hour, bins=bins, labels=labels, ordered=False)
    return period.astype(str)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds engineered features to a copy of df and returns it.
    Safe to call on both training and inference data (single-row or batch),
    though frequency/mean-based features are most meaningful when computed
    over a representative population (see note in preprocessing.py about
    saving these aggregates from training data for reuse at inference time).
    """
    out = df.copy()

    # --- Amount features -------------------------------------------------
    out["amount_log"] = np.log1p(out["TransactionAmt"].clip(lower=0))
    out["amount_percentile"] = out["TransactionAmt"].rank(pct=True)

    product_avg = out.groupby("ProductCD")["TransactionAmt"].transform("mean")
    out["amount_vs_product_avg"] = out["TransactionAmt"] / product_avg.replace(0, np.nan)

    # --- Time features -----------------------------------------------------
    # TransactionDT is seconds relative to an arbitrary reference point (not a
    # real timestamp) per the IEEE-CIS documentation, but hour/day-of-cycle
    # structure is still meaningful for behavioural patterns.
    seconds = out["TransactionDT"].astype(float)
    out["hour"] = ((seconds // 3600) % 24).astype(int)
    out["day_of_week"] = ((seconds // (3600 * 24)) % 7).astype(int)
    out["time_period"] = _time_period(out["hour"])

    # --- Card / velocity features -------------------------------------------
    card_counts = out.groupby("card1")["TransactionID"].transform("count")
    out["card_txn_count"] = card_counts
    card_amount_mean = out.groupby("card1")["TransactionAmt"].transform("mean")
    card_amount_std = out.groupby("card1")["TransactionAmt"].transform("std").replace(0, np.nan)
    out["card_amount_mean"] = card_amount_mean
    out["amount_dev_from_card_mean"] = (out["TransactionAmt"] - card_amount_mean) / card_amount_std

    # --- Email / address features -------------------------------------------
    out["email_is_missing"] = out["P_emaildomain"].isna().astype(int)
    domain_freq = out["P_emaildomain"].map(out["P_emaildomain"].value_counts(normalize=True, dropna=False))
    out["email_domain_freq"] = domain_freq
    out["addr_is_missing"] = out["addr1"].isna().astype(int) if "addr1" in out else 0

    # --- Identity / device features -----------------------------------------
    out["has_identity_info"] = out["DeviceType"].notna().astype(int) if "DeviceType" in out else 0
    out["device_type_missing"] = out["DeviceType"].isna().astype(int) if "DeviceType" in out else 1

    # --- Aggregated anonymized-feature signals ------------------------------
    c_cols = [c for c in out.columns if c.startswith("C") and c[1:].isdigit()]
    if c_cols:
        out["c_features_sum"] = out[c_cols].sum(axis=1)

    d_cols = [c for c in out.columns if c.startswith("D") and c[1:].isdigit()]
    if d_cols:
        out["d_features_missing_count"] = out[d_cols].isna().sum(axis=1)

    m_cols = [c for c in out.columns if c.startswith("M") and c[1:].isdigit()]
    if m_cols:
        out["m_match_true_count"] = (out[m_cols] == "T").sum(axis=1)
        out["m_match_false_count"] = (out[m_cols] == "F").sum(axis=1)

    return out


def engineered_feature_names() -> list[str]:
    return list(FEATURE_DOCS.keys())
