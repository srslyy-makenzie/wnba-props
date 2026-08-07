"""Heuristic baseline model (PRD §8).

Simple benchmark: probability proportional to a player's recent
first-basket rate among that game's starters. Used to sanity-check and
benchmark more complex models against.
"""

from __future__ import annotations

import pandas as pd


def predict_baseline(game_players: pd.DataFrame) -> pd.DataFrame:
    """Assign first-basket probability proportional to historical rate.

    Args:
        game_players: Rows for one game's eligible players (typically
            starters), with a `historical_first_basket_rate` column.

    Returns:
        Same rows with an added `model_prob` column, normalized to sum
        to 1 within the game (PRD §8 framing).
    """
    if "historical_first_basket_rate" not in game_players.columns:
        raise ValueError("game_players must include 'historical_first_basket_rate'")

    total = game_players["historical_first_basket_rate"].sum()
    if total <= 0:
        # Fall back to a uniform distribution if no history is available.
        n = len(game_players)
        game_players = game_players.copy()
        game_players["model_prob"] = 1.0 / n if n else 0.0
        return game_players

    game_players = game_players.copy()
    game_players["model_prob"] = game_players["historical_first_basket_rate"] / total
    return game_players
