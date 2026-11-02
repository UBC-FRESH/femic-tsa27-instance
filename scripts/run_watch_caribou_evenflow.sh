#!/usr/bin/env bash
# Run the TSA 27 caribou even-flow scenario in WS4 watcher mode.
#
# Default is the fast GPU-GA track (`ws4 gpu-watch`). Set MODE=cpu for the original
# CPU watcher.
#
# Usage:
#   bash scripts/run_watch_caribou_evenflow.sh [generations-or-iterations]
#
# Environment:
#   MODE=gpu|cpu        default gpu
#   PLAIN=1             print one final frame instead of the live TUI
#   REFRESH=N           seconds between live repaints (default 2)
#   GPU_DEVICE=cuda     torch device (use cpu for a small correctness run)
#   GPU_POPULATION=64   GPU population size
#   GPU_GENERATIONS=N   GPU generations (default 2000)
#   GPU_TABLE=path      persisted effect table (default runtime/gpu-effects/effects-s7.pt)
#   GPU_CACHE_DIR=path  simulator/candidate cache (default runtime/gpu-cache/s7)
#   REBUILD_CACHES=1    rebuild simulator/candidate caches and effect table
#   SCHEDULE_OUT=path   write the final GPU schedule here
#   INITIAL=path        start from a seed schedule
#   NO_SEED=1           CPU only: start empty instead of using the generated seed
#   WS4_ROOT=path       WS4 checkout to put first on PYTHONPATH
#
# Examples:
#   bash scripts/run_watch_caribou_evenflow.sh
#   GPU_GENERATIONS=10 PLAIN=1 bash scripts/run_watch_caribou_evenflow.sh
#   MODE=cpu bash scripts/run_watch_caribou_evenflow.sh 250000

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${MODE:-gpu}"
REFRESH="${REFRESH:-2}"
DATASET="$ROOT/build/compiled_uwr"
TARGETS="$ROOT/config/ws4/targets/evenflow_caribou.yaml"
DEFAULT_SEED="$ROOT/runtime/seed_oldest_first_s7.csv"
CACHE_DIR="${GPU_CACHE_DIR:-$ROOT/runtime/gpu-cache/s7}"
TABLE="${GPU_TABLE:-$ROOT/runtime/gpu-effects/effects-s7.pt}"
DEVICE="${GPU_DEVICE:-cuda}"
POPULATION="${GPU_POPULATION:-64}"
GENERATIONS="${GPU_GENERATIONS:-${1:-2000}}"

if [[ -n "${WS4_ROOT:-}" ]]; then
  export PYTHONPATH="$WS4_ROOT${PYTHONPATH:+:$PYTHONPATH}"
fi

if command -v ws4 >/dev/null 2>&1; then
  WS4_CMD=(ws4)
else
  WS4_CMD=(python -m ws4.cli)
fi

if [[ "$MODE" == "gpu" ]]; then
  if ! "${WS4_CMD[@]}" gpu-watch --help >/dev/null 2>&1; then
    echo "ws4 gpu-watch is not available. Set WS4_ROOT to WS4 213a000 or newer; P85/P86 is recommended." >&2
    exit 1
  fi
  if ! python -c "import torch; raise SystemExit(0 if torch.cuda.is_available() or '$DEVICE' == 'cpu' else 1)"; then
    echo "CUDA is not available. Set MODE=cpu or GPU_DEVICE=cpu for a small correctness run." >&2
    exit 1
  fi

  if [[ ! -f "$TABLE" || "${REBUILD_CACHES:-0}" == "1" ]]; then
    echo "building GPU effect table: $TABLE"
    python "$ROOT/scripts/build_gpu_effect_table.py" \
      --dataset "$DATASET" \
      --targets "$TARGETS" \
      --seed-schedule "${INITIAL:-$DEFAULT_SEED}" \
      --candidates-cache "$CACHE_DIR/candidates.pkl" \
      --simulator-cache "$CACHE_DIR/simulator.pkl" \
      --out "$TABLE" \
      --years 200 \
      --cell-accounts product.HarvestedVolume.managed.Total.CC \
      ${REBUILD_CACHES:+--rebuild-caches}
  fi

  args=(
    gpu-watch
    --dataset "$DATASET"
    --targets "$TARGETS"
    --seed-schedule "${INITIAL:-$DEFAULT_SEED}"
    --table "$TABLE"
    --cache-dir "$CACHE_DIR"
    --years 200
    --period-width 10
    --population "$POPULATION"
    --generations "$GENERATIONS"
    --device "$DEVICE"
    --refresh "$REFRESH"
  )
  if [[ "${PLAIN:-0}" == "1" ]]; then
    args+=(--plain)
  fi
  if [[ -n "${SCHEDULE_OUT:-}" ]]; then
    args+=(--schedule-out "$SCHEDULE_OUT")
  fi
  if [[ "${REBUILD_CACHES:-0}" == "1" ]]; then
    args+=(--rebuild-caches)
  fi
  exec "${WS4_CMD[@]}" "${args[@]}"
fi

ITERATIONS="${1:-1000000}"
args=(
  watch
  --dataset "$DATASET"
  --targets "$TARGETS"
  --account product.HarvestedVolume.managed.Total.CC
  --account feature.Yield.managed.Total
  --years 200
  --period-width 10
  --iterations "$ITERATIONS"
  --seed 1
  --refresh "$REFRESH"
  --islands "${ISLANDS:-0}"
)

if [[ "${PLAIN:-0}" == "1" ]]; then
  args+=(--plain)
fi

if [[ -n "${INITIAL:-}" ]]; then
  args+=(--initial-schedule "$INITIAL")
elif [[ "${NO_SEED:-0}" != "1" && -f "$DEFAULT_SEED" ]]; then
  args+=(--initial-schedule "$DEFAULT_SEED")
fi

exec "${WS4_CMD[@]}" "${args[@]}"
