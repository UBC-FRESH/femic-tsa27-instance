# Phase close-out report: P3 WS4 dataset

Phase: P3 WS4 dataset
Parent issue: #19
Pull request: #24, `feature/p3-ws4-build` into `main`
Evidence head: `aad89c4`, the head covered by CI run `40604661655`
Report commit: the commit that adds this report; its CI run is posted on pull request #24
Date: 2026-10-27
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #24, and delete the branch `feature/p3-ws4-build`.
2. Close parent issue #19 with a closeout comment that cites the merge commit.
3. Launch P4 Caribou scenarios: create its branch, set the phase statuses in `ROADMAP.md`, create its child issues as sub-issues, and start P4.1.

Settings changes, each with its exact command. Each one runs only after its own approval.

- None in P3. GitHub Pages remains deferred to P5.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Fragments are non-overlapping and every fragment has an AU/curve | 37,463 fragments; 402,791 ha; P3.1 checker passes | met |
| Caribou flags carried from the P1/UWR layers | UWR intersection fraction per fragment; 108,458 ha / 8,029 fragments | met with a stated limit: core/matrix/historical layers are still `to_fetch` |
| WS4 dataset loads and constraints are inspectable | `ws4 build` produced 40,660 fragments, 4,746 tracks, 54,510 features, 94 accounts | met |
| Base simulation completes with a recorded seed and run ID | `runs/s3_base` capacity test; `runs/s3_caribou_uwr` UWR run | met |
| Land-base reconciliation within tolerance | capacity 79,102 ha; UWR run 57,941 ha treated; THLB residual vs TSR documented | met with a stated limit |
| Dashboard and CI green on the head | local dashboard green; CI run `40604661655` passes | met |

## 2. Workflow compliance

- Parent issue before the branch: parent #19 created before `feature/p3-ws4-build`; branch from `main` at `9e60a5a`.
- Branch from `main`: merge-base `9e60a5a`.
- Commit messages start with task IDs: `P3.1 activate the WS4 dataset phase` (`b13ead0`), `P3.1 build the WS4 fragment layer with caribou flags` (`f2fef56`), `P3.1 fix the fragment tests` (`ce703fd`), `P3.2-P3.4 compile the WS4 dataset, apply UWR, and run the base` (`75a8e87`), `P3.4 queue the phase review` (`a82f56a`), `P3.4 add the base-project AU test` (`c0b12f8`), `P3.4 add pyarrow for the feather tests` (`aad89c4`), plus the report commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: the P3 commits update `ROADMAP.md`, `CHANGE_LOG.md`, and `README.md`.
- Child issues closed with closeout evidence: #20, #21, #22, #23.
- Approval gates: no tag, release, settings change, or external account was created in P3.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `b13ead0` | lint, format, types, tests, validator, docs | green |
| `f2fef56` | lint, format, types, tests, validator, docs | red: mypy test import; fixed in `ce703fd` |
| `ce703fd` | lint, format, types, tests, validator, docs | green |
| `75a8e87` | lint, format, types, tests, validator, docs | green |
| `a82f56a` | lint, format, types, tests, validator, docs | green |
| `c0b12f8` | lint, format, types, tests, validator, docs | green |
| `aad89c4` | lint, format, types, tests, validator, docs | green |

The local dashboard reported `OVERALL: GREEN. Every gate passed.` with 249 tests and 98% coverage (the new schedule-filter main path is not fully covered).

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| `40604661655` | `aad89c4` | success | Quality gates, Pre-commit parity, and Green dashboard summary pass |
| `40604447618` | `c0b12f8` | failure | Tests failed because CI lacked pyarrow; fixed by adding `pyarrow>=15` in `aad89c4` |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| Matrix 13% <40 years and the 80-year historical deferral are not enforced. | The core/matrix and HLP layers are still `to_fetch`; WS4 XML constraints need a mapping. | Mapped in `config/ws4/caribou_constraints.yaml`; P4 scenario work. |
| The UWR flag uses a 0.5 fragment threshold. | Fragments straddling the UWR boundary are painted only when at least half their area is inside. | Conservative; the direct UWR clip is 116,759 ha vs the 108,458 ha flagged. P4 can split boundary fragments. |
| THLB remains 79,102 ha vs TSR 57,908/51,454. | The legacy compile does not apply the full TSR netdown sequence. | Documented; P4 reconciles the AAC scenarios. |
| The base schedule is a capacity test. | Every eligible block is scheduled at offset 0. | Labelled; P4 builds realistic flow scenarios. |

## 6. Next phase

**P4 — Caribou scenarios.**

Goal: run the caribou policy scenarios and attribute the AAC effect.

Tasks:

- P4.1 Implement scenarios S0–S6.
- P4.2 Run the scenarios with fixed seeds.
- P4.3 Compare harvest, AAC, land base, age class, and matrix disturbance.
- P4.4 Write the attribution and uncertainty report.

Acceptance criteria:

- The scenario table reports deltas in m³/yr and percent.
- The matrix and core/UWR audits pass.
- The report states which results validate against TSR4 and which are best guesses for TSR5.

Recommended default: activate P4 and start P4.1 after this report is approved.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
