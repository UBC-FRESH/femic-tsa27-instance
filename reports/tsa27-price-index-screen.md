# TSA 27 BC interior price-index screen

**Status:** public BC interior lumber-price sensitivity, 29 October 2026.
**Not a mill-gate log-price series and not a causal attribution.**

## Purpose

The year-by-year screen held prices and costs static. This report adds the BC Timber Pricing
Branch **Interior lumber AMV** for zone 7 (Southern Interior), and asks whether price alone can
reproduce the HBS harvest path.

## BC interior AMV index

The source is the monthly BC Timber Pricing Branch “Stumpage Appraisal Parameters (Interior)”
memorandum. The zone 7 table gives lumber AMVs in dollars per thousand board feet. The index
is a spruce-pine-fir composite: the mean of balsam, fir/hemlock, lodgepole pine, white pine,
yellow pine, and spruce. Cedar and larch are excluded so the index tracks the TSA 27 softwood
mix rather than high-value cedar.

| Year | Months | SPF composite $/MBF | Factor vs 2026 |
|---:|---:|---:|---:|
| 2017 | 7 | 426.62 | 0.929 |
| 2018 | 11 | 514.30 | 1.119 |
| 2019 | 12 | 403.53 | 0.878 |
| 2020 | 12 | 451.92 | 0.984 |
| 2021 | 12 | 908.76 | 1.978 |
| 2022 | 12 | 862.04 | 1.876 |
| 2023 | 12 | 536.08 | 1.167 |
| 2024 | 12 | 500.14 | 1.089 |
| 2025 | 10 | 562.45 | 1.224 |
| 2026 | 10 | 459.43 | 1.000 |

The 2017 and 2025 rows use the months available at the linked historical pages; the 2026 row
is year-to-date. The monthly table is in `config/operational/bc_interior_amv_monthly.csv`.

## Results

Revenue is scaled by the annual AMV factor. Stumpage stays at the flat CAD 20/m³ in the main
price-only case.

| Year | HBS / AAC | AMV factor | Price-only positive | Price-only share |
|---:|---:|---:|---:|---:|
| 2017 | 74.0% | 0.929 | 5.23M m³ | 35.2% |
| 2018 | 92.8% | 1.119 | 11.36M m³ | 76.3% |
| 2019 | 49.1% | 0.878 | 2.89M m³ | 21.1% |
| 2020 | 46.9% | 0.984 | 7.16M m³ | 52.4% |
| 2021 | **30.2%** | **1.978** | **13.03M m³** | **95.4%** |
| 2022 | 55.0% | 1.876 | 12.86M m³ | 94.2% |
| 2023 | 42.5% | 1.167 | 10.82M m³ | 79.2% |
| 2024 | 58.2% | 1.089 | 9.95M m³ | 72.8% |
| 2025 | 83.4% | 1.224 | 11.14M m³ | 81.5% |
| 2026 | 47.6% YTD | 1.000 | 7.77M m³ | 56.9% |

## Stumpage table sensitivity

The Interior Appraisal Manual Table 6-1 gives South East zone average sawlog stumpage rates.
TSA 27 (Selkirk) is in the South East zone. The observed points are:

| Year | South East average stumpage | Status |
|---:|---:|---|
| 2017 | 32.53 $/m³ | 2018 proxy |
| 2018 | 32.53 $/m³ | observed |
| 2019 | 31.52 $/m³ | observed |
| 2020 | 55.22 $/m³ | observed |
| 2021 | 47.10 $/m³ | observed |
| 2022 | 47.10 $/m³ | observed |
| 2023 | 47.10 $/m³ | 2022 held |
| 2024 | 47.10 $/m³ | 2022 held |
| 2025 | 47.10 $/m³ | 2022 held |
| 2026 | 12.76 $/m³ | observed |

Substituting these rates for the flat CAD 20/m³ produces an erratic path:

| Year | HBS / AAC | Stumpage | Positive share |
|---:|---:|---:|---:|
| 2018 | 92.8% | 32.53 | 48.3% |
| 2019 | 49.1% | 31.52 | 1.2% |
| 2020 | 46.9% | 55.22 | 0.0% |
| 2021 | 30.2% | 47.10 | 89.1% |
| 2022 | 55.0% | 47.10 | 88.4% |
| 2023 | 42.5% | 47.10 | 18.7% |
| 2024 | 58.2% | 47.10 | 5.4% |
| 2025 | 83.4% | 47.10 | 27.0% |
| 2026 | 47.6% | 12.76 | 73.0% |

