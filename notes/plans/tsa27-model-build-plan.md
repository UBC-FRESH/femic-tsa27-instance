# TSA 27 Revelstoke — detailed model-building plan

**Status:** planning note for Phase P0. **Owner:** UBC-FRESH. **Companion:** `reports/tsa27-tsr-corpus-analysis.md` (the TSR evidence and the caribou policy design). This note is the implementation plan; the report is the evidence base.

## 1. Decision question

Build a public FEMIC + WS4 model instance for the Revelstoke TSA (TSA 27) that can answer:

> **What is the impact of caribou habitat constraints on AAC in the Revelstoke TSA?**

and attribute the answer to:

1. the legal UWR / core no-harvest exclusion,
2. the matrix habitat constraint (max 13% of area <40 years),
3. the LU/BEC mature+old seral constraints, and
4. the historical 80-year immature-habitat deferral.

## 2. Scope and non-goals

**In scope**

- Public, reproducible FEMIC deployment instance for TSA 27.
- Materialization of the TSR corpus and a sanitized facts/evidence index.
- FEMIC compilation of TSA 27 land base, AUs, and yield curves from public data.
- WS4 dataset with fragments, tracks, curves, treatments, and habitat accounts.
- Scenario runs for caribou policy variants, with a validation report against the TSR4 and 2022 TSR evidence.
- Cross-link as a git submodule at `femic/external/femic-tsa27-instance`.

**Out of scope**

- Reproducing the unpublished 2022 STSM base case exactly. The 2022 data package does not publish results, so the WS4 implementation is a documented best guess.
- A new AAC determination or a legal opinion on the current UWR.
- Vendoring raw provincial data or copyrighted TSR PDFs in the public repository.
- A full provincial-scale model. The instance is TSA 27 only.

## 3. Repositories and linkage

| Item | Value |
|---|---|
| Public instance repo | `UBC-FRESH/femic-tsa27-instance` |
| Host repo | `UBC-FRESH/femic` |
| Submodule path | `external/femic-tsa27-instance` |
| Workflow seed | `UBC-FRESH/ubc-fresh-dev-workflow` |
| Model engine | `UBC-FRESH/ws4` |
| Case data | public BC data mirror; no raw data in git |

The instance repo is standalone and installable. The host repo adds it as a submodule next to the other `femic-tsaXX-instance` repos. The submodule commit is pinned to a reviewed release of the instance.

## 4. Phase plan

Each phase is one parent issue and one feature branch. Each task is one child issue. The roadmap is the plan of record; this note holds the detail.

### P0 — Bootstrap the public instance

| Task | Work | Evidence |
|---|---|---|
| P0.1 | Render the workflow seed; initialize the FEMIC instance; add TSA 27 run profile and TIPSY scaffold | `femic instance init`; `femic prep validate-case` passes |
| P0.2 | Add the TSR analysis report, curated netdown tables, cycle timeline, and evidence CSV | report and tables in `reports/` and `metadata/tsr/` |
| P0.3 | Add this plan and the scenario schema | `notes/plans/` and `scenarios/` |
| P0.4 | Add TSR/public-data fetch scripts and docs | scripts run; docs build |
| P0.5 | Pass the dashboard and queue the P0 pull request | `python scripts/dashboard.py` green |

**Exit:** repo public, CI green, docs build, preflight passes with the public-data mirror, report and plan reviewed.

### P1 — Materialize public inputs

| Task | Work | Evidence |
|---|---|---|
| P1.1 | Fetch/verify VRI 2025, TSA boundary, site productivity, BEC v12, LU, UWR/core/matrix, OGMA/MOGMA, roads, cutblocks | input manifest with versions and checksums |
| P1.2 | Clip to TSA 27; build the land-base layer and caribou zone flags | land-base GeoPackage/Parquet + QA |
| P1.3 | Reconcile land-base totals with TSR4 Table 3 and 2022 Table 14 | reconciliation CSV and report |

**Exit:** reproducible input manifest; land-base totals reconcile within a stated tolerance (e.g. 1% of the TSR area for each line, with differences explained).

### P2 — Compile FEMIC model inputs

| Task | Work | Evidence |
|---|---|---|
| P2.1 | Build AUs/strata from VRI, BEC, site index, species, managed/natural | AU table + summary |
| P2.2 | Run VDYP7 natural curves and TIPSY managed curves | curve tables + diagnostics |
| P2.3 | Compile the THLB/land-base checkpoint and the model-input bundle | `data/model_input_bundle/` + manifest |
| P2.4 | QA against TSR4/2022 areas and curves | QA report |

