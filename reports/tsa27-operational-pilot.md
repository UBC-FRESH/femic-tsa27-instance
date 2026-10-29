# TSA 27 operational pilot

**Status:** structural pilot, not a historical reconstruction and not an AAC result.
**Question:** can the new WS4/FHOPS/FEMIC stack turn a strategic volume into an
economically and operationally accessible volume, and attribute the gap?

## What was built

`scripts/build_operational_pilot.py` builds a FHOPS tactical–operational scenario from the
TSA 27 compiled dataset:

- a deterministic spatial cluster of managed blocks nearest Revelstoke;
- five annual periods, 2027–2031;
- two public design-capacity mill destinations: Downie/Selkirk (Revelstoke) and Eagle River (Malakwa);
- the ground-based feller-buncher / grapple-skidder / processor / loader system;
- sawlog and pulp product yields from the block-level clear-cut curves;
- a documented cost and price ledger;
- a shared-road charge for trunk maintenance in the transport arcs;
- an amortised spur-build road project per block, so the spur is charged in the period it is
  opened.

The pilot uses 45 blocks with positive year-0 clear-cut volume from a 50-block selection.
It is deliberately small enough to solve and inspect.

## Cost and revenue assumptions

The current run uses CAD 2026 **placeholders**, not validated local values:

| Item | Value |
|---|---:|
| Harvest variable | 32.00 $/m³ |
| Planning | 1.50 $/m³ |
| Layout | 0.50 $/m³ |
| Stumpage | 20.00 $/m³ |
| Loading | 8.00 $/m³ |
| Unloading | 4.00 $/m³ |
| Contingency | 2.00 $/m³ |
| Aggregate variable | 68.00 $/m³ |
| Planning + layout + machine movement | 9,500 $/block |
| Shared trunk maintenance | embedded in transport |
| Spur build | amortised 5-year charge in the road module |
| Haul | class-based DRA route cost |
| Sawlog price | 95.00 $/m³ |
| Pulp price | 45.00 $/m³ |

The shared-road source is `runtime/operational_screen/road_costs_full_shared.csv`. It contains
the amortised new-access spur, the block's volume-weighted share of maintenance on every DRA
segment it uses, and any shared re-opening charge.

The ledger is `runtime/operational_pilot/cost_assumptions.csv`. The selected-block road
ledger is `runtime/operational_pilot/selected_road_costs.csv`.

## Results

### Current run with spur activation

- Volume: **65,206 m³** over five years
- Sawlog: 53,665 m³; pulp: 11,541 m³
- Blocks harvested: 22 of 45
- Spur roads opened: 22, across all five periods
- Product value: 5.281 M CAD
- Total cost: 4.603 M CAD
- Transport including shared road: 0.148 M CAD
  - shared trunk component: 0.042 M CAD
  - haul component: 0.106 M CAD
- Spur road module: 0.095 M CAD
- Total road-related cost: **0.137 M CAD**
- Net objective: **0.678 M CAD**
- Solver: HiGHS, optimal, within the 60 s limit

The spur charge is now fixed per block and incurred when the road is opened, not spread as a
per-cubic-metre charge over the whole block. The solver opens the 22 spurs across 2027–2031.

### Earlier structural cases

These are retained for comparison but use different road-cost treatments:

| Case | Volume | Sawlog | Pulp | Product value | Total cost | Road-related cost | Net |
|---|---:|---:|---:|---:|---:|---:|---:|
| No road-cost module | 57,266 m³ | 49,170 | 8,096 | 4.762M | 4.035M | 0.000M | 0.727M |
| One road per block, DRA class cost | 37,388 m³ | 33,902 | 3,486 | 3.134M | 2.803M | 0.306M | 0.331M |
| Shared road entirely in transport arcs | 65,206 m³ | 53,665 | 11,541 | 5.281M | 4.603M | 0.146M | 0.678M |
| Shared trunk in arcs + spur activation | **65,206 m³** | 53,665 | 11,541 | 5.281M | 4.603M | **0.137M** | **0.678M** |

The shared-road case selects more volume than the one-road-per-block case because the flat
CAD 25,000 build plus maintenance per block overcharged accessible blocks. It selects less
volume than the no-road case because haul and road charges still remove marginal blocks.
Splitting the spur into the road module changes the timing and discounting of the charge but
barely changes the selected volume.


## One-mill counterfactual: Revelstoke only

Eagle River is absent from the 2019, 2022, and 2023 BC major-mill lists, so the pilot was
re-solved with **Revelstoke as the only destination**. The scenario is
`runtime/operational_pilot/one_mill/scenario.yaml`.

| Case | Volume | Blocks | Product value | Total cost | Transport incl. shared road | Spur module | Road total | Net |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Two mills | 65,206 m³ | 22 | 5.281M | 4.603M | 0.148M | 0.095M | 0.137M | 0.678M |
| Revelstoke only | **66,439 m³** | 22 | 5.364M | 4.616M | 0.082M | 0.098M | 0.142M | **0.748M** |

The one-mill case is slightly larger and more profitable in this pilot. It avoids the long
Malakwa haul and sends the whole envelope to Revelstoke. This is consistent with the capacity
arithmetic: Downie alone is 2.10× AAC on design volume, so mill **volume** is not binding in
the 45-block pilot.

