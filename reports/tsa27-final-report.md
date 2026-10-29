# TSA 27 Revelstoke — final report

**Status:** public instance release candidate. Model built; preliminary AAC range estimated, not an official determination.

## Question

What is the impact of caribou habitat constraints on AAC in the Revelstoke TSA?

## Evidence base

The TSR corpus analysis is in `reports/tsa27-tsr-corpus-analysis.md`. It covers TSR1 1994, TSR2 1999, TSR3 2005, TSR4 2010, and the September 2022 TSR5 data package.

Key findings:

- TSR2/TSR3 modelled caribou as forest-cover/seral constraints; the area stayed in the THLB.
- TSR4 (2010) made caribou a legal spatial reserve netdown (18,909 ha) plus residual mature biodiversity constraints.
- The 2022 data package treats the UWR as a legal no-harvest LHLB exclusion (116,820 ha gross / 62,892 ha net) and proposes a core no-harvest + matrix max 13% <40 years sensitivity.
- Models used: FSSIM (1999/2005), FPS-ATLAS (2010), STSM2022/SELES10 (2022). Not Patchworks or SPADES.

## Model build

| Stage | Result |
|---|---|
| FEMIC input bundle | 37,463 stands; 6,439 THLB stands; 79,102 ha THLB; 18 AUs; 1,008 curves; 0 TIPSY errors |
| WS4 dataset | 40,660 fragments; 4,746 tracks; 54,510 features; 33,579 products; 94 accounts |
| UWR filter | 108,458 ha flagged; 8,029 fragments; 1,940 of 8,107 schedule rows excluded |

## Results

| Scenario | Harvest at offset 0 | Treated | Δ harvest vs no caribou |
|---|---:|---:|---:|
| `s6_no_caribou` | 24,218,812 m³ | 79,102 ha | — |
| `s3_tsr5_base` (UWR no-harvest) | 13,660,939 m³ | 57,941 ha | **−10,557,873 m³ (−43.6%)** |

This is a **first-period capacity comparison**, not an AAC. The schedules harvest all eligible blocks at year 0. The UWR no-harvest footprint is a large first-order constraint in this dataset.

## TSR4/TSR5 calibration

The TSR4 2010 sensitivities remain the quantitative benchmark:

- Incremental reserves back: +8.4% short/mid harvest, +2.2% long-term.
- Mature+old biodiversity removed from caribou LUs: +4.0% short/mid, +2.5% long-term.

The WS4 UWR result is much larger because it removes the entire UWR, not just the incremental reserves. It is not a like-for-like TSR4 test. The 2022 TSR5 base case is unpublished; the 2022-style result is a documented best guess.

## 2026 update: even-flow and operational attribution

The later operational work adds a preliminary even-flow range and a public-data attribution envelope.

| Result | Value |
|---|---:|
| S7 caribou/UWR max even-flow | 1.58–1.74M m³ per 10-year period (70–77% of AAC) |
| S8 no-caribou max even-flow | 2.21–2.44M m³ per 10-year period (98–108% of AAC) |
| 2019 UWR expansion | 0.841M m³ positive-margin volume removed (9.8% of pre-2019 pool) |
| Fire no-salvage | <0.6% of the positive pool in a year |
| Mill design capacity | Downie alone 2.10× AAC; not binding |
| 2021–2022 | Quantity/processing constraint robust at 77.8–96.2% and 67.1–95.6% positive vs 30.2% and 55.0% HBS |
| 2019, 2025 | Range-dependent; not uniquely identified without TSA billed stumpage |

The full synthesis is in `reports/tsa27-counterfactual-synthesis.md` and the public-data ranges are in `reports/tsa27-public-data-envelope.md` and `reports/tsa27-nested-public-scenarios.md`. The two-page answer is `reports/tsa27-executive-brief.md`.

## What is not done

- The **matrix 13% <40 years** and the **80-year historical deferral** are mapped in `config/ws4/caribou_constraints.yaml` but not enforced.
- The **AAC** requires a multi-rotation WS4 optimization and the full TSR netdown sequence. The current THLB is 79,102 ha vs the TSR 57,908/51,454 ha.
- The core/matrix and historical HLP layers are `to_fetch`.
- A TSA-27 billed-stumpage series and dated local mill-curtailment series are not available in the public record; the model uses public ranges and switches.
- Burn severity, salvage, and post-fire recovery are not modelled.

## Reproduce

```bash
python scripts/dashboard.py
python scripts/run_caribou_scenarios.py --check
python scripts/compare_caribou_scenarios.py --check
```

## Cross-links

- Instance: `UBC-FRESH/femic-tsa27-instance`
- Host: `UBC-FRESH/femic`
- Model: `UBC-FRESH/ws4`
- Workflow: `UBC-FRESH/ubc-fresh-dev-workflow`

## Release limitation

This release publishes the model, data pipeline, and first-period caribou comparison. It does **not** publish an AAC determination or a replication of the unpublished STSM results.
