# TSA 27 caribou and BEC input availability — 2026-10-30

This note records what was fetched, what was cross-checked, and what remains
request-only. Facts are tied to the command output or the local file digest.

## BEC Map

| Item | Value |
|---|---|
| Source | BC Data Catalogue, BEC Map (`WHSE_FOREST_VEGETATION.BEC_BIOGEOCLIMATIC_POLY`) |
| Dataset page | `https://catalogue.data.gov.bc.ca/dataset/bec-map` |
| Service | WFS `GetFeature`, bbox in EPSG:3005 |
| Bounding box | `1481038.6,655622.4,1582171.9,819973.0` |
| Features | 543 |
| Size | 190,795,289 bytes |
| SHA-256 | `100f14e1ab97ababe2d8dd06caf431c38f1d6e9da6e099de6eafb1b74abaa6c6` |
| Local path | `data/downloads/bc/WHSE_FOREST_VEGETATION_BEC_BIOGEOCLIMATIC_POLY/WHSE_FOREST_VEGETATION_BEC_BIOGEOCLIMATIC_POLY.geojson` |
| Retrieval | `femic data bcdc-fetch WHSE_FOREST_VEGETATION.BEC_BIOGEOCLIMATIC_POLY --bbox 1481038.6,655622.4,1582171.9,819973.0 --output-format geojson --download-root data/downloads/bc --instance-root .` |

The WFS response covers the requested bbox, which is larger than TSA 27. The model clips
to the TSA; the extra area is not used.

### Cross-check against the VRI attributes

Method: take the representative point of each P3.1 fragment, join it to the BEC polygon
(`predicate="within"`), and compare
`BEC_ZONE_CODE + BEC_SUBZONE + BEC_VARIANT` (VRI) with `ZONE + SUBZONE + VARIANT` (BEC).

| Class | Fragments |
|---|---:|
| P3.1 fragments | 37,463 |
| Fragments joined to a BEC polygon | 37,463 |
| Both variants present | 19,701 |
| Exact match | 19,390 (98.42%) |
| Mismatch | 311 (1.58%) |
| VRI variant missing | 17,452 |
| BEC supplies a variant where VRI does not | 279 |

The 279 supplied variants are mostly `ICHvk1` (176), `ICHwk1` (51), `ESSFwc4` (47), and
`ESSFwc2` (5). The dominant `lu_bec` vocabulary problem is therefore the missing VRI
variant, not the BEC version. Adopting BEC v12 is a low-risk cross-check, but it does not
by itself create a finer LU/BEC partition. See
`notes/plans/tsa27-caribou-accounting-design.md` §3.1 and §8.

## UWR 2018 vintage (designatedlands v0.1.0) — reviewed, not used

A second UWR no-harvest extract was provided on 2026-10-30: the BC
`designatedlands` v0.1.0 release, filtered to `desig = 17_uwr_no_harvest`.

| Item | Value |
|---|---|
| Source | `https://github.com/bcgov/designatedlands/releases/download/v0.1.0/designatedlands.shp.zip` |
| Vintage | v0.1.0, data run 2018-05-03 (release page: May 2018) |
| Filter | `desig = 17_uwr_no_harvest`, 16,077 features BC-wide |
| Review copy | collaborator upload, inspected in place; not retained in the instance |
| Size | 26,542,127 bytes |
| SHA-256 | `1ff0d765e2641fc4753c0fad32e06ea70aebffbfd1fd9ba49a6dcb5d003ff913` |

In the TSA 27 bounding box the extract carries u-3-005 (1,820 features), u-4-010 (19),
u-3-004 (3), and u-4-014 (3). Clipped to the TSA 27 boundary and filtered to u-3-005:

| Layer | u-3-005 union (ha) | Notes |
|---|---:|---|
| current 2020 amendment (`data/downloads/bc/uwr.geojson`) | 116,758.8 | matches TSR5 gross 116,820 within 61 ha |
| 2018 designatedlands | 116,209.6 | 610 ha below TSR5 gross |
| overlap | 116,063.1 | IoU 0.9835 |
| 2018-only | 696.5 | boundary differences |
| 2020-only | 1,245.6 | boundary differences |

This is a **2018 vintage**, not the 2010 boundary the S0 scenario needs. It is **superseded
for the base case** by the current 2020 amendment, which reconciles with TSR5 Table 14 within
61 ha. It was reviewed and **not added to the data manifest**; the base model is unchanged.
The comparison is kept here so a future collaborator does not re-upload the same file without
context. It could still serve as a pre-2020 sensitivity if one is explicitly commissioned.

## Caribou core and matrix habitat

The BC Data Catalogue was queried for `caribou core habitat` and `caribou matrix habitat`
on 2026-10-30. The matches are **boreal caribou** layers:

- "Boreal Caribou Core Habitat Areas - Peace Region"
  (`https://catalogue.data.gov.bc.ca/dataset/boreal-caribou-core-habitat-areas-peace-region`)
- "Boreal Caribou Core-Matrix Habitat"
  (`https://catalogue.data.gov.bc.ca/dataset/boreal-caribou-core-matrix-habitat`)

Neither is the southern mountain caribou recovery core/matrix layer for TSA 27. The
catalogue exposes only indirect/custom-download resources for these layers, and the
TSR report names the provincial caribou recovery program as the source for the Revelstoke
layer. The `caribou_core_matrix` manifest entry therefore remains `to_fetch`, with the
request path recorded. No substitute layer was used.

## Historical HLP zone

The historical HLP caribou zone is described in the TSR corpus but no public spatial layer
was found in the catalogue search. It remains absent from the manifest and from the model.
The S5 (TSR3-style) scenario stays unavailable.

## What this changes

- `metadata/data_manifest.yaml`: `bec_v12` moves from `to_fetch` to `available`, with the
  digest and retrieval command recorded.
- `metadata/data_manifest.lock.yaml`: regenerated; `entries=12 present=11 pending=1`.
- The only remaining pending input is `caribou_core_matrix`.
