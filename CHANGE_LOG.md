# Change Log

Newest entries last. Each milestone gets a dated entry that matches the roadmap status and the GitHub issue comments.

## 2026-10-27

- Created FEMIC TSA 27 Revelstoke Instance from the UBC-FRESH dev workflow seed. The agent contract, roadmap, docs skeleton, and validator came from the seed. Every phase is planned, and no parent issues exist yet.

### P0 bootstrap — 2026-10-27

- Created the public repository `UBC-FRESH/femic-tsa27-instance` and activated Phase P0 with parent issue #1 and child issues #2–#6.
- Added the TSR corpus analysis (`reports/tsa27-tsr-corpus-analysis.md`) with the 19-document inventory, the 2010 and 2022 THLB netdown tables, the cycle timeline, and the caribou evidence excerpts.
- Added the detailed model-building plan (`notes/plans/tsa27-model-build-plan.md`) and the S0–S6 caribou scenario schema.
- Added `scripts/fetch_tsr_corpus.py` with unit tests and the raw-data ignore rules; raw TSR PDFs and provincial data remain out of git.
- Added the data provenance and limitations docs and the TSA 27 run profile/TIPSY scaffold.
- Verification: `python scripts/dashboard.py` is green (lint, format, types, tests at 100% coverage, validator, docs). `femic prep validate-case --run-config config/run_profile.tsa27.yaml` passes with the public-data mirror.

- Opened pull request #7 for P0 review; the dashboard is green and every child issue has evidence. P0 is `pr-open`.

### P1 data materialization — 2026-10-27

- P0 closed: pull request #7 merged as `b28b9e1`; the merge tree equals the approved head tree. Child issues #2–#6 are closed.
- Activated P1 with parent issue #8 and child issues #9–#11. The first task is P1.1, the public-data manifest and verification script.

- P1.1: added `metadata/data_manifest.yaml`, the verification script and tests, and `metadata/data_manifest.lock.yaml`. Mirror checks: 5 present (VRI 2025 layer, VRI VDYP input, TSA boundary, site productivity, 19-document TSR corpus), 7 pending `to_fetch`. Dashboard green (182 tests, 100% coverage).

- P1.2: built the provisional TSA 27 land base from VRI 2025, TSA 27, landscape units, UWR u-3-005, legal OGMAs, and cutblocks. Direct UWR clip is 116,759 ha vs 116,820 ha in TSR5 Table 14 (0.05% difference). The binary VRI flag overstates the UWR edge (247,313 ha); this is documented and deferred to fragment splitting in P1.3/P2. Legal OGMA has no polygons in TSA 27; non-legal OGMAs, BEC v12, core/matrix, and the historical HLP zone remain `to_fetch`.

- P1.3: reconciled the provisional land base against TSR4 Table 3 and TSR5 Table 14. Gross 758,443 ha vs 758,502 (−0.008%); direct UWR u-3-005 116,759 ha vs 116,820 (−0.05%). AFLB and THLB are not comparable yet: the provisional forested class is 419,663 ha and the THLB candidate 246,451 ha, pending the P2 netdown sequence. Report: `reports/tsa27-land-base-reconciliation.md`.

- P1 is `pr-open`: all three tasks are complete; the phase pull request is queued for review.

### P2 FEMIC compile — 2026-10-27

- P1 closed: pull request #12 merged as `3091906`; the merge tree equals the approved head tree. Child issues #9–#11 are closed.
- Activated P2 with parent issue #13 and child issues #14–#17. The first task is P2.1, the analysis-unit and strata build.

- P2.1: built 273 AU/stratum classes from the Revelstoke VRI project (35,213 polygons; 468,114 ha). Non-forest 210,530 ha; forested AUs 257,583 ha; THLB candidate 143,428 ha; UNASSIGNED 32.6 ha. TFL/update projects excluded to avoid overlapping double counts. Dashboard green (228 tests, 100% coverage).

- P2.2/P2.3: ran VDYP7 natural curves and TIPSY/BTC managed curves. 18 model AUs, 1,008 curves, 6,939 curve points, 0 TIPSY error rows. The model-input bundle is in `data/model_input_bundle/`; the stand checkpoint is `data/vri_vclr1p_checkpoint8.feather` (37,463 stands; 6,439 THLB; 79,102 ha THLB).
- P2.4: QA report at `reports/tsa27-model-input-qa.md`. The THLB is 21,194 ha above TSR4 and 27,648 ha above TSR5 because the legacy compile did not apply the full netdown sequence; this is explained and deferred to P3. Caribou flags will be joined in P3.

- P2 is `pr-open`: all four tasks are complete; the phase pull request is queued for review.

### P3 WS4 dataset — 2026-10-27

- P2 closed: pull request #18 merged as `9e60a5a`; the merge tree equals the approved head tree. Child issues #14–#17 are closed.
- Activated P3 with parent issue #19 and child issues #20–#23. The first task is P3.1, the WS4 fragment layer and caribou attributes.

- P3.1: built 37,463 WS4 fragments (402,791 ha; 79,102 ha THLB); UWR flag covers 108,458 ha / 8,029 fragments.
- P3.2: exported Patchworks XML/fragments and compiled `build/compiled` (40,660 fragments; 4,746 tracks; 54,510 features; 94 accounts).
- P3.3: applied the UWR u-3-005 no-harvest schedule filter (1,940 of 8,107 rows excluded); matrix 13% and historical deferral mapped but not enforced.
- P3.4: ran the capacity test (24.2M m³ at offset 0) and the UWR-constrained run (13.66M m³, 57,941 ha treated). Reports: `reports/tsa27-ws4-dataset.md`, `reports/tsa27-base-run.md`.

- P3 is `pr-open`: all four tasks are complete; the phase pull request is queued for review.

### P4 Caribou scenarios — 2026-10-28

- P3 closed: pull request #24 merged as `e14d455`; the merge tree equals the approved head tree. Child issues #20–#23 are closed.
- Activated P4 with parent issue #25 and child issues #26–#29. The first task is P4.1, the scenario registry and runners.

- P4.1: added the scenario registry and runner. Supported: S3 UWR base and S6 no caribou. S0 proxy and S1/S2/S4/S5 unavailable with explicit reasons.
- P4.2: ran `s3_tsr5_base` and `s6_no_caribou`; record in `metadata/ws4/scenario_runs.json`.
- P4.3: UWR reduces first-period harvest by 10,557,873 m3 (-43.6%) and treated area by 21,160 ha (-26.8%) vs no caribou. Comparison in `metadata/ws4/scenario_comparison.csv`.
- P4.4: attribution and uncertainty report at `reports/tsa27-caribou-attribution.md`; states the result is capacity, not AAC.

- P4 is `pr-open`: all four tasks are complete; the phase pull request is queued for review.
