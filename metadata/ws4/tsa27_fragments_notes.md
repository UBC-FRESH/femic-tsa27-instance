# TSA 27 WS4 fragments — notes

**Status:** P3.1 provisional fragment layer.

## Source

- P2 stand checkpoint: `data/vri_vclr1p_checkpoint8.feather` (37,463 non-overlapping stands; 402,791 ha).
- UWR u-3-005 no-harvest: `data/downloads/bc/uwr.geojson`.
- Landscape units: `data/downloads/bc/lu.geojson`.
- Legal OGMA: `data/downloads/bc/ogma.geojson` (no polygons in TSA 27).

## Attributes

- `fragment_id` from `FEATURE_ID`.
- `au`, `curve1`, `curve2`, `thlb`, `thlb_area_ha`, `SITE_INDEX`, `PROJ_AGE_1`, species, BEC.
- `caribou_uwr_frac` = intersection area / fragment area; `caribou_uwr = 1` when fraction >= 0.5.
- `caribou_core`, `caribou_matrix`, `caribou_zone`, `caribou_immature`, `ogma` = 0 until the layers arrive.
- `lu_name`, `lu_bec` from the landscape-unit join.

## Summary

| Class | Area (ha) | Fragments |
|---|---:|---:|
| All fragments | 402,791 | 37,463 |
| THLB | 79,102 | 8,107 |
| Caribou UWR (flag >= 0.5) | 108,458 | 8,029 |

The direct UWR clip is 116,759 ha. The fragment flag is lower because fragments straddling the UWR boundary are flagged only when at least half their area is inside. This is a deliberate conservative rule; P3.3 can split boundary fragments if needed.

## Caveats

- Core/matrix caribou habitat, the historical HLP zone, and non-legal OGMA/MOGMA are still `to_fetch`.
- The fragment layer is a stand checkpoint, not a dissolved ownership/operability land base. The THLB is the legacy compile's 79,102 ha, above the TSR values.
- The WS4 export and dataset compile are P3.2.

## Reproduce

```bash
python scripts/build_ws4_fragments.py --check
```
