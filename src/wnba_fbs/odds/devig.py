"""Odds conversion and de-vig logic (PRD §9, step 1).

Converts American odds to implied probability and removes the
sportsbook's overround (vig) via proportional normalization across the
full first-basket-scorer market for a game.
"""

from __future__ import annotations

import pandas as pd


def american_to_implied_prob(american_odds: float) -> float:
    """Convert a single American odds line to its raw (vig-included) implied probability."""
    if american_odds > 0:
        return 100.0 / (american_odds + 100.0)
    if american_odds < 0:
        return -american_odds / (-american_odds + 100.0)
    raise ValueError("American odds cannot be 0.")


def devig_market(odds: pd.DataFrame, odds_col: str = "odds_american") -> pd.DataFrame:
    """Remove vig from a full first-basket-scorer market for one game.

    Args:
        odds: Rows for every player priced in one game's FBS market, with
            an American odds column.
        odds_col: Name of the American odds column.

    Returns:
        Same rows with added columns `implied_prob_raw` (includes vig) and
        `market_prob` (de-vigged, sums to 1 across the game).
    """
    out = odds.copy()
    out["implied_prob_raw"] = out[odds_col].apply(american_to_implied_prob)
    overround = out["implied_prob_raw"].sum()
    if overround <= 0:
        raise ValueError("Sum of implied probabilities must be positive.")
    out["market_prob"] = out["implied_prob_raw"] / overround
    return out
