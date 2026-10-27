# Phase close-out report: P1 Data materialization

Phase: P1 Data materialization
Parent issue: #8
Pull request: #12, `feature/p1-data` into `main`
Evidence head: `b4a3f5f`, the head covered by CI run `40591536138`
Report commit: the commit that adds this report; its CI run is posted on pull request #12
Date: 2026-10-27
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

1. Squash-merge pull request #12, and delete the branch `feature/p1-data`.
2. Close parent issue #8 with a closeout comment that cites the merge commit.
3. Launch P2 FEMIC compile: create its branch, set the phase statuses in `ROADMAP.md`, create its child issues as sub-issues, and start P2.1.

Settings changes, each with its exact command. Each one runs only after its own approval.

- None in P1. GitHub Pages remains deferred to P5; the Docs deploy workflow still fails with `Creating Pages deployment failed: Not Found` until Pages is enabled.

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Every input has a source, version, path, and digest or fetch command | `metadata/data_manifest.yaml` has 12 entries; `metadata/data_manifest.lock.yaml` records 10 present entries; 2 are explicitly `to_fetch` | met with a stated limit: BEC v12 and core/matrix caribou are pending |
| TSA 27 land-base layer with documented schema and caribou flags | `scripts/build_land_base.py`; `metadata/land_base/tsa27_land_base_summary.csv`; `metadata/land_base/tsa27_land_base_notes.md` | met with a stated limit: core/matrix/historical flags are zero until their layers arrive |
| Reconciliation explains every material difference | `reports/tsa27-land-base-reconciliation.md`; `metadata/tsr/tsa27_land_base_reconciliation.csv` | met |
| Comparable rows are within tolerance | `python scripts/reconcile_land_base.py --check` passes; gross 758,443 vs 758,502 ha (−0.008%); UWR 116,759 vs 116,820 ha (−0.05%) | met |
| Raw data is not tracked | `data/bc/`, `data/downloads/`, `data/tsr/`, `data/land_base/`, and the facts/lock artifacts are ignored; `git status` is clean | met |
| Dashboard and CI pass on the head | Local dashboard green; CI run `40591536138` passes Quality gates, Pre-commit parity, and Green dashboard summary | met |

## 2. Workflow compliance

- Parent issue before the branch: parent #8 created before `feature/p1-data`; branch created from `main` at `b28b9e1`.
- Branch from `main`: merge-base `b28b9e1`.
- Commit messages start with task IDs: `P1.1 activate P1 data materialization` (`a756080`), `P1.1 add the public-data manifest and verifier` (`da5a8ae`), `P1.2 build the provisional TSA 27 land base` (`7a6ab04`), `P1.3 reconcile the land base with the TSR tables` (`6af585e`), `P1.3 queue the phase review` (`62393ad`), `P1.3 add the direct UWR area to the land-base summary` (`f66b1cb`), `P1.3 add geospatial and stub dependencies for CI` (`b4a3f5f`), plus the report commit.
- Gates for each commit: section 3.
- Roadmap and changelog in step: the P1 commits update `ROADMAP.md`, `CHANGE_LOG.md`, and `README.md`.
- Child issues closed with closeout evidence: #9, #10, #11.
- Approval gates: no tag, release, settings change, or external account was created in P1. Pages enablement is deferred to P5.

## 3. Gate evidence

| Commit | Gates run | Result |
| --- | --- | --- |
| `a756080` | lint, format, types, tests, validator, docs | green |
| `da5a8ae` | lint, format, types, tests, validator, docs | green |
| `7a6ab04` | lint, format, types, tests, validator, docs | green |
| `6af585e` | lint, format, types, tests, validator, docs | green |
| `62393ad` | lint, format, types, tests, validator, docs | green |
| `f66b1cb` | lint, format, types, tests, validator, docs | green |
| `b4a3f5f` | lint, format, types, tests, validator, docs | green |

The local dashboard reported `OVERALL: GREEN. Every gate passed.` with 213 tests and 100% coverage.

## 4. CI evidence

| Run ID | Head commit | Conclusion | Notes |
| --- | --- | --- | --- |
| `40591536138` | `b4a3f5f` | success | Quality gates, Pre-commit parity, and Green dashboard summary pass |
| `40591379031` | `f66b1cb` | failure | Quality gates failed because CI lacked pandas/PyYAML stubs. Fixed by adding `pandas-stubs`, `types-PyYAML`, `geopandas`, and `pyogrio` to `requirements-dev.txt` in `b4a3f5f`. |
| `40591301988` | `62393ad` | failure | Same missing-stub cause; fixed in `b4a3f5f`. |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| The binary UWR flag overstates the caribou footprint (247,313 ha vs the direct clip 116,759 ha). | Whole VRI polygons are painted when they intersect a fragmented UWR edge. | The direct clip is used for area accounting; the flag is kept for fragment screening only. P2/P3 will split fragments at the UWR boundary. |
| The cutblock WFS response contains 10,000 features. | The service may cap the response. | Documented in the manifest; confirm pagination before depletion work. |
| BEC v12 polygon, core/matrix caribou, non-legal OGMA/MOGMA, and historical HLP zone are still `to_fetch`. | They were not in the shared mirror or need a program request. | Explicit `to_fetch` entries with notes; the corresponding flags are zero and labelled. |

## 6. Next phase

**P2 — FEMIC compile.**

Goal: compile the TSA 27 land base, AUs, and yield curves with FEMIC.

Tasks:

- P2.1 Build analysis units and strata from VRI, BEC, site index, species, and managed/natural status.
- P2.2 Run VDYP7 natural curves and TIPSY managed curves.
- P2.3 Compile the THLB checkpoint and the model-input bundle.
- P2.4 QA the compiled inputs against the TSR evidence.

Acceptance criteria:

- The model-input bundle has a manifest and provenance.
- The QA report covers area, volume, and curve comparisons.
- The compile is reproducible from the documented commands.

Recommended default: activate P2 and start P2.1 after this report is approved.

## 7. Decision

- [ ] Approve as written.
- [ ] Approve with the changes stated here: <changes>.
