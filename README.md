# WNBA First Basket Scorer Model

Predicts the probability of each player scoring the first basket of a WNBA
game, compares those probabilities against sportsbook odds, and surfaces
+EV betting opportunities.

Full product spec: [`docs/PRD.md`](docs/PRD.md)

## Project layout

```
wnba-first-basket/
├── docs/
│   └── PRD.md                # Product requirements doc
├── config/
│   └── config.yaml            # Pipeline configuration (thresholds, paths, API keys via env)
├── data/
│   ├── raw/                   # Untouched pulls from data sources (gitignored)
│   └── processed/             # Cleaned/feature tables (gitignored)
├── src/wnba_fbs/
│   ├── data/                  # Ingestion: play-by-play, lineups, odds
│   ├── features/              # Feature engineering
│   ├── models/                # Baseline + trained models
│   ├── odds/                  # De-vig and EV calculation
│   ├── news/                  # Same-day news adjustment layer (stretch goal)
│   └── pipeline/              # Orchestration (daily run)
├── scripts/
│   └── run_daily.sh           # Entry point for the daily pipeline
├── tests/
└── requirements.txt
```

This mirrors the PRD's data → features → model → odds comparison →
output pipeline, plus a same-day news adjustment layer that sits between
the base model and the odds comparison step (PRD §13).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in API keys (odds API, etc.)
```

## Running locally

```bash
# Run the (currently stubbed) daily pipeline end-to-end
python -m wnba_fbs.pipeline.run_daily

# Or via the convenience script
./scripts/run_daily.sh
```

## Running tests

```bash
pytest
```

## Status

Scaffolding stage — module stubs match the PRD's architecture (§8–9) but
data ingestion, feature engineering, and modeling logic are not yet
implemented. See `docs/PRD.md` §11 for the phased roadmap and `TODO`
comments throughout `src/wnba_fbs/` for the next concrete steps in each
module.
