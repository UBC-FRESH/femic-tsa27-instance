# Caribou policy scenarios

These files define the policy switches for the WS4 experiment. They are **planned** in P0; the executable schema is finalized in P3/P4. Each scenario changes one policy layer while holding the inventory, yields, and harvest rules constant.

| ID | Scenario | Purpose |
|---|---|---|
| S0 | TSR4 base (2010) | Last completed TSR; validate against the 2010 sensitivity table |
| S1 | TSR4 + incremental reserves back | Isolate the incremental GAR effect (+8.4% short/mid) |
| S2 | TSR4 no mature biodiversity in caribou LUs | Isolate the seral/biodiversity interaction (+4.0%/+2.5%) |
| S3 | TSR5 base (2022) | Legal UWR u-3-005 through the 2020 amendment |
| S4 | TSR5 recovery sensitivity | Core no-harvest + matrix max 13% <40 years |
| S5 | TSR3-style historical | Caribou as LU/BEC seral constraints + 80-year immature deferral |
| S6 | No caribou constraints | Upper-bound counterfactual; not a policy recommendation |

Fields:

- `caribou_uwr`: `2010`, `2020`, or `none` — legal UWR boundary version.
- `caribou_core`: `true` to add the provincial core habitat to the no-harvest set.
- `matrix_lt_40_max_fraction`: `0.13` for the recovery sensitivity, `null` otherwise.
- `mature_old_seral`: apply the RHLPO mature/old seral targets.
- `caribou_lu_biodiversity`: apply mature+old biodiversity targets in caribou LUs.
- `immature_deferral_years`: `80` for the TSR3-style scenario, `0` otherwise.
