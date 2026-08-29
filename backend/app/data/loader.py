"""
Dataset loader for the IEEE-CIS Fraud Detection dataset.

Responsibilities:
 - locate & load train_transaction.csv / train_identity.csv (and test_* variants)
 - validate required columns exist
 - join identity data onto transaction data via TransactionID (left join,
   since most transactions have NO identity record — this is expected)
 - report shape before/after join
 - avoid loading test data unless explicitly requested (keeps training fast
   and avoids accidentally leaking test rows into training)
 - fall back to a small SYNTHETIC dataset with the same schema when the real
   Kaggle files are not present, so the rest of the pipeline is runnable.
   This is clearly flagged everywhere it happens — synthetic data must never
   be silently confused with the real dataset.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)

REQUIRED_TRANSACTION_COLUMNS = [
    "TransactionID",
    "isFraud",
    "TransactionDT",
    "TransactionAmt",
    "ProductCD",
    "card1",
    "card4",
    "card6",
]

REQUIRED_IDENTITY_COLUMNS = ["TransactionID"]


class DatasetNotFoundError(FileNotFoundError):
    pass


@dataclass
class LoadReport:
    source: str  # "real" | "synthetic"
    transaction_shape_before_join: tuple
    shape_after_join: tuple
    identity_rows_matched: int
    missing_files: list = field(default_factory=list)


def _file_path(filename: str) -> Path:
    return Path(settings.DATA_DIR) / filename


def _validate_required_columns(df: pd.DataFrame, required: list, name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _generate_synthetic_dataset(n_rows: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates a small synthetic dataset that mirrors the IEEE-CIS schema
    (column names + rough dtypes) so the full pipeline can be exercised
    without the real Kaggle files. Values are randomly generated and carry
    NO real-world meaning. This must never be presented to a user as real
    fraud data.
    """
    rng = np.random.default_rng(seed)
    n = n_rows

    fraud_rate = 0.035  # roughly matches real-world IEEE-CIS imbalance
    is_fraud = rng.binomial(1, fraud_rate, size=n)

    base_amt = rng.lognormal(mean=3.2, sigma=1.0, size=n)
    # fraudulent transactions skew slightly higher/lower amounts in this synthetic generator
    base_amt = np.where(is_fraud == 1, base_amt * rng.uniform(0.5, 3.0, size=n), base_amt)

    transaction_dt = np.sort(rng.integers(0, 86400 * 183, size=n))  # ~6 months of seconds

    product_cd = rng.choice(["W", "C", "R", "H", "S"], size=n, p=[0.6, 0.15, 0.1, 0.1, 0.05])
    card4 = rng.choice(["visa", "mastercard", "american express", "discover"], size=n, p=[0.55, 0.3, 0.1, 0.05])
    card6 = rng.choice(["debit", "credit"], size=n, p=[0.7, 0.3])
    email_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", np.nan]
    p_email = rng.choice(email_domains, size=n, p=[0.4, 0.15, 0.1, 0.1, 0.05, 0.2])

    df_txn = pd.DataFrame({
        "TransactionID": np.arange(2_987_000, 2_987_000 + n),
        "isFraud": is_fraud,
        "TransactionDT": transaction_dt,
        "TransactionAmt": base_amt.round(2),
        "ProductCD": product_cd,
        "card1": rng.integers(1000, 20000, size=n),
        "card2": rng.choice(list(range(100, 600)) + [np.nan], size=n),
        "card3": rng.choice([150.0, 185.0, 100.0, np.nan], size=n),
        "card4": card4,
        "card5": rng.choice(list(range(100, 240)) + [np.nan], size=n),
        "card6": card6,
        "addr1": rng.choice(list(range(100, 500)) + [np.nan], size=n),
        "addr2": rng.choice([87.0, 60.0, 96.0, np.nan], size=n),
        "dist1": rng.choice(list(rng.integers(0, 500, 50)) + [np.nan] * 20, size=n),
        "P_emaildomain": p_email,
        "R_emaildomain": rng.choice(email_domains, size=n, p=[0.1, 0.05, 0.05, 0.05, 0.05, 0.7]),
    })

    # C1-C14 count-style features
    for i in range(1, 15):
        df_txn[f"C{i}"] = rng.poisson(lam=2.0, size=n)
    # D1-D15 time-delta-style features (with missingness)
    for i in range(1, 16):
        vals = rng.exponential(scale=50, size=n)
        mask = rng.random(n) < 0.3
        vals[mask] = np.nan
        df_txn[f"D{i}"] = vals
    # M1-M9 match flags
    for i in range(1, 10):
        df_txn[f"M{i}"] = rng.choice(["T", "F", np.nan], size=n, p=[0.45, 0.35, 0.2])
    # V1-V339 anonymized engineered features (Kaggle-provided, meaning undisclosed)
    n_v = 60  # reduced count for a lightweight synthetic demo (real dataset has 339)
    v_block = rng.normal(0, 1, size=(n, n_v))
    for j in range(n_v):
        df_txn[f"V{j + 1}"] = v_block[:, j]

    # Identity dataset: only a subset of transactions have identity info (realistic)
    has_identity_mask = rng.random(n) < 0.24
    identity_ids = df_txn.loc[has_identity_mask, "TransactionID"].values
    m = len(identity_ids)
    df_id = pd.DataFrame({
        "TransactionID": identity_ids,
        "DeviceType": rng.choice(["mobile", "desktop", np.nan], size=m, p=[0.55, 0.35, 0.1]),
        "DeviceInfo": rng.choice(["Windows", "iOS Device", "MacOS", "Android", np.nan], size=m),
        "id_01": rng.normal(0, 5, size=m),
        "id_02": rng.integers(1000, 500000, size=m),
    })
    for i in range(3, 12):
        df_id[f"id_{i:02d}"] = rng.normal(0, 1, size=m)

    return df_txn, df_id


