# TSA 27 caribou layer accounting — findings

**Status:** investigation report. **Date:** 2026-10-30. **Scope:** the caribou
accounting in the FEMIC TSA 27 instance and its WS4 datasets. **Repository state:** the
changes described here are committed on branch `feature/tsa27-caribou-accounting`.
`main` remains at `3b4b08e`.

## 1. What was asked

The starting question was: what is missing in the caribou layer accounting? The audit
(`scripts/audit_caribou_layers.py`) was built to answer it from the artifacts, not from
narrative. It evaluates 15 checks and reports `PASS`, `GAP`, or `FAIL`.

Result at the end of this work: **7 pass, 8 gap, 0 fail**.

## 2. Findings

### 2.1 The compiled dataset was zone-blind

`build/compiled/fragments.parquet` carried only
`fragment_id, block_id, area_ha, age, track_id`. It had no caribou zone, no LU/BEC, and
no caribou accounts. The `groups` table had one value, `forest`, for every block.

The UWR flag lived only in `data/ws4/fragments.gpkg` and was applied by filtering a
schedule CSV (`scripts/apply_caribou_constraints.py`). The model itself did not know
which stands were UWR. Core, matrix, the historical HLP zone, and the 80-year deferral
were mapped in config but not enforced.

### 2.2 The UWR block-to-fragment join was ambiguous

The export has no stable fragment id: `FRAGMENT_I` is a sequential index and `BLOCK` is
regenerated. The only shared key with the P3.1 fragments was the rounded
`(AU, area_ha, age)` tuple.

- 132 blocks matched more than one fragment.
- 32 of those had conflicting UWR flags (195.2 ha).

Resolution: `scripts/build_block_fragment_map.py` matches each ambiguous block by polygon
overlap. Every one has exactly one candidate at IoU 1.0, because the export and the P3.1
polygon come from the same stand. `metadata/ws4/block_fragment_overrides.csv` records 132
resolutions. The flagged block count is now **8,029**, matching the 8,029 flagged
fragments.

Corrected schedule and result:

| Item | Before | After |
|---|---:|---:|
| UWR-flagged blocks | 8,045 | 8,029 |
| Excluded schedule rows | 1,940 | 1,937 |
| Retained rows | 6,167 | 6,170 |
| S3 harvest at offset 0 | 13,660,939 m³ | 13,674,669 m³ |
| S3 treated area | 57,941 ha | 57,962 ha |
| Harvest delta | −43.6% | −43.5% |

The remaining UWR area issue is separate: the binary flag covers **108,458 ha**, while the
area-weighted intersection is **106,882 ha**. The flag overstates by 1,576 ha (1.47%)
because fragments at the UWR edge are flagged only when at least half their area is inside.
The flag is a screen, not an area account.

### 2.3 The seral basis was not the TSR basis

`og1` is an AU-specific ramp from CMAI age to peak-yield age. Only 10 of 18 `og1` labels
cross age 140. `og2` is age 250. Neither is the TSR rule: 40% of the forest at least 140
years old, and at least a quarter of that at least 250, by LU/BEC.

Fix: `config/seral.tsa27.yaml` defines the TSR age classes (regenerating 0–5, young 6–25,
immature 26–139, mature 140–249, overmature 250+). The tracked dataset was rebuilt with
`femic export patchworks --seral-stage-config` and now carries 95 `feature.Seral.*` labels.
At offset −1:

- mature (140–249): 135,906.7 ha
- overmature (≥250): 104,154.1 ha

The overmature value matches `og2` exactly, which independently confirms the 250 boundary.

### 2.4 Data availability

| Input | Status | Evidence |
|---|---|---|
| BEC v12 | **fetched** | 543 polygons, SHA-256 `100f14e1…`; 19,390 of 19,701 fragments with both variants match the VRI attributes (98.42%); 17,452 fragments have no VRI variant and BEC supplies one for only 279 |
| Caribou core/matrix | **request-only** | BC Data Catalogue matches are boreal caribou layers for the Peace region, not southern mountain caribou for TSA 27; no substitute used |
| Historical HLP zone | **absent** | No public spatial layer found; S5 remains unavailable |
| 2018 designatedlands UWR | **reviewed, not used** | 2018-05-03 vintage; TSA 27 u-3-005 area 116,210 ha vs 116,759 ha for the 2020 layer; IoU 0.984; current layer reconciles with TSR5 Table 14 (116,820 ha) within 61 ha |

The 2018 upload was superseded for the base case. It is not in the manifest and no model
output changed. The review is recorded in `notes/reference/tsa27-input-availability.md`.

### 2.5 The partition and target table

`scripts/partition_caribou_zones.py` is a post-compile track split. Every used
`(track, zone, LU/BEC)` combination becomes a clone with zone- and LU/BEC-qualified
labels.

`build/compiled_zone`:

- 10,600 cloned tracks
- 2 zones (`uwr`, `other`)
- 135 LU/BEC values
- 11,036 qualified feature labels
- 724 qualified product labels

`build/compiled_zone_uwr` is the no-harvest variant:

- 3,251 `uwr` tracks
- **zero treatment rows** on those tracks
- UWR area remains 108,458.4 ha
- a full 8,107-row schedule harvests **13,674,669.395 m³** and treats
  **57,962.211 ha** — exactly the filtered S3 result

