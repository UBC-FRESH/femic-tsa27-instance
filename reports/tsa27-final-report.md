# TSA 27 Revelstoke — final report

**Status:** public instance release candidate. Model built; AAC not yet estimated.

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

## What is not done

- The **matrix 13% <40 years** and the **80-year historical deferral** are mapped in `config/ws4/caribou_constraints.yaml` but not enforced.
- The **AAC** requires a multi-rotation WS4 optimization and the full TSR netdown sequence. The current THLB is 79,102 ha vs the TSR 57,908/51,454 ha.
- The core/matrix and historical HLP layers are `to_fetch`.

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
