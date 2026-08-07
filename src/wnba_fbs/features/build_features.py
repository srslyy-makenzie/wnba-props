"""Feature engineering (PRD §7).

Builds the player/team/matchup/context feature table used by the model.
"""

from __future__ import annotations

import pandas as pd

# Initial candidate feature set per PRD §7. Kept here as documentation
# until the feature pipeline is implemented, so the model's expected
# schema is explicit and easy to extend.
PLAYER_FEATURES = [
    "starter_flag",
    "position",
    "historical_first_basket_rate",
    "first_shot_attempt_rate",
    "minutes_at_start_of_game",
    "season_fg_pct",
    "usage_rate",
    "avg_time_to_first_shot_attempt",
]

TEAM_FEATURES = [
    "pace",
    "avg_time_to_first_basket",
    "opening_play_pct_postup",
    "opening_play_pct_jumper",
    "opening_play_pct_transition",
]

MATCHUP_FEATURES = [
    "opp_defense_early_basket_rate_vs_position",
]

CONTEXT_FEATURES = [
    "is_home",
    "rest_days",
    "is_back_to_back",
    "key_teammate_out",
]


def build_feature_table(
    pbp_labels: pd.DataFrame,
    lineups: pd.DataFrame,
    player_stats: pd.DataFrame,
) -> pd.DataFrame:
    """Join labels, lineups, and stats into a model-ready feature table.

    Args:
        pbp_labels: Output of ingest_pbp.extract_first_basket_labels.
        lineups: Output of ingest_lineups.fetch_historical_lineups.
        player_stats: Usage/shot stats per player-season (PRD §6).

    Returns:
        One row per (game_id, player_id) with PLAYER_FEATURES + TEAM_FEATURES
        + MATCHUP_FEATURES + CONTEXT_FEATURES columns, plus the label column
        `scored_first_basket`.
    """
    raise NotImplementedError("Implement feature joins (PRD roadmap Phase 3).")
