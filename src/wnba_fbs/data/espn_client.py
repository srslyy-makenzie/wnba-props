"""Thin wrapper around ESPN's public (unofficial) sports API.

These endpoints are undocumented by ESPN but widely used by the sports
analytics community (e.g. the `wehoop`/`sportsdataverse` R and Python
packages) and require no API key or signup.

IMPLEMENTATION NOTE: this shells out to the system `curl` binary instead
of using Python's `requests` library. In testing, plain `curl` reliably
got a 200 from these endpoints while `requests` (even with full
browser-style headers) got a 403. The most likely cause is TLS
fingerprinting on ESPN's edge/CDN — Python on macOS is often linked
against Apple's older LibreSSL rather than OpenSSL, which produces a
different low-level TLS handshake than curl's, independent of any HTTP
header. Shelling out to curl sidesteps this entirely since it's the
same TLS stack that already worked.

This requires `curl` to be available on PATH, which it is by default on
macOS and virtually all Linux distros.
"""

from __future__ import annotations

import json
import subprocess
import urllib.parse

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba"
SUMMARY_BASE = "https://site.web.api.espn.com/apis/site/v2/sports/basketball/wnba"

_STATUS_MARKER = "\nHTTPSTATUS:"


def _curl_get_json(url: str, params: dict | None = None, timeout: int = 15) -> dict:
    """GET a URL via curl and parse the JSON response.

    Raises:
        RuntimeError: on a non-200 status, curl not being found, or a timeout.
    """
    full_url = f"{url}?{urllib.parse.urlencode(params)}" if params else url

    try:
        result = subprocess.run(
            ["curl", "-s", "-w", f"{_STATUS_MARKER}%{{http_code}}", full_url],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "curl was not found on PATH. It ships by default on macOS/Linux — "
            "check your shell's PATH if this is unexpected."
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Request to {full_url} timed out after {timeout}s") from e

    if result.returncode != 0:
        raise RuntimeError(f"curl exited with code {result.returncode} for {full_url}: {result.stderr.strip()}")

    body, _, status_code = result.stdout.rpartition(_STATUS_MARKER)
    status_code = status_code.strip()

    if status_code != "200":
        raise RuntimeError(f"HTTP {status_code} for {full_url}")

    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Response from {full_url} was not valid JSON: {e}") from e


def get_scoreboard(date: str | None = None) -> dict:
    """Fetch the WNBA scoreboard.

    Args:
        date: Optional date string as YYYYMMDD. Omit for today's games.

    Returns:
        Parsed JSON. Look at the `events` list for games; each event's
        `id` is the game_id needed by get_summary().
    """
    params = {"dates": date} if date else None
    return _curl_get_json(f"{BASE}/scoreboard", params=params)


def get_summary(event_id: str) -> dict:
    """Fetch full game detail: boxscore, roster/starters, and play-by-play.

    Args:
        event_id: The game's ESPN event id (from get_scoreboard()).

    Returns:
        Parsed JSON with (among others) `boxscore` and `plays` keys.
    """
    params = {"event": event_id, "region": "us", "lang": "en", "contentorigin": "espn"}
    return _curl_get_json(f"{SUMMARY_BASE}/summary", params=params)


def get_team_roster(team_id: str) -> dict:
    """Fetch a team's current season roster (not game-specific).

    Always available regardless of game state, unlike per-game
    boxscore/rosters data which may not be populated until close to
    tip-off. Useful as a fallback player pool when game-specific starter
    data isn't posted yet.

    Returns:
        Parsed JSON with an `athletes` list.
    """
    return _curl_get_json(f"{BASE}/teams/{team_id}/roster")
