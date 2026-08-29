"""
Preprocessing pipeline.

Uses a single sklearn ColumnTransformer (numeric: median impute + scale,
categorical: constant-fill + one-hot) so the EXACT same fitted transformer
is reused at both training and inference time — this is the mechanism that
prevents train/inference skew and data leakage (STEP 3 requirement).

The fitted preprocessor is a scikit-learn object and is persisted with
joblib alongside the model (see train.py / predict.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Identifier / target / raw-time columns that should never be fed to the
# model directly (either they leak nothing useful, are IDs, or have already
# been converted into engineered features).
NON_FEATURE_COLUMNS = ["TransactionID", "isFraud", "TransactionDT"]


def split_column_types(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Splits candidate feature columns into numeric vs categorical."""
    candidate_cols = [c for c in df.columns if c not in NON_FEATURE_COLUMNS]
    numeric_cols, categorical_cols = [], []
    for c in candidate_cols:
        if pd.api.types.is_numeric_dtype(df[c]):
            numeric_cols.append(c)
        else:
            categorical_cols.append(c)
    return numeric_cols, categorical_cols


def build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False, max_categories=30)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return preprocessor


def get_output_feature_names(preprocessor: ColumnTransformer) -> list[str]:
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        # fallback for older sklearn
        names = []
        for name, trans, cols in preprocessor.transformers_:
            if name == "remainder":
                continue
            if hasattr(trans, "get_feature_names_out"):
                names.extend(trans.get_feature_names_out(cols))
            else:
                names.extend(cols)
        return names
