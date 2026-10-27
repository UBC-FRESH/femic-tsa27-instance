# Data

This directory is for fetched public data. It is ignored by git except for this file.

- `data/bc/` — VRI, TSA, site productivity, BEC, UWR, and other public BC layers.
- `data/downloads/` — raw downloads.
- `data/tsr/corpus/` — materialized TSR PDFs.

Set `FEMIC_EXTERNAL_DATA_ROOT` to a FEMIC public-data mirror to avoid downloading BC-wide layers. The TSR corpus is fetched with `scripts/fetch_tsr_corpus.py`.
