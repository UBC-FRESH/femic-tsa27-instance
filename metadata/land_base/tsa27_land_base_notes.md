# TSA 27 provisional land-base build — notes

**Status:** P1.2 provisional build. Not final; P1.3 reconciles the totals against the TSR tables.

## Inputs

| Input | Source | Version | Note |
|---|---|---|---|
| VRI 2025 | BCGW `VEG_COMP_LYR_R1_POLY` | 2025 | BEC fields come from VRI (`BEC_ZONE_CODE`, `BEC_SUBZONE`, `BEC_VARIANT`) |
| TSA boundary | BCGW `FADM_TSA_SV` | current | TSA 27 dissolved; area 758,443 ha |
| Landscape units | BCGW `RMP_LANDSCAPE_UNIT_SVW` | current | 163 polygons in the TSA 27 bbox |
| Caribou UWR | BCGW `WCP_UNGULATE_WINTER_RANGE_SP` | 2020 amendment | u-3-005, no-harvest zone only |
| Legal OGMA | BCGW `RMP_OGMA_LEGAL_CURRENT_SVW` | current | 0 polygons intersect TSA 27; non-legal OGMAs are in FSP layers, still to fetch |
| Cutblocks | BCGW `VEG_CONSOLIDATED_CUT_BLOCKS_SP` | current | WFS response capped at 10,000 features; pagination check pending |
| Roads | BCGW `FTEN_ROAD_SEGMENT_LINES_SVW` | current | Harvest-priority input, not yet joined |

## Results

The built layer is `data/land_base/tsa27_land_base.gpkg` (ignored). The tracked summary is `metadata/land_base/tsa27_land_base_summary.csv`.

| Class | Union area (ha) | Polygons | Note |
|---|---:|---:|---|
| Gross clip | 758,443 | 64,675 | Matches the 2022 TSR5 gross land base (758,502 ha) within 59 ha |
| Forested, treed VRI | 419,663 | 48,680 | Provisional AFLB-like class; parks/ownership not yet removed |
| Caribou UWR, binary flag | 247,313 | 19,609 | Edge-inflated by the binary polygon flag; the direct UWR clip is 116,759 ha |
| Legal OGMA | 0 | 0 | No legal OGMA intersects TSA 27; non-legal OGMAs are FSP-based |
| Provisional THLB candidate | 246,451 | 32,250 | Forested, outside UWR and legal OGMA only; missing operability, ownership, low-site, riparian, non-merchantable, WTP, and OGMA/MOGMA rules |
| Caribou core | 0 | 0 | `to_fetch` |
| Caribou matrix | 0 | 0 | `to_fetch` |

Direct UWR u-3-005 clip: **116,759 ha**, versus **116,820 ha** in the 2022 TSR5 Table 14 (difference 61 ha, 0.05%). That is an excellent match and confirms the source layer and filter.

## Why the binary UWR flag is larger than the direct clip

The VRI polygon layer overlaps in the source (sum of polygon areas 1,274,476 ha vs union 758,443 ha). A binary "intersects UWR" flag paints whole VRI polygons, including polygons that only touch a fragmented UWR boundary. The result is 247,313 ha of flagged VRI union, roughly twice the true 116,759 ha UWR footprint. The layer is therefore useful for **fragment screening**, not for direct area accounting. P1.3 and P2 should either compute the intersection area per fragment or split fragments at the UWR boundary.

## Caveats

- The legal OGMA layer has no polygons in TSA 27. The TSR uses non-legal OGMAs/MOGMAs adopted in Forest Stewardship Plans; those are still to fetch.
- The cutblock WFS response is capped at 10,000 features; the layer may be truncated. Confirm the total and paginate before using it for depletion.
- The BEC polygon layer was not fetched. The build uses VRI BEC attributes; fetch the BEC v12 polygon layer for the final cross-check.
- The 2022 core/matrix caribou layer and the historical HLP caribou zone/immature layers are not available yet. The corresponding flags are zero and explicitly labelled.
- The provisional THLB candidate is not comparable to the TSR4 51,044 ha long-term THLB or the 2022 51,454 ha preliminary THLB. It omits several large netdowns. P1.3 will quantify the gap.

## Next step

P1.3 reconciles these totals against TSR4 Table 3 and 2022 Table 14, explains the residuals, and decides whether to keep the binary flags or split fragments at the policy boundaries.
