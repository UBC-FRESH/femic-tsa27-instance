# Operational accessibility and the AAC-to-harvest gap

**Status:** proposed design note. No phase is activated and no issue is open yet.
**Scope:** TSA 27 Revelstoke, 2017–2026 observed harvest versus AAC, with a route to a
reproducible operational-accessibility model.

## Question

The 2022 data package shows actual scaled volume falling from 209,355 m³ in 2018 to
68,608 m³ in 2021 against a 225,000 m³ AAC. The ratio recovered to a provisional 123,835 m³
in 2022, fell to 95,521 m³ in 2023, and rose to 187,750 m³ in 2025. The question is not only
“what is the AAC?” but “what part of the AAC is physically accessible, legal, and economic
for the existing industrial network to harvest and process?”

## What the current model can and cannot do

The TSA 27 instance currently supports strategic WS4 volume and caribou constraints. It does
not contain an operational cost/revenue test, a mill-demand network, a fire-event layer
applied to the schedule, or a machine/labour capacity test. The published result is a
first-period capacity comparison, not an AAC or an operational harvest level.

The latest upstream capabilities change what is feasible:

- **WS4** (`3583f5e`) has route accounts for haul, build, and maintenance, route products to
  named destinations, additive route deltas in the optimizer, post-fire recovery status, and
  carbon accounts. See `docs/reference/roads.rst` and `docs/howto/route-products.rst`.
- **FHOPS** (`0fb9d2c8`) has tactical 1–5 year block × system × period planning with product
  yields, facilities/demand envelopes, transport arcs, road projects, silviculture, fleet
  options, `value_per_m3`, and profit/NPV objective profiles; operational shift/day machine
  scheduling with harvest systems, landings, mobilisation, and sequencing; a road/hauling
  layer with truck, loader, depot, sort-yard, and marine costs; machine-rate and productivity
  costing; and tree-scale/ground-system simulation. See
  `docs/howto/tactical_operational.rst`, `docs/reference/harvest_systems.rst`,
  `docs/reference/hauling.rst`, and `docs/reference/tree_system.rst`.
- **FEMIC** has the disturbance contract (`femic.disturbance.v1`) and point-cloud/hydrology
  data paths. It can carry fire events and post-fire recovery, but it does not yet apply
  disturbances to a harvest schedule; that is a WS4/FHOPS integration step.

## Proposed two-stage model

Use the postdoc architecture: a strategic upper level and an industrial/operational lower
level, iterated rather than solved once.

```
FEMIC inventory + land base + caribou + fire
        |
        v
WS4 strategic AAC and block/product supply
        |
        v
species/grade disaggregation (diameter distributions)
        |
        v
FHOPS tactical: block x system x period, mills, roads, costs, prices
        |
        v
FHOPS operational: machines, landings, trucking, mill receipts
        |
        v
economically accessible volume -> feedback to WS4 eligibility/volume ceiling
        |
        +------------ iterate to a fixed point ------------+
```

The upper level supplies candidate blocks and product volumes. The lower level decides which
blocks are actually worth harvesting and delivering under costs, prices, mill demand, road
access, and machine capacity. The feedback removes or discounts blocks the industrial network
will not consume, then re-solves the strategic problem. This is the mechanism that can turn a
nominal AAC into an induced, cumulative accessible volume.

## Cost accounting coverage

| Cost | Current capability | Needed for TSA 27 |
|---|---|---|
| Planning and layout | Not explicit; FHOPS fixed/variable option costs can carry it | Per-block or per-ha planning/layout table, separated from harvest |
| Machine movement | FHOPS mobilisation distances and move-in costs | Block-to-block distance matrix, lowbed/walk thresholds |
| Harvest | FHOPS machine rates + productivity by system | TSA 27 slope/stand/system calibration, not synthetic defaults |
| Stumpage | Not explicit | Species/grade stumpage rate table and deduction |
| Loading and unloading | Loader machine time; port `handling_cost_per_trip` | Landing load cost and mill unload cost per m³/trip |
| Log hauling | FHOPS hauling flow/schedule with truck fixed, variable, overtime, and handling costs | Plausible mills, road network, turn times, payloads, backhaul |
| Road construction and maintenance | WS4 route build/maintain; FHOPS road projects | One authoritative road network and no double counting |
| Revenue | FHOPS `value_per_m3` / profit and NPV profiles | Mill-gate prices by product, species, grade, destination |
| Mill capacity | FHOPS facility demand envelopes | Mill list, capacity, curtailments, closures, product acceptance |

The existing FHOPS tactical model already represents most of this as option fixed/variable
cost, transport-arc cost, road project cost, and demand value. Planning/layout and stumpage
are the two categories that need a first-class field rather than being buried in a generic
variable cost.

