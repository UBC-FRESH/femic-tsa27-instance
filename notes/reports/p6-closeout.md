# Phase close-out report: P6 WS4 GPU watcher track

Phase: P6 WS4 GPU watcher track
Parent issue: #37
Pull request: #39, `feature/p6-ws4-gpu-watcher` into `main`
Evidence head: `532583c`, the commit that tracks and ports the GPU watcher and fixes the CI type check
Report commit: the commit that refreshes this report. Its CI run is posted on the pull request.
Date: 2026-11-02
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #39, and delete the branch `feature/p6-ws4-gpu-watcher`.
2. Close child issue #38 with a closeout comment that cites the merge commit.
3. Close parent issue #37 with a closeout comment that cites the merge commit.
4. Launch P7 "TSA 27 ALS inventory feasibility" only if the maintainer wants to
   continue the inventory track: create its parent and child issues, branch from
   `main`, and start with a bounded FAIB-plot and LidarBC coverage audit. If not,
   leave the phase unstarted.

Settings changes, each with its exact command. Each one runs only after its own approval.

- None.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Effect-table builder and both watcher scripts tracked | `a17f731` adds `scripts/build_gpu_effect_table.py` and the GPU branches of both watcher scripts | met |
| No tracked script defaults to a machine-specific `/tmp` path | `scripts/run_watch_tsa27_fast_lns.sh` now uses `WS4_ROOT` or the installed `ws4`; `WS4_REPO` is a legacy alias | met |
| Report states the WS4 P85/P86 requirement and P86 soft-floor semantics | `reports/tsa27-gpu-ga-track.md`, sections "Requirements" and "Target semantics (WS4 P86)" | met |
| `MODE=cpu` still selects the CPU watcher | both watcher scripts retain the `MODE=cpu` branch | met |
| No caribou, land-base, matrix, growth, target, or AAC value changed | the change set is scripts, report, roadmap, changelog, and the coverage omit; no model input changed | met |
| Dashboard green and `bash -n` passes | section 3 | met |

## 2. Workflow compliance

- Parent issue before the branch: issue #37 was created before the branch; child
  issue #38 was created immediately after and linked as a sub-issue.
- Branch from `main`: `feature/p6-ws4-gpu-watcher` was created from the local `main`
  at `3b4b08e`.
- Commit messages that start with task IDs: `a17f731` (`P6.1 ...`), `532583c`
  (`P6.1 ...`), and the report commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: both were changed in `a17f731`; the report commit
  only adds this report.
- Child issues closed with closeout evidence: #38 remains open until the merge is
  approved, per the workflow.
- Approval gates: the maintainer's `plan and go` instruction was taken as approval to
  activate P6 and start P6.1. Merge, branch deletion, and issue closure remain gated
  on approval of this report.
- The untracked `notes/handoff/tsa27-demo-sandbox.md` was left out of this phase; it
  belongs to the demo-sandbox handoff, not the GPU watcher.

## 3. Gate evidence

At `532583c`:

```text
GATE                STATUS   SECONDS
lint                GREEN       0.07
format              GREEN       0.07
types               GREEN       0.45
tests               GREEN      24.20
validator           GREEN       0.26
docs                GREEN       0.81

OVERALL: GREEN. Every gate passed.
```

Additional checks:

```text
bash -n scripts/run_watch_caribou_evenflow.sh scripts/run_watch_no_caribou_evenflow.sh scripts/run_watch_tsa27_fast_lns.sh
OK

PYTHONPATH="$WS4_ROOT" python scripts/build_gpu_effect_table.py --help
OK

python -m mypy
Success: no issues found in 48 source files

python -m pytest tests -q
329 passed
```

The installed WS4 is older than the `candidate_cache` module; the script help and
the GPU path require `WS4_ROOT` on `PYTHONPATH`, which is documented in the report.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| pending | report commit | pending | The report commit's CI run is posted on pull request #39 before approval. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| The script help fails against the installed WS4 | The installed WS4 predates `ws4.opt.candidate_cache` | The check is run with `PYTHONPATH="$WS4_ROOT"`; the report states the requirement |
| The demo-sandbox handoff note remains untracked | It is outside P6 | Recorded here; not committed in this phase |
| The first CI run failed on a pre-existing pandas-stubs type error in two operational scripts | The GitHub runner resolves a newer pandas-stubs than the local environment | `532583c` adds a `finite_float` helper and tests; the behavior is unchanged |

## 6. Next phase

Recommended default: **P7 TSA 27 ALS inventory feasibility**, only if the inventory
track continues.

Goal: decide whether TSA 27 has enough public FAIB plots and LidarBC coverage to
justify a local first-return inventory pilot.

Tasks:
- P7.1 Audit TSA 27 FAIB plots and LidarBC point-cloud coverage, and write a go/no-go
  report. Child issue to be created on approval.
- P7.2 If the audit is a go, materialize one bounded operating area and derive
  first-return metrics with the TSA 23 INV-01 runbook.

Acceptance: the audit reports plot counts, acquisition years, spatial clustering, and
coverage; the decision is explicit; no caribou, land-base, matrix, growth, target, or
AAC value changes.

Reason for the default: the CWH and TSA 23 cards do not transfer to the Revelstoke
ESSF/ICH strata. A local coverage/plot audit is the only defensible first step.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
