"""
Feature selection.

IEEE-CIS has hundreds of raw + engineered features after one-hot encoding.
Rather than arbitrarily keeping "top 20", this module compares several
selection signals and combines them into a validated ranked shortlist:

  1. Variance filtering       - drop near-constant columns outright
  2. Correlation with target  - point-biserial correlation vs isFraud
  3. Mutual information       - sklearn mutual_info_classif (captures non-linear signal)
  4. Model-based importance   - a quick RandomForest's impurity importances
  5. SHAP importance          - mean |SHAP value| from the quick RandomForest

The final selected set is the union of the top-N features from each ranked
method (deduplicated), capped at settings.N_SELECTED_FEATURES, and its
validation-set performance is what determines whether it's accepted (checked
in train.py by comparing full-feature vs selected-feature validation AUC).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, mutual_info_classif

logger = logging.getLogger(__name__)


def variance_filter(X: np.ndarray, feature_names: list[str], threshold: float = 1e-4) -> list[str]:
    vt = VarianceThreshold(threshold=threshold)
    vt.fit(X)
    kept = [f for f, keep in zip(feature_names, vt.get_support()) if keep]
    return kept


def correlation_ranking(X: pd.DataFrame, y: np.ndarray, top_n: int) -> list[str]:
    corrs = X.apply(lambda col: np.abs(np.corrcoef(col, y)[0, 1]) if col.std() > 0 else 0.0)
    corrs = corrs.fillna(0).sort_values(ascending=False)
    return list(corrs.head(top_n).index)


def mutual_information_ranking(X: pd.DataFrame, y: np.ndarray, top_n: int, random_state: int) -> list[str]:
    mi = mutual_info_classif(X, y, random_state=random_state, discrete_features=False)
    ranked = pd.Series(mi, index=X.columns).sort_values(ascending=False)
    return list(ranked.head(top_n).index)


def model_importance_ranking(X: pd.DataFrame, y: np.ndarray, top_n: int, random_state: int):
    rf = RandomForestClassifier(
        n_estimators=150, max_depth=8, class_weight="balanced",
        n_jobs=-1, random_state=random_state,
    )
    rf.fit(X, y)
    importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    return list(importances.head(top_n).index), rf


def shap_importance_ranking(rf: RandomForestClassifier, X: pd.DataFrame, top_n: int, sample_size: int = 2000):
    try:
        import shap
    except ImportError:
        logger.warning("shap not installed; skipping SHAP-based feature selection ranking.")
        return []

    sample = X if len(X) <= sample_size else X.sample(sample_size, random_state=0)
    explainer = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(sample)
    # for binary classifiers shap may return a list [class0, class1]
    values = shap_values[1] if isinstance(shap_values, list) else shap_values
    mean_abs = np.abs(values).mean(axis=0)
    ranked = pd.Series(mean_abs, index=X.columns).sort_values(ascending=False)
    return list(ranked.head(top_n).index)


def select_features(
    X: pd.DataFrame,
    y: np.ndarray,
    n_selected: int,
    random_state: int = 42,
) -> dict:
    """
    Runs all selection methods and returns a report + final selected list.
    """
    feature_names = list(X.columns)
    top_n_per_method = max(n_selected, 30)

    variance_kept = variance_filter(X.values, feature_names)
    X_var = X[variance_kept]

    corr_top = correlation_ranking(X_var, y, top_n_per_method)
    mi_top = mutual_information_ranking(X_var, y, top_n_per_method, random_state)
    model_top, rf = model_importance_ranking(X_var, y, top_n_per_method, random_state)
    shap_top = shap_importance_ranking(rf, X_var, top_n_per_method)

    # combine via simple vote/union, prioritising features that appear in
    # multiple rankings (more robust than any single method alone)
    from collections import Counter
    votes = Counter()
    for ranked_list, weight in [(corr_top, 1), (mi_top, 1), (model_top, 2), (shap_top, 2)]:
        for rank, feat in enumerate(ranked_list):
            votes[feat] += weight * (1.0 - rank / max(len(ranked_list), 1))

    final_selected = [f for f, _ in votes.most_common(n_selected)]

    report = {
        "n_candidate_features": len(feature_names),
        "n_after_variance_filter": len(variance_kept),
        "n_selected": len(final_selected),
        "methods_used": ["variance_filter", "correlation", "mutual_information",
                          "random_forest_importance", "shap_importance" if shap_top else "shap_importance(skipped)"],
        "selected_features": final_selected,
        "top_10_by_combined_vote": [f for f, _ in votes.most_common(10)],
    }
    return report


def save_selected_features(features: list[str], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"selected_features": features}, f, indent=2)


def load_selected_features(path: str) -> list[str]:
    with open(path) as f:
        data = json.load(f)
    return data["selected_features"]
