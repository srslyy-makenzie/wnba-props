# PRD: WNBA Player Props Model & Board

**Status:** Draft
**Owner:** [Your name]
**Last updated:** 2026-08-18

---

## 1. Summary

Build a machine learning system that estimates probabilities for WNBA player prop outcomes, starting with "first basket scorer," then expanding to other markets (points, rebounds, assists, first team basket, and beyond). Model probabilities are compared against sportsbook odds to surface bets with positive expected value (+EV), and results are published on a public-facing board — a React site hosted on Cloudflare Pages — so any market the pipeline supports can be browsed by market/tab as it comes online.

## 2. Problem Statement

Sportsbooks price player prop markets using a mix of usage rate, recent form, and market heuristics. Thinner, less mainstream markets — first basket scorer being the clearest example — are often less efficiently priced than moneyline/spread/points totals. A well-calibrated model that accounts for starting lineups, usage patterns, and matchup context can identify mispriced outcomes before market correction, and the same modeling approach (per-player probability vs. de-vigged market probability) generalizes across prop types, not just first basket.

## 3. Goals & Non-Goals

**Goals**
- Predict, pre-game, the probability that each rostered/starting player scores the first field goal of the game (v1, shipped).
- Extend the same pipeline to additional player prop markets — points, rebounds, assists — and team-level props like first team basket, on a per-market rollout basis (v2+).
- Convert model probabilities to fair odds and compare against live sportsbook lines to flag +EV bets, per market.
- Produce a repeatable, auditable pipeline (data → features → model → odds comparison → output) that can run daily during the WNBA season and publish to the web board.
- Publish predictions on a public, static React site (hosted on Cloudflare Pages) organized as one tab per market, so new markets can ship independently without a frontend rewrite.
- Track model calibration and betting performance (CLV, ROI) over time, per market.

**Non-Goals (v1)**
- Live/in-game win probability or first-basket updates after tip-off.
- Automated bet placement.
- Multi-sport generalization (NBA, etc.) — architecture should allow it later, but v1 is WNBA-only.
- User accounts, personalization, or a paid subscription tier on the web board (public read-only for now).

**Now in scope (was a v1 non-goal, promoted per this update)**
- Modeling props beyond first basket (points, rebounds, assists, first team basket) is an explicit, phased goal — see §11 Milestones and §14 Market Expansion.

## 4. Users

- Primary: the project owner, for personal betting decision support.
- Secondary (potential future): a small group of collaborators/subscribers, or the general public, once the board is hosted and shareable via a URL.

## 5. Background / Domain Notes

- First basket scorer is almost always a starter (rarely a bench player, since the first FG happens within the first ~1-3 minutes). Centers/forwards who take the opening tip or get early post touches, and primary ball-handlers who shoot early in the offense, are disproportionately likely. Team pace, opening play design, and injury/lineup news are highly relevant right up to tip-off.
- Points/rebounds/assists props are driven by different signals than first basket: full-game usage rate, pace, minutes projection, opponent positional defense, and role stability matter more than "who touches the ball first." Each new market needs its own feature set and label extraction, not just a relabeling of existing first-basket features.

## 6. Data Requirements

| Data | Purpose | Candidate Sources |
|---|---|---|
| Play-by-play (historical) | Labels: first FG scorer, and per-player box-score stat lines for points/rebounds/assists markets | Sportradar, Genius Sports, stats.wnba.com, or scraped box scores |
| Starting lineups (historical + daily) | Feature: starter status, position | WNBA.com, rotowire, official injury reports |
| Player usage/shot/rebound/assist stats | Feature: early-game shot frequency, USG%, per-market rate stats (season/rolling averages by market) | Basketball-Reference / Her Hoop Stats / stats.wnba.com |
| Team pace & opening possession tendencies | Feature: team-level scoring speed, relevant to first-basket and total-possession-driven markets alike | Play-by-play derived |
| Injury reports / lineup news | Freshness for daily predictions across all markets | Team beat reporters, official reports |
| Sportsbook odds per market | EV comparison, per market (first basket, points O/U, rebounds O/U, assists O/U, first team basket) | Odds API (e.g., The Odds API), sportsbook scrape (respecting ToS) |

**Open question:** confirm reliable, ToS-compliant sources for historical WNBA play-by-play and box scores at the possession/stat-line level for each new market — highest-risk data dependency, and it compounds as more markets are added.

## 7. Feature Engineering (initial candidates)

**First basket (shipped)**
- Player: starter flag, position, historical first-basket rate, first-shot-attempt rate, minutes at start of game, career/season FG%, usage rate, average time-to-first-shot-attempt.
- Team: pace, average time-to-first-basket, opening play tendencies (post-up vs. jumper vs. transition).
- Matchup: opposing defense's rate of allowing early baskets to that position.
- Context: home/away, rest days, back-to-back, key teammate injuries affecting early touches.

