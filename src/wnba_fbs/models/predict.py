"""Pre-game inference (PRD §8-9, roadmap Phase 6).

Loads a trained (or baseline) model and produces per-player first-basket
probabilities for today's slate, ready for the odds comparison step.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_model(path: Path):
    raise NotImplementedError("Implement model loading.")


def predict_today(model, todays_features: pd.DataFrame) -> pd.DataFrame:
    """Produce model_prob for each player in today's games.

    Returns:
        DataFrame with columns: game_id, player_id, model_prob.
    """
    raise NotImplementedError("Implement daily inference (PRD roadmap Phase 6).")
