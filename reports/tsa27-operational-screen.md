# TSA 27 full-estate operational screen

**Status:** structural full-TSA economic screen, 29 October 2026. **Not a tactical schedule, not an AAC, and not a historical attribution.**

## Purpose

The 45-block FHOPS pilot proved the cost/revenue machinery. This screen extends the same logic to every currently operable managed block without solving a full 37,000-block MILP. It asks:

> At explicit cost and price assumptions, using actual DRA road routes and shared-road
> costs, how much currently operable volume has a positive delivered margin, and how
> sensitive is that volume to price and cost?

## Route distance and class cost

Haul distance is not straight-line. The screen uses `route_distances_*_all.csv`, produced by `scripts/build_ws4_route_all.py` and WS4's `RouteNetwork` over the BC Digital Road Atlas. The route table carries a class-based haul cost: highway 0.06, paved 0.10, resource/rough 0.16, and trail/overgrown/decommissioned 0.50 CAD/m³/km. The least-cost route is used.

The full screen uses the all-DRA network because the strict truck-legal filter fragments the network and creates artificial 20–90 km connectors for 44% of the estate. The strict filter is retained for the 45-block pilot. In the full screen, 99.8% of routes are fully truck-legal and the remaining 0.2% are flagged and charged a re-opening cost.

- 22,084 DRA features in the TSA 27 bounding box.
- 8,107 full-dataset blocks and 6,170 UWR blocks routed.
- Median route to Revelstoke: about 47.4 km (full) and 43.2 km (UWR).
- Median route to Malakwa: about 79.5 km (full) and 74.9 km (UWR).
- Block-to-road connector is included in the route total.

## Method

For each managed block with a year-0 clear-cut product:

- sawlog and pulp volume from the compiled product curves;
- least-cost WS4/DRA route to the nearer of two notional mills;
- variable cost: harvest, planning, layout, stumpage, loading, unloading, contingency;
- shared-road cost: amortised new spur plus the block's volume-weighted share of maintenance on every DRA segment it uses;
- fixed per block: planning, layout, machine movement, shared-road cost;
- revenue at 95 CAD/m³ sawlog and 45 CAD/m³ pulp;
- positive-margin volume ranked by margin per m³.

The shared-road method is documented in `reports/tsa27-shared-road-costs.md`.

| Item | Value |
|---|---:|
| Harvest variable | 32.00 $/m³ |
| Planning | 1.50 $/m³ |
| Layout | 0.50 $/m³ |
| Stumpage | 20.00 $/m³ |
| Loading | 8.00 $/m³ |
| Unloading | 4.00 $/m³ |
| Contingency | 2.00 $/m³ |
| Fixed planning/layout/move | 9,500 $/block |
| Road build | 60,000 $/km |
| Road maintenance | 1,500 $/km/yr |
| Spur life / discount | 20 years / 5% |
| Sawlog price | 95.00 $/m³ |
| Pulp price | 45.00 $/m³ |

These are still placeholder costs and prices, except the road-build anchor and the DRA haul classes.

## Results

| Dataset | Operable blocks | Operable volume | Positive-margin blocks | Positive-margin volume | Share | Median delivered cost | Median margin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full `compiled` | 7,206 | 24.22M m³ | 2,108 | 12.74M m³ | **52.6%** | 78.11 $/m³ | 7.17 $/m³ |
| UWR `compiled_uwr` | 5,290 | 13.66M m³ | 1,539 | 7.77M m³ | **56.9%** | 78.21 $/m³ | 7.57 $/m³ |

At these assumptions, roughly **53–57% of current operable volume** has a positive delivered margin. The rest is economically inaccessible before any mill-capacity or legal constraint is applied.

The five-year AAC envelope is 1.125M m³. The positive-margin pool can fill it:

- full: 1.069M m³ selected within the envelope
- UWR: 1.122M m³ selected within the envelope

The selected blocks carry only 1.29 $/m³ (full) and 1.72 $/m³ (UWR) of shared road cost, because the ranking selects blocks close to the existing network. The road-cost tail is concentrated in the blocks that are not selected.

