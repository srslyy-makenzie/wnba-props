"""Predict the first-basket scorer for ONE upcoming game using manually
entered data — a stopgap until the real ingestion pipeline (PRD roadmap
Phase 1) is built out.

You supply:
  1. A roster CSV: the game's starters (usually 5 per team = 10 rows) with
     each player's recent first-basket rate (how often they've scored
     their team's first basket over some recent window — you decide the
     window, e.g. last 10 games).
  2. (Optional) An odds CSV: sportsbook American odds for the same
     players' first-basket-scorer market, to flag +EV bets.

This uses the same baseline model (wnba_fbs.models.baseline) and the
same de-vig/EV logic (wnba_fbs.odds.devig / wnba_fbs.odds.ev) that the
full pipeline will eventually call automatically — so nothing here gets
thrown away once real data ingestion is built.

Usage:
    python scripts/predict_game.py --roster data/examples/sample_roster.csv
    python scripts/predict_game.py --roster data/examples/sample_roster.csv --odds data/examples/sample_odds.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wnba_fbs.models.baseline import predict_baseline  # noqa: E402
from wnba_fbs.odds.devig import devig_market  # noqa: E402
from wnba_fbs.odds.ev import flag_positive_ev  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--roster",
        required=True,
        type=Path,
        help="CSV with columns: player_id, historical_first_basket_rate",
    )
    parser.add_argument(
        "--odds",
        type=Path,
        default=None,
        help="Optional CSV with columns: player_id, odds_american",
    )
    parser.add_argument(
        "--edge-threshold",
        type=float,
        default=0.03,
        help="Minimum edge (model_prob - market_prob) to flag as +EV. Default 0.03 (3pp).",
    )
    args = parser.parse_args()

    roster = pd.read_csv(args.roster)
    required_cols = {"player_id", "historical_first_basket_rate"}
    missing = required_cols - set(roster.columns)
    if missing:
        raise SystemExit(f"Roster CSV is missing required columns: {missing}")

    predictions = predict_baseline(roster)
    predictions = predictions.sort_values("model_prob", ascending=False).reset_index(drop=True)

    print("\n=== First-basket-scorer probabilities (baseline model) ===")
    print(predictions[["player_id", "historical_first_basket_rate", "model_prob"]].to_string(index=False))

    if args.odds is None:
        print(
            "\nNo --odds file provided, so no EV comparison was run. "
            "Pass --odds to compare against sportsbook lines."
        )
        return

    odds = pd.read_csv(args.odds)
    if not {"player_id", "odds_american"}.issubset(odds.columns):
        raise SystemExit("Odds CSV must have columns: player_id, odds_american")

    devigged = devig_market(odds)
    merged = predictions.merge(devigged[["player_id", "market_prob", "odds_american"]], on="player_id", how="inner")

    if merged.empty:
        raise SystemExit(
            "No overlapping player_ids between --roster and --odds files. "
            "Check that player_id values match exactly in both CSVs."
        )

    flagged = flag_positive_ev(merged, edge_threshold=args.edge_threshold)

    print("\n=== Model vs. market (sorted by edge) ===")
    cols = ["player_id", "model_prob", "market_prob", "edge", "odds_american", "ev", "is_positive_ev"]
    print(flagged[cols].round(4).to_string(index=False))

    positive = flagged[flagged["is_positive_ev"]]
    if not positive.empty:
        print(f"\n+EV opportunities (edge > {args.edge_threshold:.0%}):")
        for _, row in positive.iterrows():
            print(
                f"  {row['player_id']}: model {row['model_prob']:.1%} vs market "
                f"{row['market_prob']:.1%} (+{row['edge']:.1%} edge) at {int(row['odds_american']):+d}"
            )
    else:
        print(f"\nNo +EV opportunities found above the {args.edge_threshold:.0%} threshold.")


if __name__ == "__main__":
    main()
