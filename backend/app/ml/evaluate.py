"""
Model evaluation utilities (STEP 6 / STEP 21).

Fraud data is highly imbalanced, so accuracy is intentionally NOT used as a
headline metric. We report precision, recall, F1, ROC-AUC, PR-AUC and the
confusion matrix, and persist plots (confusion matrix, ROC curve,
precision-recall curve, feature importance, SHAP summary where available)
under settings.REPORTS_DIR.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score, roc_curve, precision_recall_curve,
)

logger = logging.getLogger(__name__)


def evaluate_model(y_true: np.ndarray, y_proba: np.ndarray, threshold: float = 0.5) -> dict:
    y_pred = (y_proba >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred).tolist()
    metrics = {
        "threshold_used": threshold,
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall_fraud": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_proba)), 4) if len(set(y_true)) > 1 else None,
        "pr_auc": round(float(average_precision_score(y_true, y_proba)), 4) if len(set(y_true)) > 1 else None,
        "confusion_matrix": {
            "labels": ["legit(0)", "fraud(1)"],
            "matrix": cm,  # [[TN, FP], [FN, TP]]
        },
        "n_samples": int(len(y_true)),
        "n_fraud": int(y_true.sum()),
    }
    return metrics


def save_evaluation_artifacts(y_true, y_proba, model, X, reports_dir: str, model_name: str) -> None:
    """Saves plots + a metrics.json under reports_dir. Uses matplotlib (no seaborn dependency)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    metrics = evaluate_model(y_true, y_proba)
    with open(reports_path / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # Confusion matrix
    cm = np.array(metrics["confusion_matrix"]["matrix"])
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Pred Legit", "Pred Fraud"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["True Legit", "True Fraud"])
    ax.set_title(f"Confusion Matrix ({model_name})")
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(reports_path / "confusion_matrix.png", dpi=120)
    plt.close(fig)

    if len(set(y_true)) > 1:
        # ROC curve
        fpr, tpr, _ = roc_curve(y_true, y_proba)
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.plot(fpr, tpr, label=f"ROC-AUC={metrics['roc_auc']:.3f}")
        ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
        ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
        ax.set_title("ROC Curve"); ax.legend()
        fig.tight_layout()
        fig.savefig(reports_path / "roc_curve.png", dpi=120)
        plt.close(fig)

        # Precision-Recall curve
        prec, rec, _ = precision_recall_curve(y_true, y_proba)
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.plot(rec, prec, label=f"PR-AUC={metrics['pr_auc']:.3f}")
        ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
        ax.set_title("Precision-Recall Curve"); ax.legend()
        fig.tight_layout()
        fig.savefig(reports_path / "precision_recall_curve.png", dpi=120)
        plt.close(fig)

    # Feature importance (model-native)
    try:
        if hasattr(model, "feature_importances_"):
            importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False).head(20)
        elif hasattr(model, "coef_"):
            importances = pd.Series(np.abs(model.coef_[0]), index=X.columns).sort_values(ascending=False).head(20)
        else:
            importances = None
        if importances is not None:
            fig, ax = plt.subplots(figsize=(6, 6))
            importances.iloc[::-1].plot.barh(ax=ax)
            ax.set_title(f"Top 20 Feature Importances ({model_name})")
            fig.tight_layout()
            fig.savefig(reports_path / "feature_importance.png", dpi=120)
            plt.close(fig)
    except Exception as e:
        logger.warning("Could not plot feature importance: %s", e)

    # SHAP summary plot (best-effort; skipped gracefully if shap unavailable)
    try:
        import shap
        sample = X if len(X) <= 1000 else X.sample(1000, random_state=0)
        if hasattr(model, "feature_importances_"):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(sample)
            values = shap_values[1] if isinstance(shap_values, list) else shap_values
            fig = plt.figure(figsize=(7, 6))
            shap.summary_plot(values, sample, show=False)
            fig.tight_layout()
            fig.savefig(reports_path / "shap_summary.png", dpi=120)
            plt.close(fig)
    except Exception as e:
        logger.info("SHAP summary plot skipped: %s", e)

    logger.info("Saved evaluation artifacts to %s", reports_path)