That is the important change: UWR is now enforced by the model, not by an external CSV.

`config/ws4/targets/s3_seral_40_10.yaml` is generated from that dataset:

- 5,400 targets, 270 accounts, 135 LU/BEC values
- mature+old (≥140) ≥ 40% of each LU/BEC area
- old (≥250) ≥ 10% of each LU/BEC area
- 20 periods × 10 years
- dataset manifest SHA-256 in the header

Aggregates: LU/BEC area 402,790.9 ha; mature+old 240,060.8 ha; old 104,154.1 ha.
The 40% and 10% floors are 161,116.4 ha and 40,279.1 ha.

The caribou line is not in the instance, so the below-the-line rule is applied
everywhere. The target header, `config/ws4/targets/README.md`, and
`metadata/ws4/seral_targets_summary.csv` say so.

## 3. Invariants

The partition changes labels and tracks, not area or yield. From a one-year simulation
comparison (`metadata/ws4/zone_partition_invariants.csv`):

| Invariant | Base | Zone | Delta |
|---|---:|---:|---:|
| Managed area | 79,101.755 ha | 79,101.755 ha | 0.000 |
| Seral mature | 135,906.701 ha | 135,906.701 ha | 0.000 |
| Seral overmature | 104,154.095 ha | 104,154.095 ha | 0.000 |
| Zone area | 402,790.893 ha | 402,790.893 ha | 0.000 |
| Harvest | 13,674,669.395 m³ | 13,674,669.395 m³ | 0.000 |
| Treated | 57,962.211 ha | 57,962.211 ha | 0.000 |

## 4. What the numbers mean, and what they do not

- The −43.5% is **first-period capacity**, not an AAC impact. It is what happens when every
  eligible block is cut at year 0.
- The 40%/10% targets are **soft** in the optimizer (large weight, not a hard constraint).
- Matrix 13% is still not enforceable without the core/matrix layer.
- The caribou line is absent, so the 70% above-the-line rule cannot be applied.
- The 80-year deferral is a calendar-time rule; WS4 treatments carry age windows, so it is
  not expressible without an engine change.
- `build/compiled_uwr` (the old S7 variant) remains on the pre-seral XML. The missing
  `build_compiled_uwr.py` is still a reproducibility gap.
- The invariants CSV is a recorded one-year simulation check. It is not yet regenerated by
  a `--verify` mode, so the audit is reading recorded evidence rather than a live rerun.

## 5. What changed

New scripts:

- `scripts/audit_caribou_layers.py`
- `scripts/build_block_fragment_map.py`
- `scripts/partition_caribou_zones.py`
- `scripts/build_seral_targets.py`

New config and metadata:

- `config/seral.tsa27.yaml`
- `config/ws4/targets/s3_seral_40_10.yaml`
- `config/ws4/targets/README.md`
- `metadata/ws4/block_fragment_overrides.csv`
- `metadata/ws4/block_fragment_join_summary.csv`
- `metadata/ws4/zone_partition_summary.csv`
- `metadata/ws4/zone_partition_uwr_summary.csv`
- `metadata/ws4/zone_partition_invariants.csv`
- `metadata/ws4/seral_targets_summary.csv`

New tests:

- `tests/test_audit_caribou_layers.py`
- `tests/test_build_block_fragment_map.py`
- `tests/test_partition_caribou_zones.py`
- `tests/test_build_seral_targets.py`
- `tests/test_seral_config.py`

Updated:

- `scripts/apply_caribou_constraints.py` (geometry overrides)
- tracked UWR schedule and filter summary
- scenario comparison and current-facing reports/docs
- `metadata/data_manifest.yaml` and lock (BEC v12 available)
- `metadata/ws4/dataset_manifest.yaml`
- `CHANGE_LOG.md`

Ignored artifacts: `build/compiled`, `build/compiled_zone`, `build/compiled_zone_uwr`,
`output/patchworks`, `runtime/caribou_audit`, and the BEC download.

## 6. Repository state

- Base commit: `3b4b08ef77f89d4a2da17305b43a44c2fdd62394`
- Branch: `feature/tsa27-caribou-accounting`.
- `main` is unchanged at `3b4b08e`; this work is not merged.
- `DEMO.md` was untracked before this work and is not part of this change.

## 7. Reproduce

```bash
python scripts/audit_caribou_layers.py
python scripts/build_block_fragment_map.py --check
python scripts/apply_caribou_constraints.py
python scripts/partition_caribou_zones.py
python scripts/partition_caribou_zones.py \
  --out build/compiled_zone_uwr \
  --summary metadata/ws4/zone_partition_uwr_summary.csv \
  --no-harvest-zones uwr
python scripts/build_seral_targets.py --check
python scripts/dashboard.py
```

`python scripts/dashboard.py` is GREEN (411 tests, 97.32% coverage).

## 8. Sources

- `reports/tsa27-tsr-corpus-analysis.md` — TSR evidence and caribou policy layers.
- `notes/plans/tsa27-caribou-accounting-design.md` — the design and open decisions.
- `notes/reference/tsa27-input-availability.md` — BEC, core/matrix, HLP, 2018 UWR.
- `scripts/audit_caribou_layers.py` — the check definitions.
- `metadata/ws4/*` — the tracked join, partition, invariant, and target summaries.
