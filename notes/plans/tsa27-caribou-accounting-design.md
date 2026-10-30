# TSA 27 caribou layer accounting — design note

**Status:** proposed. **Date:** 2026-10-30. **Owner:** UBC-FRESH.
**Companions:** `reports/tsa27-tsr-corpus-analysis.md` (evidence and policy design),
`notes/plans/tsa27-model-build-plan.md` (phase plan), `scripts/audit_caribou_layers.py`
(the current-state oracle).

## 1. Why this note

The 2026-10-30 audit (`runtime/caribou_audit/summary.csv`) found that the compiled WS4
dataset carries no caribou attributes and no caribou accounts. Only the UWR flag exists, in
the P3.1 GeoPackage, and it is applied by filtering a schedule CSV. The core, matrix, and
historical layers are mapped in `config/ws4/caribou_constraints.yaml` but not enforced.

This note decides **where the zone and LU/BEC partitions live** and **which accounts and
targets express the four policy layers**. It does not change any data. It is the design
input for the follow-on tasks in section 7.

## 2. What the model can express today (evidence)

The compiled dataset is a state machine over tracks:

- A **fragment** row is `fragment_id, block_id, area_ha, age, track_id`
  (`ws4/docs/reference/compiled-dataset.rst`; verified in `build/compiled/fragments.parquet`).
- A **track** is the tuple of the recipe's define fields. `state_variables` returns the
  non-constant define fields (`ws4/build/expansion.py:39`), and the current XML defines
  `AU, IFM, ORIGIN, SILV_STATE, RETENTION, treatment`
  (`output/patchworks/forestmodel.xml`, `<define>` block).
- A **feature** is a per-track curve (`ws4/build/compiler.py:509`). Its account value is
  `sum(area × curve(age))` over the fragments on that track (`ws4/sim/engine.py:490`).
- An **account** is a label. The `accounts.parquet` table is a curated list; the simulator
  reports every feature and product label it computes.
- A **target** names an account, a period, and an absolute minimum or maximum
  (`ws4/docs/howto/write-targets.rst`). There is **no ratio target**. The optimizer is
  weighted goal programming, so a bound is a penalty, not a hard constraint
  (`ws4/docs/reference/optimizer.rst`).
- `groups.parquet` is hard-coded to `forest` by the ForestModelXML compiler
  (`ws4/build/compiler.py`, `build_canonical_dataset`). It is not a zone partition.

FEMIC already has two relevant hooks:

- `--seral-stage-config` emits `feature.Seral.<stage>` and
  `feature.Seral.<au_token>.<stage>` from configurable per-AU age bounds
  (`femic/src/femic/fmg/patchworks.py:3657`; `femic/docs/reference/patchworks-export.rst`).
  The default boundaries are CMAI/peak-yield based, not TSR based.
- `og1` is an AU ramp from CMAI age to peak-yield age, and `og2` is age 250
  (`femic/src/femic/fmg/patchworks.py:1299`, `:1321`). That is why only 10 of 18 `og1`
  labels cross age 140.

The current export does **not** use `--seral-stage-config`, and its define fields cannot
carry a zone or LU. Additional stratification columns reach the fragments shapefile but not
the track key, because `define_fields` is fixed in the recipe writer
(`femic/src/femic/fmg/patchworks.py:4912`).

## 3. Target data contract

### 3.1 Fragment attributes (P3.1)

Add or fill these on `data/ws4/fragments.gpkg`, and carry them through the Patchworks export
with an exact key (section 4.4):

| Attribute | Type | Source | Rule |
|---|---|---|---|
| `caribou_uwr` | 0/1 | UWR u-3-005, current amendment | 1 when the fragment is inside the no-harvest zone |
| `caribou_core` | 0/1 | provincial core habitat | 1 inside core |
| `caribou_matrix` | 0/1 | provincial matrix habitat | 1 inside matrix |
| `caribou_zone` | 0/1 | historical HLP zone | 1 inside the TSR2/TSR3 caribou zone |
| `caribou_immature` | 0/1 | historical immature habitat | 1 when immature at the start year |
| `lu_bec` | str | landscape unit + BEC v12 | `<lu>|<bec_zone><subzone><variant>` |
| `ogma` | 0/1 | legal and non-legal OGMA/MOGMA | 1 inside either |
| `thlb` | 0/1 | FEMIC compile | unchanged |

Add one **mutually exclusive** domain so no area is double counted:

