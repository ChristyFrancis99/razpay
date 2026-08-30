"""Seed the local Risk Intelligence database with real IEEE-CIS demo transactions.

This script intentionally does NOT copy the IEEE-CIS dataset into the repository.
It reads the user's local CSVs in chunks, scores a small representative sample with
the SAME inference pipeline used by the API, and persists only the scored results
needed by the dashboard.

Run from the backend directory:
    python -m scripts.seed_demo_data

The real dataset is required. This script never silently falls back to synthetic data.
"""
from __future__ import annotations

import argparse
import logging
import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.core.config import settings
from app.database.database import SessionLocal, init_db
from app.database.models import ScoredTransaction
from app.services.fraud_service import score_and_explain

logger = logging.getLogger("seed_demo_data")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed scored IEEE-CIS transactions for the local demo dashboard.")
    parser.add_argument("--rows", type=int, default=100, help="Number of scored transactions to persist (default: 100).")
    parser.add_argument(
        "--candidate-pool",
        type=int,
        default=400,
        help="Candidate rows to score before selecting a balanced risk mix (default: 400).",
    )
    parser.add_argument("--seed", type=int, default=settings.RANDOM_STATE, help="Deterministic sampling seed.")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete ALL existing scored transactions before seeding. Use only for a disposable local demo database.",
    )
    return parser


def _paths() -> tuple[Path, Path]:
    txn_path = Path(settings.DATA_DIR) / settings.TRANSACTION_TRAIN_FILE
    identity_path = Path(settings.DATA_DIR) / settings.IDENTITY_TRAIN_FILE
    missing = [str(p) for p in (txn_path, identity_path) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "IEEE-CIS training files were not found. Put train_transaction.csv and "
            f"train_identity.csv in {settings.DATA_DIR}. Missing: {', '.join(missing)}"
        )
    return txn_path, identity_path


def _sample_candidates(txn_path: Path, pool_per_class: int, seed: int) -> pd.DataFrame:
    """Read the large transaction CSV in chunks and keep a bounded sample per target class."""
    rng = np.random.default_rng(seed)
    samples: dict[int, list[pd.DataFrame]] = {0: [], 1: []}
    collected = {0: 0, 1: 0}

    # Keep the complete row schema so feature engineering sees the same raw fields
    # available during normal inference. chunksize keeps memory bounded.
    for chunk in pd.read_csv(txn_path, chunksize=10_000, low_memory=False):
        if "isFraud" not in chunk.columns or "TransactionID" not in chunk.columns:
            raise ValueError("train_transaction.csv must contain TransactionID and isFraud columns.")

        for target in (0, 1):
            subset = chunk[chunk["isFraud"] == target]
            if subset.empty:
                continue
            remaining = pool_per_class - collected[target]
            if remaining <= 0:
                continue
            take = min(remaining, len(subset))
            # Sampling within each chunk avoids retaining the full dataset in memory.
            sampled = subset.sample(n=take, random_state=int(rng.integers(0, 2**31 - 1)))
            samples[target].append(sampled)
            collected[target] += take

        if all(collected[t] >= pool_per_class for t in (0, 1)):
            break

    if not samples[0] and not samples[1]:
        raise RuntimeError("No rows could be sampled from train_transaction.csv.")

    frames = [pd.concat(samples[t], ignore_index=True) for t in (0, 1) if samples[t]]
    candidates = pd.concat(frames, ignore_index=True)
    candidates = candidates.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return candidates


def _merge_identity(candidates: pd.DataFrame, identity_path: Path) -> pd.DataFrame:
    """Join identity rows only for the selected candidate TransactionIDs."""
    ids = set(pd.to_numeric(candidates["TransactionID"], errors="coerce").dropna().astype("int64").tolist())
    identity_parts: list[pd.DataFrame] = []

    for chunk in pd.read_csv(identity_path, chunksize=20_000, low_memory=False):
        if "TransactionID" not in chunk.columns:
            raise ValueError("train_identity.csv must contain TransactionID.")
        numeric_ids = pd.to_numeric(chunk["TransactionID"], errors="coerce")
        matched = chunk[numeric_ids.isin(ids)]
        if not matched.empty:
            identity_parts.append(matched)

    if not identity_parts:
        return candidates.copy()

    identity = pd.concat(identity_parts, ignore_index=True).drop_duplicates("TransactionID")
    return candidates.merge(identity, how="left", on="TransactionID", suffixes=("", "_identity"))


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    return value


