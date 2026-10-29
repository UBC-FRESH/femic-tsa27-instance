#!/usr/bin/env bash
# Run the TSA 27 no-caribou even-flow scenario in WS4 watcher mode.
#
# Usage:
#   bash scripts/run_watch_no_caribou_evenflow.sh [iterations]
#
# Environment:
#   PLAIN=1       print one final frame instead of the live TUI
#   ISLANDS=N     run N parallel searches (0 = one search; default 0)
#   REFRESH=N     seconds between live repaints (default 2)
#   INITIAL=path  start from a seed schedule (for example a generated oldest-first seed)
#   NO_SEED=1     start empty instead of using the generated seed
#
# Examples:
#   bash scripts/run_watch_no_caribou_evenflow.sh
#   bash scripts/run_watch_no_caribou_evenflow.sh 250000
#   PLAIN=1 bash scripts/run_watch_no_caribou_evenflow.sh
#   ISLANDS=8 bash scripts/run_watch_no_caribou_evenflow.sh 100000

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ITERATIONS="${1:-1000000}"
ISLANDS="${ISLANDS:-0}"
REFRESH="${REFRESH:-2}"
DEFAULT_SEED="$ROOT/runtime/seed_oldest_first_s8.csv"

args=(
  watch
  --dataset "$ROOT/build/compiled"
  --targets "$ROOT/config/ws4/targets/evenflow_no_caribou.yaml"
  --account product.HarvestedVolume.managed.Total.CC
  --account feature.Yield.managed.Total
  --years 200
  --period-width 10
  --iterations "$ITERATIONS"
  --seed 1
  --refresh "$REFRESH"
  --islands "$ISLANDS"
)

if [[ "${PLAIN:-0}" == "1" ]]; then
  args+=(--plain)
fi

if [[ -n "${INITIAL:-}" ]]; then
  args+=(--initial-schedule "$INITIAL")
elif [[ "${NO_SEED:-0}" != "1" && -f "$DEFAULT_SEED" ]]; then
  args+=(--initial-schedule "$DEFAULT_SEED")
fi

exec ws4 "${args[@]}"
