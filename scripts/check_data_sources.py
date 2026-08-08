"""Sanity-check that the real data sources are reachable and shaped as expected.

Run this locally (not in this sandbox, which has no network access) after
wiring up your .env:

    python scripts/check_data_sources.py

It does NOT require an odds API key to check ESPN, but will skip the
odds check if ODDS_API_KEY isn't set.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wnba_fbs.data import ingest_odds, ingest_pbp  # noqa: E402


def check_espn() -> None:
    print("--- ESPN (play-by-play / lineups) ---")
    # WNBA is in-season roughly May-Oct; if today returns nothing, try a
    # known recent date instead. Adjust as needed.
    today = date.today().strftime("%Y%m%d")
    game_ids = ingest_pbp.fetch_game_ids(today)
    print(f"Games found for {today}: {len(game_ids)} -> {game_ids}")

    if not game_ids:
        print("No games today — try a specific date, e.g.:")
        print("  ingest_pbp.fetch_game_ids('20260615')")
        return

    event_id = game_ids[0]
    raw = ingest_pbp.fetch_play_by_play(event_id, cache_dir=Path("data/raw/pbp"))
    plays = raw.get("plays", [])
    print(f"Event {event_id}: {len(plays)} plays returned (cached to data/raw/pbp/{event_id}.json)")

    labels = ingest_pbp.extract_first_basket_labels({event_id: raw})
    if labels.empty:
        print("Could not extract a first-basket label — game may not have started, or ESPN's field names shifted.")
    else:
        print(labels.to_string(index=False))


def check_odds() -> None:
    print("\n--- The Odds API (sportsbook odds) ---")
    if not ingest_odds.ODDS_API_KEY:
        print("ODDS_API_KEY not set in .env — skipping. Get a free key at https://the-odds-api.com")
        return

    events = ingest_odds.fetch_upcoming_events()
    print(f"Upcoming/live events: {len(events)}")
    if events.empty:
        print("No upcoming events returned — check back closer to game day.")
        return

    print(events.head().to_string(index=False))
    event_id = events.iloc[0]["event_id"]

    markets = ingest_odds.list_available_markets(event_id)
    print(f"\nMarkets available for event {event_id}: {markets}")
    if ingest_odds.FBS_MARKET_KEY not in markets:
        print(
            f"NOTE: '{ingest_odds.FBS_MARKET_KEY}' not found for this event. "
            "First-basket-scorer may not be offered by your region's bookmakers "
            "for this game — see the caveat in ingest_odds.py."
        )


if __name__ == "__main__":
    check_espn()
    check_odds()