This is not a usable central case. The tabular average sawlog rate is **not the same as
stumpage actually billed** on TSA 27 cutting authorities. It varies by tenure, appraisal, and
species mix, and the 2023–2025 rows are held at the 2022 value. The table sensitivity shows
that the screen is highly sensitive to stumpage, not that the tabular series is the right
input.

The model keeps the flat CAD 20/m³ as the central assumption until a TSA 27 billed-stumpage
series is available.

## Findings

### BC AMV tracks 2018, 2019, and 2025 better than the U.S. PPI

- 2019 AMV falls to 0.878 and the positive pool falls to 21.1%; HBS falls to 49.1%.
- 2025 AMV rises to 1.224 and the positive pool rises to 81.5%; HBS is 83.4%.
- 2018 AMV is 1.119 and the positive pool is 76.3%; HBS is 92.8%.

This is a much better directional fit than the U.S. PPI, especially for 2025.

### Price still cannot explain 2021–2023

The 2021 AMV is the highest in the series at **1.978×** the 2026 level. The price-only screen
puts **95.4%** of the UWR pool in positive margin. Actual HBS is the lowest year at **30.2%**.
2022 and 2023 show the same mismatch.

That is the signature of a **quantity/processing constraint**, not a price constraint. A
high-price year with low harvest requires mill demand, processing capacity, contractor
availability, or operational access to be binding.

### 2019 is the one year where price and policy align

In 2019:

- AMV falls from 1.119 to 0.878;
- UWR u-3-005 expands by 10,601 ha;
- HBS falls from 92.8% to 49.1%.

The combination is consistent with a price/margin shock amplified by the legal land-base step.
It still does not explain the full 47% one-year drop.

### The stumpage table is a warning, not a fit

The South East average sawlog table swings from 31.52 to 55.22 $/m³ and back to 12.76 $/m³.
It does not produce a stable or credible annual screen. That is a data problem: the model
needs stumpage actually billed on TSA 27 cutting authorities, not the zone-average table.

## Cross-check: U.S. PPI

The earlier U.S. softwood-lumber PPI (`WPU0811`) gave a similar 2021 mismatch but a much worse
2025 fit: 0.942 price factor and 39.6% positive share against 83.4% actual. The BC AMV is the
preferred index because it is the actual BC interior appraisal input. The U.S. series remains
in `config/operational/softwood_lumber_price_index.csv` as a cross-check.

## Interpretation

The BC AMV screen is a falsification test, not a fit. It shows that:

- BC interior lumber price explains part of the 2019 low and most of the 2025 recovery;
- it does not explain the 2021–2023 lows;
- those years require a quantity/processing explanation;
- the attribution should keep market, mill demand/capacity, and access as separate layers.

## Caveats

- AMV is lumber value, not a sawlog or mill-gate log price.
- The SPF composite is an unweighted species mean, not the TSA 27 species mix.
- 2017 uses 7 months, 2025 uses 10 months, and 2026 is year-to-date.
- The base CAD 95/m³ sawlog and CAD 45/m³ pulp prices are placeholders.
- Stumpage is a flat CAD 20/m³; the indexed case is a sensitivity, not an average sawlog
  stumpage table.
- Mill capacity, product acceptance, and curtailments are not applied.
- The screen is a filter, not a schedule.

## Files

- `scripts/fetch_bc_interior_amv.py`
- `config/operational/bc_interior_amv_monthly.csv`
- `config/operational/bc_interior_amv_index.csv`
- `config/operational/softwood_lumber_price_index.csv`
- `config/operational/bc_interior_stumpage.csv`
- `scripts/build_year_by_year_screen.py`
- `runtime/annual_snapshots/year_by_year_screen.csv`
- `reports/tsa27-year-by-year-screen.md`

## Next

1. Parse the Interior Non-Appraised Tabular Stumpage Rates for zone 7 and build an average
   sawlog-stumpage series.
2. Add dated mill demand and curtailment events.
3. Run the nested counterfactuals with the BC AMV as the market switch.
