"""Daily pipeline orchestration (PRD roadmap Phase 6).

data -> features -> model -> (optional news adjustment) -> odds comparison -> output

Run with: python -m wnba_fbs.pipeline.run_daily
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def main() -> None:
    config = load_config()
    log.info("Loaded config from %s", CONFIG_PATH)
    log.info("Model type: %s | EV edge threshold: %s", config["model"]["type"], config["ev"]["edge_threshold"])

    # TODO once modules are implemented (PRD roadmap Phases 1-6):
    # 1. lineups = ingest_lineups.fetch_daily_lineups(today)
    # 2. features = build_features.build_feature_table(...)
    # 3. model = predict.load_model(...)
    # 4. predictions = predict.predict_today(model, features)
    # 5. if config["news_adjustment"]["enabled"]:
    #        predictions = adjust.apply_structured_adjustments(predictions, lineups)
    # 6. odds = ingest_odds.fetch_fbs_odds(...) -> devig.devig_market(...)
    # 7. flagged = ev.flag_positive_ev(merged, config["ev"]["edge_threshold"])
    # 8. write flagged opportunities to data/processed/ and/or print report

    log.warning("Pipeline is scaffolded but not yet implemented — see TODOs above and PRD roadmap.")


if __name__ == "__main__":
    main()
