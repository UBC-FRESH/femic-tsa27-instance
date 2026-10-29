# TSA 27 shared-road build and maintenance costs

**Status:** structural shared-road screen, 29 October 2026. **Not a schedule, not an AAC, and not a historical attribution.**

## Purpose

The earlier full-estate screen charged every block a synthetic **one-road-per-block** allowance: CAD 25,000 build plus five years of CAD 2,500 maintenance. That placeholder ignored both the existing road network and the fact that neighbouring blocks share roads. This report replaces it with the actual DRA route segments each block uses, a new-access spur to the nearest truck-legal road, and maintenance allocated across all blocks that use the same segment.

## What changed

- Routes are the all-DRA WS4 least-cost routes. The strict truck-legal filter used for the 45-block pilot fragments the full network and produces 20–90 km artificial connectors for 44% of the estate, so it is not used for the full screen.
- Each route is decomposed into its DRA segments.
- A block-to-road connector is priced as a new spur.
- Existing DRA segments carry maintenance only; no second build charge is applied.
- Resource-road maintenance is shared by all blocks that use the segment, weighted by block volume.
- The 0.2% of routes that use trail/overgrown/decommissioned linework are flagged and carry a shared re-opening charge.

## Network facts

| Item | Full `compiled` | UWR `compiled_uwr` |
|---|---:|---:|
| Blocks with a route | 7,206 | 5,290 |
| Unique road segments used | 159,260 | 150,880 |
| Unique route length | 2,130.8 km | 1,995.7 km |
| Resource-road segments used | 153,744 | 145,368 |
| Non-truck segments used | 87 | 87 |
| Median block-to-road connector | 0.305 km | 0.234 km |
| P90 connector | 4.247 km | 3.791 km |
| Share with connector > 2 km | 20.8% | 17.7% |
| Share of routes fully truck-legal | 99.8% | 99.8% |

## Cost method

A new spur is charged as an amortised capital cost:

```
spur_5yr = connector_km * build_rate * CRF(5%, 20 years) * 5 years
CRF = 0.080243
```

Existing shared maintenance is:

```
segment_cost_5yr = length_km * maintenance_rate * 5 years
block_share = segment_cost_5yr * block_volume / segment_user_volume
```

The block road cost is the spur charge plus its share of every segment on its route. This avoids charging the same trunk road to every block.

## Coefficients

| Item | Low | Central | High | Basis |
|---|---:|---:|---:|---|
| Road build | 38,000 $/km | **60,000 $/km** | 100,000 $/km | FPInnovations Jade Road trial range 37,700–63,000 $/km; FERIC TR-28 D8H subgrade 32,960 $/km in 2026 CAD; central adds surfacing/culverts |
| Resource-road maintenance | 750 $/km/yr | **1,500 $/km/yr** | 3,000 $/km/yr | Planning assumption; no TSA-27-specific public per-kilometre rate found |
| Discount rate | — | 5% | — | Real public-sector discount convention |
| Spur life | — | 20 years | — | Planning assumption |
| Period | — | 5 years | — | Matches the five-year screen envelope |

The build rate is anchored in public FERIC/FPInnovations cost work. The maintenance rate is an explicit assumption and should be replaced with a local road-maintenance contract rate when one is available.

## Results

Central coefficients, shared-road accounting:

| Dataset | Positive-margin blocks | Positive-margin volume | Share | Selected in 5-year envelope | Median delivered cost | Median margin |
|---|---:|---:|---:|---:|---:|---:|
| Full `compiled` | 2,108 | 12.74M m³ | **52.6%** | 1.069M m³ | 78.11 $/m³ | 7.17 $/m³ |
| UWR `compiled_uwr` | 1,539 | 7.77M m³ | **56.9%** | 1.122M m³ | 78.21 $/m³ | 7.57 $/m³ |

Road-cost distribution, blocks with at least 100 m³:

| Dataset | Median road cost | P90 road cost | Median spur build | Share above 10 $/m³ |
|---|---:|---:|---:|---:|
| Full | 5.73 $/m³ | 69.12 $/m³ | 7,927 $ | 37.6% |
| UWR | 6.18 $/m³ | 68.15 $/m³ | 6,109 $ | 38.4% |

