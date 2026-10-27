Data provenance
===============

The repository does not vendor raw provincial data or TSR PDFs. It tracks metadata, curated
tables, and short evidence excerpts, and it fetches the raw sources at runtime.

Public data sources
-------------------

- Timber Supply Review documents: BC TSR FTP catalogue and the September 2022 TSR5 data
  package on the ``www2.gov.bc.ca`` asset path.
- VRI 2025, TSA boundaries, site productivity, BEC, UWR, landscape units, OGMA/MOGMA, roads,
  and cutblocks: BC Geographic Warehouse layers, as listed in the model-building plan.
- Core and matrix caribou habitat: provincial caribou recovery program layers.
- Caribou herd ranges: provincial caribou herd locations.

Storage
-------

Raw data and PDFs are fetched into ignored paths:

- ``data/tsr/corpus/`` for TSR PDFs,
- ``data/downloads/`` for public data downloads,
- ``reference/tsr_pdfs/`` and ``reference/tsr_fulltext/`` for local working copies.

The shared public-data mirror is a FEMIC checkout at
``femic/external/femic-public-data/data``. Set ``FEMIC_EXTERNAL_DATA_ROOT`` to its ``data``
directory for case preflight and compilation.

Tracked artifacts
-----------------

- ``metadata/tsr/tsa_documents_with_2022.json``: document metadata and public URLs.
- ``metadata/tsr/tsa27_thlb_netdown_table3.csv``: curated TSR4 2010 netdown sequence.
- ``metadata/tsr/tsa27_thlb_netdown_table14_2022.csv``: curated 2022 land-base table.
- ``metadata/tsr/tsa27_tsr_cycle_timeline.csv``: cycle/model/caribou summary.
- ``metadata/tsr/tsa27_caribou_evidence.csv``: short evidence excerpts with page references.

Manifest and lock
-----------------

``metadata/data_manifest.yaml`` lists every input, its source, version, local or mirror path,
and check. ``metadata/data_manifest.lock.yaml`` records the digest, size, and file count for
every ``available`` entry. Regenerate the lock with:

.. code-block:: bash

   export FEMIC_EXTERNAL_DATA_ROOT="${FEMIC_EXTERNAL_DATA_ROOT:-../femic/external/femic-public-data/data}"
   python scripts/verify_public_data.py --write-lock

``to_fetch`` entries are reported as pending, not silently skipped. Each one names its
``fetch_command`` or the request path for a non-catalogue layer.

Records
-------

Each fetched dataset or document should record its source URL, version or date, checksum,
retrieval command, and licence in the input manifest before it is used in a model run.
