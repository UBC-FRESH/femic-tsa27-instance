# TSA 27 year-by-year operational screen

**Status:** reduced-form annual screen, 29 October 2026.
**Not a schedule, not an AAC, and not a full historical reconstruction.**

## Purpose

The static screen showed that roughly half of current operable volume has a positive delivered
margin under central shared-road costs. This report asks two narrower questions:

1. How much of the supply pool disappears when the **2019 UWR expansion** is added back for
   2017–2018?
2. How much does **fire with no salvage** remove from the annual supply pool?

Prices, costs, and mill capacity are held static, so the year-to-year variation here is
supply-side only.

## UWR timing counterfactual

The current UWR dataset removes the full u-3-005 footprint. The 2019 approval added about
10,601 ha. The block-level add-back identifies **792 blocks / 9,647 ha** affected by the
expansion. Of those, 223 blocks are in the full operational screen.

| Pool | Blocks | Total volume | Positive volume | Positive share | Selected in 5-year envelope | Median margin |
|---|---:|---:|---:|---:|---:|---:|
| Pre-2019 u-3-005 | 5,513 | 14.88M m³ | 8.61M m³ | 57.8% | 1.124M m³ | 7.29 $/m³ |
| Post-2019 u-3-005 | 5,290 | 13.66M m³ | 7.77M m³ | 56.9% | 1.122M m³ | 7.57 $/m³ |
| Expansion blocks only | 223 | 1.22M m³ | 0.84M m³ | 68.7% | 0.84M m³ | 5.82 $/m³ |

The 2019 expansion removes:

- **1.223M m³** of total operable volume, about **8.2%** of the pre-2019 pool;
- **0.841M m³** of positive-margin volume, about **9.8%** of the pre-2019 positive pool.

The expansion blocks are higher-margin than average (68.7% positive), so they reduce the
positive pool proportionally more than the total pool. The timing matches the 2019 harvest
drop from 92.8% to 49.1% of AAC, but the size cannot explain a 47% one-year drop.

## Fire no-salvage screen

The fire overlay is applied to the UWR pool for each year. Burned operable volume is removed
with no salvage and no re-entry. Fixed costs remain.

| Year | HBS m³ | Harvest/AAC | Fire volume removed m³ | Positive before m³ | Positive after m³ | Positive share after |
|---:|---:|---:|---:|---:|---:|---:|
| 2017 | 166,545 | 74.0% | 0 | 8.61M | 8.61M | 57.8% |
| 2018 | 208,727 | 92.8% | 47,385 | 8.61M | 8.59M | 57.9% |
| 2019 | 110,545 | 49.1% | 0 | 7.77M | 7.77M | 56.9% |
| 2020 | 105,455 | 46.9% | 0 | 7.77M | 7.77M | 56.9% |
| 2021 | 68,000 | 30.2% | 587 | 7.77M | 7.77M | 56.9% |
| 2022 | 123,835 | 55.0% | 42,286 | 7.77M | 7.75M | 56.9% |
| 2023 | 95,521 | 42.5% | 33,411 | 7.77M | 7.76M | 56.9% |
| 2024 | 130,930 | 58.2% | 44,957 | 7.77M | 7.74M | 56.9% |
| 2025 | 187,750 | 83.4% | 0 | 7.77M | 7.77M | 56.9% |
| 2026 | 107,110 | 47.6% YTD | 0 | 7.77M | 7.77M | 56.9% |

The largest annual removal is **47,385 m³** in 2018 and **44,957 m³** in 2024. The positive
share barely moves. Fire cannot explain the 2019–2021 or 2023 lows in this screen.

## What the annual screen shows

- The **supply-side pool is stable** from 2019 through 2026: positive volume stays at 7.77M m³,
  56.9% of the UWR pool.
- HBS harvest swings from **30.2%** to **83.4%** of AAC over the same period.
- The 2019 UWR step is a real, bounded reduction: **0.84M m³ positive**, about **9.8%** of the
  pre-2019 positive pool.
- Fire with no salvage removes at most **0.6%** of the positive pool in a year.

The residual is not a shrinking land base, a collapsing cutblock program, or fire. It is the
**undercut** relative to AAC: mill demand, processing capacity, markets, and stand/volume
quality. The 2019 UWR step is the main legal timing event and belongs in the caribou
counterfactual, but it is not the main aggregate driver.

## Caveats

- The pre-2019 pool is a reduced-form add-back from the full screen, not a WS4 recompile with
  historical UWR boundaries.
- The add-back covers 9,647 ha of the 10,601 ha expansion because of block clipping and
  eligibility.
- Fire no-salvage is an extreme case. It removes burned volume entirely and does not model
  salvage, re-entry, or post-fire recovery.
- Prices, costs, and mill capacity are static. The screen cannot reproduce the HBS year-to-year
  path by itself.
- Eagle River's operating status is unverified; the screen still uses it as a destination.
- 2026 HBS is January–September only.
- The screen is a filter, not a schedule.

## Files

- `scripts/build_uwr_timing.py`
- `scripts/build_year_by_year_screen.py`
- `runtime/annual_snapshots/uwr_expansion_blocks.csv`
- `runtime/annual_snapshots/uwr_timing_summary.csv`
- `runtime/annual_snapshots/year_by_year_screen.csv`
- `reports/tsa27-annual-snapshots.md`
- `reports/tsa27-operational-screen.md`

## Next

1. Recompile the WS4 UWR dataset with the 2019 expansion removed, rather than adding blocks
   back in the reduced-form screen.
2. Add dated mill capacity and curtailment events.
3. Add dated price and cost series.
4. Run the nested counterfactuals: actual, no caribou, no fire, no access constraint, no
   mill-capacity constraint, and price/cost shocks.