The median is low because most blocks sit close to existing roads. The long right tail is the access constraint: a block with a multi-kilometre spur carries a large fixed charge. The blocks selected within the five-year envelope carry 1.29 $/m³ (full) and 1.72 $/m³ (UWR) of shared road cost, because the ranking favours blocks near the existing network.

## Sensitivity

### Build and maintenance rates

| Dataset | Case | Positive volume | Share |
|---|---|---:|---:|
| Full | Low (38k $/km, 750 $/km/yr) | 13.86M m³ | 57.2% |
| Full | Central | 12.74M m³ | 52.6% |
| Full | High (100k $/km, 3,000 $/km/yr) | 11.21M m³ | 46.3% |
| UWR | Low | 8.45M m³ | 61.9% |
| UWR | Central | 7.77M m³ | 56.9% |
| UWR | High | 6.78M m³ | 49.6% |

### Price and cost

| Dataset | Case | Positive volume | Share |
|---|---|---:|---:|
| Full | Base | 12.74M m³ | 52.6% |
| Full | Price −20% | 1.14M m³ | 4.7% |
| Full | Cost +20% | 2.02M m³ | 8.3% |
| UWR | Base | 7.77M m³ | 56.9% |
| UWR | Price −20% | 0.69M m³ | 5.0% |
| UWR | Cost +20% | 1.34M m³ | 9.8% |

The result is still dominated by price and cost. Shared-road accounting raises the positive-margin share relative to the one-road-per-block placeholder, because CAD 37,500 per block was too high for the many blocks close to existing roads. It also penalises remote blocks more sharply than the flat placeholder did.

## Comparison with the placeholder

| Dataset | Placeholder volume | Placeholder share | Shared-road volume | Shared-road share |
|---|---:|---:|---:|---:|
| Full | 10.15M m³ | 41.9% | 12.74M m³ | 52.6% |
| UWR | 6.03M m³ | 44.2% | 7.77M m³ | 56.9% |

This is a cost-accounting change, not a new inventory or harvest constraint. It does not change the AAC or the caribou land base.

## Interpretation

1. Shared-road accounting makes the economic screen less punitive at the median, but the long-spur tail remains a real access barrier.
2. The UWR estate is not proportionally worse than the full estate in this screen; both are around 53–57% positive before price and cost shocks.
3. A 20% price reduction still removes almost all positive-margin volume. That fragility is the mechanism most consistent with the post-2017 AAC-to-harvest gap.
4. The screen is a static filter. It does not model road activation timing, cutblock sequencing, or the cost of reopening a road for a single entry.

## Caveats

- Maintenance is an assumption, not a TSA-27 contract rate.
- Spurs are straight-line block-centroid-to-road distances. Terrain, wetlands, and stream crossings are not costed.
- The full screen uses all DRA linework for connectivity; 0.2% of routes use non-truck segments and carry a re-opening charge.
- Existing roads carry no build cost, which assumes they are already open. Road condition, season, and deactivation status are not modelled.
- Maintenance is allocated across all candidate users of a segment. If only the positive-margin subset operates, the per-cubic-metre maintenance share rises.
- Spurs are charged per block; adjacent blocks that could share one spur are not consolidated.
- The two mills are notional public design-capacity destinations; no curtailment timing.
- No species/grade prices, no stumpage by grade, no road activation timing.
- The screen is a filter, not a schedule.

## Files

- `scripts/build_shared_road_costs.py`
- `config/operational/road_cost_assumptions.csv`
- `runtime/operational_screen/road_costs_full_shared.csv`
- `runtime/operational_screen/road_costs_uwr_shared.csv`
- `runtime/operational_screen/road_segments_full_shared.csv`
- `runtime/operational_screen/road_segments_uwr_shared.csv`
- `runtime/operational_screen/road_costs_full_shared_summary.json`
- `runtime/operational_screen/road_costs_uwr_shared_summary.json`
- `runtime/operational_screen/screen_full_shared.csv`
- `runtime/operational_screen/screen_uwr_shared.csv`
- `tests/test_build_shared_road_costs.py`

## Next

1. Add re-opening and closure timing for existing shared roads; new-spur activation is now modelled in the FHOPS pilot.
2. Add 2017–2026 road, fire, UWR, and cutblock snapshots.
3. Attribute the historical ratio year by year against the shared-road cost surface.
