# Phase close-out report: P2 FEMIC compile

Phase: P2 FEMIC compile
Parent issue: #13
Pull request: #18, `feature/p2-compile` into `main`
Evidence head: `7f2ab00`, the head covered by CI run `40602050672`
Report commit: the commit that adds this report; its CI run is posted on pull request #18
Date: 2026-10-27
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #18, and delete the branch `feature/p2-compile`.
2. Close parent issue #13 with a closeout comment that cites the merge commit.
3. Launch P3 WS4 dataset: create its branch, set the phase statuses in `ROADMAP.md`, create its child issues as sub-issues, and start P3.1.

Settings changes, each with its exact command. Each one runs only after its own approval.

- None in P2. GitHub Pages remains deferred to P5.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| AU table with a documented rule set and area summary | `metadata/analysis_units/tsa27_analysis_units.csv`; 273 classes; notes file | met |
| Yield curves with VDYP7/TIPSY provenance and diagnostics | VDYP7 7.16k and BTC run `tsa27_btc5_tsa27`; `reports/tsa27-model-input-summary.md`; 1,008 curves, 0 TIPSY error rows | met |
| Model-input bundle with manifest and reproducible commands | `data/model_input_bundle/`; `metadata/model_input_bundle_manifest.yaml`; checksums recorded | met |
| QA report compares area, volume, and curves with the TSR evidence | `reports/tsa27-model-input-qa.md`; THLB residual explained | met with a stated limit |
| Dashboard and CI green on the head | Local dashboard green; CI run `40602050672` passes | met |

## 2. Workflow compliance

- Parent issue before the branch: parent #13 created before `feature/p2-compile`; branch from `main` at `3091906`.
- Branch from `main`: merge-base `3091906`.
- Commit messages start with task IDs: `P2.1 activate the FEMIC compile phase` (`902fbde`), `P2.1 build TSA 27 analysis units and strata` (`6ff0167`), `P2.2-P2.4 compile yields and QA the model inputs` (`0502490`), `P2.4 queue the phase review` (`7f2ab00`), plus the report commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: the P2 commits update `ROADMAP.md`, `CHANGE_LOG.md`, and `README.md`.
- Child issues closed with closeout evidence: #14, #15, #16, #17.
- Approval gates: no tag, release, settings change, or external account was created in P2.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `902fbde` | lint, format, types, tests, validator, docs | green |
| `6ff0167` | lint, format, types, tests, validator, docs | green |
| `0502490` | lint, format, types, tests, validator, docs | green |
| `7f2ab00` | lint, format, types, tests, validator, docs | green |

The local dashboard reported `OVERALL: GREEN. Every gate passed.` with 228 tests and 100% coverage.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| `40602050672` | `7f2ab00` | success | Quality gates, Pre-commit parity, and Green dashboard summary all pass |
| `40595323309` | `3091906` (main, P1 merge) | success | P1 merge head |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| The compiled THLB is 79,102 ha, above TSR4 (57,908) and TSR5 (51,454). | The legacy compile does not apply the full TSR netdown sequence (ownership, operability, low sites, non-merchantable, riparian, WTP, OGMA/MOGMA, caribou UWR). | Documented in the QA report; P3 will reconcile fragments and join the P1 caribou flags. |
| The legacy model has 18 AUs, not the 273 P2.1 classes. | The legacy pipeline builds its own BEC/species stratification. | The P2.1 table remains a diagnostic; P2.3 uses the model's 18 AUs. Documented. |
| The TIPSY rules use a catch-all. | TSA 27-specific species/BEC rules were not available in the instance. | `config/tipsy/tsa27.yaml` documents the provisional catch-all; replace with TSR/FSP rules later. |
| P1 caribou flags are not in the checkpoint. | The legacy compile reads VRI directly, not the P1 land-base layer. | P3 will join the flags to WS4 fragments. |

## 6. Next phase

**P3 — WS4 dataset.**

Goal: compile the fragment-level WS4 dataset and add the caribou, LU/BEC, and seral accounts.

Tasks:

- P3.1 Build the fragment layer with land-base and caribou attributes.
- P3.2 Compile tracks, curves, treatments, features, and products.
- P3.3 Add caribou and seral constraints.
- P3.4 Run the base simulation and reconcile the land base.

Acceptance criteria:

- The dataset loads and the constraints are inspectable.
- The base simulation completes with a recorded seed and run ID.
- The land-base reconciliation is within the stated tolerance.

Recommended default: activate P3 and start P3.1 after this report is approved.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
