# P8 TSA 27 ALS acquisition and remeasurement request

Date: 2026-11-02
Status: request package prepared; no acquisition or remeasurement commitment.

## Why

The P7 audit is a no-go for an operational local first-return inventory:

- 67 FAIB plots, all PSP_G: 63 ICH and 4 ESSF;
- no plot measured since 2018; last visits are 1992-2013;
- 160 LidarBC point-cloud tiles (2019/2021) covering 3.03% of TSA 27;
- 13 plots overlap the footprint, all ICH, with 18-27 year plot/LiDAR offsets.

The existing VRI-based model remains the operational model. An ALS card needs
plots and point clouds that are close in time and space.

## Request

Remeasure the 13 high-priority ICH plots and acquire contemporary point clouds
over them. A 2 km request bbox is provided for each plot.

| Priority | Plots | Definition | 2 km request footprint |
| --- | ---: | --- | ---: |
| High | 13 | Inside the 2019 point-cloud footprint; ICH; 18-27 year offsets | 13,475.4 ha union |
| Medium | 9 | Within 5 km of a tile, not inside | 14,400 ha bbox sum |
| Secondary | 45 | Outside 5 km | 72,000 ha bbox sum |
| All | 67 | | 60,367.9 ha union |

High-priority plots:

| Site | BEC | Last visit | 2019 offset |
| --- | --- | ---: | ---: |
| 4021258 | ICH mw | 1992 | 27 |
| 4021333 | ICH mw | 1992 | 27 |
| 4021334 | ICH mw | 1992 | 27 |
| 4021335 | ICH mw | 1992 | 27 |
| 4021336 | ICH mw | 1992 | 27 |
| 4021338 | ICH mw | 1992 | 27 |
| 4021339 | ICH mw | 1992 | 27 |
| 4021340 | ICH mw | 1992 | 27 |
| 4021341 | ICH mw | 2001 | 18 |
| 4021342 | ICH mw | 1995 | 24 |
| 4021343 | ICH mw | 1994 | 25 |
| 4021344 | ICH mw | 1994 | 25 |
| 4022491 | ICH wk | 1993 | 26 |

## Specification

- Plot remeasurement: full PSP protocol, live/dead trees, DBH, height, species,
  damage, and plot support; record the measurement date and field crew.
- Point cloud: classified LAS/LAZ with first returns, acquisition date, density,
  CRS, and vertical datum; co-registered 1 m DEM/DSM where available.
- Time matching: prefer a 2026 point cloud and 2026 remeasurement. If only the 2019
  point cloud is available, the remeasurement still reduces the offset from 18-27
  years to about 7 years, but that must be recorded as a time-lag pilot.
- Extent: the 2 km bboxes in `tsa27-als-acquisition-request.csv`; a merged tile set
  is fine.
- Transfer: Globus or the public-data mirror, with a SHA-256 manifest.
- Metadata: project/contract ID, acquisition dates, sensor, density, classification
  scheme, and any vertical-datum limitation.

## What it unblocks

A local ICH first-return fit with 13 plots, a temporal or spatial holdout, and a
comparison with the VRI-based model. Thirteen plots is still a small pilot; the
result would be research-grade, not operational.

## Limits

- The 2 km bbox is an acquisition footprint, not a density or quality guarantee.
- Remeasuring a plot does not reconstruct its 2019 state; a 2026 point cloud is the
  cleaner pairing.
- The partner may have different priorities, boundaries, or field capacity.
- No point cloud has been requested, downloaded, or processed, and no plot has been
  remeasured by this package.

## Files

- `reports/tsa27-als-acquisition-request.csv`
- `reports/tsa27-als-acquisition-request.md`
- Source audit: `reports/tsa27-als-inventory-feasibility.md`