```text
caribou_domain = uwr      if caribou_uwr = 1
               = core     elif caribou_core = 1
               = matrix   elif caribou_matrix = 1
               = hlp      elif caribou_zone = 1
               = other    otherwise
```

The order is a policy choice: UWR is legal and wins over everything; core is the recovery
no-harvest; matrix is a cover constraint; HLP is the historical counterfactual. Record the
order in the dataset manifest.

### 3.2 Track state variables

Add two define fields to the recipe and to the fragment shapefile:

```xml
<define field="ZONE" column="ZONE" />
<define field="LUBEC" column="LUBEC" />
```

`ZONE` takes `caribou_domain`; `LUBEC` takes `lu_bec`. Every select that creates a track
must include the partition predicate. Treatments must **not** assign `ZONE` or `LUBEC`, so
the partition persists through harvest and regeneration. This is what makes the domain and
LU totals constant over the horizon (section 3.4).

### 3.3 Feature labels

Per track, emit:

| Label | Curve | Purpose |
|---|---|---|
| `feature.Area.<domain>` | unity | domain area, one label per domain |
| `feature.Area.matrix.lt40` | 1 for age < 40, 0 at age ≥ 40 | matrix cover numerator |
| `feature.Area.matrix.total` | unity | matrix cover denominator |
| `feature.Seral.mature.<lubec>` | 1 for 140 ≤ age ≤ 249 | mature seral |
| `feature.Seral.old.<lubec>` | 1 for age ≥ 250 | old seral |
| `feature.Seral.regenerating.<lubec>` | 1 for age ≤ 5 | optional age-class audit |

The seral thresholds come from `--seral-stage-config`, set per AU or globally:

```yaml
default:
  mature:
    min_age: 140
    max_age: 249
  overmature:
    min_age: 250
    max_age: null
```

This replaces `og1`/`og2` for TSR targets. Keep the `og1`/`og2` labels for backward
compatibility and reporting, but do not build a target on them.

For harvest by domain, suffix the product labels in the same way:
`product.HarvestedVolume.<domain>.Total.CC` and `product.HarvestedVolume.<domain>.<species>.CC`.

### 3.4 Accounts and targets

Because `ZONE` and `LUBEC` persist, these totals are constant over the horizon:

```text
feature.Area.matrix.total          = constant M
feature.Seral.mature.<lubec> + feature.Seral.old.<lubec> + ... = constant T_lubec
feature.Area.<domain>              = constant for each domain
```

A constant denominator turns each ratio constraint into an absolute bound, which is the
only form WS4 targets accept:

| Policy | Target on | Bound | TSR source |
|---|---|---|---|
| Matrix cover | `feature.Area.matrix.lt40` | ≤ `0.13 × M` | 2022 recovery sensitivity, max 13% <40 years |
| Mature+old below the line | `feature.Seral.mature.<lubec> + feature.Seral.old.<lubec>` | ≥ `0.40 × T_lubec` | TSR3/TSR4, age class 8+ (≥140) |
| Old below the line | `feature.Seral.old.<lubec>` | ≥ `0.10 × T_lubec` | 25% of the ≥140 area (age class 9+) |
| Above the line | same accounts | ≥ `0.70 × T_lubec` | TSR3/TSR4 |
| UWR / core no-harvest | no treatment rows on those tracks | zero eligible treatments | legal UWR; recovery core |
| Deferral | schedule rows absent for offsets 0–79 on `hlp` immature tracks | simulation only | TSR2/TSR3 counterfactual |

Two consequences to state explicitly:

- The matrix and seral bounds are **soft** in the optimizer (large weight, not a hard
  constraint). Report the realized ratio from the run and treat the target status as
  advisory, not a guarantee.
- The 80-year deferral is a **calendar-time** rule. WS4 treatments carry age windows, not
  calendar windows, so the deferral is enforceable only in simulation by withholding
  schedule rows. An optimizer would need an engine extension. Do not claim it as enforced
  until that exists.

### 3.5 Target table values

The target files are generated, not hand-edited:

```bash
python scripts/build_caribou_targets.py \
  --dataset build/compiled_zone \
  --scenario config/ws4/scenarios/s4_tsr5_recovery.yaml \
  --out config/ws4/targets/s4_recovery.yaml
```

The builder reads the pre-simulation account values (`ws4 simulate --years 1`), computes
`M` and each `T_lubec`, and writes the absolute bounds. It must record the values and the
dataset manifest hash in the target file header so the target is traceable.

