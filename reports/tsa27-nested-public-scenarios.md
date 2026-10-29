# TSA 27 nested public-data scenarios

**Status:** nested public-data grid, 29 October 2026.
**Not a single-point attribution.**

## Dimensions

The grid varies, for every year 2017–2026:

- UWR pool: pre-2019 for 2017–2018, post-2019 for 2019–2026;
- BC interior AMV price factor;
- six public stumpage anchors: 12.76, 20.00, 32.53, 47.10, 55.22, 60.53 $/m³;
- cost factor 1.0 or 1.2;
- fire no-salvage on or off.

That is 240 combinations.

## Annual envelope

| Year | AMV factor | Min positive share | Median | Max | HBS / AAC |
|---:|---:|---:|---:|---:|---:|
| 2017 | 0.929 | 0.0% | 0.0% | 62.2% | 74.0% |
| 2018 | 1.119 | 0.0% | 6.9% | 81.3% | 92.8% |
| 2019 | 0.878 | 0.0% | 0.0% | 47.9% | 49.1% |
| 2020 | 0.984 | 0.0% | 0.0% | 70.7% | 46.9% |
| 2021 | **1.978** | **77.8%** | 88.7% | 96.2% | **30.2%** |
| 2022 | **1.876** | **67.1%** | 87.6% | 95.6% | **55.0%** |
| 2023 | 1.167 | 0.0% | 14.7% | 83.4% | 42.5% |
| 2024 | 1.089 | 0.0% | 4.1% | 79.9% | 58.2% |
| 2025 | 1.224 | 0.0% | 24.2% | 85.2% | 83.4% |
| 2026 | 1.000 | 0.0% | 0.0% | 73.0% | 47.6% |

## What survives the nested grid

### 2021–2022 remain quantity/processing years

Even at the worst corner — highest public stumpage, cost +20%, fire no-salvage — the 2021
positive-margin share is **77.8%** and 2022 is **67.1%**. HBS is **30.2%** and **55.0%**.

The positive pool is large enough to fill the 1.125M m³ five-year envelope in every 2021–2022
combination. Actual harvest is far below that. The constraint is on the quantity side:
mill demand, processing capacity, contractor availability, or operational access.

This is the strongest result in the model.

### 2019 and 2025 are not identified

- 2019: positive share **0.0–47.9%** against HBS **49.1%**.
- 2025: positive share **0.0–85.2%** against HBS **83.4%**.

Both can fit at the low-stumpage corner and fail at the high-stumpage corner. The public data
do not pin down the realized stumpage/market combination. The model reports the range.

### 2023–2024 stay wide

2023 is **0–83.4%** and 2024 is **0–79.9%**. These years need TSA-specific billed stumpage and
dated mill demand to narrow.

## Interpretation

The nested grid strengthens the earlier conclusion:

- caribou/UWR is a bounded legal effect, with 2019 as the clear timing event;
- fire is small at TSA scale;
- access and road cost condition margins;
- mill **volume** capacity is not binding;
- 2021–2022 are quantity/processing years across the full public range;
- 2019 and 2025 remain range-dependent.

## Files

- `scripts/build_nested_public_scenarios.py`
- `runtime/annual_snapshots/nested_public_scenarios.csv`
- `runtime/annual_snapshots/nested_public_scenarios_summary.csv`
- `reports/tsa27-public-data-envelope.md`
- `reports/tsa27-counterfactual-synthesis.md`

## Next

1. Add a dated mill-demand switch from BCTS Okanagan-Columbia volume sold.
2. Narrow 2019/2025 with TSA-specific billed stumpage.
3. Keep the nested range as the reporting format.
