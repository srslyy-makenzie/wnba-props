# WNBA Player Props Model & Board

Predicts probabilities for WNBA player prop markets — starting with first
basket scorer, expanding to points/rebounds/assists and first team basket —
compares those probabilities against sportsbook odds to surface +EV betting
opportunities, and publishes the results on a React site hosted on
Cloudflare Pages.

Full product spec: [`docs/PRD.md`](docs/PRD.md)

## Project layout

```
wnba-props/
├── docs/
│   └── PRD.md                 # Product requirements doc
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
│   ├── web_export.py          # Builds the multi-market predictions.json for web/
│   └── pipeline/              # Orchestration (daily run)
├── scripts/
│   ├── predict_today.py       # End-to-end: backfill -> rates -> lineups -> predictions -> predictions.json
│   └── run_daily.sh           # Entry point for the daily pipeline
├── web/                        # React (Vite + TS) frontend, hosted on Cloudflare Pages
│   ├── public/data/predictions.json  # Written by scripts/predict_today.py
│   └── src/                   # App, components, styles
├── tests/
└── requirements.txt
```

This mirrors the PRD's data → features → model → odds comparison →
output → web pipeline, plus a same-day news adjustment layer that sits
between the base model and the odds comparison step (PRD §15).

## Setup

**Python (pipeline):**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in API keys (odds API, etc.)
```

**Web (frontend):**

```bash
cd web
npm install
```

## Running locally

```bash
# Generate today's predictions, written to web/public/data/predictions.json
python scripts/predict_today.py

# In a second terminal, run the frontend against that data
cd web
npm run dev
```

`scripts/predict_today.py` prints predictions to the console as well, so
you don't need the frontend running just to see today's board.

## Deploying the web board

`web/` builds to a static site with `npm run build` and deploys to
Cloudflare Pages — see [`web/README.md`](web/README.md) for the
dashboard/CLI deploy steps. No backend/API server is involved; the
Python pipeline's JSON output is the only data source, and it ships as a
static asset alongside the built site.

## Running tests

```bash
pytest
```

## Status

First basket scorer: baseline heuristic model shipped, daily pipeline
automated, results published via the React web board. Feature-rich
modeling and odds/EV integration for first basket are still open (PRD
§11, phases 3-5), as is every other market (points, rebounds, assists,
first team basket) — see `docs/PRD.md` §14 for the process to bring a
new market online.
