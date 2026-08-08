"""Historical + daily play-by-play ingestion via ESPN's public API (PRD §6).

Resolves the PRD §12 open question (reliable, ToS-compliant possession-level
data source) with ESPN's free, no-key hidden API — the same data source
underlying the community `wehoop`/`sportsdataverse` packages. It's
unofficial and undocumented by ESPN, so field names can shift; the
extraction logic below is defensive (skips/logs plays it can't parse
instead of crashing a whole day's run) and raw responses should be
cached to data/raw/ so re-parsing doesn't require re-fetching.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from .espn_client import get_scoreboard, get_summary

log = logging.getLogger(__name__)


def fetch_game_ids(date: str) -> list[str]:
    """Get ESPN event ids for every WNBA game on a given date.

    Args:
        date: YYYYMMDD.

    Returns:
        List of event id strings.
    """
    scoreboard = get_scoreboard(date=date)
    return [event["id"] for event in scoreboard.get("events", [])]


def fetch_play_by_play(event_id: str, cache_dir: Path | None = None) -> dict:
    """Fetch raw play-by-play + boxscore JSON for one game.

    Args:
        event_id: ESPN event id (see fetch_game_ids).
        cache_dir: If given, cache the raw response as JSON here
            (recommended: data/raw/) so historical backfills don't
            re-hit ESPN on every re-run.

    Returns:
        Raw parsed JSON from ESPN's summary endpoint.
    """
    cache_path = Path(cache_dir) / f"{event_id}.json" if cache_dir is not None else None
    if cache_path is not None and cache_path.exists():
        return json.loads(cache_path.read_text())

    data = get_summary(event_id)

    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(data))

    return data


def _is_field_goal_make(play: dict) -> bool:
    """Best-effort check that a play is a made field goal (not a free throw)."""
    if not play.get("scoringPlay"):
        return False
    play_type = (play.get("type") or {}).get("text", "").lower()
    text = (play.get("text") or "").lower()
    if "free throw" in play_type or "free throw" in text:
        return False
    return True


def extract_first_basket_labels(raw_games: dict[str, dict]) -> pd.DataFrame:
    """Reduce raw ESPN play-by-play to one row per game: who scored first.

    Args:
        raw_games: Mapping of event_id -> raw JSON from fetch_play_by_play.

    Returns:
        DataFrame with columns: game_id, first_basket_player_id,
        first_basket_player_name, team_id, period, clock.
    """
    rows = []
    for event_id, data in raw_games.items():
        plays = data.get("plays", [])
        found = False
        for play in plays:
            if not _is_field_goal_make(play):
                continue
            participants = play.get("participants") or []
            if not participants:
                log.warning("Game %s: scoring play with no participants, skipping: %r", event_id, play.get("text"))
                continue
            athlete = participants[0].get("athlete", {})
            rows.append(
                {
                    "game_id": event_id,
                    "first_basket_player_id": athlete.get("id"),
                    "first_basket_player_name": athlete.get("displayName"),
                    "team_id": (play.get("team") or {}).get("id"),
                    "period": (play.get("period") or {}).get("number"),
                    "clock": (play.get("clock") or {}).get("displayValue"),
                }
            )
            found = True
            break
        if not found:
            log.warning("Game %s: no field goal make found in plays (check ESPN response shape).", event_id)

    return pd.DataFrame(rows)