**Exit:** model-input bundle with manifest, provenance, and QA.

### P3 — Build the WS4 dataset

| Task | Work | Evidence |
|---|---|---|
| P3.1 | Build fragments with area, AU, age, site index, species, THLB, caribou/LU/BEC/OGMA flags | fragments layer + schema |
| P3.2 | Compile tracks, curves, treatments, features/products | compiled dataset + manifest |
| P3.3 | Add caribou accounts and constraints (UWR/core, matrix 13% <40, seral, deferral) | constraint config + unit tests |
| P3.4 | Run the base simulation; reconcile land base and harvest flow | run log + reconciliation |

**Exit:** dataset loads; constraints are inspectable; base-case simulation completes.

### P4 — Caribou policy scenarios and AAC analysis

| Task | Work | Evidence |
|---|---|---|
| P4.1 | Implement scenarios S0–S6 from the report | scenario YAMLs |
| P4.2 | Run simulations/optimizations with fixed seeds | run IDs + logs |
| P4.3 | Compare harvest/AAC, land base, age class, matrix disturbance | scenario table + figures |
| P4.4 | Attribute the AAC effect and validate against TSR evidence | attribution report + uncertainty |

**Exit:** scenario table with deltas, validation against TSR4/2022 evidence, and a written uncertainty assessment.

### P5 — Publish and release

| Task | Work | Evidence |
|---|---|---|
| P5.1 | Write the final report, docs, and figures | published report |
| P5.2 | Add the instance as a femic submodule | host PR |
| P5.3 | Tag a release after review | tag + release notes |

**Exit:** public release with reproducible commands, evidence, and limitations.

## 5. Data sources and ownership

| Dataset | Public source | Used for | Storage |
|---|---|---|---|
| TSA boundary | BCGW `WHSE_ADMIN_BOUNDARIES.FADM_TSA_SV` | Case clip | public mirror |
| VRI 2025 | BCGW `VEG_COMP_LYR_R1_POLY`; VDYP7 input GDB | Stand attributes | public mirror |
| Site productivity | `Site_Prod_BC.gdb` | Site index | public mirror |
| BEC v12 | BCGW `BEC_BIOGEOCLIMATIC_POLY` | LU/BEC strata | public mirror |
| UWR u-3-005 | BCGW `WCP_UNGULATE_WINTER_RANGE_SP` | No-harvest exclusion | public mirror |
| Core/matrix caribou | Provincial caribou recovery program layers | Recovery sensitivity | public mirror / request |
| Herd ranges | Provincial caribou herd locations | Reporting/overlap | public mirror |
| LU boundaries | BCGW `FADM_LANDSCAPE_UNIT_SV` | Seral accounting | public mirror |
| OGMA/MOGMA | BCGW / FSP | Old/mature reserves | public mirror |
| Roads | BCGW road layers | Harvest priority | public mirror |
| Cutblocks | BCGW `VEG_CONSOLIDATED_CUT_BLOCKS_SP` | Depletion | public mirror |
| TSR documents | BC TSR FTP + www2 2022 package | Policy evidence | fetched, not vendored |

Raw data is never committed. `scripts/fetch_public_data.sh` and `scripts/fetch_tsr_corpus.py` write to ignored paths; the manifest records the source URL, version/date, checksum, and retrieval command.

## 6. Caribou policy implementation in WS4

The full design is in Appendix A of the report. The implementation contract is:

### 6.1 Zone flags on fragments

`caribou_uwr`, `caribou_core`, `caribou_matrix`, `caribou_zone` (historical HLP zone), `caribou_immature` (historical deferral), and `lu_bec` are fragment attributes.

### 6.2 Land-base exclusion

- Base case (2022): fragments with `caribou_uwr = 1` are non-harvestable for the horizon.
- Core sensitivity: `caribou_core = 1` is also non-harvestable.
- Historical scenario: `caribou_immature = 1` is non-harvestable for years 0–80, then released.

### 6.3 Matrix cover constraint

- Account `matrix_area_lt_40` and `matrix_area_total` by matrix zone.
- Constraint: `matrix_area_lt_40 / matrix_area_total <= 0.13` at each period.
- Evaluate at the period midpoint; document the age definition and the period length.

### 6.4 Seral constraints