This is a filter, not a schedule.

## Road-cost distribution

For blocks with at least 100 m³:

| Dataset | Median road cost | P90 road cost | Median spur build | Share above 10 $/m³ |
|---|---:|---:|---:|---:|
| Full | 5.73 $/m³ | 69.12 $/m³ | 7,927 $ | 37.6% |
| UWR | 6.18 $/m³ | 68.15 $/m³ | 6,109 $ | 38.4% |

Most blocks are close to existing roads. The long right tail is the blocks that need a multi-kilometre spur.

## Sensitivity

### Build and maintenance rates

| Case | Positive-margin volume | Share |
|---|---:|---:|
| Full, low (38k $/km, 750 $/km/yr) | 13.86M m³ | 57.2% |
| Full, central | 12.74M m³ | 52.6% |
| Full, high (100k $/km, 3,000 $/km/yr) | 11.21M m³ | 46.3% |
| UWR, low | 8.45M m³ | 61.9% |
| UWR, central | 7.77M m³ | 56.9% |
| UWR, high | 6.78M m³ | 49.6% |

### Price and cost

Using central shared-road costs:

| Case | Positive-margin volume | Share |
|---|---:|---:|
| Full, base | 12.74M m³ | 52.6% |
| Full, price −20% | 1.14M m³ | 4.7% |
| Full, cost +20% | 2.02M m³ | 8.3% |
| UWR, base | 7.77M m³ | 56.9% |
| UWR, price −20% | 0.69M m³ | 5.0% |
| UWR, cost +20% | 1.34M m³ | 9.8% |

A 20% price reduction or a 20% cost increase removes most of the positive-margin volume. This is the economic fragility mechanism that can produce an AAC-to-harvest gap without changing the AAC or the legal land base.

## Interpretation

1. The screen supports the operational hypothesis: most nominal volume is marginal at plausible costs and prices once real road distances and shared access costs are used.
2. Shared-road accounting raises the positive-margin share relative to the one-road-per-block placeholder, because the flat CAD 37,500 per block overcharged blocks close to existing roads. It also penalises remote blocks more sharply.
3. The UWR dataset is not proportionally worse than the full dataset in this screen; both are around 53–57% positive.
4. The screen cannot attribute the 2019–2021 collapse. It shows a mechanism, not a year-by-year history.
5. The result is still dominated by placeholder prices, the maintenance assumption, and a notional mill pair. Actual mill capacity and dated prices will change the absolute numbers.

## Caveats

- Maintenance is an assumption, not a TSA-27 contract rate.
- Spurs are straight-line block-centroid-to-road distances; terrain and stream crossings are not costed.
- Existing roads carry no build cost; condition, season, and deactivation status are not modelled.
- Maintenance is allocated across all candidate users of a segment. If only the positive-margin subset operates, the per-cubic-metre share rises.
- Spurs are charged per block; adjacent blocks that could share one spur are not consolidated.
- Road activation timing and cutblock sequencing are not modelled.
- No mill curtailment dates, species/grade prices, or stumpage by grade.
- Eagle River's operating status is unverified. Downie alone is 2.1× AAC on design volume, so the aggregate capacity conclusion is robust, but the two-mill destination set is not.
- No fire/salvage, UWR timing, or historical land-base snapshots.
- The screen is a filter, not a schedule.

## Files

- `scripts/build_operational_screen.py`
- `scripts/build_shared_road_costs.py`
- `config/operational/road_cost_assumptions.csv`
- `runtime/operational_screen/screen_full_shared.csv`
- `runtime/operational_screen/screen_uwr_shared.csv`
- `runtime/operational_screen/road_costs_full_shared.csv`
- `runtime/operational_screen/road_costs_uwr_shared.csv`
- `reports/tsa27-shared-road-costs.md`

## Next

1. Add re-opening and closure timing for existing shared roads; new-spur activation is now modelled in the FHOPS pilot.
2. Add 2017–2026 road, fire, UWR, and cutblock snapshots.
3. Attribute the historical ratio year by year against the shared-road cost surface.
