"""Same-day news adjustment layer (PRD §13, stretch goal).

Sits between the base model output and the odds-comparison step, so
historical model training is unaffected and this can be added
incrementally (PRD §13 architecture note).

v1 (structured_only): official injury designations + confirmed starting
lineups, mapped directly to feature/probability adjustments.

v2 (structured_and_llm_extraction): also incorporates beat reporter
tweets/articles, extracted into structured fields (player, role_change,
confidence) via an LLM-based extraction step.
"""

from __future__ import annotations

import pandas as pd


def apply_structured_adjustments(predictions: pd.DataFrame, lineup_status: pd.DataFrame) -> pd.DataFrame:
    """v1: zero out scratched players and redistribute their probability.

    Args:
        predictions: game_id, player_id, model_prob rows for today's slate.
        lineup_status: game_id, player_id, status ("confirmed" | "probable" | "out").

    Returns:
        predictions with model_prob adjusted: scratched ("out") players set
        to 0, remaining players in that game renormalized to sum to 1.
    """
    raise NotImplementedError("Implement v1 structured news adjustment (PRD §13).")


def extract_role_changes_via_llm(articles: list[str]) -> pd.DataFrame:
    """v2: extract structured role-change signals from free text.

    Uses an LLM-based extraction step rather than a custom-trained NLP
    model, given WNBA's relatively low daily news volume (PRD §13).

    Returns:
        DataFrame with columns: player, role_change, confidence.
    """
    raise NotImplementedError("Implement v2 LLM-based extraction (PRD §13, v2 stretch goal).")
