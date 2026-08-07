"""Starting lineup ingestion, historical and daily (PRD §6).

Historical lineups feed feature engineering; daily/pre-tip-off lineups
feed same-day predictions and the news adjustment layer.
"""

from __future__ import annotations

import pandas as pd


def fetch_historical_lineups(season: str) -> pd.DataFrame:
    """Fetch historical starting lineups for a season.

    Returns:
        DataFrame with columns: game_id, team, player_id, position, is_starter.
    """
    raise NotImplementedError("Wire up historical lineup source (PRD §6).")


def fetch_daily_lineups(date: str) -> pd.DataFrame:
    """Fetch confirmed or projected starting lineups for a given date.

    Used same-day, close to tip-off, per the news adjustment layer
    (PRD §13 stretch goal, v1: structured lineup confirmations).

    Returns:
        DataFrame with columns: game_id, team, player_id, position,
        status ("confirmed" | "probable" | "out").
    """
    raise NotImplementedError("Wire up daily lineup / injury report source (PRD §6, §13).")
