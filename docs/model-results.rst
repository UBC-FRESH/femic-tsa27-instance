Model results
=============

The model is built and runs. The first-period caribou comparison is:

.. list-table::
   :header-rows: 1
   :widths: 35 25 25 15

   * - Scenario
     - Harvest at offset 0
     - Treated area
     - Δ harvest
   * - ``s6_no_caribou``
     - 24,218,812 m³
     - 79,102 ha
     - —
   * - ``s3_tsr5_base`` (UWR no-harvest)
     - 13,660,939 m³
     - 57,941 ha
     - −43.6%

This is **capacity**, not AAC. The schedules harvest all eligible blocks at year 0. A multi-rotation WS4 optimization is required for an AAC estimate.

Model build
-----------

- FEMIC: 37,463 stands; 6,439 THLB stands; 79,102 ha THLB; 18 AUs; 1,008 curves; 0 TIPSY errors.
- WS4: 40,660 fragments; 4,746 tracks; 54,510 features; 33,579 products; 94 accounts.
- UWR filter: 108,458 ha flagged; 1,940 of 8,107 schedule rows excluded.

Limitations
-----------

- Matrix 13% <40 years and the 80-year historical deferral are mapped but not enforced.
- The THLB is 79,102 ha vs the TSR 57,908/51,454 ha; the full netdown sequence is the AAC follow-on.
- The 2022 TSR5 results are unpublished.

Reports
-------

- ``reports/tsa27-final-report.md`` — full report.
- ``reports/tsa27-caribou-attribution.md`` — attribution and uncertainty.
- ``reports/tsa27-caribou-scenario-comparison.md`` — comparison table.
- ``reports/tsa27-tsr-corpus-analysis.md`` — TSR evidence.