## Data needed

1. **Operational block attributes** — area, volume/ha, stem size, stem density, slope,
   harvest system, landing, distance to road, eligibility window. Build from the TSA 27
   fragments and VRI/site index layers; do not reuse synthetic FHOPS defaults.
2. **Road and mill network** — vertices, segments, haul/build/maintain rates, block linkages,
   destinations, product eligibility. The WS4 route tables are the natural canonical form;
   FHOPS can consume the same network.
3. **Mill demand and capacity** — facilities, accepted products, demand envelopes, capacity,
   opening inventory, prices. Include current curtailments/closures, not a static 2013 list.
4. **Prices and stumpage** — delivered log values by species/grade and destination; interior
   stumpage rates and deductions.
5. **Machine and labour rates** — FHOPS rate cards plus TSA 27 system assignments; validation
   against local contractor rates.
6. **Fires since 2017** — BC Wildfire Service perimeters, burn severity, salvage eligibility,
   and post-fire recovery. Overlay on blocks; mark burned volume, salvage window, and changed
   access.
7. **Processing-capacity events** — mill closures, curtailments, shift reductions, and
   ownership changes; date-stamped so the 2017–2026 ratio can be reproduced year by year.

## Context found while building the pilot

### Fire overlap

Using the BC Wildfire historical fire perimeters (WFS, `PROT_HISTORICAL_FIRE_POLYS_SP`) and
the TSA 27 block layer, fires from 2017 onward overlap the following block area:

| Year | Fires intersecting blocks | Block overlap (ha) |
|---:|---:|---:|
| 2017 | 4 | 374 |
| 2018 | 23 | 1,583 |
| 2019 | 1 | 2 |
| 2021 | 12 | 1,214 |
| 2022 | 14 | 940 |
| 2023 | 9 | 1,470 |
| 2024 | 10 | 562 |
| 2025 | 1 | 3 |

The largest overlaps are the 2023 fires N42074 (710 ha) and N40596 (492 ha), and the 2021
fires N41814 (577 ha) and N41254 (343 ha). This is a block-overlap screen, not a salvage or
volume-loss estimate. The next step is to intersect the perimeters with the current blocks,
mark burned area and salvage eligibility, and test whether the 2021/2023 fire years changed
the accessible volume.

### Processing capacity

The public record describes a province-wide contraction: more than 30 BC sawmills have closed
since 2017, with further closures and curtailments through 2025–2026. The local Revelstoke
cluster still includes Downie Timber and Selkirk Cedar, but the TSA 27 model does not yet have
a dated mill-capacity table. The 2019 provincial mill list and current company announcements
are the starting point for a mill-by-mill capacity and curtailment history.

## Publication method to reproduce


The postdoc work supplies the conceptual template:

- **Paradis (2016), Hierarchical Forest Management Planning: A Bilevel Wood Supply Modelling
  Approach** — two-phase rolling-horizon principal–agent model; the upper level is public wood
  supply, the lower level is profit-maximising fibre consumption.
- **Paradis et al. (2017), A bi-level model formulation for the distributed wood supply
  planning problem** — the classic even-flow model assumes infinite fibre demand; the
  bilevel formulation anticipates species-unbalanced industrial consumption and mitigates
  wood-supply failure risk.
- **Paradis and LeBel (2018), Estimating the value-creation potential of wood supply using a
  hybrid simulation-optimization approach** — retrofits value-creation indicators onto a
  long-term AAC model and links it to a profit-maximising network-flow model of primary
  processing facilities; scenarios vary capacity, prices, stumpage, and facility openings.
- **Paradis and LeBel (2018), Retro-fitting value-creation potential indicators to long-term
  wood supply models** — disaggregates species-wise volume into log assortments and values
  them.
- **Paradis and LeBel (2017), Compiling disaggregation coefficients to link long- and
  short-term planning models** and **Diameter Distribution Models for Quebec** — the bridge
  from strategic volume to product/grade assortments.

The TSA 27 version should replace Quebec's species/grade assumptions with BC interior
species, grades, and mill specifications, but keep the bilevel/iterative structure.

## First bounded pilot

Do not start with the full 200-year model. Start with a one-operating-area, 1–5 year tactical
pilot:

1. Export a TSA 27 block subset with area, volume, slope, stem size, and candidate harvest
   system.
2. Build a road/mill network with two or three plausible destinations and current demand
   envelopes.
3. Populate machine, haul, stumpage, price, and road-cost tables from public/industry values.
4. Solve FHOPS tactical with `max_discounted_profit`; compare selected volume with the WS4
   candidate volume.
5. Attribute the gap to cost, price, road access, mill capacity, and legal/operational
   eligibility.
6. Only then iterate the full strategic model and add the 2017–2026 fire/capacity timeline.

