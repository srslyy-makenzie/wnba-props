import pandas as pd
import pytest

from wnba_fbs.odds.devig import american_to_implied_prob, devig_market
from wnba_fbs.odds.ev import american_to_payout_multiple, compute_ev, flag_positive_ev


def test_american_to_implied_prob_favorite():
    assert american_to_implied_prob(-150) == pytest.approx(0.6)


def test_american_to_implied_prob_underdog():
    assert american_to_implied_prob(150) == pytest.approx(0.4)


def test_devig_market_sums_to_one():
    odds = pd.DataFrame(
        {
            "player_id": ["a", "b", "c"],
            "odds_american": [150, 200, 300],
        }
    )
    result = devig_market(odds)
    assert result["market_prob"].sum() == pytest.approx(1.0)
    # Favorite-ish odds (lower payout) should retain a higher share of probability.
    assert result.loc[result["player_id"] == "a", "market_prob"].iloc[0] > (
        result.loc[result["player_id"] == "c", "market_prob"].iloc[0]
    )


def test_payout_multiple_matches_known_values():
    assert american_to_payout_multiple(100) == pytest.approx(1.0)
    assert american_to_payout_multiple(-200) == pytest.approx(0.5)


def test_compute_ev_positive_when_model_beats_market():
    # +150 implies ~40% breakeven; a 50% model prob should be +EV.
    ev = compute_ev(model_prob=0.5, american_odds=150, stake=1.0)
    assert ev > 0


def test_flag_positive_ev_respects_threshold():
    predictions = pd.DataFrame(
        {
            "player_id": ["a", "b"],
            "model_prob": [0.30, 0.20],
            "market_prob": [0.20, 0.19],
            "odds_american": [150, 150],
        }
    )
    flagged = flag_positive_ev(predictions, edge_threshold=0.05)
    a_row = flagged.loc[flagged["player_id"] == "a"].iloc[0]
    b_row = flagged.loc[flagged["player_id"] == "b"].iloc[0]
    assert a_row["is_positive_ev"]  # 10pp edge > 5pp threshold
    assert not b_row["is_positive_ev"]  # 1pp edge < 5pp threshold
