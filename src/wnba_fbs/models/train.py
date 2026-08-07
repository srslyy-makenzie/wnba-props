"""Model training (PRD §8, roadmap Phases 2-3).

Trains a logistic regression / gradient boosted trees model per-game,
normalized across that game's candidate players so probabilities sum
to ~1 (the "race to score first" framing in PRD §8).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def train_model(feature_table: pd.DataFrame, model_type: str = "logistic_regression"):
    """Fit a model on the historical feature table.

    Args:
        feature_table: Output of build_features.build_feature_table.
        model_type: One of "logistic_regression", "xgboost" (PRD §8).

    Returns:
        A fitted model object.
    """
    raise NotImplementedError("Implement training loop (PRD roadmap Phases 2-3).")


def evaluate_calibration(model, holdout_features: pd.DataFrame) -> dict:
    """Compute Brier score / log loss / reliability curve data (PRD §10).

    Returns:
        Dict with keys: brier_score, log_loss, reliability_curve.
    """
    raise NotImplementedError("Implement calibration evaluation (PRD §10).")


def save_model(model, path: Path) -> None:
    raise NotImplementedError("Implement model persistence.")
