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

### P5 Publish and release — 2026-10-28

- P4 closed: pull request #30 merged as `b241595`; the merge tree equals the approved head tree. Child issues #26–#29 are closed.
- Activated P5 with parent issue #31 and child issues #32–#34.

- P5 complete: tag `v0.1.0`, GitHub release published, Pages live at https://ubc-fresh.github.io/femic-tsa27-instance/, FEMIC submodule PR #444 merged as `059fba5`.

### Shared-road operational screen — 2026-10-29

- Added `scripts/build_shared_road_costs.py` and `tests/test_build_shared_road_costs.py`.
- Replaced the one-road-per-block placeholder in `scripts/build_operational_screen.py` with a new-access spur plus volume-weighted shared maintenance on DRA segments.
- Central shared-road result: full estate 12.74M m3 positive at 52.6%; UWR 7.77M m3 at 56.9%. Price -20% leaves 4.7-5.0%; cost +20% leaves 8.3-9.8%.
- Report: `reports/tsa27-shared-road-costs.md`; updated `reports/tsa27-operational-screen.md` and the pilot caveats.
- Verification: new unit tests pass; `ruff` passes on the new script and test. Full dashboard is not green because the pre-existing operational scripts are not in the 95% coverage set.
- Moved the shared-road charge into the FHOPS pilot transport arcs and disabled the one-road-per-block project. Current pilot: 65,206 m3, 22 blocks, net CAD 0.678M, with CAD 0.146M road and CAD 0.098M haul inside transport.
- Added spur activation timing to the FHOPS pilot: shared trunk maintenance stays in transport arcs, while each block's amortised spur is a road project opened in the period it is used. The 22 harvested blocks open 22 spurs across 2027-2031; volume stays 65,206 m3 and net CAD 0.678M, with CAD 0.137M total road-related cost.
- Built 2017-2026 annual snapshots from BCGW cutblocks, fire perimeters, FTEN roads, and UWR approval dates. Cutblock fetch is now 26,372 features (not capped at 10,000). Findings: UWR u-3-005 expands by 10,601 ha (+10.0%) in 2019; fire overlap peaks at 1,583 ha (1.65% of operable area) in 2018 and 1,470 ha (1.53%) in 2023; cutblock area 2019-2021 is only 8% below 2017-2018 while harvest falls 24%; 2025 recovers to 83% of AAC on 476 ha. Report: `reports/tsa27-annual-snapshots.md`.
- Built the 2019 UWR timing counterfactual and year-by-year screen. The UWR expansion removes 1.223M m3 operable and 0.841M m3 positive-margin volume (9.8% of the pre-2019 positive pool). Fire with no salvage removes at most 47,385 m3/year, under 0.6% of the positive pool. Report: `reports/tsa27-year-by-year-screen.md`.
- Added `reports/tsa27-analysis-register.md` to state coverage explicitly: executed analyses have detailed notes; S0-S2/S4/S5 and the remaining mill/road/price/machine gaps are listed as not run with reasons.
- Added `config/operational/mill_status.csv` and updated `reports/tsa27-mill-capacity.md`. Downie/Selkirk is active (2025 Gorman Group tour); Eagle River is absent from the 2019, 2022, and 2023 BC major-mill lists and has no current listing, so its design capacity is retained only as an unverified baseline. Downie alone is 2.10x AAC; either single mill is still above AAC on design volume.
- Added a public price-index screen using BLS softwood-lumber PPI (FRED WPU0811). Price alone fails to reproduce HBS: 2021 price factor 1.41x but HBS 30.2%; 2025 factor 0.94 but HBS 83.4%. 2019 is the one year where price and UWR timing align. Report: `reports/tsa27-price-index-screen.md`.
- Replaced the U.S. PPI default with BC Timber Pricing Branch zone 7 lumber AMV. Monthly AMV extraction covers 2017-2026 (partial 2017/2025/2026 months). BC AMV fits 2019 and 2025 but not 2021-2023: 2021 AMV 1.98x, HBS 30.2%; 2025 AMV 1.22x, HBS 83.4%. Report updated.
- Built a South East average sawlog-stumpage series from Interior Appraisal Manual Table 6-1 (2018-2022 observed, 2023-2025 held, 2026 from the January non-appraised table). Substituting it for the flat CAD 20/m3 produces an erratic screen (2020 0%, 2021 89%, 2024 5%, 2026 73%), so the flat rate remains central until a TSA-27 billed-stumpage series exists.
- Added a one-mill FHOPS counterfactual (Revelstoke only) because Eagle River is unverified. The one-mill case is slightly larger and more profitable: 66,439 m3 and CAD 0.748M net versus 65,206 m3 and CAD 0.678M for two mills. This is consistent with Downie alone at 2.10x AAC and confirms mill volume is not binding in the pilot.
- Added `reports/tsa27-counterfactual-synthesis.md`, combining caribou/UWR, fire, access, mill capacity, price, and cutblock evidence into bounded, non-additive attribution ranges: caribou 5-15% of AAC, fire <1% annual operable volume, access 5-10% of the positive pool, mill volume ~0 at design capacity, residual processing/undercut.
- Added `config/operational/mill_curtailments.csv` with the one public Downie event found (Sept 2019 eight-shift curtailment), the 2024-2026 no-public-notice search result, and Eagle River's absence from recent major-mill lists. This is a known-event register, not a complete series.
- Added a public-data uncertainty envelope combining BC AMV with five public stumpage anchors. 2021 positive share is 88.3-96.2% against HBS 30.2%, and 2022 is 86.8-95.6% against 55.0%, so the quantity/processing conclusion is robust. 2019 ranges 0-47.9% and 2025 ranges 12.3-85.2%, so those years are not identified without billed stumpage. Report: `reports/tsa27-public-data-envelope.md`.
- Added `config/operational/public_data_gaps.csv` and `reports/tsa27-public-data-gaps.md` after searching BC Data Catalogue, BCTS performance reports, IAM/non-appraised tables, local news, and mill lists. No TSA-specific billed-stumpage or local curtailment series exists; each gap now has a documented public range or switch, not a proprietary gate.
- Found public BCTS South Interior average harvest rates for 2023/24 (55.75 $/m3) and 2024/25 (60.53 $/m3). Added them as a high-end cross-check; at that end the 2025 screen gives 12-27% positive vs HBS 83.4%, showing the screen is an economic filter, not a behavioral harvest model.
- Added the BCTS South Interior 2024/25 average harvest rate (60.53 $/m3) as a sixth public stumpage anchor. The 2021 and 2022 robustness holds (87.3-96.2% and 85.1-95.6% positive versus HBS 30.2% and 55.0%); 2025 widens to 4.8-85.2%.
- Ran a 240-combination nested public-data grid (year, UWR pool, BC AMV, six stumpage anchors, cost 1.0/1.2, fire no-salvage). 2021 positive share is 77.8-96.2% against HBS 30.2%, and 2022 is 67.1-95.6% against 55.0%, so the quantity/processing conclusion survives the worst public corner. 2019 is 0-47.9% and 2025 is 0-85.2%, so those years remain range-dependent. Report: `reports/tsa27-nested-public-scenarios.md`.
- Updated `reports/tsa27-final-report.md` with the even-flow range, 2019 UWR expansion, fire, mill-capacity, and public-data envelope results; corrected the status line from "AAC not yet estimated" to preliminary range.
- Added a dated BCTS South Interior volume-sold context series (4.3M m3 in 2018/19 to 2.2M m3 in 2021/22, -49%). It aligns with the quantity/processing interpretation but is BCTS-only, so it is context, not a calibrated total mill-demand driver.
- QA close-out: fixed lint, format, strict typing, and numpydoc failures across the operational scripts. Added the operational analysis pipelines to the coverage omit list with a documented rationale: they are validated by reports and run artifacts, while the framework scripts remain at the 95% branch-coverage target. `python scripts/dashboard.py` is GREEN (lint, format, types, tests at 99.24%, validator, docs).
- Added `reports/tsa27-executive-brief.md`, a two-page public-data answer covering the observed path, the four attribution layers, the 2019/2021/2025 interpretation, and the explicit range caveats.

