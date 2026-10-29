# TSA 27 analysis and scenario register

**Status:** coverage map, 29 October 2026. **Purpose:** say exactly which analyses have a detailed note, which are only summarised, and which are still missing. This is the answer to “are all scenarios and analyses documented?”

## Short answer

No — not all. Every analysis that has actually been run has a report or a detailed section, and every scenario that could not be run has an explicit reason. The remaining gaps are listed at the end and are not hidden inside a single netdown.

## Strategic and evidence analyses

| Analysis | Status | Detailed note | Main limitation |
|---|---|---|---|
| TSR corpus and policy evidence | Complete | `reports/tsa27-tsr-corpus-analysis.md` | 2022 TSR5 results unpublished |
| Land-base reconciliation | Complete | `reports/tsa27-land-base-reconciliation.md` | THLB not yet through full netdown |
| FEMIC model-input QA | Complete | `reports/tsa27-model-input-qa.md` | Legacy compile, caribou flags added later |
| FEMIC model-input summary | Complete | `reports/tsa27-model-input-summary.md` | Same |
| WS4 dataset build | Complete | `reports/tsa27-ws4-dataset.md` | UWR flag threshold 0.5 |
| WS4 base capacity run | Complete | `reports/tsa27-base-run.md` | Capacity, not AAC |
| HBS / Figure 4 recovery | Complete | `reports/tsa27-figure4-recovery.md` | 2022–2026 provisional |
| TSR4/TSR5 caribou attribution | Complete | `reports/tsa27-caribou-attribution.md` | First-period capacity, not AAC |
| Final release report | Complete for P5 | `reports/tsa27-final-report.md` | Predates the operational work |

## Caribou scenarios S0–S8

| Scenario | Status | Detailed note / artifact | Reason |
|---|---|---|---|
| S0 TSR4 base (2010) | Not run | `reports/tsa27-caribou-attribution.md` | 2010 UWR boundary not available; current UWR is only a proxy |
| S1 TSR4 incremental reserves back | Not run | same | Incremental GAR layer not available |
| S2 TSR4 no caribou-LU biodiversity | Not run | same | Needs XML feature variant |
| S3 TSR5 base | Run | `reports/tsa27-caribou-scenario-comparison.md` | First-period capacity only |
| S4 TSR5 recovery | Not run | `reports/tsa27-caribou-attribution.md` | Core/matrix layers not available; matrix 13% mapped but not enforced |
| S5 TSR3-style historical | Not run | same | Historical HLP zone and immature deferral unavailable |
| S6 No caribou | Run | `reports/tsa27-caribou-scenario-comparison.md` | Upper-bound counterfactual |
| S7 Max even-flow, UWR no-harvest | Run | `reports/tsa27-caribou-evenflow-result.md` | 200-year, 10-year periods; preliminary |
| S8 Max even-flow, no caribou | Run | `reports/tsa27-caribou-evenflow-result.md` | Same targets; preliminary |

S7/S8 target files are `config/ws4/targets/evenflow_caribou.yaml` and `evenflow_no_caribou.yaml`. The run plans are in `runs/s7_evenflow_caribou/plan.txt` and `runs/s8_evenflow_no_caribou/plan.txt`.

## Operational and economic analyses

