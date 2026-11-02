ALS inventory feasibility
=========================

This page records the P7 audit of whether TSA 27 has enough public FAIB plots and
LidarBC point-cloud coverage for a local first-return inventory.

.. warning::

   The result is a **no-go** for an operational local inventory. It is not a new
   model, not a card, and not a change to the VRI-based TSA 27 model.

Result
------

- 67 FAIB plots, all PSP_G: 63 ICH and 4 ESSF.
- No plot measured since 2018; the last visits are 1992-2013.
- 160 LidarBC point-cloud tiles: 153 in 2019 and 7 in 2021.
- Point-cloud footprint: 23,008.1 ha, or 3.03% of TSA 27.
- 13 plots fall inside the footprint; all are ICH and have 18-27 year offsets.
- 22 plots are within 5 km of a tile and 33 within 10 km.

Decision
--------

No local card. The plot and LiDAR dates are too far apart, and the spatial overlap
is too small. The TSA 23 time-lag evidence showed volume error rising to about
99 m3/ha at 21-30 years, so the 13 overlapping plots are a stress test, not a
calibration set.

The defensible options are:

1. Re-measure the 13 overlapping ICH plots against the 2019 point clouds.
2. Acquire contemporary point clouds over any new recent plots.
3. Add recent plots inside the existing footprint.
4. Keep the VRI-based model and treat ALS as research-only.

Acquisition request
-------------------

The P8 request package asks for remeasurement of the 13 overlapping ICH plots and
contemporary point clouds. The high-priority 2 km request union is 13,475.4 ha; the
all-plot union is 60,367.9 ha. See
`reports/tsa27-als-acquisition-request.md` and
`reports/tsa27-als-acquisition-request.csv`.

Evidence
--------

- `reports/tsa27-als-inventory-feasibility.md`
- `reports/tsa27-als-acquisition-request.md`
- `reports/tsa27-als-acquisition-request.csv`
- `reports/tsa27-als-inventory-feasibility.json`
- `scripts/audit_als_inventory_feasibility.py`

No point-cloud payload was downloaded, no card was fitted, and no model value
changed.
