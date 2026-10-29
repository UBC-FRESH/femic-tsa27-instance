# TSA 27 public-data uncertainty envelope

**Status:** public-data-only envelope, 29 October 2026.
**Not a single-point attribution and not a proprietary cost model.**

## Principle

The model uses public data only. Where a public series does not exist, the model carries an
explicit range instead of inventing a gate. This report combines the public price index with
five public stumpage anchors and the pre/post-2019 UWR pool.

## Inputs

- Price: BC interior zone 7 lumber AMV, annual factor vs 2026.
- Stumpage anchors: **12.76, 20.00, 32.53, 47.10, 55.22, 60.53 $/m³**.
  - 12.76 is the 2026 South East average.
  - 20.00 is the model’s flat central assumption.
  - 32.53, 47.10, and 55.22 are observed South East averages from 2018–2022.
  - 60.53 is the BCTS South Interior 2024/25 average harvest rate.
- UWR pool: pre-2019 for 2017–2018; post-2019 from 2019 onward.
- All other costs and the shared-road surface are unchanged.

## Annual envelope

| Year | AMV factor | Min positive share | Median | Max | HBS / AAC |
|---:|---:|---:|---:|---:|---:|
| 2017 | 0.929 | 0.0% | 2.3% | 62.2% | 74.0% |
| 2018 | 1.119 | 0.0% | 28.5% | 81.3% | 92.8% |
| 2019 | 0.878 | 0.0% | 0.1% | 47.9% | 49.1% |
| 2020 | 0.984 | 0.0% | 6.7% | 70.7% | 46.9% |
| 2021 | **1.978** | **87.3%** | **90.1%** | **96.2%** | **30.2%** |
| 2022 | **1.876** | **85.1%** | **89.0%** | **95.6%** | **55.0%** |
| 2023 | 1.167 | 0.0% | 39.0% | 83.4% | 42.5% |
| 2024 | 1.089 | 0.0% | 21.4% | 79.9% | 58.2% |
| 2025 | 1.224 | 4.8% | 48.5% | 85.2% | 83.4% |
| 2026 | 1.000 | 0.0% | 8.5% | 73.0% | 47.6% |

## BCTS South Interior cross-check

The BCTS Annual Performance Report 2024/25 gives South Interior average harvest rates:

| Fiscal year | South Interior average harvest rate |
|---|---:|
| 2023/24 | 55.75 $/m³ |
| 2024/25 | 60.53 $/m³ |

These sit at the high end of the public stumpage envelope. At 55.22–60.53 $/m³, the 2025
screen gives only 4.8–12.3% positive, while HBS is 83.4%. The screen is an economic filter, not a behavioral
harvest model: tenure obligations, non-market harvest, and mill-specific fibre needs can
produce harvest above the positive-margin pool. That is exactly why the output is a range.

Source: `config/operational/bcts_south_interior_harvest_rate.csv`.

### BCTS South Interior demand context

BCTS reports South Interior volume sold, not Okanagan-Columbia alone:

| Fiscal year | South Interior volume sold |
|---|---:|
| 2017/18 | 4.2M m³ |
| 2018/19 | 4.3M m³ |
| 2019/20 | 3.7M m³ |
| 2020/21 | 4.0M m³ |
| 2021/22 | 2.2M m³ |
| 2022/23 | 2.4M m³ |

The 2021/22 value is **49% below** 2018/19. That is a public demand-activity signal aligned
with the quantity/processing interpretation, but it is BCTS-only and not a total mill-demand
series. It is therefore context, not a calibrated demand driver.

Source: `config/operational/bcts_south_interior_volume.csv`.

## What is robust

### 2021 and 2022 are quantity/processing years

Even at the **highest** public stumpage anchor (60.53 $/m³), the 2021 positive-margin share is
**87.3%**. HBS is **30.2%**. The 2022 minimum is **85.1%** against HBS **55.0%**.

No public price or stumpage combination brings the 2021–2022 supply screen down to the
observed harvest. Something on the quantity side — mill demand, processing capacity,
contractor availability, or operational access — has to be binding in those years.

This is the strongest result in the public-data envelope.

### 2019 is sensitive to the stumpage choice

The 2019 range is **0.0% to 47.9%** against HBS **49.1%**:

- at 12.76 $/m³, the screen gives 47.9%, almost exactly HBS;
- at 20.00 $/m³, it gives 21.1%;
- at 32.53 $/m³ and above, it gives essentially zero.

So 2019 can be made consistent with the harvest by choosing a low stumpage realization, but
the public data do not uniquely pin that down. The UWR step is still the clear timing event;
its quantitative share is not identified without billed stumpage.

### 2025 is also sensitive to stumpage

The 2025 range is **4.8% to 85.2%** against HBS **83.4%**:

- at 12.76 $/m³, the screen gives 85.2%, close to HBS;
- at 47.10 $/m³, it gives 27.0%;
- at 55.22 $/m³, it gives 12.3%.

The 2025 recovery is consistent with a low realized stumpage / strong market combination, but
the public data do not identify the exact split.

### 2023 and 2024 remain wide

2023 ranges 0–83.4% and 2024 ranges 0–79.9%. These years need a TSA-specific billed-stumpage
series and dated mill demand to narrow the range.

## Revised attribution

| Layer | What the public-data envelope supports |
|---|---|
| 2021–2022 | **Quantity/processing constraint is robust** across all public price/stumpage combinations |
| 2019 | Price + UWR timing can fit at low stumpage; cannot uniquely attribute |
| 2025 | Recovery fits low stumpage/strong market; cannot uniquely attribute |
| Caribou/UWR | 5–15% of AAC from TSR sensitivities; 2019 timing remains the clear event |
| Fire | <1% of annual operable volume |
| Access | 5–10% of the positive pool; spatial, not a sudden aggregate collapse |
| Mill volume | ≈0 at design capacity; one mill is 2.10× AAC |
| Residual | Quantity/processing for 2021–2022; unresolved for 2019/2025 |

## Why this is the right public-data model

A single billed-stumpage number does not exist in the public record at TSA scale. Rather than
invent one, the model reports the range. The range is wide for 2019 and 2025 and narrow for
2021–2022. The narrow years are the ones that identify the mechanism.

## Files

- `scripts/build_public_data_envelope.py`
- `runtime/annual_snapshots/public_data_envelope.csv`
- `runtime/annual_snapshots/public_data_envelope_summary.csv`
- `config/operational/bc_interior_amv_index.csv`
- `config/operational/bc_interior_stumpage.csv`
- `config/operational/bcts_south_interior_harvest_rate.csv`
- `config/operational/bcts_south_interior_volume.csv`

## Next

1. Search public BCTS Okanagan-Columbia auction/billed-rate summaries for a TSA-adjacent
   realization rate.
2. Add dated mill demand and curtailment events as explicit switches.
3. Keep the envelope as the reporting format; do not collapse it to one netdown.
