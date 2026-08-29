"""
Explainable Fraud Agent (STEP 9).

Wraps a trained model with a SHAP explainer and turns raw SHAP contributions
into a human-readable, structured explanation. Falls back to model-native
feature importance if SHAP is unavailable or fails for a given model type.

Descriptions of anonymized columns (V*, most C/D columns) are deliberately
generic — we never claim a specific real-world meaning for a Kaggle-
anonymized feature.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from app.ml.feature_engineering import FEATURE_DOCS

logger = logging.getLogger(__name__)

_ANON_PREFIXES = ("V", "C", "D", "M", "id_")


def _describe_feature(feature_name: str) -> str:
    base = feature_name.split("_")[0] if "_" in feature_name and feature_name not in FEATURE_DOCS else feature_name
    if feature_name in FEATURE_DOCS:
        return FEATURE_DOCS[feature_name]
    # one-hot encoded categorical, e.g. "cat__ProductCD_W"
    for prefix in _ANON_PREFIXES:
        if feature_name.startswith(prefix) and any(ch.isdigit() for ch in feature_name):
            return f"Anonymized dataset signal '{feature_name}' (Kaggle does not disclose its real-world meaning)."
    if "emaildomain" in feature_name.lower():
        return "Email domain associated with the transaction."
    if "productcd" in feature_name.lower():
        return "Product category code for the transaction."
    if "card" in feature_name.lower():
        return "Card-related attribute of the transaction."
    return f"Model input feature '{feature_name}'."


class FraudExplainer:
    def __init__(self, model, background: Optional[pd.DataFrame] = None):
        self.model = model
        self._shap_explainer = None
        self._background = background
        self._init_shap()

    def _init_shap(self):
        try:
            import shap
            if hasattr(self.model, "feature_importances_"):
                self._shap_explainer = shap.TreeExplainer(self.model)
            elif hasattr(self.model, "coef_") and self._background is not None:
                self._shap_explainer = shap.LinearExplainer(self.model, self._background)
        except Exception as e:
            logger.info("SHAP explainer unavailable (%s); will fall back to model importances.", e)
            self._shap_explainer = None

    def explain_instance(self, X_row: pd.DataFrame, top_k: int = 5) -> dict:
        """X_row: single-row DataFrame with the SELECTED feature columns, already preprocessed."""
        feature_names = list(X_row.columns)
        contributions = None

        if self._shap_explainer is not None:
            try:
                shap_values = self._shap_explainer.shap_values(X_row)
                values = shap_values[1] if isinstance(shap_values, list) else shap_values
                contributions = np.asarray(values)[0]
            except Exception as e:
                logger.warning("SHAP explanation failed (%s); falling back to feature importances.", e)

        if contributions is None:
            if hasattr(self.model, "feature_importances_"):
                base_importance = self.model.feature_importances_
            elif hasattr(self.model, "coef_"):
                base_importance = self.model.coef_[0]
            else:
                base_importance = np.zeros(len(feature_names))
            # scale by the row's (standardized) feature values so the sign/direction
            # is instance-specific rather than a flat global ranking
            contributions = base_importance * X_row.iloc[0].values

        contrib_series = pd.Series(contributions, index=feature_names)
        ranked = contrib_series.reindex(contrib_series.abs().sort_values(ascending=False).index)

        top_factors = []
        positive_contributions = []
        negative_contributions = []
        for feat, val in ranked.head(top_k).items():
            direction = "increase" if val > 0 else "decrease"
            entry = {
                "feature": feat,
                "impact": round(float(val), 4),
                "direction": direction,
                "description": _describe_feature(feat),
            }
            top_factors.append(entry)
            (positive_contributions if val > 0 else negative_contributions).append(entry)

        return {
            "top_risk_factors": top_factors,
            "positive_contributions": positive_contributions,
            "negative_contributions": negative_contributions,
        }


def build_explanation_text(risk_level: str, decision: str, top_factors: list[dict]) -> str:
    if not top_factors:
        return f"This transaction was scored {risk_level} risk, resulting in a {decision} decision, based on the model's overall assessment."
    factor_phrases = [f"{f['description']}" for f in top_factors[:3]]
    joined = "; ".join(factor_phrases)
    return (
        f"This transaction was scored {risk_level} risk, resulting in a {decision} decision. "
        f"The strongest contributing signals were: {joined}."
    )
