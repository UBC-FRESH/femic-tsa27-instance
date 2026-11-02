#!/usr/bin/env bash
# Run the TSA 27 even-flow scenario with the latest WS4 LNS path.
#
# Usage:
#   bash scripts/run_watch_tsa27_fast_lns.sh [iterations]
#
# Defaults to the caribou-restricted UWR dataset and the caribou even-flow targets.
# Set SCENARIO=no-caribou to use the unrestricted dataset/targets.
#
# Environment:
#   WS4_ROOT=path                    WS4 checkout to put first on PYTHONPATH
#   WS4_REPO=path                    Legacy alias for WS4_ROOT
#   SCENARIO=caribou|no-caribou      default caribou
#   PLAIN=1                          print one final frame instead of the live TUI
#   ISLANDS=N                        parallel islands (0 = one search)
#   REFRESH=N                        seconds between live repaints (default 2)
#   INITIAL=path                     override the starting schedule
#   NO_SEED=1                        start empty instead of the generated seed
#   LNS_WEIGHT=0.2                   LNS operator weight
#   LNS_DESTROY=0.1                  fraction of the schedule destroyed
#   LNS_MAX_DESTROY=64               hard cap on blocks destroyed per move
#   SEED=1                           search seed
#
# Examples:
#   WS4_ROOT=/path/to/ws4 bash scripts/run_watch_tsa27_fast_lns.sh
#   bash scripts/run_watch_tsa27_fast_lns.sh 250000
#   PLAIN=1 bash scripts/run_watch_tsa27_fast_lns.sh
#   SCENARIO=no-caribou LNS_MAX_DESTROY=64 bash scripts/run_watch_tsa27_fast_lns.sh 100000
#   ISLANDS=8 bash scripts/run_watch_tsa27_fast_lns.sh 100000

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ITERATIONS="${1:-1000000}"
SCENARIO="${SCENARIO:-caribou}"
ISLANDS="${ISLANDS:-0}"
REFRESH="${REFRESH:-2}"
SEED="${SEED:-1}"
LNS_WEIGHT="${LNS_WEIGHT:-0.2}"
LNS_DESTROY="${LNS_DESTROY:-0.1}"
LNS_MAX_DESTROY="${LNS_MAX_DESTROY:-64}"
WS4_ROOT="${WS4_ROOT:-${WS4_REPO:-}}"

case "$SCENARIO" in
  caribou)
    DATASET="$ROOT/build/compiled_uwr"
    TARGETS="$ROOT/config/ws4/targets/evenflow_caribou.yaml"
    DEFAULT_SEED="$ROOT/runtime/seed_oldest_first_s7.csv"
    ;;
  no-caribou)
    DATASET="$ROOT/build/compiled"
    TARGETS="$ROOT/config/ws4/targets/evenflow_no_caribou.yaml"
    DEFAULT_SEED="$ROOT/runtime/seed_oldest_first_s8.csv"
    ;;
  *)
    echo "SCENARIO must be 'caribou' or 'no-caribou' (got: $SCENARIO)" >&2
    exit 2
    ;;
esac

if [[ ! -d "$DATASET" ]]; then
  echo "missing dataset: $DATASET" >&2
  exit 2
fi
if [[ ! -f "$TARGETS" ]]; then
  echo "missing targets: $TARGETS" >&2
  exit 2
fi

# Use the latest checked-out WS4 source when available. The installed ws4 may predate
# the LNS short-chain fast path and the bounded-destroy option.
if [[ -n "$WS4_ROOT" && -d "$WS4_ROOT/ws4" ]]; then
  export PYTHONPATH="$WS4_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  WS4=(python3 -m ws4.cli)
elif command -v ws4 >/dev/null 2>&1; then
  WS4=(ws4)
elif command -v python3 >/dev/null 2>&1 && python3 -c "import ws4" >/dev/null 2>&1; then
  WS4=(python3 -m ws4.cli)
else
  echo "WS4 is not available. Set WS4_ROOT to a WS4 checkout or install the ws4 package." >&2
  exit 2
fi

if ! "${WS4[@]}" watch --help 2>&1 | grep -q -- '--lns-max-destroy'; then
  echo "this WS4 does not support --lns-max-destroy; set WS4_ROOT to a newer WS4 checkout" >&2
  exit 2
fi

args=(
  watch
  --dataset "$DATASET"
  --targets "$TARGETS"
  --account product.HarvestedVolume.managed.Total.CC
  --account feature.Yield.managed.Total
  --years 200
  --period-width 10
  --iterations "$ITERATIONS"
  --seed "$SEED"
  --refresh "$REFRESH"
  --islands "$ISLANDS"
  --lns-weight "$LNS_WEIGHT"
  --lns-destroy "$LNS_DESTROY"
  --lns-max-destroy "$LNS_MAX_DESTROY"
)

if [[ "${PLAIN:-0}" == "1" ]]; then
  args+=(--plain)
fi

if [[ -n "${INITIAL:-}" ]]; then
  args+=(--initial-schedule "$INITIAL")
elif [[ "${NO_SEED:-0}" != "1" && -f "$DEFAULT_SEED" ]]; then
  args+=(--initial-schedule "$DEFAULT_SEED")
fi

echo "scenario=$SCENARIO dataset=$DATASET targets=$TARGETS"
echo "iterations=$ITERATIONS lns_weight=$LNS_WEIGHT lns_destroy=$LNS_DESTROY lns_max_destroy=$LNS_MAX_DESTROY"
echo "ws4=${WS4[*]}"

exec "${WS4[@]}" "${args[@]}"
