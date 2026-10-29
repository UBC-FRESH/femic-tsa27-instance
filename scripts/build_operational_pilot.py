#!/usr/bin/env python3
"""Build a TSA 27 tactical-operational pilot for FHOPS.

This is a structural pilot, not a historical reconstruction. It selects a deterministic
spatial cluster of operable managed blocks, assigns the ground-based feller-buncher /
grapple-skidder system, creates five annual periods, two notional mill destinations, and a
documented cost/revenue ledger. Replace the placeholder prices and rates before drawing
policy conclusions.

Usage:
    python scripts/build_operational_pilot.py
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from ws4.opt.engine import OptimizeConfig, Optimizer  # type: ignore[import-not-found]  # local checkout is not installed as a typed package
from ws4.sim.engine import Simulator  # type: ignore[import-not-found]  # local checkout is not installed as a typed package

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "build/compiled"
TARGETS = ROOT / "config/ws4/targets/evenflow_no_caribou.yaml"
OUT = ROOT / "runtime/operational_pilot"

# Cost and price assumptions are CAD 2026 placeholders for a structural pilot. They are
# deliberately explicit so sensitivity runs can replace one line at a time.
ASSUMPTIONS = {
    "harvest_variable_per_m3": 32.0,
    "planning_per_m3": 1.5,
    "layout_per_m3": 0.5,
    "stumpage_per_m3": 20.0,
    "loading_per_m3": 8.0,
    "unloading_per_m3": 4.0,
    "contingency_per_m3": 2.0,
    "planning_fixed_per_block": 3000.0,
    "layout_fixed_per_block": 4000.0,
    "machine_move_fixed_per_block": 2500.0,
    "haul_per_m3_km": 0.12,
    "sawlog_price_per_m3": 95.0,
    "pulp_price_per_m3": 45.0,
}
SAWLOG = {"CE", "CW", "FDI", "HW"}
PERIODS = [
    ("2027-P1", "2027-01-01", "2027-12-31", 365, 8760, 1.0),
    ("2028-P1", "2028-01-01", "2028-12-31", 366, 8760, 0.97),
    ("2029-P1", "2029-01-01", "2029-12-31", 365, 8760, 0.94),
    ("2030-P1", "2030-01-01", "2030-12-31", 365, 8760, 0.91),
    ("2031-P1", "2031-01-01", "2031-12-31", 365, 8760, 0.88),
]
MILLS = {
    "mill_revelstoke": (51.0000, -118.2000),
    "mill_malakwa": (50.96, -118.74),
}


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocks", type=int, default=200)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument(
        "--routes",
        type=Path,
        default=ROOT / "runtime/operational_pilot/route_network/route_distances_ws4.csv",
    )
    parser.add_argument(
        "--road-costs",
        type=Path,
        default=ROOT / "runtime/operational_screen/road_costs_full_shared.csv",
    )
    parser.add_argument(
        "--mills",
        choices=("all", "revelstoke", "malakwa"),
        default="all",
        help="Restrict the destination set for a mill-capacity counterfactual.",
    )
    return parser.parse_args()


def block_volumes(sim: Simulator, block: int) -> tuple[float, float]:
    """Return sawlog and pulp volume for a block's year-0 clear-cut.

    Parameters
    ----------
    sim : Simulator
        Compiled WS4 simulator.
    block : int
        Block identifier.

    Returns
    -------
    tuple of float
        Sawlog and pulp volume in cubic metres.
    """
    products = sim.block_chain_products(block, (("CC", 0),))
    sawlog = 0.0
    pulp = 0.0
    for (_year, label), value in products.items():
        if not label.startswith("product.HarvestedVolume.managed.") or not label.endswith(".CC"):
            continue
        suffix = label.removeprefix("product.HarvestedVolume.managed.").removesuffix(".CC")
        if suffix == "Total":
            continue
        if suffix in SAWLOG:
            sawlog += float(value)
        else:
            pulp += float(value)
    return sawlog, pulp


def main() -> None:
    """Write the scenario and cost ledger."""
    args = parse_args()
    optimizer = Optimizer.from_dataset(
        DATASET,
        OptimizeConfig(years=200, targets_path=str(TARGETS), iterations=1, seed=1),
    )
    candidates = optimizer.candidates()
    operable = {int(block) for block, chains in candidates.items() if chains}
    blocks = gpd.read_file(ROOT / "data/ws4/blocks.geojson").to_crs(3005)
    blocks["x"] = blocks.geometry.centroid.x
    blocks["y"] = blocks.geometry.centroid.y
    fragments = pd.read_parquet(DATASET / "fragments.parquet")
    area = fragments.groupby("block_id")["area_ha"].sum()
    age = fragments.groupby("block_id")["age"].min()
    sim = Simulator.from_dataset(DATASET)
    route_km: dict[tuple[int, str], float] = {}
    route_cost: dict[tuple[int, str], float] = {}
    road_cost: dict[int, dict[str, float]] = {}
    if args.road_costs.is_file():
        road_frame = pd.read_csv(args.road_costs)
        for road_row in road_frame.itertuples(index=False):
            road_cost[int(str(road_row.block_id))] = {
                "road_cost_per_m3": float(str(road_row.road_cost_per_m3)),
                "road_cost_5yr": float(str(road_row.road_cost_5yr)),
                "spur_build_5yr": float(str(road_row.spur_build_5yr)),
                "shared_maintenance_5yr": float(str(road_row.shared_maintenance_5yr)),
                "shared_upgrade_5yr": float(str(road_row.shared_upgrade_5yr)),
            }
    if args.routes.is_file():
        route_frame = pd.read_csv(args.routes)
        for route in route_frame.itertuples(index=False):
            if pd.notna(route.total_km):
                route_km[(int(str(route.block_id)), str(route.destination))] = float(
                    str(route.total_km)
                )
            if hasattr(route, "total_cost_per_m3") and pd.notna(route.total_cost_per_m3):
                route_cost[(int(str(route.block_id)), str(route.destination))] = float(
                    str(route.total_cost_per_m3)
                )

    if args.mills == "all":
        active_mills = dict(MILLS)
    elif args.mills == "revelstoke":
        active_mills = {"mill_revelstoke": MILLS["mill_revelstoke"]}
    else:
        active_mills = {"mill_malakwa": MILLS["mill_malakwa"]}

    transformer = Transformer.from_crs(4326, 3005, always_xy=True)
    mills = {name: transformer.transform(lon, lat) for name, (lat, lon) in active_mills.items()}
    mill_xy = pd.DataFrame([{"mill": name, "x": x, "y": y} for name, (x, y) in mills.items()])
    anchor = mill_xy.iloc[0]
    blocks["distance_to_anchor_km"] = (
        (blocks.x - anchor.x) ** 2 + (blocks.y - anchor.y) ** 2
    ) ** 0.5 / 1000.0
    blocks = blocks[blocks.block_id.isin(operable)].copy()
    blocks = blocks.sort_values(["distance_to_anchor_km", "block_id"]).head(args.blocks)

    # Row dictionaries are heterogeneous by design; values are normalised before use.
    selected: list[dict[str, Any]] = []
    for row in blocks.itertuples(index=False):
        block = int(row.block_id)
        sawlog, pulp = block_volumes(sim, block)
        if sawlog + pulp <= 0.0:
            continue
        block_area = float(area.get(block, 0.0))
        if block_area <= 0.0:
            continue
        road_cost_row = road_cost.get(block)
        if road_cost_row is None:
            raise SystemExit(
                f"no shared-road cost for block {block}; run scripts/build_shared_road_costs.py"
            )
        selected.append(
            {
                "block_id": block,
                "area_ha": block_area,
                "age": int(age.get(block, 0)),
                "sawlog_m3": sawlog,
                "pulp_m3": pulp,
                "sawlog_yield": sawlog / block_area,
                "pulp_yield": pulp / block_area,
                "x": float(row.x),
                "y": float(row.y),
                "distance_km": float(row.distance_to_anchor_km),
                "road_cost_per_m3": road_cost_row["road_cost_per_m3"],
                "road_cost_5yr": road_cost_row["road_cost_5yr"],
                "spur_build_5yr": road_cost_row["spur_build_5yr"],
                "shared_maintenance_5yr": road_cost_row["shared_maintenance_5yr"],
                "shared_upgrade_5yr": road_cost_row["shared_upgrade_5yr"],
                "shared_road_cost_per_m3": (
                    road_cost_row["shared_maintenance_5yr"] + road_cost_row["shared_upgrade_5yr"]
                )
                / (sawlog + pulp),
            }
        )
    if not selected:
        raise SystemExit("no blocks with year-0 clear-cut products")

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    total_sawlog = sum(float(row["sawlog_m3"]) for row in selected)
    total_pulp = sum(float(row["pulp_m3"]) for row in selected)
    # Keep the pilot demand envelope inside the selected volume so the first model is feasible;
    # this is a structural pilot, not a full AAC test.
    per_year = min(225000.0, 0.8 * (total_sawlog + total_pulp) / len(PERIODS))
    sawlog_share = total_sawlog / (total_sawlog + total_pulp)
    demand_sawlog = per_year * sawlog_share
    demand_pulp = per_year - demand_sawlog

    variable = sum(
        ASSUMPTIONS[key]
        for key in (
            "harvest_variable_per_m3",
            "planning_per_m3",
            "layout_per_m3",
            "stumpage_per_m3",
            "loading_per_m3",
            "unloading_per_m3",
            "contingency_per_m3",
        )
    )
    fixed = sum(
        ASSUMPTIONS[key]
        for key in (
            "planning_fixed_per_block",
            "layout_fixed_per_block",
            "machine_move_fixed_per_block",
        )
    )
    weighted_road_cost = sum(
        float(row["road_cost_per_m3"]) * (float(row["sawlog_m3"]) + float(row["pulp_m3"]))
        for row in selected
    ) / (total_sawlog + total_pulp)
    weighted_spur_cost = sum(float(row["spur_build_5yr"]) for row in selected) / (
        total_sawlog + total_pulp
    )
    weighted_shared_road_cost = sum(
        float(row["shared_road_cost_per_m3"]) * (float(row["sawlog_m3"]) + float(row["pulp_m3"]))
        for row in selected
    ) / (total_sawlog + total_pulp)

    lines: list[str] = []
    lines += [
        "name: tsa27-operational-pilot",
        "planning_level: tactical_operational",
        'schema_version: "0.1.0"',
        'specification_version: "0.1.0"',
        "purpose: >",
        "  Structural TSA 27 pilot for operational accessibility and cost/revenue testing.",
        "  Prices and rates are explicit placeholders, not validated local values.",
        "units:",
        "  area: ha",
        "  volume: m3",
        "  harvest_capacity: m3_per_period",
        "  transport_capacity: m3_per_period",
        "  cost: CAD_2026",
        "  value: CAD_2026_per_m3",
        "  discount_rate: effective_annual_fraction",
        "  distance: km",
        "periods:",
    ]
    for sequence, (period_id, start, end, days, hours, discount) in enumerate(PERIODS, start=1):
        lines += [
            f"  - period_id: {period_id}",
            "    level: year",
            f"    sequence: {sequence}",
            f'    start_date: "{start}"',
            f'    end_date: "{end}"',
            f"    duration_days: {days}",
            f"    available_hours: {hours}",
            f"    discount_factor: {discount}",
            "    season_tags: [year]",
        ]
    lines += [
        "products:",
        "  - product_id: sawlog",
        "    species_group: mixed_conifer",
        "    grade: sawlog",
        "  - product_id: pulp",
        "    species_group: mixed_conifer",
        "    grade: pulp",
        "planning_units:",
    ]
    for row in selected:
        block = int(row["block_id"])
        lines += [
            f"  - block_id: B{block}",
            f"    gross_area_ha: {float(row['area_ha']):.6f}",
            f"    operable_area_ha: {float(row['area_ha']):.6f}",
            "    forest_class: interior",
            "    initial_state: mature",
            "    product_yields_m3_per_ha:",
            f"      sawlog: {float(row['sawlog_yield']):.6f}",
            f"      pulp: {float(row['pulp_yield']):.6f}",
        ]
    lines += ["harvest_system_options:"]
    for period_id, *_ in PERIODS:
        for row in selected:
            block = int(row["block_id"])
            lines += [
                f"  - option_id: B{block}__ground_fb_skid__{period_id}",
                f"    block_id: B{block}",
                "    system_id: ground_fb_skid",
                f"    period_id: {period_id}",
                "    eligible: true",
                "    min_area_ha: 0.0",
                f"    max_area_ha: {float(row['area_ha']):.6f}",
                f"    variable_cost_per_m3: {variable:.3f}",
                f"    fixed_cost: {fixed:.3f}",
                "    productivity_m3_per_period: 1000000.0",
            ]
    lines += ["fleet_capacity:"]
    for period_id, *_ in PERIODS:
        lines += [
            "  - system_id: ground_fb_skid",
            f"    period_id: {period_id}",
            "    capacity_m3: 225000.0",
            "    capacity_hours: 8760.0",
        ]
    lines += ["facilities:"]
    for mill in active_mills:
        lines += [
            f"  - facility_id: {mill}",
            "    facility_type: sawmill",
            "    accepted_products: [sawlog, pulp]",
        ]
    lines += ["facility_demand:"]
    for period_id, *_ in PERIODS:
        for product, target in (("sawlog", demand_sawlog), ("pulp", demand_pulp)):
            price = (
                ASSUMPTIONS["sawlog_price_per_m3"]
                if product == "sawlog"
                else ASSUMPTIONS["pulp_price_per_m3"]
            )
            for mill in active_mills:
                lines += [
                    f"  - facility_id: {mill}",
                    f"    product_id: {product}",
                    f"    period_id: {period_id}",
                    "    minimum_m3: 0.0",
                    f"    target_m3: {target / len(active_mills):.3f}",
                    f"    maximum_m3: {target / len(active_mills):.3f}",
                    f"    value_per_m3: {price:.3f}",
                ]
    lines += ["transport_arcs:"]
    for period_id, *_ in PERIODS:
        for row in selected:
            block = int(row["block_id"])
            for mill, (mx, my) in mills.items():
                route_name = "destination." + mill.removeprefix("mill_")
                distance = route_km.get((block, route_name))
                if distance is None:
                    distance = math.hypot(float(row["x"]) - mx, float(row["y"]) - my) / 1000.0
                arc_cost = route_cost.get((block, route_name))
                if arc_cost is None:
                    arc_cost = distance * ASSUMPTIONS["haul_per_m3_km"]
                arc_cost += float(row["shared_road_cost_per_m3"])
                for product in ("sawlog", "pulp"):
                    lines += [
                        f"  - arc_id: B{block}__{mill}__{product}__{period_id}",
                        f"    origin_id: B{block}",
                        f"    destination_id: {mill}",
                        f"    product_id: {product}",
                        "    mode: truck",
                        f"    period_id: {period_id}",
                        f"    cost_per_m3: {arc_cost:.4f}",
                        "    capacity_m3: 100000.0",
                    ]
    lines += ["roads:"]
    for row in selected:
        block = int(row["block_id"])
        lines += [
            f"  - road_id: spur_B{block}",
            f"    build_cost: {float(row['spur_build_5yr']):.2f}",
            "    maintenance_cost_per_period: 0.0",
            f"    earliest_period_id: {PERIODS[0][0]}",
            "    capacity_m3_per_period: 100000.0",
        ]
    lines += ["block_road_access:"]
    for row in selected:
        block = int(row["block_id"])
        lines += [
            f"  - block_id: B{block}",
            f"    road_id: spur_B{block}",
        ]
    scenario = out / "scenario.yaml"
    scenario.write_text("\n".join(lines) + "\n")
    pd.DataFrame(
        [
            {
                "block_id": int(row["block_id"]),
                "volume_m3": float(row["sawlog_m3"]) + float(row["pulp_m3"]),
                "road_cost_per_m3": float(row["road_cost_per_m3"]),
                "road_cost_5yr": float(row["road_cost_5yr"]),
                "spur_build_5yr": float(row["spur_build_5yr"]),
                "shared_maintenance_5yr": float(row["shared_maintenance_5yr"]),
                "shared_upgrade_5yr": float(row["shared_upgrade_5yr"]),
            }
            for row in selected
        ]
    ).to_csv(out / "selected_road_costs.csv", index=False)

    with (out / "cost_assumptions.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["category", "basis", "value_cad_2026"])
        for key, value in ASSUMPTIONS.items():
            writer.writerow(
                [key, "per_m3" if key.endswith("per_m3") else "per_block_or_period", value]
            )
        writer.writerow(
            [
                "aggregate_variable_per_m3",
                "harvest+planning+layout+stumpage+loading+unloading+contingency",
                f"{variable:.3f}",
            ]
        )
        writer.writerow(
            ["aggregate_fixed_per_block", "planning+layout+machine movement", f"{fixed:.3f}"]
        )
        writer.writerow(["road_cost_source", "shared-road screen", str(args.road_costs)])
        writer.writerow(
            [
                "aggregate_road_cost_per_m3",
                "spur+shared maintenance (full ledger)",
                f"{weighted_road_cost:.3f}",
            ]
        )
        writer.writerow(
            [
                "aggregate_spur_cost_per_m3",
                "amortised spur in road module",
                f"{weighted_spur_cost:.3f}",
            ]
        )
        writer.writerow(
            [
                "aggregate_shared_road_cost_per_m3",
                "shared maintenance/upgrade in transport arcs",
                f"{weighted_shared_road_cost:.3f}",
            ]
        )
        writer.writerow(["selected_blocks", "pilot", len(selected)])
        writer.writerow(["available_sawlog_m3", "year-0 clear-cut", f"{total_sawlog:.1f}"])
        writer.writerow(["available_pulp_m3", "year-0 clear-cut", f"{total_pulp:.1f}"])
        writer.writerow(["aac_per_year", "pilot demand envelope", f"{per_year:.1f}"])
    (out / "README.md").write_text(
        "# TSA 27 operational pilot\n\n"
        "Structural pilot generated by `scripts/build_operational_pilot.py`. Prices and rates\n"
        "are explicit placeholders; they are not validated local costs or mill-gate prices.\n\n"
        f"- blocks: {len(selected)}\n"
        f"- sawlog available (year 0): {total_sawlog:,.0f} m3\n"
        f"- pulp available (year 0): {total_pulp:,.0f} m3\n"
        f"- demand envelope: {per_year:,.0f} m3/year split by available product mix\n"
        f"- variable cost: {variable:.2f} CAD/m3; fixed: {fixed:.2f} CAD/block\n"
        "- amortised spur build is in the road module; shared road maintenance is in "
        "transport arcs\n"
        "- scenario: `scenario.yaml`\n"
        "- assumptions: `cost_assumptions.csv`\n"
    )
    print(
        f"wrote {scenario}: {len(selected)} blocks, "
        f"sawlog {total_sawlog:.0f}, pulp {total_pulp:.0f}"
    )


if __name__ == "__main__":
    main()