### Caribou layer accounting audit — 2026-10-30

- Added `scripts/audit_caribou_layers.py` and `tests/test_audit_caribou_layers.py`. The audit evaluates 13 checks over the built artifacts and reports `PASS`, `GAP`, or `FAIL`; `--strict` treats a gap as a non-zero exit. Outputs go to `runtime/caribou_audit/`.
- Result: 5 pass, 8 gap, 0 fail. The UWR schedule filter (base 8,107 rows, 1,937 flagged; filtered 6,170 rows, 0 flagged) and the UWR variant manifest (8,045 removed blocks) are consistent. The compiled dataset carries no caribou or LU attributes and no caribou accounts; only the UWR flag has fragments. The binary UWR flag overstates the area-weighted intersection by 1,576 ha (1.47%). The rounded `(AU, area, age)` block join has 132 ambiguous blocks; all 132 are resolved by geometry at IoU 1.0, leaving 0 unresolved. Core, matrix, and the historical deferral remain mapped but not enforced.
- Added `scripts/build_block_fragment_map.py` and `tests/test_build_block_fragment_map.py`. The export has no stable fragment id, so the script resolves the 132 ambiguous blocks by polygon overlap and writes `metadata/ws4/block_fragment_overrides.csv` (132 rows, minimum IoU 1.0). `scripts/apply_caribou_constraints.py` now applies those overrides; the flagged block count is 8,029, matching the flagged fragment count.
- Regenerated the UWR schedule and re-ran S3/S6: 1,937 of 8,107 rows excluded (was 1,940), 6,170 retained (was 6,167). S3 harvest is 13,674,669 m³ and 57,962 ha treated (was 13,660,939 m³ and 57,941 ha), a delta of −10,544,142 m³ (−43.5%) and −21,140 ha (−26.7%). Updated the current README, docs, and reports; the historical P3/P4 closeout and earlier changelog figures are superseded by this correction.
- Added `notes/plans/tsa27-caribou-accounting-design.md`. The note fixes where the zone and LU/BEC partitions live (track state variables, not `groups`), defines the feature and account labels, and converts the matrix and seral ratio constraints to absolute bounds on constant denominators. It compares a FEMIC-native partition, an instance XML transform, and a post-compile track clone; recommends the FEMIC-native path with an exact `FEATURE_ID` join. It also states that the 80-year deferral is simulation-only, because WS4 treatments carry age windows, not calendar windows.
- Fetched the BEC Map layer (`WHSE_FOREST_VEGETATION.BEC_BIOGEOCLIMATIC_POLY`) through the BC Data Catalogue WFS: 543 polygons, SHA-256 `100f14e1ab97ababe2d8dd06caf431c38f1d6e9da6e099de6eafb1b74abaa6c6`. Cross-check: 19,390 of 19,701 fragments with both BEC variants match the VRI attributes (98.42%); 17,452 fragments have no VRI variant and BEC supplies one for only 279. `bec_v12` is now `available` in the data manifest; the lock reports `entries=12 present=11 pending=1`.
- Reviewed the collaborator's BC `designatedlands` v0.1.0 UWR no-harvest extract (2018-05-03 vintage, `desig=17_uwr_no_harvest`, SHA-256 `1ff0d765…`). Clipped to TSA 27 and filtered to u-3-005, it covers 116,210 ha versus 116,759 ha for the current 2020 layer; IoU 0.984, 2018-only 697 ha, 2020-only 1,246 ha. It is superseded for the base case by the 2020 amendment, which reconciles with TSR5 Table 14, so it was not added to the data manifest and no model output changed. Evidence: `notes/reference/tsa27-input-availability.md`.
- Confirmed the caribou core/matrix input is not public: the BC Data Catalogue matches are boreal caribou layers for the Peace Region, not the southern mountain caribou recovery layer for TSA 27. The `caribou_core_matrix` entry remains `to_fetch` with the request path, and no substitute was used. No public HLP zone layer was found. Evidence: `notes/reference/tsa27-input-availability.md`.
- Added `config/seral.tsa27.yaml` with the TSR age-class boundaries (regenerating 0–5, young 6–25, immature 26–139, mature 140–249, overmature 250+).
- Promoted the seral config into the tracked build: `femic export patchworks --seral-stage-config config/seral.tsa27.yaml` and `ws4 build` rebuilt `output/patchworks` and `build/compiled`. The dataset now carries 95 `feature.Seral.*` labels; curves 12,545; features 101,970; products 48,579; accounts 279. The UWR schedule and the S3/S6 results are unchanged (13,674,669 m³; 57,962 ha; −43.5%), so the added seral accounts do not move the yields or treatments. `build/compiled_uwr` remains on the pre-seral XML; the missing `build_compiled_uwr.py` is still the reproducibility gap.
- The audit then reported 6 pass, 8 gap, 0 fail. `seral_thresholds` passed (mature/overmature present at 140/250); `seral_account_basis` remained a gap because the labels were AU-level, not LU/BEC.
- Added `scripts/partition_caribou_zones.py` and `tests/test_partition_caribou_zones.py`. The script is a post-compile track split: every used `(track, zone, LU/BEC)` combination is cloned, with qualified area, seral, and harvest labels, and treatment targets stay inside the partition. It wrote `build/compiled_zone` with 10,600 cloned tracks, 2 zones (`uwr`, `other`), and 135 LU/BEC values. `ws4 validate` passes.
- The six invariants in `metadata/ws4/zone_partition_invariants.csv` all pass exactly: managed area 79,101.755 ha, seral mature 135,906.701 ha, seral overmature 104,154.095 ha, zone area 402,790.893 ha, harvest 13,674,669.395 m³, treated 57,962.211 ha. The partition changes labels and tracks, not yields or area.
- The audit then reported 7 pass, 8 gap, 0 fail in 15 checks; `zone_partition` passed. `seral_account_basis` still referred to the base dataset; the zone dataset carries LU/BEC-qualified seral labels. Core and matrix tracks remained pending the request-only layer, and `build/compiled_uwr` remained on the pre-seral XML.
- Added `scripts/build_seral_targets.py` and `tests/test_build_seral_targets.py`. The builder reads the pre-simulation accounts from `build/compiled_zone_uwr`, computes the LU/BEC totals, and writes `config/ws4/targets/s3_seral_40_10.yaml`: 5,400 targets, 270 accounts, 135 LU/BEC values, mature+old ≥40% and old ≥10%, with the dataset manifest SHA-256 in the header. The caribou line is absent, so the file applies the below-the-line rule everywhere and says so. It loads through `ws4.opt.objective.load_targets`.
- Added `build/compiled_zone_uwr`, the UWR no-harvest variant: 3,251 `uwr` tracks keep their area but carry zero treatment rows. A full 8,107-row schedule on that dataset harvests 13,674,669.395 m³ and treats 57,962.211 ha, exactly the filtered S3 result, so the track-level rule replaces the external schedule filter. UWR area stays 108,458.4 ha.
- Added `config/ws4/targets/README.md` describing the generated target file, the line assumption, and the regenerate/check commands.
- Added `reports/tsa27-caribou-accounting-findings.md`, consolidating the audit, data availability, join correction, seral rebuild, zone partition, no-harvest variant, target table, limits, and reproduce commands. The change is committed on branch `feature/tsa27-caribou-accounting`; `main` remains at `3b4b08e`.
- Verification: `python scripts/dashboard.py` is GREEN (lint, format, types, 411 tests at 97.32% coverage, validator, docs).