- Accounts `old_seral_ha`, `mature_old_seral_ha`, and `total_forest_ha` by LU/BEC (or NDT/BEC/BEO if the target uses that basis).
- Targets: 40% ≥140 years and 25% of those ≥250 years below the caribou line; 70% ≥140 years above; plus the RHLPO mature+old biodiversity targets in the caribou LUs.
- Version the target table: `targets_2010.yaml` and `targets_2022.yaml`.

### 6.5 Harvest priority

- Base case: emulate STSM's stand preference (volume/ha, cycle time, road distance) in the WS4 simulation.
- Document any deliberate difference (e.g. WS4 optimization vs STSM priority queue).

### 6.6 Scenario matrix

| ID | Scenario | UWR | Core | Matrix 13% | Seral | Deferral |
|---|---|---|---|---|---|---|
| S0 | TSR4 base (2010) | 2010 | no | no | yes | no |
| S1 | TSR4 + incremental reserves back | partial | no | no | yes | no |
| S2 | TSR4 no mature biodiversity in caribou LUs | 2010 | no | no | caribou LUs off | no |
| S3 | TSR5 base (2022) | 2020 | no | no | yes | no |
| S4 | TSR5 recovery sensitivity | 2020 | yes | yes | yes | no |
| S5 | TSR3-style historical | HLP zone | no | no | yes | 80 yr |
| S6 | No caribou constraints | no | no | no | as base | no |

### 6.7 Validation

- Land-base reconciliation against TSR4 Table 3 and 2022 Table 14.
- Harvest-flow comparison against TSR4 base case (207,100 / 135,900 / 240,500 m³/yr).
- Sensitivity deltas vs TSR4 (+8.4% incremental reserves; +4.0%/+2.5% mature biodiversity).
- Matrix constraint audit: ≤13% <40 years in S4.
- Core/UWR audit: zero harvest in excluded fragments.
- Seral audit: old/mature targets met by LU/BEC.
- Reproducibility: dataset manifest, scenario config, seed, run ID, WS4 version.

## 7. Verification commands

```bash
# repository quality gates
python scripts/dashboard.py

# FEMIC case preflight against the public-data mirror
export FEMIC_EXTERNAL_DATA_ROOT="${FEMIC_EXTERNAL_DATA_ROOT:-../femic/external/femic-public-data/data}"
femic prep validate-case --run-config config/run_profile.tsa27.yaml

# TSR corpus
python scripts/fetch_tsr_corpus.py
femic tsr extract --documents-path metadata/tsr/tsa_documents_with_2022.json \
  --corpus-root data/tsr/corpus \
  --output-path metadata/tsr/tsa_candidate_facts_2022plus.json --tsa 27

# WS4 build and run
ws4 build --xml output/patchworks/forestmodel.xml \
  --fragments output/patchworks/fragments.shp --out build/compiled
ws4 simulate --dataset build/compiled --schedule scenarios/s3_base.schedule.csv \
  --years 250 --out runs/s3_base
```

## 8. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| 2022 STSM results unpublished | WS4 cannot be validated against the current TSR | label WS4 as a best-guess implementation; validate against TSR4; refresh when TSR5 publishes |
| UWR boundary vintage (2010 vs 2020) | different caribou footprint | version the layer; run both S0 and S3 |
| CFLB (2010) vs AFLB (2022) accounting | reconciliation mismatch | harmonize to AFLB; keep a crosswalk table |
| Core/matrix layers not public | cannot run S4 | use the provincial caribou recovery program layers; record access and version |
| TSR PDF licensing | cannot vendor documents | fetch at runtime; track metadata and short evidence excerpts only |
| Large public data | repo bloat | fetch scripts + public mirror; `.gitignore` raw data |
| WS4 vs STSM model differences | attribution error | run simulation first; document differences; sensitivity tests |

## 9. First bounded move

1. Create the GitHub repository and Phase 0 parent/child issues (external action; approved by the maintainer's instruction).
2. Commit the seed + instance scaffold + report + this plan on `main`.
3. Create `feature/p0-bootstrap`, set P0 active, and open the P0 pull request.
4. Run the dashboard and record the result in `CHANGE_LOG.md`.
5. Stop and report the P0 evidence; wait for approval before P1.

## 10. References

- `reports/tsa27-tsr-corpus-analysis.md` — TSR questions, evidence, and answers.
- `docs/` — project docs to be filled during P0.
- `AGENTS.md` — the workflow contract.
- `ROADMAP.md` — the phase/task plan of record.
