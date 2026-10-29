# TSA 27 caribou even-flow result

**Status:** preliminary even-flow search result, 28 October 2026. **Not an AAC determination.** **Scenario:** S7 caribou / UWR no-harvest, 200-year horizon, 10-year periods.

## Configuration

| Item | Value |
|---|---|
| Dataset | `build/compiled_uwr` |
| Targets | `config/ws4/targets/evenflow_caribou.yaml` |
| Harvest account | `product.HarvestedVolume.managed.Total.CC` |
| Horizon | 200 years, 20 periods of 10 years |
| Even-flow band | ±5%, nonlinear, weight 10,000 |
| Flow reference | Period 1 |
| Harvest floor | 3,000,000 m³/period, soft, weight 0.1 |
| Ending inventory constraint | None |
| Solver display | 8 islands, 19,365 iterations, 948 s |

The 3,000,000 m³/period floor is **300,000 m³/year**, or **133% of the 225,000 m³/year AAC**. It is deliberately above the achievable level, so every period reports “below” while the flow term shapes the profile.

## Result

| Period | Harvest (m³) | Annual equivalent | Share of AAC | Inventory (m³) |
|---:|---:|---:|---:|---:|
| 1 | 1.66M | 166,000 | 74% | 13.5M |
| 2 | 1.58M | 158,000 | 70% | 13.9M |
| 3 | 1.58M | 158,000 | 70% | 14.3M |
| 4 | 1.58M | 158,000 | 70% | 14.8M |
| 5 | 1.58M | 158,000 | 70% | 15.1M |
| 6 | 1.58M | 158,000 | 70% | 15.4M |
| 7 | 1.58M | 158,000 | 70% | 15.5M |
| 8 | 1.58M | 158,000 | 70% | 15.5M |
| 9 | 1.71M | 171,000 | 76% | 15.3M |
| 10 | 1.73M | 173,000 | 77% | 15.1M |
| 11 | 1.74M | 174,000 | 77% | 14.8M |
| 12 | 1.74M | 174,000 | 77% | 14.4M |
| 13 | 1.74M | 174,000 | 77% | 14.1M |
| 14 | 1.74M | 174,000 | 77% | 13.8M |
| 15 | 1.74M | 174,000 | 77% | 13.5M |
| 16 | 1.75M | 175,000 | 78% | 13.2M |
| 17 | 1.74M | 174,000 | 77% | 12.9M |
| 18 | 1.74M | 174,000 | 77% | 12.7M |
| 19 | 1.74M | 174,000 | 77% | 12.5M |
| 20 | 1.74M | 174,000 | 77% | 12.2M |

Values are read from the live watcher frame and are rounded. The watcher’s `0.00 eval/s` is an island-mode display artifact; it is not a measured solve rate.

## Shape

The flow reference is period 1 at 1.66M m³:

- Period 2: 1.58M, about **−4.8%**
- Final period: 1.74M, about **+4.8%**

The profile is therefore within the ±5% band around the period-1 reference. The objective is 2.64M, which is almost entirely the soft-floor and flow penalties, not an infeasibility.

## Inventory behaviour

Managed inventory starts at **13.5M m³**, rises to **15.5M** by periods 7–8, then declines to **12.2M** at period 20.

- Final inventory is about **90% of the initial inventory**.
- The early hump is growth while harvest is below increment.
- The later decline is the even-flow harvest drawing down the accumulated stock.
- With no ending-inventory target, this is permitted; it is not a stock failure.

## Comparison with no-caribou

| Scenario | Harvest per period | Annual equivalent | Share of AAC | Final inventory |
|---|---:|---:|---:|---:|
| S8 no caribou | 2.21–2.44M | 221–244k | 98–108% | 18.6M |
| S7 caribou/UWR | 1.58–1.74M | 158–174k | 70–77% | 12.2M |

The UWR run is about **29% lower** in even-flow harvest:

```text
1.58 / 2.21 = 0.715
1.74 / 2.44 = 0.713
```

The S8 inventory starts at 23.6M and ends at 18.6M, about 79% of its initial level. The S7 inventory ends at about 90% of its initial level.

## Interpretation

1. The caribou scenario has found a stable near-AAC-relative even flow of about **1.7M m³/period**, or **~170,000 m³/year**.
2. That is roughly **76% of the current AAC**, not 100%.
3. The soft 3M floor is above the achievable level; it is a pull, not the answer. The actual ceiling is closer to **1.7–1.8M m³/period** and should be found with a level search, not by treating 3M as a target.
4. The preliminary UWR effect is **about −29% on even-flow harvest**.

## Important caveat: this is not yet a clean caribou attribution

The comparison uses different datasets:

- `build/compiled` has the full managed inventory: **24.2M m³**.
- `build/compiled_uwr` has the UWR-filtered inventory: **13.7M m³**.

The UWR dataset removes about **44% of the managed inventory**, while the even-flow harvest is about **29% lower**. The difference therefore includes both the removed UWR land base and the policy constraint.

A clean counterfactual requires a **same-land-base UWR variant**: keep the UWR blocks in the dataset, give them no-harvest twin tracks, and run the same targets. That isolates the policy from the inventory removal.

This result should also be compared against the TSR evidence:

- TSR4 incremental caribou reserve add-back: **+8.4% short/mid, +2.2% long-term**.
- TSR4 mature/old biodiversity removal in caribou LUs: **+4.0% short/mid, +2.5% long-term**.
- TSR2 all-caribou removal: **+8.2% long-term**.
- Current WS4 first-period UWR capacity comparison: **−43.6%**.

Those are different questions and different baselines. The even-flow result is more relevant to AAC than the first-period capacity comparison, but it is still not a TSR-equivalent AAC determination.

## Recommended next tests

1. **Level search:** test constant even-flow floors around 1.6M, 1.7M, 1.8M, and 1.9M m³/period.
2. **Same-land-base counterfactual:** UWR blocks present but ineligible, versus eligible.
3. **Ending-inventory sensitivity:** add 80% and 100% terminal inventory floors.
4. **Seed/island robustness:** repeat with at least three seeds and a longer horizon.
5. **No-caribou reference on the same targets:** compare against S8 at identical even-flow and inventory settings.

## Provenance

- Targets: `config/ws4/targets/evenflow_caribou.yaml`
- Dataset: `build/compiled_uwr`
- Scenario registry: `config/ws4/scenario_registry.yaml`
- Related reports:
- `reports/tsa27-caribou-attribution.md`
- `reports/tsa27-interim-attribution.md`
- `reports/tsa27-operational-pilot.md`
- Watcher frame supplied 2026-10-28; this report records the displayed result, not a saved run directory.
