"""+EV flagging and expected value calculation (PRD §9, steps 2-5)."""

from __future__ import annotations

import pandas as pd

from .devig import american_to_implied_prob


def american_to_payout_multiple(american_odds: float) -> float:
    """Convert American odds to a payout multiple on a 1-unit stake (profit, not incl. stake)."""
    if american_odds > 0:
        return american_odds / 100.0
    if american_odds < 0:
        return 100.0 / -american_odds
    raise ValueError("American odds cannot be 0.")


def compute_ev(model_prob: float, american_odds: float, stake: float = 1.0) -> float:
    """EV = (model_prob * payout) - (1 - model_prob) * stake (PRD §9, step 4)."""
    payout = stake * american_to_payout_multiple(american_odds)
    return (model_prob * payout) - ((1 - model_prob) * stake)


def flag_positive_ev(
    predictions: pd.DataFrame,
    edge_threshold: float = 0.03,
    odds_col: str = "odds_american",
) -> pd.DataFrame:
    """Compare model_prob to de-vigged market_prob and flag +EV opportunities.

    Args:
        predictions: Must include model_prob, market_prob, and odds_col
            (odds_col used for the EV dollar-value calculation).
        edge_threshold: Minimum (model_prob - market_prob) to flag, in
            fraction terms, e.g. 0.03 = 3 percentage points (PRD §9, step 3).

    Returns:
        Same rows with added columns: edge, ev, is_positive_ev — sorted by
        edge descending (PRD §9, step 5: rank/surface top opportunities).
    """
    required = {"model_prob", "market_prob", odds_col}
    missing = required - set(predictions.columns)
    if missing:
        raise ValueError(f"predictions is missing required columns: {missing}")

    out = predictions.copy()
    out["edge"] = out["model_prob"] - out["market_prob"]
    out["ev"] = out.apply(lambda r: compute_ev(r["model_prob"], r[odds_col]), axis=1)
    out["is_positive_ev"] = out["edge"] > edge_threshold
    return out.sort_values("edge", ascending=False).reset_index(drop=True)
