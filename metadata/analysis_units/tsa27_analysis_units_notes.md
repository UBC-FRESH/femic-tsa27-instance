# TSA 27 analysis units — notes

**Status:** P2.1 provisional AU build from the P1 land base.

## Base layer

The build selects `PROJECT == "REVELSTOKE_VRI"` from the P1 land-base layer. This is the TSA 27 base VRI project. The TFL 55/56 VRI projects, the Mount Revelstoke project, the Clearwater project, and the fire/update overlays are excluded to avoid overlapping double counts. They need a separate ownership/TFL exclusion step in P2.3.

The selected base has **35,213 polygons** and **468,114 ha** of union area.

## Rule set

- **Species group:** `SPECIES_CD_1` mapped to `BL`, `CW`, `HW`, `SX`, `FDI`, `PL`, `AT`, or `OTHER`; missing is `UNK`.
- **BEC:** `BEC_ZONE_CODE` + `BEC_SUBZONE` (for example `ESSFvc`).
- **Site index:** `SI1` <10 m, `SI2` 10–15 m, `SI3` 15–20 m, `SI4` ≥20 m, `SI0` missing.
- **Origin:** `managed` when `OPENING_IND == "Y"` or `last_harvest_year > 0`; otherwise `natural`.
- **AU ID:** `<species>-<BEC>-<SI class>-<origin>`.

Every polygon gets an AU ID. Non-forested polygons are `NONFOREST`; forested polygons missing species, site index, or age are `UNASSIGNED` with a reason.

## Summary

| Class | Union area (ha) | Polygons |
|---|---:|---:|
| NONFOREST | 210,530 | 8,283 |
| All forested AUs | 257,583 | 26,930 |
| UNASSIGNED | 32.6 | — |
| THLB-candidate AUs | 143,428 | — |
| **Total selected base** | **468,114** | **35,213** |

There are **273 AU/stratum classes**.

## Caveats

- The TSA 27 gross land base in the 2022 TSR5 table is 758,502 ha, which includes TFLs and other land not administered for TSA timber supply. The 468,114 ha selected base is the Revelstoke VRI project, not the gross TSA.
- The AU areas are union areas within each AU. Cross-AU overlaps from the VRI source are reduced but not eliminated; P2.3 must produce a non-overlapping THLB checkpoint.
- `UNASSIGNED` is 32.6 ha, which is small but must be resolved or explicitly excluded before the yield compile.
- The managed/natural split uses the opening and cutblock signals as a proxy. It is not a full RESULTS silviculture history.
- The THLB-candidate area (143,428 ha) is not the final THLB; the remaining netdowns are P2.3/P2.4 work.

## Reproduce

```bash
python scripts/build_analysis_units.py
python scripts/build_analysis_units.py --check
```
