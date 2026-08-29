"""
Inference-time prediction (STEP 8/9/10/11).

Loads the persisted model + preprocessor + selected feature list and exposes
a single `score_transaction` entry point used by services/fraud_service.py.
The SAME preprocessing pipeline object fitted during training is reused here
verbatim (loaded via joblib) — this is what guarantees train/inference
consistency (implementation rule #5).
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.feature_engineering import engineer_features
from app.ml.preprocessing import split_column_types, get_output_feature_names
from app.ml.explain import FraudExplainer

logger = logging.getLogger(__name__)


class ModelNotTrainedError(RuntimeError):
    pass


class FraudModelBundle:
    """Lazily-loaded singleton bundle of model + preprocessor + feature list + metadata."""

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.selected_features: list[str] = []
        self.metadata: dict = {}
        self.explainer: FraudExplainer | None = None
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        model_path = Path(settings.MODEL_DIR) / settings.MODEL_FILE
        preproc_path = Path(settings.MODEL_DIR) / settings.PREPROCESSOR_FILE
        features_path = Path(settings.MODEL_DIR) / settings.SELECTED_FEATURES_FILE
        metadata_path = Path(settings.MODEL_DIR) / settings.METADATA_FILE

        missing = [str(p) for p in (model_path, preproc_path, features_path) if not p.exists()]
        if missing:
            raise ModelNotTrainedError(
                f"Model artifacts not found: {missing}. Run `python -m app.ml.train` first."
            )

        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preproc_path)
        with open(features_path) as f:
            self.selected_features = json.load(f)["selected_features"]
        if metadata_path.exists():
            with open(metadata_path) as f:
                self.metadata = json.load(f)

        self.explainer = FraudExplainer(self.model)
        self._loaded = True
        logger.info("Loaded model bundle: %s (%d selected features)",
                    self.metadata.get("model_name", "unknown"), len(self.selected_features))

    @property
    def is_ready(self) -> bool:
        return self._loaded


@lru_cache()
def get_model_bundle() -> FraudModelBundle:
    bundle = FraudModelBundle()
    try:
        bundle.load()
    except ModelNotTrainedError as e:
        logger.warning(str(e))
    return bundle


def _row_to_model_input(raw_row: dict, bundle: FraudModelBundle) -> pd.DataFrame:
    """Takes a single raw transaction dict (as would come from the API/dataset),
    runs it through feature engineering + the fitted preprocessor, and returns
    a single-row DataFrame restricted to the selected feature columns."""
    df = pd.DataFrame([raw_row])
    if "TransactionID" not in df:
        df["TransactionID"] = [-1]
    df_fe = engineer_features(df)

    numeric_cols, categorical_cols = split_column_types(df_fe)
    # only keep columns the preprocessor was actually fit on
    fitted_numeric = bundle.preprocessor.transformers_[0][2]
    fitted_categorical = bundle.preprocessor.transformers_[1][2]
    for col in fitted_numeric:
        if col not in df_fe.columns:
            df_fe[col] = np.nan
    for col in fitted_categorical:
        if col not in df_fe.columns:
            df_fe[col] = None
    df_fe = df_fe.copy()

    X = bundle.preprocessor.transform(df_fe[fitted_numeric + fitted_categorical])
    feature_names = get_output_feature_names(bundle.preprocessor)
    X_df = pd.DataFrame(X, columns=feature_names)

    for col in bundle.selected_features:
        if col not in X_df.columns:
            X_df[col] = 0.0
    return X_df[bundle.selected_features]


def score_transaction(raw_row: dict) -> dict:
    """
    Returns {"fraud_probability": float, "explanation": {...}} for a single
    raw transaction dict. Raises ModelNotTrainedError if no model is trained yet.
    """
    bundle = get_model_bundle()
    if not bundle.is_ready:
        raise ModelNotTrainedError("Model is not trained yet. Run `python -m app.ml.train` first.")

    X_row = _row_to_model_input(raw_row, bundle)
    proba = float(bundle.model.predict_proba(X_row)[:, 1][0])
    explanation = bundle.explainer.explain_instance(X_row, top_k=5)
    return {"fraud_probability": proba, **explanation}