**Points / rebounds / assists (planned, v2+)**
- Player: season and rolling (last 5/10 game) per-market averages, minutes projection, usage rate, role (starter/bench, primary vs. secondary scorer/rebounder/playmaker).
- Matchup: opponent's positional defense allowed for that stat, pace-adjusted opponent possessions.
- Context: home/away, rest days, back-to-back, injuries to teammates that redistribute usage/touches.
- Line-relative framing: since these are typically over/under markets rather than "who's first," features feed a distribution estimate (e.g., predicted mean + variance) rather than a single per-player probability that sums to 1 across the roster.

**First team basket (planned)**
- Team-level analog of first basket: team pace, opening play tendencies, home/away, jump-ball win rate proxy.

## 8. Modeling Approach

- **First basket framing:** multiclass / per-player binary probability that sums to ~1 across the ~10 starters + occasional bench player per game (softmax-style or logistic regression per player normalized within game).
- **Points/rebounds/assists framing:** per-player regression (predict expected value + variance, e.g. via quantile regression or a Poisson/negative-binomial model for count-like stats such as rebounds/assists) to price an over/under line rather than a "who's first" probability.
- **First team basket framing:** analogous to first basket, but at team granularity (2 teams per game instead of ~10 players) — effectively a coin-flip model adjusted for pace/home-court factors.
- **Candidate models:** start with logistic regression / gradient boosted trees (XGBoost/LightGBM) for interpretability and small-data robustness given WNBA's shorter season and smaller sample sizes; consider a Bradley-Terry / conditional logit structure for the "race to be first" markets (first basket, first team basket) specifically.
- **Baseline:** simple heuristic model (e.g., proportional to recent rate, or rolling average for O/U markets) to benchmark against, per market.
- **Calibration:** Brier score and reliability curves for probability markets (first basket, first team basket); calibrated prediction intervals for regression-based O/U markets (points/rebounds/assists) — output is used directly for EV calculation either way.

## 9. EV / Odds Comparison Logic

1. Convert sportsbook American/decimal odds to implied probability, removing vig (via standard overround normalization across the relevant market for that game — the full FBS field for first basket, or the two sides of an O/U line for points/rebounds/assists).
2. Compare model probability (or, for O/U markets, model-implied probability of over vs. under at the posted line) vs. de-vigged market probability per player/team.
3. Flag +EV when model probability exceeds market-implied probability by a configurable threshold (e.g., >3-5 percentage points, adjustable per market).
4. Output expected value: `EV = (model_prob * payout) - (1 - model_prob) * stake`.
5. Rank/surface top opportunities per game per day, grouped by market.

## 10. Success Metrics

- **Model quality:** Brier score / log loss (probability markets) or calibration of prediction intervals (O/U markets) on held-out season(s), per market.
- **Betting performance (paper-traded first):** closing line value (CLV), simulated ROI over a season, hit rate vs. expected hit rate — tracked per market so a weak new market doesn't mask a strong established one.
- **Operational:** pipeline runs daily without manual intervention during season; predictions available before lines lock; the web board reflects the latest run without manual publishing steps.

## 11. Milestones / Roadmap

| Phase | Deliverable |
|---|---|
| 1. Data foundation | Historical play-by-play + lineup data pulled, cleaned, first-basket labels extracted — **done** |
| 2. Baseline model | Heuristic + simple logistic regression for first basket, backtested on past season(s) — **done** |
| 3. Feature-rich model | Full feature set, gradient boosting model, calibration tuning (first basket) |
| 4. Odds integration | Live odds ingestion, de-vig logic, EV ranking output (first basket) |
| 5. Backtesting & paper trading | Simulate bets on a past/current season, track CLV and ROI (first basket) |
| 6. Automation | Daily scheduled run producing predictions before games start — **done** (`scripts/predict_today.py`) |
| 7. Web board (React + Cloudflare Pages) | Static site rendering the daily predictions JSON, one tab per market — **done** for first basket; other markets render as "coming soon" tabs until their data lands |
| 8. Points market | Data/labels, baseline, feature-rich model, odds integration for player points O/U |
| 9. Rebounds market | Same phased build-out as points, for player rebounds O/U |
| 10. Assists market | Same phased build-out as points, for player assists O/U |
| 11. First team basket market | Team-level "race to score first" model, odds integration |
| 12. Cross-market polish | Shared backtesting/CLV tracking dashboard across all live markets; performance leaderboard by market |

## 12. Web Architecture

