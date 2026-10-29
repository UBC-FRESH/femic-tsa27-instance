# TSA 27 public-data gap register

**Status:** public-data treatment register, 29 October 2026. **Principle:** use the best public data; where a series does not exist, carry a public range or a documented switch, not a proprietary gate.

## What was searched

- BC Data Catalogue: no TSA-level stumpage-billed dataset.
- BCTS quarterly and annual performance reports: business-area volume and provincial gross revenue, but no area-specific billed-rate series.
- Interior Appraisal Manual and monthly non-appraised tables: zone-average sawlog rates, not TSA-27 billed rates.
- Local news, company listings, BC Major Timber Processing Facilities 2019/2022/2023: one dated Downie event, no 2024–2026 local curtailment series.
- BCWS fire perimeters: perimeters available; severity and salvage not.

## Treatment

| Gap | Public finding | Model treatment |
|---|---|---|
| TSA-27 billed stumpage | No TSA-specific public series | 12.76–55.22 $/m³ envelope; flat 20 $/m³ central |
| Dated mill curtailments | One 2019 Downie event; no 2024–2026 notice | One-mill and two-mill pilot switches |
| Mill product acceptance | No public grade table | Design-capacity bounds; sawlog/pulp simplification |
| Historical UWR | Current boundary plus approval dates | Pre/post-2019 add-back |
| Fire severity/salvage | Perimeters only | No-salvage upper bound |
| Historical block state | Cutblock start years only | Current blocks plus annual cutblock overlay |
| Contractor/machine costs | No TSA-27 public rate series | Placeholder rates; FHOPS capacity envelope |
| Log prices | BC AMV 2017–2026 | AMV factors; U.S. PPI cross-check |

## Why this is still a model, not a guess

The public-data envelope shows where the answer is robust and where it is not:

- **2021 and 2022:** positive share is 88–96% and 87–96% across every public price/stumpage anchor, against HBS 30.2% and 55.0%. The quantity/processing conclusion survives the full public range.
- **2019 and 2025:** the range spans the observed harvest, so those years are not uniquely identified without billed stumpage.
- **Fire:** under 1% of annual operable volume.
- **Mill volume:** one mill is still 2.10× AAC.

That is the honest public-data result: a firm mechanism where the range is narrow, and a range where the data are weak.

## Files

- `config/operational/public_data_gaps.csv`
- `reports/tsa27-public-data-envelope.md`
- `reports/tsa27-counterfactual-synthesis.md`
- `reports/tsa27-analysis-register.md`

## Next

1. Search BCTS Okanagan-Columbia auction summaries for a public realization rate.
2. Add dated mill-demand switches from public quarterly reports.
3. Keep the envelope as the reporting format.
