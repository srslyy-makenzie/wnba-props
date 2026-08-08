"""Thin wrapper around ESPN's public (unofficial) sports API.

These endpoints are undocumented by ESPN but widely used by the sports
analytics community (e.g. the `wehoop`/`sportsdataverse` R and Python
packages) and require no API key or signup. Because they're unofficial,
ESPN publishes no uptime/rate-limit guarantees or stability promises —
keep request volume reasonable, cache raw responses locally
(data/raw/), and expect occasional field/shape changes.

Reference: https://github.com/pseudo-r/Public-ESPN-API
"""

from __future__ import annotations

import requests

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba"
SUMMARY_BASE = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/wnba"

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "wnba-fbs-model/0.1 (personal research project)"})


def get_scoreboard(date: str | None = None) -> dict:
    """Fetch the WNBA scoreboard.

    Args:
        date: Optional date string as YYYYMMDD. Omit for today's games.

    Returns:
        Parsed JSON. Look at the `events` list for games; each event's
        `id` is the game_id needed by get_summary().
    """
    params = {"dates": date} if date else {}
    resp = _SESSION.get(f"{BASE}/scoreboard", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_summary(event_id: str) -> dict:
    """Fetch full game detail: boxscore, roster/starters, and play-by-play.

    Args:
        event_id: The game's ESPN event id (from get_scoreboard()).

    Returns:
        Parsed JSON with (among others) `boxscore` and `plays` keys.
    """
    params = {"event": event_id, "region": "us", "lang": "en", "contentorigin": "espn"}
    resp = _SESSION.get(f"{SUMMARY_BASE}/summary", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()
