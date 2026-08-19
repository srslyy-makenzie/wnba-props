"""Turn a window of historical ESPN games into per-player first-basket rates.

This is the missing piece between raw label extraction (ingest_pbp) and
a usable feature for the baseline model (models.baseline). PRD §7 lists
`historical_first_basket_rate` as the core player feature; this module
computes it.

Approach (deliberately simple for v1 — see PRD §8 baseline framing):
    rate = (# times this player scored the game's first basket in the
            lookback window) / (# games their team played in that window)

Using team-games-played as the denominator is a proxy for
"games this player started" (PRD §7 lists minutes-at-start as a
separate feature) — it will slightly understate the true rate for
players who missed games to injury/rest, and slightly overstate it for
bench players who rarely start. Good enough for a v1 baseline; refine
later by joining against actual lineup data per game if needed.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from ..data.ingest_pbp import extract_first_basket_labels, fetch_game_ids, fetch_play_by_play

log = logging.getLogger(__name__)


def build_first_basket_history(
    start_date: date,
    end_date: date,
    cache_dir: Path | None = None,
) -> pd.DataFrame:
    """Fetch and label every game in [start_date, end_date].

    Args:
        start_date, end_date: Inclusive date range to backfill.
        cache_dir: Passed through to fetch_play_by_play; strongly
            recommended (e.g. Path("data/raw/pbp")) so re-runs don't
            re-hit ESPN for games already fetched.

    Returns:
        DataFrame from extract_first_basket_labels, across all games in
        range, plus a `date` column.
    """
    raw_games: dict[str, dict] = {}
    game_dates: dict[str, str] = {}

    current = start_date
    total_games_found = 0
    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        try:
            game_ids = fetch_game_ids(date_str)
        except RuntimeError as e:
            log.warning("Failed to fetch scoreboard for %s: %s", date_str, e)
            current += timedelta(days=1)
            continue
        except Exception:
            log.exception("Failed to fetch scoreboard for %s, skipping.", date_str)
            current += timedelta(days=1)
            continue

        if game_ids:
            print(f"  {date_str}: {len(game_ids)} game(s)")
        total_games_found += len(game_ids)

        for event_id in game_ids:
            try:
                raw_games[event_id] = fetch_play_by_play(event_id, cache_dir=cache_dir)
                game_dates[event_id] = date_str
            except RuntimeError as e:
                log.warning("Failed to fetch game %s on %s: %s", event_id, date_str, e)
            except Exception:
                log.exception("Failed to fetch/parse game %s on %s, skipping.", event_id, date_str)

        current += timedelta(days=1)

    print(f"Backfill scan complete: {total_games_found} game(s) found across the window.")

    labels = extract_first_basket_labels(raw_games)
    if not labels.empty:
        labels["date"] = labels["game_id"].map(game_dates)
    return labels


def compute_team_game_counts(labels: pd.DataFrame, raw_games: dict[str, dict] | None = None) -> pd.DataFrame:
    """Count games played per team in the backfilled window.

    Uses the two teams present in each game's first-basket label as a
    proxy for "which teams played that day" — works as long as
    extract_first_basket_labels found a label for every game (check the
    logged warnings from that function for games it couldn't parse).

    Returns:
        DataFrame with columns: team_id, games_played.
    """
    if labels.empty:
        return pd.DataFrame(columns=["team_id", "games_played"])
    return (
        labels.groupby("team_id")["game_id"]
        .nunique()
        .reset_index()
        .rename(columns={"game_id": "games_played"})
    )


def compute_player_rates(labels: pd.DataFrame) -> pd.DataFrame:
    """Compute each player's first-basket rate over the backfilled window.

    Args:
        labels: Output of build_first_basket_history.

    Returns:
        DataFrame with columns: player_id, player_name, team_id,
        first_basket_count, team_games, historical_first_basket_rate.
    """
    if labels.empty:
        return pd.DataFrame(
            columns=[
                "player_id",
                "player_name",
                "team_id",
                "first_basket_count",
                "team_games",
                "historical_first_basket_rate",
            ]
        )

    counts = (
        labels.groupby(["first_basket_player_id", "team_id"])
        .size()
        .reset_index(name="first_basket_count")
        .rename(columns={"first_basket_player_id": "player_id"})
    )

    name_lookup = (
        labels.dropna(subset=["first_basket_player_name"])
        .drop_duplicates(subset=["first_basket_player_id"])
        .set_index("first_basket_player_id")["first_basket_player_name"]
    )
    counts["player_name"] = counts["player_id"].map(name_lookup)

    team_games = compute_team_game_counts(labels)
    merged = counts.merge(team_games, on="team_id", how="left")
    merged["historical_first_basket_rate"] = merged["first_basket_count"] / merged["games_played"]
    merged = merged.rename(columns={"games_played": "team_games"})
    print(f"Computed rates for {len(merged)} players from {len(labels)} historical first-basket events.")
    return merged
