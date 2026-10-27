Model design
============

The WS4 model is built in layers so that each caribou policy can be switched independently.

Land base
---------

The land base follows the TSR classification: gross land base, analysis forest land base
(AFLB), legally harvestable land base (LHLB), and timber harvesting land base (THLB). The
2022 TSR5 data package is the current accounting: the caribou UWR is a legal no-harvest
exclusion from the LHLB, not a THLB netdown.

Caribou layers
--------------

- **UWR / core no-harvest:** fragments flagged ``caribou_uwr`` or ``caribou_core`` are
  non-harvestable for the horizon. The base case uses the legal UWR; the recovery sensitivity
  adds the core habitat.
- **Matrix habitat:** fragments flagged ``caribou_matrix`` remain harvestable, but the zone
  carries a cover constraint of at most 13% of area younger than 40 years.
- **Seral constraints:** old and mature+old accounts by LU/BEC, with the RHLPO targets used in
  the TSR4 base case and the mature biodiversity targets in the caribou landscape units.
- **Immature deferral:** the historical TSR2/TSR3 counterfactual makes immature caribou
  habitat non-harvestable for the first 80 years, then releases it.

Harvest behaviour
-----------------

The base case emulates the STSM 2022 stand preference (volume per hectare, cycle time, and
distance to road) in WS4 simulation mode. Optimization is used only for policy exploration
and is labelled as such.

Scenarios
---------

The scenario matrix is in ``notes/plans/tsa27-model-build-plan.md`` and
``reports/tsa27-tsr-corpus-analysis.md``. The core set is: TSR4 base, TSR4 incremental
reserves back, TSR4 no mature biodiversity in caribou LUs, TSR5 base, TSR5 recovery
sensitivity, TSR3-style historical, and no caribou constraints.

Verification
------------

Each run records the dataset manifest, scenario config, seed, WS4 version, and run ID. The
analysis reports land-base reconciliation, harvest-flow comparison, matrix and core audits,
seral audits, and the uncertainty that comes from the unpublished TSR5 results.
