# TSA 27 caribou attribution and uncertainty

**Status:** P4.4. First-period capacity comparison, not an AAC determination.

## Question

What is the impact of caribou habitat constraints on AAC in the Revelstoke TSA?

## What the current WS4 model can answer

The dataset and runs support two scenarios:

| Scenario | Status | What it does |
|---|---|---|
| `s3_tsr5_base` | supported | Applies the UWR u-3-005 no-harvest filter to the schedule |
| `s6_no_caribou` | supported | No caribou filter |

The comparison is a **first-period capacity comparison**:

| Scenario | Harvest at offset 0 | Treated area |
|---|---:|---:|
| `s3_tsr5_base` | 13,674,669 m³ | 57,962 ha |
| `s6_no_caribou` | 24,218,812 m³ | 79,102 ha |
| **UWR effect** | **−10,544,142 m³ (−43.5%)** | **−21,140 ha (−26.7%)** |

The UWR filter removed 1,937 of 8,107 scheduled block rows. The 132 ambiguous `(AU, area, age)` pairs are resolved by geometry, so the block flags match the 8,029 flagged fragments.

This shows that the legal UWR no-harvest footprint is a very large first-order constraint in the current WS4 dataset. It is **not** an AAC impact: the schedules harvest all eligible blocks at year 0, and there is no multi-rotation harvest-flow optimization.

## TSR4 validation

The TSR4 2010 sensitivities are the quantitative benchmark:

- Adding back the incremental caribou reserves (4,076 ha, +7% THLB) raised short/mid harvest by **8.4%** and LTHL by **2.2%**.
- Removing mature+old biodiversity constraints in caribou LUs raised short/mid harvest by **4.0%** and LTHL by **2.5%**.

The WS4 UWR result is much larger because it removes the **entire** UWR no-harvest footprint (108,458 ha flagged), not just the incremental reserves. It is not directly comparable to the TSR4 incremental sensitivity. A like-for-like TSR4 test requires the 2010 UWR boundary and the incremental/status-quo split, which are not in the instance.

## TSR5 best guess

The 2022 TSR5 data package gives the legal UWR as 116,820 ha gross / 62,892 ha net LHLB removal. The WS4 fragment flag covers 108,458 ha with a 0.5 intersection threshold; the direct UWR clip is 116,759 ha. The WS4 THLB is 79,102 ha, above the TSR5 51,454 ha because the legacy compile does not apply the full netdown sequence.

The base-case UWR exclusion is therefore directionally consistent with TSR5, but the absolute harvest/AAC effect cannot be read from the current first-period run.

## Scenarios not run

| Scenario | Status | Reason |
|---|---|---|
| S0 TSR4 base | proxy | 2010 UWR boundary is not available; current UWR used as proxy |
| S1 TSR4 incremental back | unavailable | Incremental GAR layer is not available |
| S2 TSR4 no caribou-LU biodiversity | unavailable | Needs an XML feature variant removing those constraints |
| S4 TSR5 recovery | unavailable | Core/matrix caribou layers are not available; matrix 13% mapped but not enforced |
| S5 TSR3-style historical | unavailable | Historical HLP zone and immature deferral layers are not available |

These are explicit gaps, not silent omissions.

## AAC interpretation

The current result is a **capacity/first-period comparison**, not an AAC. To estimate the AAC effect, the next step is a multi-rotation WS4 optimization with:

- the full TSR netdown sequence (to close the 79,102 ha vs 51,454 ha THLB gap);
- the 2010 and 2020 UWR boundary versions;
- the matrix 13% <40 years constraint and the historical deferral;
- a harvest-flow objective over 250 years.

The TSR4 sensitivities and the TSR5 data package remain the evidence base for calibrating that run.

## Reproducibility

- Scenario registry: `config/ws4/scenario_registry.yaml`
- Scenario record: `metadata/ws4/scenario_runs.json`
- Comparison: `metadata/ws4/scenario_comparison.csv`, `reports/tsa27-caribou-scenario-comparison.md`
- Runs: `runs/s3_tsr5_base/`, `runs/s6_no_caribou/` (ignored)
- Dataset manifest: `metadata/ws4/dataset_manifest.yaml`

## Verdict

The model is built and runs. It shows a large first-order UWR no-harvest effect, but it does **not** yet produce an AAC estimate. The remaining work is the multi-rotation AAC optimization and the unsupported policy layers, not a rebuild of the pipeline.
