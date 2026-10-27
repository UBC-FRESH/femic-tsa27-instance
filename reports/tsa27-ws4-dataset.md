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
| curves | 7,973 |
| features | 54,510 |
| products | 33,579 |
| treatments | 3,000 |
| accounts | 94 |

Fragment area: 402,791 ha; managed/THLB: 79,102 ha.

## Build command

```bash
femic export patchworks --tsa 27 --bundle-dir data/model_input_bundle \
  --checkpoint data/vri_vclr1p_checkpoint8.feather \
  --output-dir output/patchworks --start-year 2026 --horizon-years 300

ws4 build --xml output/patchworks/forestmodel.xml \
  --fragments output/patchworks/fragments/fragments.shp --out build/compiled
```

## Limits

- The XML/fragments carry the age/species features from the Patchworks export, including `og1`/`og2` seral accounts.
- The caribou UWR constraint is applied at the schedule level (P3.3), not inside the XML.
- The matrix 13% and historical deferral are not yet enforced.
- The base-run schedule is a capacity test, not an AAC forecast.
