# TSA 27 land-base reconciliation

This report compares the provisional P1.2 land base with the TSR4 2010 and 2022 TSR5 tables.
Only the gross land base and the direct caribou UWR clip are directly comparable at this stage.

Inputs: `metadata/land_base/tsa27_land_base_summary.csv`, `metadata/tsr/tsa27_thlb_netdown_table3.csv`, and `metadata/tsr/tsa27_thlb_netdown_table14_2022.csv`.

| Metric | WS4 (ha) | TSR (ha) | Difference (ha) | Difference (%) | Comparable | Within tolerance |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| gross_land_base | 758,444 | 758,502 | -58 | -0.01 | yes | yes |
| caribou_uwr_gross | 116,759 | 116,820 | -61 | -0.05 | yes | yes |
| caribou_uwr_net |  | 62,892 |  |  | no | n/a |
| aflb | 419,663 | 216,217 | 203,446 | 94.09 | no | no |
| thlb_2022 | 246,451 | 51,454 | 194,997 | 378.97 | no | no |
| thlb_2010 | 246,451 | 57,908 | 188,543 | 325.59 | no | no |
| caribou_2010_netdown |  | 18,909 |  |  | no | n/a |
| ogma_2010 | 0 | 5,549 | -5,549 | -100.00 | no | no |

## Findings

- The gross land base matches the 2022 TSR5 value within 59 ha (0.008%), confirming the TSA 27 boundary and VRI clip.
- The direct UWR u-3-005 no-harvest clip matches the 2022 TSR5 gross value within 61 ha (0.05%), confirming the layer and filter.
- The binary VRI UWR flag is **not** used for area accounting: it reports 247,313 ha because whole VRI polygons are painted at the fragmented UWR edge. The direct clip is 116,759 ha.
- The forested VRI class (419,663 ha) is not the AFLB (216,217 ha); it still contains ownership, non-administered, road, and park exclusions.
- The provisional THLB candidate (246,451 ha) is not comparable to the TSR THLB (51,454 ha in 2022; 51,044 ha long-term in 2010). The remaining netdowns are the P2 work.
- Legal OGMA has no polygons in TSA 27; the TSR uses non-legal FSP OGMAs/MOGMAs.

## Decision for P2

Keep the direct UWR clip as the caribou area accounting layer. Do not use the binary VRI flag for area totals; use it only for fragment screening until fragments are split at the UWR boundary.

P2 must apply the remaining TSR netdowns (ownership, non-administered, roads, parks, inoperable, unstable/ESA, non-merchantable, low sites, riparian, community watersheds, WHA, PSP, backlog, cultural, WTP, OGMA/MOGMA) before the THLB is compared to the TSR.
