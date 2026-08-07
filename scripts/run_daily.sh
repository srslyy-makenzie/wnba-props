#!/usr/bin/env bash
# Convenience wrapper for the daily pipeline (PRD roadmap Phase 6).
set -euo pipefail
cd "$(dirname "$0")/.."
python -m wnba_fbs.pipeline.run_daily
