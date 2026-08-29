"""
Training pipeline.

Runnable as a script:

    python -m app.ml.train

Or imported and called via run_training_pipeline().

Flow: load -> validate -> feature engineer -> time-aware split -> preprocess
-> feature select -> train + compare 3 model families -> evaluate -> pick
best model by validation PR-AUC (appropriate for imbalanced fraud data,
more informative than ROC-AUC alone) -> save model + preprocessor + selected
features + metadata.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from app.core.config import settings
from app.data.loader import load_raw_datasets, dataset_report
from app.ml.feature_engineering import engineer_features
from app.ml.preprocessing import build_preprocessor, split_column_types, get_output_feature_names
from app.ml.feature_selection import select_features, save_selected_features
from app.ml.evaluate import evaluate_model, save_evaluation_artifacts

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def time_aware_split(df: pd.DataFrame, test_size: float, val_size: float) -> dict:
    """
    Splits by TransactionDT (a monotonically increasing relative-time value in
    IEEE-CIS) so validation/test always come strictly AFTER training in time,
    avoiding the leakage that a random shuffle-split would introduce for
    temporal transaction data.
    """
    df_sorted = df.sort_values("TransactionDT").reset_index(drop=True)
    n = len(df_sorted)
    n_test = int(n * test_size)
    n_val = int(n * val_size)
    n_train = n - n_test - n_val

    train_df = df_sorted.iloc[:n_train]
    val_df = df_sorted.iloc[n_train:n_train + n_val]
    test_df = df_sorted.iloc[n_train + n_val:]

    periods = {
        "train_period": [int(train_df["TransactionDT"].min()), int(train_df["TransactionDT"].max())],
        "validation_period": [int(val_df["TransactionDT"].min()), int(val_df["TransactionDT"].max())],
        "test_period": [int(test_df["TransactionDT"].min()), int(test_df["TransactionDT"].max())],
        "train_rows": n_train, "validation_rows": n_val, "test_rows": len(test_df),
    }
    logger.info("Time-aware split: %s", periods)
    return {"train": train_df, "val": val_df, "test": test_df, "periods": periods}


def run_training_pipeline() -> dict:
    t0 = time.time()
    Path(settings.MODEL_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.REPORTS_DIR).mkdir(parents=True, exist_ok=True)

    # --- STEP 1/2: load + validate ---------------------------------------
    df, load_report = load_raw_datasets(split="train")
    report = dataset_report(df)
    logger.info("Dataset report: %s", report)
    if load_report.source == "synthetic":
        logger.warning(
            "TRAINING ON SYNTHETIC DATA — real IEEE-CIS files were not found under %s. "
            "This run demonstrates that the pipeline works end-to-end, but the resulting "
            "model has NO real fraud-detection validity. Place the real Kaggle CSVs and "
            "re-run to train a meaningful model.", settings.DATA_DIR,
        )

    # --- STEP 4: feature engineering ---------------------------------------
    df_fe = engineer_features(df)

    # --- STEP 7: time-aware split -------------------------------------------
    splits = time_aware_split(df_fe, settings.TEST_SIZE, settings.VAL_SIZE)
    train_df, val_df, test_df = splits["train"], splits["val"], splits["test"]

    y_train = train_df["isFraud"].values
    y_val = val_df["isFraud"].values
    y_test = test_df["isFraud"].values

    # --- STEP 3: preprocessing (fit on TRAIN ONLY to avoid leakage) --------
    numeric_cols, categorical_cols = split_column_types(train_df)
    preprocessor = build_preprocessor(numeric_cols, categorical_cols)
    X_train = preprocessor.fit_transform(train_df[numeric_cols + categorical_cols])
    X_val = preprocessor.transform(val_df[numeric_cols + categorical_cols])
    X_test = preprocessor.transform(test_df[numeric_cols + categorical_cols])

    feature_names = get_output_feature_names(preprocessor)
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    X_val_df = pd.DataFrame(X_val, columns=feature_names)
    X_test_df = pd.DataFrame(X_test, columns=feature_names)

    # --- STEP 5: feature selection ------------------------------------------
    fs_report = select_features(X_train_df, y_train, settings.N_SELECTED_FEATURES, settings.RANDOM_STATE)
    selected = fs_report["selected_features"]
    logger.info("Feature selection: %d -> %d features", len(feature_names), len(selected))

    X_train_sel = X_train_df[selected]
    X_val_sel = X_val_df[selected]
    X_test_sel = X_test_df[selected]

    # --- STEP 6: train & compare model families -----------------------------
    candidates = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=settings.RANDOM_STATE
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=10, class_weight="balanced",
            n_jobs=-1, random_state=settings.RANDOM_STATE,
        ),
    }
    if HAS_XGBOOST:
        pos = max(int(y_train.sum()), 1)
        neg = len(y_train) - pos
        candidates["xgboost"] = XGBClassifier(
            n_estimators=400, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=neg / pos, eval_metric="aucpr",
            random_state=settings.RANDOM_STATE, n_jobs=-1,
        )
    else:
        logger.warning("xgboost not installed — comparing only logistic_regression and random_forest.")

    comparison = {}
    fitted_models = {}
    for name, model in candidates.items():
        logger.info("Training %s ...", name)
        model.fit(X_train_sel, y_train)
        val_proba = model.predict_proba(X_val_sel)[:, 1]
        pr_auc = average_precision_score(y_val, val_proba)
        roc_auc = roc_auc_score(y_val, val_proba)
        comparison[name] = {"validation_pr_auc": round(float(pr_auc), 4), "validation_roc_auc": round(float(roc_auc), 4)}
        fitted_models[name] = model
        logger.info("%s -> PR-AUC=%.4f ROC-AUC=%.4f", name, pr_auc, roc_auc)

    best_name = max(comparison, key=lambda k: comparison[k]["validation_pr_auc"])
    best_model = fitted_models[best_name]
    logger.info("Best model selected: %s (%s)", best_name, comparison[best_name])

    # --- STEP 6/9/21: full evaluation of best model on held-out TEST set ---
    test_proba = best_model.predict_proba(X_test_sel)[:, 1]
    eval_metrics = evaluate_model(y_test, test_proba)
    save_evaluation_artifacts(
        y_test, test_proba, best_model, X_test_sel, settings.REPORTS_DIR,
        model_name=best_name,
    )

    # --- STEP 8: save model + preprocessor + feature list + metadata -------
    model_path = Path(settings.MODEL_DIR) / settings.MODEL_FILE
    preproc_path = Path(settings.MODEL_DIR) / settings.PREPROCESSOR_FILE
    features_path = Path(settings.MODEL_DIR) / settings.SELECTED_FEATURES_FILE
    metadata_path = Path(settings.MODEL_DIR) / settings.METADATA_FILE

    joblib.dump(best_model, model_path)
    joblib.dump(preprocessor, preproc_path)
    save_selected_features(selected, str(features_path))

    metadata = {
        "model_name": best_name,
        "data_source": load_report.source,
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "training_duration_seconds": round(time.time() - t0, 1),
        "dataset_report": report,
        "split_periods": splits["periods"],
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "n_raw_features_after_encoding": len(feature_names),
        "feature_selection_report": {k: v for k, v in fs_report.items() if k != "selected_features"},
        "model_comparison": comparison,
        "test_set_metrics": eval_metrics,
    }
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info("Training complete in %.1fs. Artifacts saved to %s", time.time() - t0, settings.MODEL_DIR)
    return metadata


if __name__ == "__main__":
    run_training_pipeline()
