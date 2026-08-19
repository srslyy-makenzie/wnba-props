"""Predict first-basket scorer for TODAY's actual WNBA games, end to end.

Pipeline: backfill recent games -> compute historical first-basket rates
-> fetch today's lineups -> run the baseline model -> print predictions
-> write web/public/data/predictions.json for the React frontend.

Usage:
    python scripts/predict_today.py
    python scripts/predict_today.py --lookback-days 45

Notes:
  - Run this close to tip-off. Before ESPN posts confirmed starters
    (usually ~30-60 min pre-game), lineup data may fall back to full
    rosters — check the warning it prints for each game.
  - The backfill hits ESPN once per day in the lookback window, so a
    30-45 day lookback means 30-45+ requests the first time you run it.
    Results are cached to data/raw/pbp/ so subsequent runs reuse cached
    games and only fetch new ones.
  - This uses the baseline heuristic model only (PRD §8) — it is not the
    calibrated gradient-boosted model described as a later PRD milestone.
  - Odds come from The Odds API (needs ODDS_API_KEY in .env). As of this
    writing, no bookmaker lists a `player_first_basket_scorer` market
    for WNBA (confirmed via ingest_odds.list_available_markets()) — so
    every player will show odds_available=false until a book adds one.
    The wiring is real; there's just nothing to price yet.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from wnba_fbs.data import ingest_lineups, ingest_odds, ingest_pbp, ingest_schedule  # noqa: E402
from wnba_fbs.web_export import write_predictions_json  # noqa: E402
from wnba_fbs.features.historical_rates import build_first_basket_history, compute_player_rates  # noqa: E402
from wnba_fbs.models.baseline import predict_baseline  # noqa: E402
from wnba_fbs.odds.devig import devig_market  # noqa: E402
from wnba_fbs.odds.ev import flag_positive_ev  # noqa: E402

CACHE_DIR = Path("data/raw/pbp")
RATES_CACHE = Path("data/processed/first_basket_rates.csv")
PREDICTIONS_JSON_PATH = Path("web/public/data/predictions.json")
ODDS_COLUMNS = ["odds_american", "market_prob", "edge", "ev", "is_positive_ev"]


def _redact_api_key(message: str) -> str:
    """Strip apiKey=... query params from an exception message before it's printed or persisted.

    requests raises HTTPError/RequestException with the full request URL
    (including apiKey) baked into str(e) — this scrubs it so the key never
    lands in console output or web/public/data/predictions.json (which is
    committed and deployed publicly).
    """
    return re.sub(r"apiKey=[^&\s]+", "apiKey=***", message)


def get_odds_events() -> pd.DataFrame:
    try:
        events = ingest_odds.fetch_upcoming_events()
        print(f"Fetched {len(events)} upcoming event(s) from The Odds API.")
        return events
    except Exception as e:
        print(f"WARNING: could not fetch events from The Odds API ({_redact_api_key(str(e))}) — proceeding without odds.")
        return pd.DataFrame(columns=["event_id", "commence_time", "home_team", "away_team"])


def match_odds_event(team_names: dict, odds_events: pd.DataFrame) -> str | None:
    """Match an ESPN game to its Odds-API event id by comparing team names (ids differ per provider)."""
    espn_names = {info["display_name"] for info in team_names.values()}
    if not espn_names or odds_events.empty:
        return None
    for _, row in odds_events.iterrows():
        if {row["home_team"], row["away_team"]} == espn_names:
            return row["event_id"]
    return None


def attach_odds(predictions: pd.DataFrame, odds_event_id: str | None) -> tuple[pd.DataFrame, str]:
    """Merge de-vigged first-basket odds + EV onto predictions, if a market exists for this game.

    Returns the predictions frame (always carrying ODDS_COLUMNS, null when
    unavailable) and a human-readable note on odds availability for this game.
    """
    out = predictions.copy()
    for col in ODDS_COLUMNS:
        out[col] = None

    if odds_event_id is None:
        return out, "No matching game found on The Odds API."

    try:
        fbs_odds = ingest_odds.fetch_fbs_odds(odds_event_id)
    except ValueError as e:
        return out, _redact_api_key(str(e))
    except Exception as e:
        return out, f"Odds API request failed: {_redact_api_key(str(e))}"

    devigged = devig_market(fbs_odds).drop_duplicates(subset=["player_id"], keep="first")
    devigged = devigged.rename(columns={"player_id": "player_name"})
    priced = flag_positive_ev(devigged, odds_col="odds_american")

    out = out.drop(columns=ODDS_COLUMNS).merge(
        priced[["player_name", "odds_american", "market_prob", "edge", "ev", "is_positive_ev"]],
        on="player_name",
        how="left",
    )
    return out, f"Priced {len(priced)} player(s) from {devigged['sportsbook'].nunique()} sportsbook(s)."


def _clean_nan(record: dict) -> dict:
    return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in record.items()}


def get_or_build_rates(lookback_days: int, refresh: bool) -> pd.DataFrame:
    if RATES_CACHE.exists() and not refresh:
        print(f"Using cached rates from {RATES_CACHE} (pass --refresh-rates to rebuild).")
        rates = pd.read_csv(RATES_CACHE, dtype={"player_id": str})
        return rates

    end = date.today() - timedelta(days=1)  # yesterday: today's games haven't happened yet
    start = end - timedelta(days=lookback_days)
    print(f"Backfilling {start} to {end} from ESPN (cached under {CACHE_DIR}/)...")

    labels = build_first_basket_history(start, end, cache_dir=CACHE_DIR)
    if labels.empty:
        print("WARNING: no historical games found in this window. Try --lookback-days with a larger value,")
        print("or check that WNBA is in season for these dates.")

    rates = compute_player_rates(labels)
    RATES_CACHE.parent.mkdir(parents=True, exist_ok=True)
    rates.to_csv(RATES_CACHE, index=False)
    print(f"Computed rates for {len(rates)} players, cached to {RATES_CACHE}.")
    return rates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lookback-days", type=int, default=30, help="Days of history to backfill for rates.")
    parser.add_argument("--refresh-rates", action="store_true", help="Rebuild rates instead of using the cache.")
    args = parser.parse_args()

    rates = get_or_build_rates(args.lookback_days, args.refresh_rates)

    today_str = date.today().strftime("%Y%m%d")

    try:
        schedule = ingest_schedule.fetch_today_schedule(today_str)
    except Exception as e:
        print(f"WARNING: could not fetch today's schedule ({e}) — overview page will show no games.")
        schedule = []

    game_ids = ingest_pbp.fetch_game_ids(today_str)
    if not game_ids:
        print(f"No WNBA games found for today ({today_str}). Nothing to predict.")
        generated_at = datetime.now().strftime("%b %d, %Y %I:%M %p")
        write_predictions_json([], generated_at, PREDICTIONS_JSON_PATH, active_market="first_basket", schedule=schedule)
        return

    print(f"\nFound {len(game_ids)} game(s) today: {game_ids}\n")

    odds_events = get_odds_events()
    prediction_games = []

    for event_id in game_ids:
        lineup = ingest_lineups.fetch_lineup(event_id)
        if lineup.empty:
            print(f"--- Game {event_id}: no lineup data returned, skipping. ---\n")
            continue

        starters = lineup[lineup["is_starter"]]
        is_confirmed_starters = not starters.empty
        if not is_confirmed_starters:
            print(f"--- Game {event_id}: no confirmed starters yet (too early pre-game) — using full roster. ---")
            game_players = lineup
        else:
            game_players = starters

        merged = game_players.assign(player_id=game_players["player_id"].astype(str)).merge(
            rates.assign(player_id=rates["player_id"].astype(str))[["player_id", "historical_first_basket_rate"]],
            on="player_id",
            how="left",
        )
        merged["historical_first_basket_rate"] = merged["historical_first_basket_rate"].fillna(0.0)

        predictions = predict_baseline(merged).sort_values("model_prob", ascending=False)

        try:
            team_names = ingest_lineups.fetch_team_names(event_id)
        except Exception:
            team_names = {}

        odds_event_id = match_odds_event(team_names, odds_events)
        predictions, odds_note = attach_odds(predictions, odds_event_id)
        print(f"--- Game {event_id}: first-basket odds — {odds_note} ---")

        print(f"--- Game {event_id}: first-basket probabilities ---")
        display_cols = ["player_name", "team_id", "historical_first_basket_rate", "model_prob"] + ODDS_COLUMNS
        print(predictions[display_cols].round(4).to_string(index=False))
        print()

        prediction_games.append(
            {
                "event_id": event_id,
                "teams": team_names,
                "is_confirmed_starters": is_confirmed_starters,
                "odds_note": odds_note,
                "players": [
                    _clean_nan(r)
                    for r in predictions[
                        ["player_name", "team_id", "historical_first_basket_rate", "model_prob"] + ODDS_COLUMNS
                    ].to_dict("records")
                ],
            }
        )

    generated_at = datetime.now().strftime("%b %d, %Y %I:%M %p")
    write_predictions_json(
        prediction_games,
        generated_at,
        PREDICTIONS_JSON_PATH,
        active_market="first_basket",
        schedule=schedule,
    )
    print(f"Predictions written to {PREDICTIONS_JSON_PATH.resolve()} — served by the web/ React app.")


if __name__ == "__main__":
    main()
