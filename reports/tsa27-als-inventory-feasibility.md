# TSA 27 ALS inventory feasibility

Date: 2026-11-02
Status: audit complete; **no-go** for an operational local first-return inventory
from the current public data.

## Purpose

Decide whether TSA 27 has enough public FAIB plots and LidarBC point-cloud coverage
to justify a local first-return inventory. This audit does not download tiles, fit a
card, change the caribou layers, or change the model.

## Inputs

- TSA 27 boundary: `data/ws4/land_base.geojson` (758,443.7 ha).
- Public FAIB plot header and visit table.
- LidarBC discovery manifest for the TSA 27 bounding box.

## Results

| Item | Result |
| --- | ---: |
| FAIB plots inside TSA 27 | 67 |
| ICH / ESSF plots | 63 / 4 |
| All plots | PSP_G |
| Plots measured since 2018 | 0 |
| Last plot measurement range | 1992-2013 |
| LidarBC point-cloud tiles | 160 |
| Point-cloud acquisition years | 2019 (153), 2021 (7) |
| Point-cloud footprint inside TSA 27 | 23,008.1 ha |
| Footprint share of TSA 27 | 3.03% |
| Plots inside the point-cloud footprint | 13 |
| Plot/LiDAR time offsets | 18-27 years |
| Plots within 5 km / 10 km of a tile | 22 / 33 |
| Nearest-plot distance | min 0 m, median 10.4 km, max 47.5 km |

The 13 overlapping plots are all ICH; their plot visits are 1992-2001 and the
point clouds are 2019. The other 54 plots are outside the point-cloud footprint.

## Decision

**No-go for an operational local first-return inventory.**

A defensible local card needs plots and point clouds that are close in time and
space. TSA 27 has neither: no public FAIB plot has been measured since 2013, only
3.03% of the TSA has point-cloud coverage, and the 13 overlapping plots have
18-27 year offsets. The TSA 23 time-lag evidence showed volume error rising to
about 99 m3/ha at 21-30 years, so those overlaps are not a calibration set.

A research pilot is technically possible with the 13 ICH plots, but it would be a
time-lag stress test, not a local inventory. It should not be promoted to a card or
used for WS4/FHOPS decisions.

To make a local pilot defensible, one of these must happen:

1. Re-measure the 13 overlapping ICH plots and pair the new visits with the 2019
   point clouds.
2. Acquire contemporary point clouds over the recent plot locations, if any recent
   plots can be added.
3. Add recent public or partner plots inside the existing point-cloud footprint.
4. Keep the existing VRI-based model and treat ALS as a research-only transfer.

## Limits

- The footprint is the union of tile bounding boxes clipped to the TSA; it is an
  upper bound, not valid-pixel coverage.
- The FAIB header is PSP-only in this TSA; non-PSP plots are not represented.
- The audit does not assess point density, ground returns, or plot geometry quality.
- No point-cloud payload was downloaded.

## Reproduction

```bash
python scripts/audit_als_inventory_feasibility.py \
  --boundary data/ws4/land_base.geojson \
  --plots <faib_plot_header.csv> \
  --visits <faib_sample_byvisit.csv> \
  --selection <tsa27_lidarbc_selection.json> \
  --output reports/tsa27-als-inventory-feasibility.json
```

The machine-readable summary is `reports/tsa27-als-inventory-feasibility.json`.
