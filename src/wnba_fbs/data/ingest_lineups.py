"""Starting lineup ingestion via ESPN's public API (PRD §6).

Historical lineups feed feature engineering; daily/pre-tip-off lineups
feed same-day predictions and the news adjustment layer (PRD §13).

ESPN's boxscore payload marks each rostered player with a `starter`
boolean. This is generally only reliably populated close to tip-off for
today's games (ESPN publishes projected/confirmed starters shortly
before the game) and is always populated after the fact for completed
games.
"""

from __future__ import annotations

import pandas as pd

from .espn_client import get_summary


def _parse_lineup(summary: dict, event_id: str) -> pd.DataFrame:
    rows = []
    boxscore = summary.get("boxscore", {})
    for team_entry in boxscore.get("players", []):
        team_id = (team_entry.get("team") or {}).get("id")
        for stat_group in team_entry.get("statistics", []):
            for athlete_entry in stat_group.get("athletes", []):
                athlete = athlete_entry.get("athlete", {})
                rows.append(
                    {
                        "game_id": event_id,
                        "team_id": team_id,
                        "player_id": athlete.get("id"),
                        "player_name": athlete.get("displayName"),
                        "position": (athlete.get("position") or {}).get("abbreviation"),
                        "is_starter": bool(athlete_entry.get("starter", False)),
                    }
                )
    return pd.DataFrame(rows)


def fetch_lineup(event_id: str) -> pd.DataFrame:
    """Fetch the lineup (starters + bench) for one game.

    Works for both completed games (historical backfill) and today's
    games once ESPN has posted projected/confirmed starters — check the
    `is_starter` column and re-fetch closer to tip-off if it looks empty.

    Returns:
        DataFrame with columns: game_id, team_id, player_id, player_name,
        position, is_starter.
    """
    summary = get_summary(event_id)
    return _parse_lineup(summary, event_id)


def fetch_historical_lineups(event_ids: list[str]) -> pd.DataFrame:
    """Fetch lineups for a batch of completed games (e.g. a backfill run).

    Args:
        event_ids: List of ESPN event ids, e.g. from
            ingest_pbp.fetch_game_ids called across a season's dates.

    Returns:
        Concatenated DataFrame in the same shape as fetch_lineup().
    """
    frames = [fetch_lineup(eid) for eid in event_ids]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