def load_raw_datasets(split: str = "train", use_synthetic: Optional[bool] = None) -> tuple[pd.DataFrame, LoadReport]:
    """
    Loads and joins transaction + identity data for the given split ("train" or "test").
    Returns (joined_dataframe, LoadReport).

    If the real files are absent and ALLOW_SYNTHETIC_FALLBACK is enabled (default),
    a synthetic dataset is generated instead and the report's `source` field is
    set to "synthetic" so callers/UI can display this clearly.
    """
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")

    txn_file = settings.TRANSACTION_TRAIN_FILE if split == "train" else settings.TRANSACTION_TEST_FILE
    id_file = settings.IDENTITY_TRAIN_FILE if split == "train" else settings.IDENTITY_TEST_FILE

    txn_path = _file_path(txn_file)
    id_path = _file_path(id_file)

    missing_files = [str(p) for p in (txn_path, id_path) if not p.exists()]

    should_use_synthetic = use_synthetic if use_synthetic is not None else bool(missing_files)

    if should_use_synthetic:
        if not settings.ALLOW_SYNTHETIC_FALLBACK and use_synthetic is not True:
            raise DatasetNotFoundError(
                f"Required dataset files not found: {missing_files}. "
                f"Place IEEE-CIS CSVs under {settings.DATA_DIR} or enable ALLOW_SYNTHETIC_FALLBACK."
            )
        logger.warning(
            "Real dataset files not found (%s). Falling back to SYNTHETIC data for split='%s'. "
            "This is for pipeline development/demo only — not real fraud data.",
            missing_files, split,
        )
        df_txn, df_id = _generate_synthetic_dataset(settings.SYNTHETIC_ROWS, settings.RANDOM_STATE)
        source = "synthetic"
    else:
        logger.info("Loading real dataset files: %s, %s", txn_path, id_path)
        df_txn = pd.read_csv(txn_path)
        df_id = pd.read_csv(id_path)
        source = "real"

    if split == "train":
        _validate_required_columns(df_txn, REQUIRED_TRANSACTION_COLUMNS, "train_transaction")
    else:
        # test set has no isFraud column
        req = [c for c in REQUIRED_TRANSACTION_COLUMNS if c != "isFraud"]
        _validate_required_columns(df_txn, req, "test_transaction")
    _validate_required_columns(df_id, REQUIRED_IDENTITY_COLUMNS, "identity")

    shape_before = df_txn.shape

    merged = df_txn.merge(df_id, how="left", on="TransactionID")
    matched = merged["TransactionID"].isin(df_id["TransactionID"]).sum()

    report = LoadReport(
        source=source,
        transaction_shape_before_join=shape_before,
        shape_after_join=merged.shape,
        identity_rows_matched=int(matched),
        missing_files=missing_files,
    )

    logger.info(
        "Loaded %s split (source=%s): txn shape=%s -> joined shape=%s, identity matched=%d rows",
        split, source, shape_before, merged.shape, matched,
    )

    return merged, report


def dataset_report(df: pd.DataFrame) -> dict:
    """Produces the STEP 2 dataset validation report."""
    n = len(df)
    report = {
        "total_transactions": n,
        "number_of_features": df.shape[1],
        "duplicate_transaction_ids": int(df["TransactionID"].duplicated().sum()) if "TransactionID" in df else None,
        "missing_value_percentage_overall": round(float(df.isna().mean().mean()) * 100, 3),
        "infinite_value_columns": [
            c for c in df.select_dtypes(include=[np.number]).columns
            if np.isinf(df[c]).any()
        ],
    }
    if "isFraud" in df.columns:
        fraud_count = int(df["isFraud"].sum())
        report.update({
            "total_fraud": fraud_count,
            "fraud_percentage": round(fraud_count / n * 100, 3) if n else 0.0,
            "target_distribution": df["isFraud"].value_counts().to_dict(),
        })
    return report
