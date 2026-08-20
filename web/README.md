# WNBA Props — web

React (Vite + TypeScript) frontend for the prediction board. It renders
whatever `public/data/predictions.json` contains — one tab per prop
market, each with its own set of game cards. `first_basket` is the only
market with real data today; the rest (`player_points`,
`player_rebounds`, `player_assists`, `first_team_basket`) show up as
disabled "coming soon" tabs until the Python pipeline produces
predictions for them (see `docs/PRD.md`).

## Data flow

`scripts/predict_today.py` (run from the repo root) writes
`web/public/data/predictions.json`. Vite serves everything under
`public/` at the site root, so the app fetches it as `/data/predictions.json`
in both dev and the production build — no API server involved.

## Local development

```bash
cd web
npm install
npm run dev
```

Regenerate the data file from the repo root whenever you want fresh
predictions:

```bash
python scripts/predict_today.py
```

## Build

```bash
npm run build     # outputs to web/dist
npm run preview   # serve the production build locally
```

## Deploy to Cloudflare

This deploys as a Worker serving static assets (Cloudflare's current
unified path — `wrangler.toml` here uses `[assets]`, not the older
Pages-specific `pages_build_output_dir`). Two options:

**Cloudflare dashboard (recommended for the ongoing daily-run setup):**
connect the repo, and in the build settings set the **Path** to `web`
(this is a monorepo — `package.json`/`wrangler.toml` live in `web/`,
not the repo root), build command to `npm run build`, deploy command to
`npx wrangler deploy`. Since `predictions.json` lives under
`web/public/data/`, committing a fresh copy after each
`predict_today.py` run and pushing is enough to trigger a redeploy.

**CLI (one-off or manual deploys):**

```bash
npm run build
npx wrangler deploy
```

`wrangler.toml` in this directory pins the project name and asset
directory so plain `npx wrangler deploy` also works after a build.
