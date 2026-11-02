# TSA 27 GPU-GA watcher track

**Status:** implemented 1 November 2026; formalized as P6 on 2 November 2026.
**Not a new attribution result; this is the fast solver track for the existing even-flow targets.**

## What was added

- `scripts/build_gpu_effect_table.py` builds a persisted, target-independent WS4 effect table for GPU search.
- `scripts/run_watch_caribou_evenflow.sh` and `scripts/run_watch_no_caribou_evenflow.sh` now default to the GPU-GA watcher.
- `MODE=cpu` keeps the original CPU watcher path.
- S7 and S8 effect tables and caches are built locally under `runtime/`.

## Requirements

Use WS4 at `213a000` or newer, with the optional GPU extra. The P85/P86 line is
recommended for the fast-start cache, live target reload, and the documented
target semantics:

```bash
python -m pip install -e "$WS4_ROOT[gpu]"
```

The watcher scripts put `WS4_ROOT` first on `PYTHONPATH` when it is set:

```bash
export WS4_ROOT=/path/to/ws4
```

If `WS4_ROOT` is unset, the installed `ws4` console script is used. The fast-LNS
script accepts the legacy `WS4_REPO` alias but no tracked script defaults to a
machine-specific `/tmp` path.

## Run

```bash
# S7 caribou / UWR
WS4_ROOT=/path/to/ws4 bash scripts/run_watch_caribou_evenflow.sh

# S8 no caribou
WS4_ROOT=/path/to/ws4 bash scripts/run_watch_no_caribou_evenflow.sh
```

Quick smoke test:

```bash
WS4_ROOT=/path/to/ws4 GPU_GENERATIONS=10 GPU_POPULATION=16 PLAIN=1 \
  bash scripts/run_watch_no_caribou_evenflow.sh
```

CPU fallback:

```bash
MODE=cpu bash scripts/run_watch_no_caribou_evenflow.sh
```

## Effect tables

The first GPU run builds the table automatically. Current local artifacts:

| Scenario | Dataset | Effect table | Size | Build time |
|---|---|---|---:|---:|
| S7 caribou | `build/compiled_uwr` | `runtime/gpu-effects/effects-s7.pt` | 31 MB | 35.8 s |
| S8 no caribou | `build/compiled` | `runtime/gpu-effects/effects-s8.pt` | 42 MB | 53.6 s |

The table uses a target-independent cell basis for
`product.HarvestedVolume.managed.Total.CC` over the 200-year horizon, so target edits do not
require a rebuild unless they add a new account.

## Smoke results

On the local RTX PRO 6000 Blackwell Max-Q:

| Run | Population | Generations | Evaluations | Search time |
|---|---:|---:|---:|---:|
| S8 smoke | 16 | 2 | 48 | 0.42 s |
| S8 short | 64 | 1,000 | 64,064 | 2.58 s |
| S8 longer | 64 | 20,000 | 1,280,064 | 43.8 s |

The 20,000-generation run still shows a positive penalty because the target file's
3,000,000 m³/period soft floor is above the achievable even-flow level. That is expected;
the GPU-GA track is maximizing against the same targets, not changing them. See the
target-semantics section below.

## Target semantics (WS4 P86)

WS4 P86 documents that a target minimum or maximum is a one-sided penalty hinge, not a
hard feasibility bound:

- An unreachable harvest minimum is a valid pull-up aspiration; a persistent penalty is
  the expected outcome, not a solver failure.
- Period-level aspirations plus a dominant even-flow target produce the maximum
  even-flow harvest as an emergent level.
- A `1e9` priority tier is near-lexicographic; weights are the softer dominance control.
- Unit-scale normalization matters when percentage flow penalties are compared with
  volume-level penalties.

For TSA 27, the 3,000,000 m³/period floor is above the achievable even-flow level in the
current compiled dataset. The persistent positive penalty is therefore a target-design
result. Changing the floor or weights is a scenario decision, not a solver fix, and is
outside P6.

## Caveats

- The GPU path keeps the WS4 prototype contract: one priority tier, no patch accounts, no
  route accounts, and no spatial rules.
- The effect table is built for the active account basis. Adding a new account or changing
  the dataset requires a rebuild.
- The watcher defaults to `MODE=gpu`; use `MODE=cpu` if CUDA or torch is unavailable.
- The GPU-GA objective is the same exact target penalty, but it is not an AAC determination.

## Files

- `scripts/build_gpu_effect_table.py`
- `scripts/run_watch_caribou_evenflow.sh`
- `scripts/run_watch_no_caribou_evenflow.sh`
- `scripts/run_watch_tsa27_fast_lns.sh`
- `runtime/gpu-effects/effects-s7.pt`
- `runtime/gpu-effects/effects-s8.pt`
- `runtime/gpu-cache/s7/`
- `runtime/gpu-cache/s8/`

Runtime artifacts are intentionally ignored by Git.
