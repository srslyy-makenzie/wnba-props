"""Today's game schedule ingestion via ESPN's public API (PRD §6).

Separate from ingest_pbp/ingest_lineups, which care about play-by-play and
rosters for modeling. This module is purely for the overview page: tip-off
time, venue, broadcast, and W-L record — display context, not features.
"""

from __future__ import annotations

from .espn_client import get_scoreboard


def _overall_record(competitor: dict) -> str | None:
    for record in competitor.get("records", []):
        if record.get("type") == "total":
            return record.get("summary")
    return None


def fetch_today_schedule(date: str | None = None) -> list[dict]:
    """Fetch today's (or a given date's) WNBA games with display context.

    Args:
        date: Optional YYYYMMDD. Omit for today.

    Returns:
        List of dicts: {
            "event_id": str,
            "start_time_iso": str,
            "start_time_display": str,   # ESPN's precomputed local-ish string, e.g. "Wed, August 19th at 7:30 PM EDT"
            "status": str,               # e.g. "Scheduled", "In Progress", "Final"
            "venue": {"name": str, "city": str, "state": str} | None,
            "broadcasts": list[str],
            "teams": {
                team_id: {"display_name": str, "abbreviation": str, "home_away": str, "record": str | None},
                ...
            },
        }
    """
    scoreboard = get_scoreboard(date=date)
    games = []

    for event in scoreboard.get("events", []):
        competitions = event.get("competitions") or [{}]
        comp = competitions[0]

        venue_raw = comp.get("venue") or {}
        venue = (
            {
                "name": venue_raw.get("fullName"),
                "city": (venue_raw.get("address") or {}).get("city"),
                "state": (venue_raw.get("address") or {}).get("state"),
            }
            if venue_raw
            else None
        )

        broadcasts = sorted(
            {name for b in comp.get("broadcasts", []) for name in b.get("names", [])}
        )

        teams = {}
        for competitor in comp.get("competitors", []):
            team = competitor.get("team") or {}
            tid = team.get("id")
            if not tid:
                continue
            teams[tid] = {
                "display_name": team.get("displayName") or team.get("name") or f"Team {tid}",
                "abbreviation": team.get("abbreviation") or "???",
                "home_away": competitor.get("homeAway"),
                "record": _overall_record(competitor),
            }

        status = comp.get("status") or {}
        status_type = status.get("type") or {}

        games.append(
            {
                "event_id": event.get("id"),
                "start_time_iso": event.get("date"),
                "start_time_display": status_type.get("detail") or event.get("date") or "",
                "status": status_type.get("description") or "Unknown",
                "venue": venue,
                "broadcasts": broadcasts,
                "teams": teams,
            }
        )

    return games