def _row_to_dict(row: pd.Series) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    for key, value in row.items():
        if key == "isFraud":
            # Target is used only for sampling/validation and must never be sent to inference.
            continue
        if str(key).endswith("_identity"):
            continue
        safe = _json_safe(value)
        if safe is not None:
            raw[str(key)] = safe
    # Ensure TransactionID remains an integer-like value where possible.
    if "TransactionID" in raw:
        raw["TransactionID"] = int(float(raw["TransactionID"]))
    return raw


def _select_balanced(scored: list[dict[str, Any]], rows: int) -> list[dict[str, Any]]:
    """Prefer a useful LOW/MEDIUM/HIGH/CRITICAL mix, then fill remaining slots."""
    low_quota = max(1, round(rows * 0.30))
    medium_quota = max(1, round(rows * 0.25))
    high_quota = max(1, round(rows * 0.25))
    critical_quota = max(1, rows - low_quota - medium_quota - high_quota)
    quotas = {
        "LOW": low_quota,
        "MEDIUM": medium_quota,
        "HIGH": high_quota,
        "CRITICAL": critical_quota,
    }

    buckets: dict[str, list[dict[str, Any]]] = {level: [] for level in quotas}
    for item in scored:
        level = item.get("risk_level")
        if level in buckets:
            buckets[level].append(item)

    selected: list[dict[str, Any]] = []
    for level, quota in quotas.items():
        # For higher-risk buckets choose the strongest examples; for LOW choose the safest.
        reverse = level in {"HIGH", "CRITICAL"}
        bucket = sorted(buckets[level], key=lambda x: x["fraud_probability"], reverse=reverse)
        selected.extend(bucket[:quota])

    if len(selected) < rows:
        selected_ids = {item["transaction_id"] for item in selected}
        remaining = [item for item in scored if item["transaction_id"] not in selected_ids]
        remaining.sort(key=lambda x: x["fraud_probability"], reverse=True)
        selected.extend(remaining[: rows - len(selected)])

    return selected[:rows]


def main() -> int:
    args = _parser().parse_args()
    if args.rows < 1 or args.candidate_pool < args.rows:
        raise SystemExit("--rows must be >= 1 and --candidate-pool must be >= --rows.")

    random.seed(args.seed)
    np.random.seed(args.seed)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    txn_path, identity_path = _paths()
    init_db()

    db = SessionLocal()
    try:
        if args.clear:
            deleted = db.query(ScoredTransaction).delete(synchronize_session=False)
            db.commit()
            logger.warning("Cleared %d existing scored transactions.", deleted)

        existing = {row[0] for row in db.query(ScoredTransaction.transaction_id).all()}

        # Split the candidate pool evenly by isFraud so the demo has a chance to expose
        # a meaningful range of model outputs instead of selecting only normal rows.
        pool_per_class = max(1, (args.candidate_pool + 1) // 2)
        candidates = _sample_candidates(txn_path, pool_per_class=pool_per_class, seed=args.seed)
        candidates = candidates[~candidates["TransactionID"].astype(str).isin(existing)].copy()
        candidates = _merge_identity(candidates, identity_path)

        logger.info("Candidate rows available for scoring: %d", len(candidates))
        if candidates.empty:
            logger.info("All sampled transactions are already present. Nothing to seed.")
            return 0

        scored: list[dict[str, Any]] = []
        for _, row in candidates.iterrows():
            try:
                raw = _row_to_dict(row)
                result = score_and_explain(raw, db=None)
                result["_raw_row"] = raw
                result["_target_is_fraud"] = int(row["isFraud"])
                scored.append(result)
            except Exception as exc:
                logger.warning("Skipping candidate %s: %s", row.get("TransactionID"), exc)
            if len(scored) >= args.candidate_pool:
                break

        if not scored:
            raise RuntimeError("No candidate transaction could be scored. Confirm the trained model artifacts are available.")

        selected = _select_balanced(scored, args.rows)
        seeded = 0
        for item in selected:
            # Reuse the same production scoring/persistence function. This is deliberate:
            # demo records must follow exactly the same path as POST /api/transactions/predict.
            score_and_explain(item["_raw_row"], db=db)
            seeded += 1

        db.commit()

        levels = pd.Series([item["risk_level"] for item in selected]).value_counts().to_dict()
        decisions = pd.Series([item["recommended_decision"] for item in selected]).value_counts().to_dict()
        fraud_targets = pd.Series([item["_target_is_fraud"] for item in selected]).value_counts().to_dict()

        logger.info("Seeded %d transactions into %s", seeded, settings.DATABASE_URL)
        logger.info("Risk levels: %s", levels)
        logger.info("Recommended decisions: %s", decisions)
        logger.info("Original IEEE-CIS target labels in selected sample (not used by inference): %s", fraud_targets)
        logger.info("Refresh the frontend and open Transactions / Investigations.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