It does not show that one mill can absorb the whole TSA indefinitely. Product acceptance,
grade mix, sawmill recovery, and current operating shifts are still outside the model.

## Actual WS4/DRA route distances

The current scenario uses actual DRA road distances from `scripts/build_ws4_route_distances.py`
and WS4 `RouteNetwork`:

- 18,189 truck-legal DRA features after removing trail, skid, water, ferry, runway,
  alleyway, overgrown, and decommissioned linework.
- 142,836 vertices / 143,336 segments in the block-containing component.
- All 45 pilot blocks route to both mills.
- The route network is in `runtime/operational_pilot/route_network_truck/`.

Class-based haul costing uses the least-cost path, not the least-length path. Resource-road
rates differ from the flat 0.12 $/m³/km assumption.

## What this does and does not show

**Does show:**
- FHOPS can consume a TSA 27 block/product subset and solve a tactical cost/revenue model.
- Shared trunk maintenance can be carried in transport arcs while the block-level spur is a
  real road project with an opening period.
- Road cost and haul distance materially change the selected volume.
- The cost categories are explicit and can be sensitivity-tested one at a time.

**Does not show:**
- A historical 2017–2026 harvest level. The compiled dataset is current, not a historical
  series, and the pilot periods are 2027–2031.
- An AAC. The pilot is a 45-block subset with placeholder costs and prices.
- The effect of fire, mill curtailment, or caribou. Those layers are not applied in this run.
- Re-opening or closure timing for existing shared roads. Existing DRA segments are assumed
  open from period 1; only the new spurs have an activation period.
- Eagle River's operating status. The pilot uses Malakwa as a design-capacity destination, but
  Eagle River is absent from the 2019, 2022, and 2023 BC major-mill lists. Downie alone is
  still 2.1× AAC on design volume, so the capacity conclusion is robust, but the destination
  set is not verified.
- Full capital recovery of a spur. The road module carries the 5-year amortised charge, not
  the full construction bill.
- A product/grade model. Sawlog/pulp is a two-product simplification of the species curves.

## Reproduce

```bash
cd "$(git rev-parse --show-toplevel)"
python scripts/build_operational_pilot.py --blocks 50 \
  --routes runtime/operational_pilot/route_network_truck/route_distances_ws4_truck.csv \
  --road-costs runtime/operational_screen/road_costs_full_shared.csv

PYTHONPATH="${FHOPS_ROOT:?set FHOPS_ROOT to the FHOPS checkout}/src" \
python -m fhops.cli.main plan tactical-operational \
  runtime/operational_pilot/scenario.yaml \
  --harvest-mode continuous \
  --demand-basis minimum \
  --objective-profile max_discounted_profit \
  --enable-roads \
  --solver highs --time-limit 60 \
  --out-json runtime/operational_pilot/run_spur/result.json \
  --out-harvest-csv runtime/operational_pilot/run_spur/harvest.csv \
  --out-production-csv runtime/operational_pilot/run_spur/production.csv \
  --out-flows-csv runtime/operational_pilot/run_spur/flows.csv \
  --out-roads-csv runtime/operational_pilot/run_spur/roads.csv
```

The `PYTHONPATH` points at the clean latest FHOPS audit worktree. Once the local FHOPS
checkout is updated, the system `fhops` entry point can be used.

## Next steps

1. Replace the 45-block pilot with an operating-area subset of several hundred blocks and
   solve with a longer time limit or a two-stage rolling horizon.
2. Replace notional mills with a current mill list, product acceptance, capacity, and
   curtailment history.
3. Add re-opening and closure timing for existing shared roads, not only new spurs.
4. Add slope, stem size, landing, and system assignment from terrain and VRI data.
5. Add stumpage and log-price tables by species/grade and destination.
6. Overlay BC Wildfire Service perimeters since 2017 and mill-capacity events.
7. Feed the selected/economic volume back into WS4 as an eligibility or volume ceiling and
   iterate to a fixed point.

## Artifacts

- `scripts/build_operational_pilot.py`
- `runtime/operational_pilot/scenario.yaml`
- `runtime/operational_pilot/cost_assumptions.csv`
- `runtime/operational_pilot/selected_road_costs.csv`
- `runtime/operational_pilot/run_spur/result.json`
- `runtime/operational_pilot/run_spur/summary.json`
- `runtime/operational_pilot/run_spur/harvest.csv`
- `runtime/operational_pilot/run_spur/production.csv`
- `runtime/operational_pilot/run_spur/flows.csv`
- `runtime/operational_pilot/run_spur/roads.csv`
- `runtime/operational_pilot/one_mill/scenario.yaml`
- `runtime/operational_pilot/run_one_mill/result.json`
- `runtime/operational_pilot/run_one_mill/summary.json`
- `runtime/operational_pilot/run_shared/result.json`
- `runtime/operational_pilot/run_roads/result.json`
- `runtime/operational_pilot/run_no_roads/result.json`
- `runtime/operational_pilot/route_network_truck/route_distances_ws4_truck.csv`
- `runtime/operational_pilot/route_network/route_distances_full_all.csv`
- `runtime/operational_pilot/route_network/route_distances_uwr_all.csv`
- `runtime/operational_pilot/fire_overlap_2017_2026.csv`
- `notes/plans/tsa27-operational-aac-gap-plan.md`
