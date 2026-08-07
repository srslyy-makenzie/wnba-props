"""Historical play-by-play ingestion (PRD §6).

Pulls possession-level play-by-play so first-basket labels can be
extracted (who scored the first field goal of each game).

TODO (PRD §12 highest-risk item): confirm a reliable, ToS-compliant
source for historical WNBA play-by-play at the possession level.
Candidates: Sportradar, Genius Sports, stats.wnba.com, scraped box scores.
"""

from __future__ import annotations

import pandas as pd


def fetch_play_by_play(season: str) -> pd.DataFrame:
    """Fetch raw play-by-play events for a given season.

    Args:
        season: e.g. "2026".

    Returns:
        DataFrame of raw play-by-play events. Columns TBD once a source
        is selected; expected to include at minimum: game_id, period,
        clock, team, player, event_type, points.
    """
    raise NotImplementedError("Select and wire up a play-by-play data source (PRD §6, §12).")


def extract_first_basket_labels(pbp: pd.DataFrame) -> pd.DataFrame:
    """Reduce raw play-by-play to one row per game: who scored first.

    Args:
        pbp: Output of fetch_play_by_play.

    Returns:
        DataFrame with columns: game_id, first_basket_player_id, team,
        seconds_into_game.
    """
    raise NotImplementedError("Implement first-basket label extraction (PRD roadmap Phase 1).")
