"""Builds the JSON data payload consumed by the React frontend (web/).

The pipeline used to render a self-contained HTML dashboard directly from
Python (string-templated). That's been replaced by a static React app
hosted on Cloudflare Pages — this module's only job now is to shape
predictions into the JSON contract that app fetches at `/data/predictions.json`.

Data contract, `MARKETS`: the payload is a list of "markets" (prop types)
rather than a flat list of games, so the frontend can render a tab per
market. Only `first_basket` has real data today; the others are declared
with `status: "coming_soon"` and an empty game list so the frontend can
already render disabled tabs for them ahead of PRD's planned expansion
into points/rebounds/assists props (see docs/PRD.md).
"""

from __future__ import annotations

import json
from pathlib import Path

MARKET_CATALOG = [
    {
        "id": "first_basket",
        "label": "First Basket",
        "description": "Probability each player scores the game's first field goal.",
    },
    {
        "id": "player_points",
        "label": "Points",
        "description": "Over/under and probability distributions for player point totals.",
    },
    {
        "id": "player_rebounds",
        "label": "Rebounds",
        "description": "Over/under and probability distributions for player rebound totals.",
    },
    {
        "id": "player_assists",
        "label": "Assists",
        "description": "Over/under and probability distributions for player assist totals.",
    },
    {
        "id": "first_team_basket",
        "label": "First Team Basket",
        "description": "Probability each team scores the game's first field goal.",
    },
]


def build_predictions_payload(
    games: list[dict],
    generated_at: str,
    active_market: str = "first_basket",
    schedule: list[dict] | None = None,
) -> dict:
    """Assemble the full multi-market payload.

    Args:
        games: games for `active_market`, in the same shape predict_today.py
            has always built: {event_id, teams, is_confirmed_starters, players}.
        generated_at: display string, e.g. "Aug 18, 2026 4:12 PM".
        active_market: which catalog entry `games` belongs to. Every other
            catalog entry is emitted as an empty, "coming_soon" market.
        schedule: today's games for the overview page (ingest_schedule.fetch_today_schedule
            shape) — display context (time/venue/broadcast/record), independent of any market.

    Returns:
        {"generated_at": str, "schedule": [...], "markets": [{id, label, description, status, games}, ...]}
    """
    markets = []
    for entry in MARKET_CATALOG:
        is_active = entry["id"] == active_market
        markets.append(
            {
                **entry,
                "status": "active" if is_active else "coming_soon",
                "games": games if is_active else [],
            }
        )

    return {"generated_at": generated_at, "schedule": schedule or [], "markets": markets}


def write_predictions_json(
    games: list[dict],
    generated_at: str,
    output_path: Path,
    active_market: str = "first_basket",
    schedule: list[dict] | None = None,
) -> None:
    payload = build_predictions_payload(games, generated_at, active_market, schedule=schedule)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
