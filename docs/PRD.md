# PRD: WNBA First Basket Scorer Prediction Model

**Status:** Draft
**Owner:** [Your name]
**Last updated:** 2026-08-06

---

## 1. Summary

Build a machine learning system that estimates the probability of each player scoring the first basket in a given WNBA game, then compares those probabilities against sportsbook "first basket scorer" odds to surface bets with positive expected value (+EV).

## 2. Problem Statement

Sportsbooks price "first basket scorer" (FBS) markets using a mix of usage rate, recent form, and market heuristics, but these lines are often thinner and less efficiently priced than mainstream markets (moneyline, spread, player points). A well-calibrated model that accounts for starting lineups, usage patterns, and matchup context can identify mispriced outcomes before market correction.

## 3. Goals & Non-Goals

**Goals**
- Predict, pre-game, the probability that each rostered/starting player scores the first field goal of the game.
- Convert model probabilities to fair odds and compare against live sportsbook lines to flag +EV bets.
- Produce a repeatable, auditable pipeline (data → features → model → odds comparison → output) that can run daily during the WNBA season.
- Track model calibration and betting performance (CLV, ROI) over time.

**Non-Goals (v1)**
- Live/in-game win probability or first-basket updates after tip-off.
- Modeling other props (rebounds, assists, total points) — may be future scope.
- Automated bet placement.
- Multi-sport generalization (NBA, etc.) — architecture should allow it later, but v1 is WNBA-only.

## 4. Users

- Primary: the project owner, for personal betting decision support.
- Secondary (potential future): a small group of collaborators/subscribers if the tool is shared.

## 5. Background / Domain Notes

- First basket scorer is almost always a starter (rarely a bench player, since the first FG happens within the first ~1-3 minutes).
- Centers/forwards who take the opening tip or get early post touches, and primary ball-handlers who shoot early in the offense, are disproportionately likely.
- Team pace, opening play design, and injury/lineup news are highly relevant right up to tip-off.

## 6. Data Requirements

| Data | Purpose | Candidate Sources |
|---|---|---|
| Play-by-play (historical) | Label: who scored first FG each game | Sportradar, Genius Sports, stats.wnba.com, or scraped box scores |
| Starting lineups (historical + daily) | Feature: starter status, position | WNBA.com, rotowire, official injury reports |
| Player usage/shot stats | Feature: early-game shot frequency, USG% | Basketball-Reference / Her Hoop Stats / stats.wnba.com |
| Team pace & opening possession tendencies | Feature: team-level scoring speed | Play-by-play derived |
| Injury reports / lineup news | Freshness for daily predictions | Team beat reporters, official reports |
| Sportsbook FBS odds | EV comparison | Odds API (e.g., The Odds API), sportsbook scrape (respecting ToS) |

**Open question:** confirm a reliable, ToS-compliant source for historical WNBA play-by-play at the possession level — this is the highest-risk data dependency.

## 7. Feature Engineering (initial candidates)

- Player: starter flag, position, historical first-basket rate, first-shot-attempt rate, minutes at start of game, career/season FG%, usage rate, average time-to-first-shot-attempt.
- Team: pace, average time-to-first-basket, opening play tendencies (post-up vs. jumper vs. transition).
- Matchup: opposing defense's rate of allowing early baskets to that position.
- Context: home/away, rest days, back-to-back, key teammate injuries affecting early touches.

## 8. Modeling Approach

- **Framing:** multiclass / per-player binary probability that sums to ~1 across the ~10 starters + occasional bench player per game (softmax-style or logistic regression per player normalized within game).
- **Candidate models:** start with logistic regression / gradient boosted trees (XGBoost/LightGBM) for interpretability and small-data robustness given WNBA's shorter season and smaller sample sizes; consider a Bradley-Terry / conditional logit structure since this is fundamentally a "who wins the race to score first" problem.
- **Baseline:** simple heuristic model (e.g., proportional to recent first-basket rate) to benchmark against.
- **Calibration:** Brier score and reliability curves are critical since output is used directly as a probability for EV calculation.

## 9. EV / Odds Comparison Logic

1. Convert sportsbook American/decimal odds to implied probability, removing vig (via standard overround normalization across the full FBS market for that game).
2. Compare model probability vs. de-vigged market probability per player.
3. Flag +EV when model probability exceeds market-implied probability by a configurable threshold (e.g., >3-5 percentage points, adjustable).
4. Output expected value: `EV = (model_prob * payout) - (1 - model_prob) * stake`.
5. Rank/surface top opportunities per game per day.

## 10. Success Metrics

- **Model quality:** Brier score / log loss on held-out season(s), calibration curve tightness.
- **Betting performance (paper-traded first):** closing line value (CLV), simulated ROI over a season, hit rate vs. expected hit rate.
- **Operational:** pipeline runs daily without manual intervention during season; predictions available before lines lock.

## 11. Milestones / Roadmap

| Phase | Deliverable |
|---|---|
| 1. Data foundation | Historical play-by-play + lineup data pulled, cleaned, first-basket labels extracted |
| 2. Baseline model | Heuristic + simple logistic regression, backtested on past season(s) |
| 3. Feature-rich model | Full feature set, gradient boosting model, calibration tuning |
| 4. Odds integration | Live odds ingestion, de-vig logic, EV ranking output |
| 5. Backtesting & paper trading | Simulate bets on a past/current season, track CLV and ROI |
| 6. Automation | Daily scheduled run producing a report before games start |
| 7. UI/dashboard | Simple dashboard or notification for daily +EV picks |

## 12. Risks / Open Questions

- **Data availability:** possession-level historical WNBA data may be harder to source than NBA equivalents — needs validation early.
- **Market liquidity:** FBS markets may be low-limit/thin, capping practical bet sizing even if +EV is found.
- **Sample size:** WNBA has a shorter season (~40 games/team) than NBA, so historical training data is more limited — may need multiple seasons or partial pooling across similar player archetypes.
- **Lineup uncertainty:** late scratches/lineup changes close to tip-off can invalidate predictions — need a process for last-minute refresh.
- **Odds source reliability/ToS:** need a compliant way to pull sportsbook odds (API vs. scraping).

## 13. Out of Scope / Future Ideas

- Extending to other props (first team basket, first 3-pointer, etc.)
- NBA/other league generalization
- Real-time in-game updates
- Public-facing product/subscription
- **Same-day news incorporation (stretch goal):** layer same-day injury reports, confirmed starting lineups, and role-change news on top of base model probabilities as a pre-tip-off override/adjustment step, rather than a separate model. Phased approach:
  - v1 (low effort): structured signals only — official injury designations (out/questionable/probable) and confirmed starting lineups, mapped directly to feature adjustments (e.g., zero out scratched players, redistribute usage to replacements).
  - v2 (higher effort): unstructured signals — beat reporter tweets/articles on rotation plans or late role changes, extracted into structured fields (player, role_change, confidence) via an LLM-based extraction step rather than a custom-trained NLP model, given WNBA's relatively low daily news volume.
  - Architecture: sits as a same-day adjustment layer between the base model output and the odds-comparison step, so historical model training is unaffected and this can be added incrementally.
  - Key risk: sportsbooks often react quickly to the same news, narrowing the edge window; source reliability matters more than volume.

---

### Next steps
- [ ] Validate historical play-by-play data source
- [ ] Build first-basket label extraction script
- [ ] Stand up baseline heuristic model for quick sanity check