## 4. Implementation options

### 4.1 Option A — FEMIC-native partition (target)

Extend `femic export patchworks` with a partition config that:

1. adds `ZONE` and `LUBEC` to `define_fields` and to the fragments shapefile;
2. duplicates each select per occupied partition value and appends the predicate;
3. appends the partition token to the area and seral feature labels;
4. stamps `FEATURE_ID` on the export so the join back to P3.1 is exact.

Pros: one source of truth, zone-aware tracks, no shadow compiler, exact join.
Cons: a FEMIC change and release; larger XML and track count; the instance must pin the
FEMIC version that has it.

### 4.2 Option B — instance-side XML transform (interim)

`scripts/build_ws4_zone_xml.py` reads `output/patchworks/forestmodel.xml`, adds the two
define fields, rewrites each `<select>` per partition value with zone-qualified labels, and
writes `output/patchworks/forestmodel.zone.xml`. A second script adds `ZONE`/`LUBEC` to the
fragments shapefile from the P3.1 attributes.

Pros: standalone, no FEMIC release, testable against the current XML.
Cons: a transform over a moving XML schema; it must be re-validated whenever FEMIC changes
the export; it is a second recipe writer in all but name.

### 4.3 Option C — post-compile track clone (fallback)

`scripts/add_caribou_accounts.py` reads `build/compiled` and the P3.1 attributes, clones each
used `(track, domain, lu_bec)` combination, rewrites `fragments.track_id`, and adds the
zone-qualified feature labels, curves, and accounts.

Pros: no FEMIC or WS4 change; smallest rebuild; can be tested against the current dataset.
Cons: a shadow compiler; the treatment/strata/product copying is easy to get wrong; the
P3.1-to-export join is still the fragile `(AU, area, age)` key unless Option A stamps an id.
Use only if a FEMIC release is not possible before the next scenario run.

**Recommendation:** Option A as the target; Option B if a scenario run is needed before the
FEMIC release; Option C only as a tested bridge, with the audit extended to prove the
partition is exact.

### 4.4 The join must be exact

The current UWR filter maps export blocks to P3.1 fragments on rounded `(AU, area, age)`.
The audit found 66 duplicate fragment keys, 132 ambiguous blocks, and 32 blocks with
conflicting flags (195.2 ha). Any partition built on this join inherits that ambiguity.
Option A must stamp `FEATURE_ID` on the export. Option B/C must fail loudly on more than one
match, not take the maximum.

**Interim resolution (2026-10-30).** `scripts/build_block_fragment_map.py` now resolves every
ambiguous block by polygon overlap and writes `metadata/ws4/block_fragment_overrides.csv`.
The export polygon and the P3.1 polygon come from the same stand, so all 132 ambiguous blocks
have exactly one candidate at IoU 1.0. `scripts/apply_caribou_constraints.py` applies the
overrides, and the flagged block count (8,029) now matches the flagged fragment count. This
makes the current join exact without a FEMIC change. It does not remove the long-term need to
stamp `FEATURE_ID` on the export, because a geometry join is heavier and depends on both
geometries being present.

## 5. Track count and performance

The current dataset has 4,746 track rows, of which 3,487 are used by at least one fragment.
A UWR × LU/BEC split alone takes the used tracks to **7,936** (measured by joining the
compiled fragments to the P3.1 attributes). Add core and matrix and plan for roughly
**10,000–12,000** tracks. Mitigations:

- Use one `caribou_domain` variable (5 values), not three independent 0/1 flags.
- Partition only LUs that actually carry a seral target; leave `other` unpartitioned.
- Drop empty combinations before writing the XML.
- Keep the 135 observed `lu_bec` values as the vocabulary; do not expand to the full
  BEC × LU cross-product.

The XML and compile time will grow. The optimizer's neighbourhood also grows with the
number of blocks, not tracks, so the main cost is compile and memory, not the search.

## 6. Validation plan

Extend `scripts/audit_caribou_layers.py` with these checks. Each must be able to fail.

