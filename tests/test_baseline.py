import pandas as pd
import pytest

from wnba_fbs.models.baseline import predict_baseline


def test_predict_baseline_normalizes_within_game():
    game = pd.DataFrame(
        {
            "player_id": ["a", "b", "c"],
            "historical_first_basket_rate": [0.2, 0.1, 0.1],
        }
    )
    result = predict_baseline(game)
    assert result["model_prob"].sum() == pytest.approx(1.0)
    assert result.loc[result["player_id"] == "a", "model_prob"].iloc[0] == pytest.approx(0.5)


def test_predict_baseline_falls_back_to_uniform_when_no_history():
    game = pd.DataFrame(
        {
            "player_id": ["a", "b"],
            "historical_first_basket_rate": [0.0, 0.0],
        }
    )
    result = predict_baseline(game)
    assert result["model_prob"].tolist() == [0.5, 0.5]
