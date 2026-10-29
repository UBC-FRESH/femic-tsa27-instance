# TSA 27 annual snapshots, 2017–2026

**Status:** annual public-layer overlay, 29 October 2026. **Not a historical inventory reconstruction and not a harvest attribution by itself.**

## Purpose

The current compiled dataset is a single estate. To explain the post-2017 AAC-to-harvest gap, the model needs to know what changed in each year. This report builds the first annual snapshot layer from public data:

- cutblock area opened each year;
- fire perimeters and the operable volume they overlap;
- active FTEN road length;
- approved UWR u-3-005 area;
- the recovered HBS harvest series.

It is a screening layer. It shows timing and scale, not causal attribution.

## Sources

| Layer | Source | Use |
|---|---|---|
| Cutblocks | BCGW `VEG_CONSOLIDATED_CUT_BLOCKS_SP` | Annual opening area, clipped to TSA 27 |
| Fire | BCGW `PROT_HISTORICAL_FIRE_POLYS_SP` | Annual perimeter and block overlap |
| Roads | BCGW `FTEN_ROAD_SEGMENT_LINES_SVW` | Active length by retirement date |
| UWR | BCGW `WCP_UNGULATE_WINTER_RANGE_SP` | Approved u-3-005 area by approval date |
| Harvest | HBS recovered series | Annual scaled volume and ratio to AAC |

The cutblock and fire layers were fetched from the BCGW WFS for the TSA 27 bounding box. The cutblock fetch returned **26,372** features, replacing the earlier 10,000-feature capped file. The fire fetch returned **1,517** features.

## Method

- Clip every layer to the TSA 27 boundary in EPSG:3005.
- Cutblock year is `HARVEST_START_YEAR_CALENDAR`, with the harvest date as a fallback.
- Fire year is `FIRE_YEAR`; each fire is intersected with the current WS4 blocks.
- Operable volume at risk is the block's year-0 operable volume apportioned by the burned fraction of the block. It is **not** a loss or salvage estimate.
- Active road length includes FTEN segments whose retirement date is empty or later than the year-end. There is no build-date field, so this is a retirement proxy, not a construction history.
- UWR area is the union of approved u-3-005 polygons whose `APPROVAL_DATE` is on or before the year. This is an approval-date proxy from the current boundary layer.

## Annual table

| Year | HBS m³ | Harvest / AAC | Cutblock ha | Cumulative cutblock ha | Fire block overlap ha | Operable volume at risk m³ | Active road km | UWR u-3-005 ha |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2017 | 166,545 | 74.0% | 745.2 | 745.2 | 370.0 | 0 | 2,381.3 | 106,157.5 |
| 2018 | 208,727 | 92.8% | 1,110.3 | 1,855.6 | 1,582.7 | 58,677 | 2,362.5 | 106,157.5 |
| 2019 | 110,545 | 49.1% | 473.5 | 2,329.0 | 2.0 | 0 | 2,352.5 | 116,758.8 |
| 2020 | 105,455 | 46.9% | 773.9 | 3,102.9 | 0.0 | 0 | 2,301.8 | 116,758.8 |
| 2021 | 68,000 | 30.2% | 459.8 | 3,562.7 | 1,213.6 | 8,687 | 2,252.1 | 116,758.8 |
| 2022 | 123,835 | 55.0% | 510.4 | 4,073.1 | 940.0 | 42,286 | 2,229.3 | 116,758.8 |
| 2023 | 95,521 | 42.5% | 517.1 | 4,590.2 | 1,470.0 | 99,338 | 2,229.3 | 116,758.8 |
| 2024 | 130,930 | 58.2% | 550.9 | 5,141.1 | 536.5 | 56,572 | 2,226.6 | 116,758.8 |
| 2025 | 187,750 | 83.4% | 476.2 | 5,617.3 | 2.7 | 0 | 2,199.2 | 116,758.8 |
| 2026 | 107,110 | 47.6% | 153.9 | 5,771.2 | 0.0 | 0 | 2,193.5 | 116,758.8 |

2026 is January–September only. The 2026 cutblock value is also partial.

## Findings

### 1. The clearest legal land-base timing event is the 2019 UWR expansion

