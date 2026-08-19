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


def _build_athlete_maps(summary: dict) -> tuple[dict[str, dict], dict[str, str]]:
    """Build both name->{id,team_id} and id->name maps from the boxscore.

    Play-by-play participants often carry a real `id` but no `displayName`
    (a partial inline object) — the id->name map lets us backfill the name
    even when the id itself didn't need any fallback resolution.
    """
    name_to_athlete: dict[str, dict] = {}
    id_to_name: dict[str, str] = {}
    boxscore = summary.get("boxscore", {})
    for team_entry in boxscore.get("players", []):
        team_id = (team_entry.get("team") or {}).get("id")
        for stat_group in team_entry.get("statistics", []):
            for athlete_entry in stat_group.get("athletes", []):
                athlete = athlete_entry.get("athlete", {})
                aid, name = athlete.get("id"), athlete.get("displayName")
                if name and aid:
                    name_to_athlete[name] = {"id": aid, "team_id": team_id}
                    id_to_name[aid] = name
    return name_to_athlete, id_to_name


def _match_name_in_text(text: str, name_to_athlete: dict[str, dict]) -> dict | None:
    """Find which known player's name the play's text starts with, if any."""
    if not text:
        return None
    candidates = [name for name in name_to_athlete if text.startswith(name)]
    if not candidates:
        return None
    best = max(candidates, key=len)  # longest match avoids partial-name false positives
    return name_to_athlete[best]


def extract_first_basket_labels(raw_games: dict[str, dict]) -> pd.DataFrame:
    """Reduce raw ESPN play-by-play to one row per game: who scored first.

    IMPORTANT: play-by-play `participants` entries appear to lack a usable
    inline athlete id/name for this league (likely a $ref-style reference
    object). Relying on that directly caused rows with a None player_id,
    which pandas' groupby silently drops later on — a real bug caught
    only by comparing "games scanned" against "players computed." This
    function now requires a resolved id, falling back to matching the
    play's text against that same game's boxscore (which does have real
    inline ids for completed games), and logs the actual play text on
    failure instead of silently moving on.

    Args:
        raw_games: Mapping of event_id -> raw JSON from fetch_play_by_play.

    Returns:
        DataFrame with columns: game_id, first_basket_player_id,
        first_basket_player_name, team_id, period, clock.
    """
    rows = []
    for event_id, data in raw_games.items():
        plays = data.get("plays", [])
        name_to_athlete, id_to_name = _build_athlete_maps(data)
        found = False

        for play in plays:
            if not _is_field_goal_make(play):
                continue

            participants = play.get("participants") or []
            athlete = (participants[0].get("athlete") or {}) if participants else {}
            player_id = athlete.get("id")
            player_name = athlete.get("displayName")
            team_id = (play.get("team") or {}).get("id")

            if not player_id:
                matched = _match_name_in_text(play.get("text", ""), name_to_athlete)
                if matched:
                    player_id = matched["id"]
                    team_id = team_id or matched["team_id"]

            if not player_id:
                log.warning(
                    "Game %s: scoring play found but could not resolve a player id via "
                    "participants or boxscore name-match. Play text: %r",
                    event_id,
                    play.get("text"),
                )
                continue  # try the next scoring play in this game instead of giving up

            # id resolved (possibly without a name from participants directly, since
            # ESPN's inline participant objects can carry id without displayName) —
            # backfill the name from the boxscore whenever it's missing.
            if not player_name:
                player_name = id_to_name.get(player_id)

            rows.append(
                {
                    "game_id": event_id,
                    "first_basket_player_id": player_id,
                    "first_basket_player_name": player_name,
                    "team_id": team_id,
                    "period": (play.get("period") or {}).get("number"),
                    "clock": (play.get("clock") or {}).get("displayValue"),
                }
            )
            found = True
            break

        if not found:
            log.warning("Game %s: no resolvable field goal make found in plays.", event_id)

    return pd.DataFrame(rows)