- **Frontend:** React + TypeScript, built with Vite, in `web/`. Static output (`web/dist`) is deployable as-is — no server-side rendering or API backend required.
- **Hosting:** Cloudflare Pages. Either connect the repo (root directory `web`, build command `npm run build`, output directory `dist`) for git-triggered redeploys, or deploy manually with `wrangler pages deploy dist` (see `web/README.md`).
- **Data contract:** the Python pipeline (`scripts/predict_today.py`) writes `web/public/data/predictions.json`, which Vite serves at `/data/predictions.json` in both dev and the production build. Shape:
  ```json
  {
    "generated_at": "Aug 18, 2026 4:12 PM",
    "markets": [
      {
        "id": "first_basket",
        "label": "First Basket",
        "description": "...",
        "status": "active",
        "games": [ { "event_id", "teams", "is_confirmed_starters", "players": [...] } ]
      },
      { "id": "player_points", "label": "Points", "status": "coming_soon", "games": [] }
    ]
  }
  ```
  This shape is the extension point for market expansion: adding a market means the pipeline starts populating its `games` array with real data and flipping its `status` to `"active"` — no frontend schema change needed. The frontend already renders a disabled tab for any market with `status: "coming_soon"`.
- **No backend/database in v1 of the web board.** The site is static; there's no live API, session state, or database. If interactivity (saved picks, historical browsing, per-user views) becomes a goal later, that would introduce a backend — out of scope until there's a concrete need.

## 13. Risks / Open Questions

- **Data availability:** possession-level historical WNBA data may be harder to source than NBA equivalents — needs validation early, and re-validation per new market (box-score stat lines are generally easier to source than play-by-play, but still needs confirming).
- **Market liquidity:** prop markets, especially first basket and first team basket, may be low-limit/thin, capping practical bet sizing even if +EV is found.
- **Sample size:** WNBA has a shorter season (~40 games/team) than NBA, so historical training data is more limited — may need multiple seasons or partial pooling across similar player archetypes, and this constraint gets worse (not better) as markets multiply and split the same limited data across more models.
- **Lineup uncertainty:** late scratches/lineup changes close to tip-off can invalidate predictions across every market — need a process for last-minute refresh.
- **Odds source reliability/ToS:** need a compliant way to pull sportsbook odds (API vs. scraping), per market.
- **Scope creep risk:** adding markets one at a time (§11) is deliberate — resist building points/rebounds/assists/first-team-basket simultaneously before first basket's model quality and EV pipeline (phases 3-5) are actually validated.

## 14. Market Expansion Process

When adding a new market (points, rebounds, assists, or beyond), follow the same phased path first basket went through:

1. **Label extraction:** confirm a historical data source and extract the target stat per player/team per game.
2. **Baseline heuristic:** simplest reasonable estimate (e.g., rolling average) to sanity-check against.
3. **Feature-rich model:** build out the market-specific feature set (§7), train, calibrate.
4. **Odds integration:** ingest sportsbook lines for that market, de-vig, compute EV.
5. **Backtest/paper trade:** validate before treating output as decision-support.
6. **Wire into the pipeline + web board:** `scripts/predict_today.py` populates that market's `games` array in `web/public/data/predictions.json` and flips its catalog entry to `status: "active"` in `src/wnba_fbs/web_export.py`'s `MARKET_CATALOG`.

## 15. Out of Scope / Future Ideas

- NBA/other league generalization.
- Real-time in-game updates.
- Paid subscription tier, user accounts, or personalized picks on the web board.
- **Same-day news incorporation (stretch goal):** layer same-day injury reports, confirmed starting lineups, and role-change news on top of base model probabilities as a pre-tip-off override/adjustment step, rather than a separate model. Phased approach:
  - v1 (low effort): structured signals only — official injury designations (out/questionable/probable) and confirmed starting lineups, mapped directly to feature adjustments (e.g., zero out scratched players, redistribute usage to replacements).
  - v2 (higher effort): unstructured signals — beat reporter tweets/articles on rotation plans or late role changes, extracted into structured fields (player, role_change, confidence) via an LLM-based extraction step rather than a custom-trained NLP model, given WNBA's relatively low daily news volume.
  - Architecture: sits as a same-day adjustment layer between the base model output and the odds-comparison step, so historical model training is unaffected and this can be added incrementally, and applies uniformly across markets once more than one is live.
  - Key risk: sportsbooks often react quickly to the same news, narrowing the edge window; source reliability matters more than volume.

---

### Next steps
- [x] Validate historical play-by-play data source
- [x] Build first-basket label extraction script
- [x] Stand up baseline heuristic model for quick sanity check
- [x] Stand up React + Cloudflare Pages web board with a multi-market data contract
- [ ] Ship feature-rich first-basket model + odds integration (§11 phases 3-5)
- [ ] Pick the next market to build (points is the likely first candidate — most liquid, most data available) and follow §14
