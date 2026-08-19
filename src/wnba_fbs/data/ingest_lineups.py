"""Starting lineup ingestion via ESPN's public API (PRD §6).

Historical lineups feed feature engineering; daily/pre-tip-off lineups
feed same-day predictions and the news adjustment layer (PRD §13).

ESPN's summary endpoint uses different shapes depending on game state:
  - During/after a game: `boxscore.players[].statistics[].athletes[]`,
    each athlete entry has a `starter` boolean.
  - Before a game (commonly the only shape available pre-tip-off):
    a `rosters[]` block instead, with each team's `roster[]` of
    athletes, some marked `starter`.
This module tries the boxscore shape first (richer, has real starter
data once the game exists) and falls back to the rosters shape. If
both come up empty, it logs the top-level keys actually present so a
real response can be inspected rather than failing silently.
"""

from __future__ import annotations

import logging

import pandas as pd

from .espn_client import get_summary, get_team_roster

log = logging.getLogger(__name__)


def _parse_boxscore_shape(summary: dict, event_id: str) -> list[dict]:
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
    return rows


def _parse_rosters_shape(summary: dict, event_id: str) -> list[dict]:
    rows = []
    for team_entry in summary.get("rosters", []):
        team_id = (team_entry.get("team") or {}).get("id")
        for athlete_entry in team_entry.get("roster", []):
            athlete = athlete_entry.get("athlete", athlete_entry)
            rows.append(
                {
                    "game_id": event_id,
                    "team_id": team_id,
                    "player_id": athlete.get("id"),
                    "player_name": athlete.get("displayName") or athlete.get("fullName"),
                    "position": (athlete.get("position") or {}).get("abbreviation"),
                    "is_starter": bool(athlete_entry.get("starter", False)),
                }
            )
    return rows


def _extract_team_ids(summary: dict) -> list[str]:
    """Pull both teams' ids from the game header — present even pre-game."""
    try:
        competitors = summary["header"]["competitions"][0]["competitors"]
    except (KeyError, IndexError, TypeError):
        return []
    return [c["team"]["id"] for c in competitors if "team" in c and "id" in c["team"]]


def _parse_via_team_rosters(summary: dict, event_id: str) -> list[dict]:
    """Fallback: full season roster per team, no per-game starter info.

    Used when neither the boxscore nor per-game rosters shapes have any
    players yet (i.e. too early pre-game). is_starter is always False
    here since this endpoint has no game-specific starter data — the
    caller should treat this as "full roster, starters unknown," not as
    a confirmed lineup.
    """
    rows = []
    for team_id in _extract_team_ids(summary):
        try:
            roster_data = get_team_roster(team_id)
        except Exception:
            log.exception("Failed to fetch team roster for team_id=%s (game %s).", team_id, event_id)
            continue
        for athlete in roster_data.get("athletes", []):
            rows.append(
                {
                    "game_id": event_id,
                    "team_id": team_id,
                    "player_id": athlete.get("id"),
                    "player_name": athlete.get("displayName") or athlete.get("fullName"),
                    "position": (athlete.get("position") or {}).get("abbreviation"),
                    "is_starter": False,  # unknown at this level — see docstring
                }
            )
    return rows


def _parse_lineup(summary: dict, event_id: str) -> pd.DataFrame:
    rows = _parse_boxscore_shape(summary, event_id)
    if rows:
        return pd.DataFrame(rows)

    rows = _parse_rosters_shape(summary, event_id)
    if rows:
        return pd.DataFrame(rows)

    rows = _parse_via_team_rosters(summary, event_id)
    if rows:
        log.warning(
            "Game %s: no per-game lineup/starter data yet — using full season "
            "rosters as a fallback player pool (starters unknown, too early pre-game).",
            event_id,
        )
        return pd.DataFrame(rows)

    log.warning(
        "Game %s: found no players via boxscore, rosters, or team-roster fallback. "
        "Top-level response keys were: %s.",
        event_id,
        sorted(summary.keys()),
    )
    return pd.DataFrame()


def fetch_team_names(event_id: str) -> dict[str, dict]:
    """Fetch readable team names/abbreviations for a game's two teams.

    Useful for display purposes — the rest of this module works with
    ESPN's numeric team_id, which isn't meaningful to show a person.

    Returns:
        Mapping of team_id -> {"display_name": str, "abbreviation": str}.
    """
    summary = get_summary(event_id)
    out: dict[str, dict] = {}
    try:
        competitors = summary["header"]["competitions"][0]["competitors"]
    except (KeyError, IndexError, TypeError):
        return out
    for c in competitors:
        team = c.get("team", {})
        tid = team.get("id")
        if tid:
            out[tid] = {
                "display_name": team.get("displayName") or team.get("name") or f"Team {tid}",
                "abbreviation": team.get("abbreviation") or "???",
            }
    return out


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