## Immediate blockers

- No authoritative TSA 27 mill list with current capacity and product acceptance.
- No TSA 27 road network linked to the WS4 block ids and mill destinations.
- No species/grade log-price and stumpage table tied to the same products.
- No fire-perimeter overlay applied to the current schedule.
- No operational block attributes (slope, stem size, landing, system) in the compiled
  dataset.
- FHOPS planning/layout and stumpage costs need explicit fields or a documented fixed/variable
  cost convention.

## Progress — 29 October 2026

- Built a shared-road cost allocator from the all-DRA WS4 route network.
- Replaced the one-road-per-block placeholder with a new-access spur plus volume-weighted
  maintenance on the DRA segments each block uses.
- Central full-estate result: 12.74M m3 positive at 52.6% of operable volume; UWR 7.77M m3 at
  56.9%. Price -20% leaves 4.7-5.0%; cost +20% leaves 8.3-9.8%.
- Report: `reports/tsa27-shared-road-costs.md`.
- The strict truck-legal filter is retained for the 45-block pilot; it fragments the full
  network and is not suitable for the full screen without major new connectors.
- Fed the shared-road charge into the FHOPS pilot: shared trunk maintenance in transport arcs, plus an amortised spur road project with an activation period. Current pilot: 65,206 m3, 22 blocks, net CAD 0.678M; 22 spurs open across 2027-2031; total road-related cost CAD 0.137M.
- Built 2017-2026 annual snapshots of cutblocks, fire overlap, active FTEN roads, and UWR approval area. UWR u-3-005 expands by 10,601 ha in 2019; fire overlap peaks at 1.65% of operable area; cutblock area does not track the harvest collapse. Report: `reports/tsa27-annual-snapshots.md`.
- Ran the 2019 UWR timing counterfactual and year-by-year screen: the UWR expansion removes 1.223M m3 operable and 0.841M m3 positive-margin volume (9.8% of the pre-2019 positive pool); fire with no salvage removes at most 47,385 m3/year (<0.6% of the positive pool).
- Added a public price-index screen (BLS softwood-lumber PPI). Price alone does not reproduce HBS: 2021 is high price/low harvest; 2025 is low price/high harvest; 2019 is the one year where price and UWR timing align.
- Replaced the U.S. PPI with BC interior zone 7 lumber AMV; added a South East average sawlog-stumpage table sensitivity. The tabular stumpage series is too erratic to use as central (2020 0%, 2021 89%, 2024 5%), so the flat CAD 20/m3 remains until a TSA-27 billed series is available.
- Ran a one-mill FHOPS counterfactual (Revelstoke only): 66,439 m3 and CAD 0.748M net versus 65,206 m3 and CAD 0.678M for two mills. Downie alone is 2.10x AAC, so mill volume is not binding in the pilot.
- Wrote `reports/tsa27-counterfactual-synthesis.md` with bounded, non-additive attribution ranges: caribou 5-15% of AAC, fire <1%, access 5-10% of the positive pool, mill volume ~0 at design capacity, residual processing/undercut.
- Built a public-data uncertainty envelope instead of waiting for a proprietary billed-stumpage series. 2021-2022 quantity/processing is robust across all public stumpage anchors; 2019 and 2025 are not identified without billed stumpage.
- Searched BC Data Catalogue, BCTS performance reports, IAM/non-appraised tables, local news, and mill lists. No TSA-specific billed-stumpage or local curtailment series exists; added a public-data gap register with a treatment for each gap.
- Ran a 240-combination nested public-data grid. 2021-2022 quantity/processing remains robust (77.8-96.2% and 67.1-95.6% positive against 30.2% and 55.0% HBS); 2019 and 2025 remain range-dependent.
- Next: add a dated BCTS Okanagan-Columbia volume-sold demand switch and keep the nested range as the reporting format.

## Sources read

- `ws4` `3583f5e`, `docs/reference/roads.rst`, `docs/howto/route-products.rst`,
  `docs/reference/recovery.rst`, `docs/reference/disturbance.rst`.
- `fhops` `0fb9d2c8`, `docs/howto/tactical_operational.rst`,
  `docs/reference/harvest_systems.rst`, `docs/reference/hauling.rst`,
  `docs/reference/tree_system.rst`, `docs/howto/rolling_horizon.rst`.
- `femic` `69a5a65`, `docs/reference/contracts/disturbance-contract.rst`,
  `docs/reference/contracts/carbon-domain.rst`.
- TSA 27 `reports/tsa27-figure4-recovery.md`, `reports/tsa27-tsr-corpus-analysis.md`.
- `clews-c2070-fresh` `README.md` (diagnostic status; cost surfaces, facility layer, species
  composition remain blocked).