| Check | Oracle | Pass condition |
|---|---|---|
| `zone_partition_covers` | `feature.Area.<domain>` at offset -1 | sum equals fragment area; every fragment in exactly one domain |
| `zone_no_harvest_treatments` | `treatments` rows on `uwr` and `core` tracks | zero rows |
| `matrix_total_constant` | `feature.Area.matrix.total` over the horizon | max − min ≤ 1 ha |
| `matrix_cover` | `feature.Area.matrix.lt40 / total` each period | ≤ 0.13 + tolerance, reported not assumed |
| `seral_floor` | `(mature + old) / T_lubec` each period | ≥ 0.40 (or 0.70 above the line) |
| `old_floor` | `old / T_lubec` each period | ≥ 0.10 |
| `harvest_by_domain` | sum of domain harvest accounts | equals total harvest |
| `uwr_area` | domain area vs TSR5 gross/net | gross reconciles to 116,820 ha; net is reported as not comparable until the netdown sequence exists |
| `target_traceability` | target file header | dataset manifest hash and `M`/`T` values recorded |

The first five are the real oracles for the policy layers. The current audit already checks
the schedule filter, the variant manifest, and the area reconciliation.

## 7. Bounded work plan

| Task | Work | Evidence |
|---|---|---|
| C1 | Fetch core/matrix habitat and BEC v12; decide the HLP availability | BEC fetched 2026-10-30 (543 features, sha256 `100f14e1…`); core/matrix confirmed request-only; HLP not found. See `notes/reference/tsa27-input-availability.md`. |
| C2 | Add `caribou_domain`, `lu_bec`, and the exact `FEATURE_ID` carry-through | fragment summary; join audit shows zero ambiguous blocks |
| C3 | Add the seral-stage config with 140/250 boundaries | `config/seral.tsa27.yaml`; the tracked dataset was rebuilt with 95 `feature.Seral.*` labels (mature 140–249, overmature 250+); `seral_thresholds` passes. LU/BEC partitioning remains C4. |
| C4 | Implement the chosen partition (A, B, or C) | Partial: `build/compiled_zone` with 10,600 cloned tracks (UWR × LU/BEC, 135 values); 6/6 invariants pass. Core/matrix tracks pending. |
| C5 | Generate the accounts and target tables | `s3_seral_40_10.yaml` (5,400 targets, 135 LU/BEC, manifest hash); UWR no-harvest variant `build/compiled_zone_uwr`. Matrix targets still need the layer. |
| C6 | Extend the audit with section 6 checks | audit passes or reports named gaps |
| C7 | Run S4 recovery and a same-land-base S3 counterfactual | scenario table with matrix/seral audits |

Do not start C4 until C1 and C2 are complete. The partition is meaningless without the
layers and an exact join.

## 8. Open decisions and risks

1. **Core/matrix definition and vintage.** The provincial recovery layer is the only public
   source named in the report. Its version must be recorded; the 2022 package does not
   publish the polygons. The 2018 designatedlands UWR extract was reviewed and is
   superseded by the 2020 layer; see `notes/reference/tsa27-input-availability.md`.
2. **BEC v12 vs VRI BEC.** The current `lu_bec` uses VRI attributes. TSR targets may use
   BEC v12 or NDT/BEC/BEO. Choose one basis and version the target table.
3. **The caribou line and BEO.** The 40%/70% split is "below/above the caribou line"; the
   instance has no line layer. Do not invent one. Apply one target basis everywhere and
   label it as an assumption until the line is available.
4. **Matrix denominator.** "13% of total area" could mean total matrix area, forested matrix
   area, or the matrix land base. The target builder must name the denominator.
5. **Soft vs hard.** WS4 targets are penalties. If a hard 13% cap is required, it needs an
   engine change or a post-run rejection loop.
6. **Deferral.** Calendar-time eligibility is not expressible in the current treatment
   model. Keep it simulation-only and say so.
7. **Track explosion.** 10,000–12,000 tracks is plausible but untested. Measure compile
   time and memory before committing to the full LU/BEC partition.
8. **TSR5 is unpublished.** The matrix and core results remain a documented best guess;
   TSR4 remains the quantitative benchmark.

## 9. Sources

- `reports/tsa27-tsr-corpus-analysis.md` — the four policy layers, TSR thresholds, 2010 and
  2022 land-base tables.
- `notes/plans/tsa27-model-build-plan.md` — the phase plan and the expected account list.
- `config/ws4/caribou_constraints.yaml` — current enforcement status.
- `metadata/data_manifest.yaml` — input availability.
- `scripts/audit_caribou_layers.py` — the current-state evidence.
- `ws4/docs/reference/compiled-dataset.rst`, `ws4/docs/howto/write-targets.rst` — dataset
  and target contracts.
- `femic/docs/reference/patchworks-export.rst`,
  `femic/src/femic/fmg/patchworks.py` — seral-stage and define-field behaviour.
