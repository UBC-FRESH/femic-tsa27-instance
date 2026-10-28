# Phase close-out report: P4 Caribou scenarios

Phase: P4 Caribou scenarios
Parent issue: #25
Pull request: #30, `feature/p4-caribou` into `main`
Evidence head: `f0aebd2`, the head covered by CI run `40609391666`
Report commit: the commit that adds this report; its CI run is posted on pull request #30
Date: 2026-10-28
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #30, and delete the branch `feature/p4-caribou`.
2. Close parent issue #25 with a closeout comment that cites the merge commit.
3. Launch P5 Publish and release: create its branch, set the phase statuses in `ROADMAP.md`, create its child issues as sub-issues, and start P5.1.

Settings changes, each with its exact command. Each one runs only after its own approval.

- None in P4. GitHub Pages remains deferred to P5.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Every scenario has a status and reason | `config/ws4/scenario_registry.yaml`; S3/S6 supported, S0 proxy, S1/S2/S4/S5 unavailable | met |
| Supported runs complete and write account values | `runs/s3_tsr5_base`, `runs/s6_no_caribou`; `metadata/ws4/scenario_runs.json` | met |
| Comparison reports harvest and treated-area deltas | `metadata/ws4/scenario_comparison.csv`; UWR −10,557,873 m³ (−43.6%), −21,160 ha (−26.8%) | met |
| Report separates TSR4 validation from TSR5 best guess | `reports/tsa27-caribou-attribution.md` | met |
| Dashboard and CI green on the head | local dashboard green; CI run `40609391666` passes | met |

## 2. Workflow compliance

- Parent issue before the branch: parent #25 created before `feature/p4-caribou`; branch from `main` at `e14d455`.
- Branch from `main`: merge-base `e14d455`.
- Commit messages start with task IDs: `P4.1 activate the caribou scenario phase` (`e1efe90`), `P4.1-P4.4 run the caribou scenarios and write the attribution` (`e7d567e`), `P4.4 queue the phase review` (`efc469b`), `P4.4 fix the schedule-filter test` (`f0aebd2`), plus the report commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: the P4 commits update `ROADMAP.md`, `CHANGE_LOG.md`, and `README.md`.
- Child issues closed with closeout evidence: #26, #27, #28, #29.
- Approval gates: no tag, release, settings change, or external account was created in P4.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `e1efe90` | lint, format, types, tests, validator, docs | green |
| `e7d567e` | lint, format, types, tests, validator, docs | green |
| `efc469b` | lint, format, types, tests, validator, docs | green |
| `f0aebd2` | lint, format, types, tests, validator, docs | green |

The local dashboard reported `OVERALL: GREEN. Every gate passed.` with 267 tests and 99% coverage.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| `40609391666` | `f0aebd2` | success | Quality gates, Pre-commit parity, and Green dashboard summary pass |
| `40609340523` | `efc469b` | success | Previous head |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| The result is first-period capacity, not an AAC. | The schedules harvest all eligible blocks at year 0; there is no multi-rotation harvest-flow optimization. | Labelled in the attribution report; multi-rotation AAC is the next modelling step. |
| Matrix 13% and historical deferral are not enforced. | Core/matrix and HLP layers are `to_fetch`. | Mapped in `config/ws4/caribou_constraints.yaml`; explicit unsupported scenarios. |
| S0 uses the current UWR as a proxy for 2010. | The 2010 UWR boundary is not available. | Marked proxy, not a validated TSR4 replication. |
| THLB remains 79,102 ha vs TSR 57,908/51,454. | The legacy compile does not apply the full TSR netdown sequence. | Documented; a P5/AAC follow-on should close it. |

## 6. Next phase

**P5 — Publish and release.**

Goal: publish the instance and cross-link it from the FEMIC repository.

Tasks:

- P5.1 Write the final report, docs, and figures.
- P5.2 Add the instance as a submodule at `femic/external/femic-tsa27-instance`.
- P5.3 Tag and release after review.

Acceptance criteria:

- A clean checkout reproduces the documented commands.
- The host repository pins a reviewed instance commit.
- The release notes state the limitations and the unpublished-TSR uncertainty.

Recommended default: activate P5 and start P5.1 after this report is approved.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
