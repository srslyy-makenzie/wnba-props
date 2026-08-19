"""Sportsbook odds ingestion via The Odds API (PRD §6, §9).

IMPORTANT CAVEAT: The Odds API's player-prop coverage is "selected US
sports and bookmakers" and is expanding over time — as of this writing
their docs don't guarantee a first-basket-scorer market specifically
exists for WNBA (it's much more commonly offered for points/rebounds/
assists props, and FBS-style markets are more established for NBA/NFL).
Use `list_available_markets()` below to check what's actually offered
for a given game before assuming `player_first_basket_scorer` exists —
if it doesn't, you may need a different odds source or book-specific
scrape for this particular market.

Docs: https://the-odds-api.com/liveapi/guides/v4/
"""

from __future__ import annotations

import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.environ.get("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
SPORT_KEY = "basketball_wnba"

# Best-guess market key for first-basket-scorer props. VERIFY this against
# list_available_markets() for an actual event before relying on it — see
# module docstring caveat above.
FBS_MARKET_KEY = "player_first_basket_scorer"


def _require_api_key() -> str:
    if not ODDS_API_KEY:
        raise RuntimeError("ODDS_API_KEY not set. Copy .env.example to .env and fill it in.")
    return ODDS_API_KEY


def fetch_upcoming_events() -> pd.DataFrame:
    """List upcoming/live WNBA games with their Odds-API event ids.

    Returns:
        DataFrame with columns: event_id, commence_time, home_team, away_team.
    """
    api_key = _require_api_key()
    resp = requests.get(
        f"{BASE_URL}/sports/{SPORT_KEY}/events",
        params={"apiKey": api_key},
        timeout=15,
    )
    resp.raise_for_status()
    events = resp.json()
    return pd.DataFrame(
        [
            {
                "event_id": e["id"],
                "commence_time": e["commence_time"],
                "home_team": e["home_team"],
                "away_team": e["away_team"],
            }
            for e in events
        ]
    )


def list_available_markets(event_id: str, region: str = "us") -> list[str]:
    """Query which player-prop markets The Odds API actually has for this game.

    Use this before calling fetch_fbs_odds() to confirm FBS_MARKET_KEY
    (or whatever key represents first-basket-scorer) is really offered.

    Probes markets one at a time rather than all in a single request:
    The Odds API returns a 422 for the *entire* request if any single
    market key in a comma-separated list isn't valid for this sport, so
    a batched probe can't distinguish "not offered" from "request
    rejected." Costs more API calls but degrades per-market instead of
    all-or-nothing.

    Returns:
        Sorted list of market keys found across all bookmakers for this event.
    """
    api_key = _require_api_key()
    probe_markets = ["player_points", "player_rebounds", "player_assists", "player_first_basket_scorer"]

    keys = set()
    for market in probe_markets:
        resp = requests.get(
            f"{BASE_URL}/sports/{SPORT_KEY}/events/{event_id}/odds",
            params={"apiKey": api_key, "regions": region, "markets": market, "oddsFormat": "american"},
            timeout=15,
        )
        if resp.status_code == 422:
            # This market isn't offered for this sport/event at all — skip it.
            continue
        resp.raise_for_status()
        data = resp.json()
        for bookmaker in data.get("bookmakers", []):
            for m in bookmaker.get("markets", []):
                keys.add(m["key"])

    return sorted(keys)


def fetch_fbs_odds(event_id: str, region: str = "us", market_key: str = FBS_MARKET_KEY) -> pd.DataFrame:
    """Fetch first-basket-scorer odds for a given game.

    Args:
        event_id: Odds-API event id (see fetch_upcoming_events()).
        region: Bookmaker region, e.g. "us".
        market_key: Verify via list_available_markets() first.

    Returns:
        DataFrame with columns: game_id, player_id (name, since the odds
        API doesn't share ESPN's player ids — join on name), sportsbook,
        odds_american.
    """
    api_key = _require_api_key()
    resp = requests.get(
        f"{BASE_URL}/sports/{SPORT_KEY}/events/{event_id}/odds",
        params={"apiKey": api_key, "regions": region, "markets": market_key, "oddsFormat": "american"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for bookmaker in data.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market["key"] != market_key:
                continue
            for outcome in market.get("outcomes", []):
                rows.append(
                    {
                        "game_id": event_id,
                        "player_id": outcome.get("description") or outcome.get("name"),
                        "sportsbook": bookmaker.get("title"),
                        "odds_american": outcome.get("price"),
                    }
                )

    if not rows:
        raise ValueError(
            f"No '{market_key}' outcomes found for event {event_id}. "
            "Run list_available_markets() to see what's actually offered."
        )

    return pd.DataFrame(rows)