UWR u-3-005 rises from **106,157.5 ha** in 2017–2018 to **116,758.8 ha** in 2019, an increase of **10,601.3 ha (+10.0%)**. The step coincides with the harvest drop from 92.8% of AAC in 2018 to 49.1% in 2019 and 46.9% in 2020.

This is consistent with the earlier model result that the UWR land base removes a large share of managed inventory. It does not prove that the UWR expansion caused the full 2019 drop; the timing is the important evidence.

### 2. Fire is real but too small to explain the aggregate gap

Fire overlap peaks at **1,582.7 ha** in 2018 and **1,470.0 ha** in 2023. Those are **1.65%** and **1.53%** of the operable block area. Operable volume at risk peaks at **99,338 m³** in 2023, about **0.41%** of the 24.22M m³ operable pool.

The lowest harvest year, 2021, has 1,213.6 ha of fire overlap but only **8,687 m³** of operable volume at risk. Fire cannot be the main aggregate driver, although individual operating areas and salvage decisions can still be affected.

### 3. Cutblock area did not collapse with the harvest

Cutblock area in 2019–2021 totals **1,707.2 ha**, only **8.0% below** the 2017–2018 total of 1,855.6 ha. HBS harvest falls **24.3%** over the same comparison and **67.4%** from 2018 to 2021.

The 2025 recovery to **83.4% of AAC** happens with only **476.2 ha** of cutblock area, less than half of the 2018 area. The land base was not the binding constraint in 2025.

### 4. Harvest intensity moved in the opposite direction to the gap

Cutblock hectares per 1,000 m³ of harvest:

| Year | ha / 1,000 m³ |
|---:|---:|
| 2018 | 5.32 |
| 2020 | 7.34 |
| 2021 | 6.76 |
| 2023 | 5.41 |
| 2025 | 2.54 |

The 2020–2021 trough harvested more area per unit volume, consistent with lower-volume or partial stands. The 2025 recovery harvested much less area per unit volume, consistent with higher-volume stands or a different product mix. This points to volume quality, stand selection, and mill demand, not a simple shortage of cutblock area.

### 5. The active road network contracted slowly

Active FTEN length falls from **2,381.3 km** in 2017 to **2,193.5 km** in 2026, a **7.9%** decline. That is a retirement proxy, not a full access history, but it does not show a sudden access collapse in 2019–2021.

## What this means for the attribution

The annual snapshots sharpen the interim story:

- **Caribou/UWR timing** is the clearest legal land-base event, at 2019.
- **Fire** is spatially real but small at TSA scale; it is an operating-area and salvage issue, not the aggregate driver.
- **Cutblock area** does not track the harvest collapse or recovery.
- **Road retirements** are gradual.
- The remaining explanation is the one the cost screen already points to: **product value, mill demand, processing capacity, and stand/volume quality**, with access and fire as local modifiers.

This supports a caribou share in the **5–15% of AAC** range rather than a dominant share, but the 2019 timing means the UWR step deserves a dedicated counterfactual.

## Caveats

- Cutblocks are a current layer with satellite-change-detection records; the annual area is an opening proxy, not scaled harvest volume.
- Fire overlap is a perimeter intersection. It does not include burn severity, unsalvaged loss, salvage eligibility, or post-fire recovery.
- UWR area uses current boundaries and approval dates, not the 2010/2014/2020 boundary versions.
- Active road length uses retirement dates as a proxy; there is no build-date field.
- HBS 2022–2026 are provisional monthly-preview values; 2026 is year-to-date.
- The current WS4 blocks are used for every year. This is not a historical block roll-back.

## Files

- `scripts/fetch_annual_snapshot_layers.py`
- `scripts/build_annual_snapshots.py`
- `tests/test_build_annual_snapshots.py`
- `runtime/annual_snapshots/annual_snapshot_summary.csv`
- `runtime/annual_snapshots/fire_overlap_by_year.csv`
- `data/downloads/bc/cutblocks_tsa_bbox.geojson`
- `data/downloads/bc/fire_perimeters_tsa_bbox.geojson`

## Next

1. Replace the current-block fire overlay with a year-specific block roll-back.
2. Add burn severity and salvage eligibility.
3. Run the operational screen year by year against HBS.
4. Build the nested counterfactuals: actual, no caribou, no fire, no access constraint, no mill-capacity constraint, and price/cost shocks.
