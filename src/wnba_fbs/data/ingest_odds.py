"""Sportsbook first-basket-scorer odds ingestion (PRD §6, §9).

Candidate source: an odds aggregation API (e.g. The Odds API) rather than
direct sportsbook scraping, to stay ToS-compliant (PRD §12).
"""

from __future__ import annotations

import os

import pandas as pd
import requests

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")


def fetch_fbs_odds(game_id: str) -> pd.DataFrame:
    """Fetch first-basket-scorer odds for a given game.

    Returns:
        DataFrame with columns: game_id, player_id, sportsbook, odds_american.
    """
    if not ODDS_API_KEY:
        raise RuntimeError("ODDS_API_KEY not set. Copy .env.example to .env and fill it in.")
    raise NotImplementedError("Wire up odds API integration (PRD §6, roadmap Phase 4).")
