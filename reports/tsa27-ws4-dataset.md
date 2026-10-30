# TSA 27 WS4 dataset

The P3.2 build compiled the WS4 dataset from the P2 model-input bundle.

## Sources

- `output/patchworks/forestmodel.xml` (sha256 `88a029...`)
- `output/patchworks/fragments/fragments.shp` (sha256 `b1ddbe...`)
- P3.1 fragments: `data/ws4/fragments.gpkg` (ignored)
- Manifest: `metadata/ws4/dataset_manifest.yaml`

## Dataset

| Table | Rows |
|---|---:|
| fragments | 40,660 |
| blocks | 40,660 |
| tracks | 4,746 |
| curves | 12,545 |
| features | 101,970 |
| products | 48,579 |
| treatments | 3,000 |
| accounts | 279 |

Fragment area: 402,791 ha; managed/THLB: 79,102 ha.

## Build command

```bash
femic export patchworks --tsa 27 --bundle-dir data/model_input_bundle \
  --checkpoint data/vri_vclr1p_checkpoint8.feather \
  --output-dir output/patchworks --start-year 2026 --horizon-years 300 \
  --seral-stage-config config/seral.tsa27.yaml

ws4 build --xml output/patchworks/forestmodel.xml \
  --fragments output/patchworks/fragments/fragments.shp --out build/compiled
```

## Zone partition

The UWR and LU/BEC partition is a post-compile track split, not a second recipe:

```bash
python scripts/partition_caribou_zones.py
```

| Item | Value |
|---|---:|
| Source tracks used | 3,487 |
| Cloned tracks | 10,600 |
| Zones | `uwr`, `other` |
| LU/BEC values | 135 |
| Qualified feature labels | 11,036 |
| Qualified product labels | 724 |

`build/compiled_zone` validates. The invariants in
`metadata/ws4/zone_partition_invariants.csv` all pass: managed area, seral mature and
overmature area, total zone area, harvest, and treated area are identical to the source
dataset. Core and matrix tracks are not present because those layers are still request-only.

`build/compiled_zone_uwr` is the no-harvest variant: 3,251 `uwr` tracks keep their area but
carry **zero treatment rows**. A full 8,107-row schedule on that dataset reproduces the
filtered S3 result — 13,674,669.395 m³ and 57,962.211 ha — so the track-level rule replaces
the external schedule filter.

`config/ws4/targets/s3_seral_40_10.yaml` is generated from that dataset by
`scripts/build_seral_targets.py`: 5,400 targets, 270 accounts, 135 LU/BEC values, with
mature+old ≥40% and old ≥10% of each LU/BEC area. The caribou line is absent, so the
below-the-line rule is applied everywhere and the file says so.

## Limits

- The XML/fragments carry the age/species features from the Patchworks export, including `og1`/`og2` and the 95 TSR-aligned `feature.Seral.*` labels (mature 140–249, overmature 250+).
- The caribou UWR constraint is applied at the schedule level (P3.3), not inside the XML.
- The matrix 13% and historical deferral are not yet enforced.
- The base-run schedule is a capacity test, not an AAC forecast.
