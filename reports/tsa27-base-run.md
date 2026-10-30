# TSA 27 WS4 base run

**Status:** P3.4 capacity test. Not an AAC forecast.

## Dataset

- XML: `output/patchworks/forestmodel.xml`
- Fragments: `output/patchworks/fragments/fragments.shp`
- Compiled dataset: `build/compiled`
- Fragments: 40,660; tracks 4,746; curves 12,545; features 101,970; products 48,579; treatments 3,000; accounts 279.
- Fragment area: 402,791 ha.
- Managed/THLB area: 79,102 ha.

## Run

- Schedule: `scenarios/s3_base.schedule.csv` — 8,107 eligible blocks, all at offset 0.
- Years: 250.
- Output: `runs/s3_base/`.
- Harvest in period 0: **24,218,812 m³**; treated area 79,102 ha.

This is a **capacity test**, not a harvest-flow forecast. Scheduling every eligible block at year 0 is deliberate: it proves the dataset, treatments, curves, and simulator all work. P4 will build realistic harvest-flow scenarios and the caribou policy matrix.

## Reconciliation

| Item | Value |
|---|---:|
| Fragment area | 402,791 ha |
| Managed/THLB area | 79,102 ha |
| Caribou UWR flag area (P3.1) | 108,458 ha |
| UWR exclusion in this run | none (P3.3 not yet applied) |
| Harvest | 24,218,812 m³ at offset 0 |

The THLB remains the P2 value (79,102 ha); the P1/P2 gap to the TSR THLB is unchanged and is a P4 reconciliation item.

## Limits

- The caribou constraints are not yet applied. P3.3 will add the UWR exclusion and the matrix/seral mapping.
- The schedule is a capacity test, not a base case.
- The XML/fragments are generated and ignored; the manifest records their hashes.

## UWR no-harvest run

The P3.3 schedule filter removed 1,937 of 8,107 scheduled block rows that carry the UWR u-3-005 flag. The 132 ambiguous `(AU, area, age)` pairs are resolved by geometry (`metadata/ws4/block_fragment_overrides.csv`), so the flagged block count matches the 8,029 flagged fragments.

- Schedule: `scenarios/s3_base_caribou_uwr_excluded.schedule.csv`
- Output: `runs/s3_caribou_uwr/`
- Harvest in period 0: **13,674,669 m³** (down 10,544,142 m³, −43.5% from the unconstrained capacity test).
- Treated area: **57,962 ha** (down 21,140 ha, −26.7%).

This is the first real caribou constraint in the model: the legal UWR no-harvest areas are excluded from harvest. The matrix 13% and historical 80-year deferral remain mapped but not enforced; they are P4 scenario work.