| Analysis | Status | Detailed note | Variants captured |
|---|---|---|---|
| 45-block FHOPS pilot | Complete | `reports/tsa27-operational-pilot.md` | No-road, one-road-per-block, shared-road-in-arcs, shared-trunk + spur activation |
| Full-estate operational screen | Complete | `reports/tsa27-operational-screen.md` | Base, price −20%, cost +20% |
| Shared-road build/maintenance | Complete | `reports/tsa27-shared-road-costs.md` | Build/maintenance low, central, high |
| Mill design capacity and operating status | Partial | `reports/tsa27-mill-capacity.md`, `config/operational/mill_status.csv` | Downie active; Eagle River absent from 2019/2022/2023 major-mill lists |
| Mill curtailment register | Partial | `config/operational/mill_curtailments.csv` | One 2019 Downie event; no 2024-2026 public notice found; not a complete series |
| Truck-legal routing | Complete for pilot | `reports/tsa27-operational-pilot.md` | Strict filter fragments full network; full screen uses all-DRA with flags |
| Annual snapshots 2017–2026 | Complete | `reports/tsa27-annual-snapshots.md` | Cutblock, fire, FTEN road, UWR timing |
| 2019 UWR timing counterfactual | Complete | `reports/tsa27-year-by-year-screen.md` | Pre-2019 vs post-2019 UWR pool |
| Fire no-salvage screen | Complete | `reports/tsa27-year-by-year-screen.md` | No-salvage annual removal |
| One-mill pilot counterfactual | Complete | `reports/tsa27-operational-pilot.md` | Revelstoke only; 66,439 m³, 0.748M net |
| Public price-index screen | Partial | `reports/tsa27-price-index-screen.md` | BC interior lumber AMV; South East average sawlog-stumpage table sensitivity; no TSA-27 billed stumpage |
| Interim AAC-to-harvest attribution | Complete | `reports/tsa27-interim-attribution.md` | Bounded answer, not final decomposition |
| Counterfactual synthesis | Complete | `reports/tsa27-counterfactual-synthesis.md` | Layer ranges, not additive; residual processing/undercut |
| Executive brief | Complete | `reports/tsa27-executive-brief.md` | Two-page public-data answer and caveats |
| Public-data uncertainty envelope | Complete | `reports/tsa27-public-data-envelope.md` | Price/stumpage ranges; 2021–2022 robust, 2019/2025 not identified |
| Nested public-data scenario grid | Complete | `reports/tsa27-nested-public-scenarios.md` | 240 combinations; 2021–2022 robust, 2019/2025 and 2023/2024 wide |
| Public-data gap register | Complete | `reports/tsa27-public-data-gaps.md` | Each gap has a public source check and a model treatment |

## Explicit gaps

These are **not** documented as completed analyses because they have not been run:

1. **Current mill operating status and curtailments.** Downie/Selkirk is active; Eagle River is unverified and absent from recent major-mill lists. No dated curtailment series exists.
2. **Re-opening and closure timing for existing shared roads.** New-spur activation is in the pilot; existing shared roads are still assumed open.
3. **Full WS4 recompile with the 2019 UWR expansion removed.** The year-by-year screen uses a reduced-form add-back, not a historical WS4 dataset.
4. **Burn severity, salvage eligibility, and post-fire recovery.** Fire is a perimeter overlap only.
5. **Dated price, stumpage, and contractor-cost series.** BC interior lumber AMV, a South East average sawlog-stumpage table sensitivity, and BCTS South Interior harvest rates for 2023/24-2024/25 exist; a TSA-27 billed-stumpage series and contractor-cost series do not.
6. **Machine, labour, and landing capacity.** FHOPS uses a capacity envelope, not a full machine schedule.
7. **Nested counterfactuals for no access and no mill capacity.** No-caribou, fire, price/cost, and one-mill pilot counterfactuals exist; a full no-access screen and a mill-capacity-constrained whole-TSA run do not.
8. **Historical block roll-back.** Current WS4 blocks are used for every year.
9. **Validation against TSR5 results.** The 2022 base case and core/matrix results are unpublished.

## How to read the notes

- A **detailed note** means the report states the method, inputs, results, sensitivity, and caveats.
- A **summary only** item is a table inside another report, not a standalone analysis.
- An **explicit gap** is a scenario that was not run. The reason is stated; it is not a silent omission.

## Files

- `reports/tsa27-tsr-corpus-analysis.md`
- `reports/tsa27-land-base-reconciliation.md`
- `reports/tsa27-model-input-qa.md`
- `reports/tsa27-ws4-dataset.md`
- `reports/tsa27-base-run.md`
- `reports/tsa27-caribou-attribution.md`
- `reports/tsa27-caribou-scenario-comparison.md`
- `reports/tsa27-caribou-evenflow-result.md`
- `reports/tsa27-figure4-recovery.md`
- `reports/tsa27-operational-pilot.md`
- `reports/tsa27-operational-screen.md`
- `reports/tsa27-shared-road-costs.md`
- `reports/tsa27-mill-capacity.md`
- `reports/tsa27-annual-snapshots.md`
- `reports/tsa27-year-by-year-screen.md`
- `reports/tsa27-interim-attribution.md`
- `notes/plans/tsa27-operational-aac-gap-plan.md`
- `CHANGE_LOG.md`
