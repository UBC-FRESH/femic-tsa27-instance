#!/usr/bin/env python3
"""Full-TSA economic accessibility screen for the TSA 27 operational question.

This is a reduced-form screen, not a tactical schedule. It asks which currently operable
managed blocks have a positive delivered margin under explicit cost and price assumptions,
and how much volume survives. It is the full-estate companion to the 45-block FHOPS pilot.

Usage:
    python scripts/build_operational_screen.py --dataset build/compiled --label full
    python scripts/build_operational_screen.py --dataset build/compiled_uwr --label uwr
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
ASSUMPTIONS = {
    "harvest": 32.0,
    "planning": 1.5,
    "layout": 0.5,
    "stumpage": 20.0,
    "loading": 8.0,
    "unloading": 4.0,
    "contingency": 2.0,
    "fixed_planning": 3000.0,
    "fixed_layout": 4000.0,
    "fixed_move": 2500.0,
    "road_build": 25000.0,
    "road_maintenance": 2500.0,
    "haul_per_m3_km": 0.12,
    "sawlog_price": 95.0,
    "pulp_price": 45.0,
}
SAWLOG = {"CE", "CW", "FDI", "HW"}
MILLS = {"revelstoke": (-118.2, 51.0), "malakwa": (-118.74, 50.96)}


def parse_args() -> argparse.Namespace:
    """Return command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "build/compiled")
    parser.add_argument("--label", default="full")
    parser.add_argument("--years", type=int, default=200)
    parser.add_argument("--out", type=Path, default=ROOT / "runtime/operational_screen")
    parser.add_argument("--price-factor", type=float, default=1.0)
    parser.add_argument("--cost-factor", type=float, default=1.0)
    parser.add_argument("--routes", type=Path, default=None)
    parser.add_argument("--road-costs", type=Path, default=None)
    return parser.parse_args()


def block_products(sim: Simulator, block: int) -> tuple[float, float]:
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
    """Run the screen and write block-level and summary CSVs."""
    args = parse_args()
    optimizer = Optimizer.from_dataset(
        args.dataset,
        OptimizeConfig(years=args.years, iterations=1, seed=1),
    )
    candidates = optimizer.candidates()
    operable = {int(block) for block, chains in candidates.items() if chains}
    blocks = gpd.read_file(ROOT / "data/ws4/blocks.geojson").to_crs(3005)
    blocks["x"] = blocks.geometry.centroid.x
    blocks["y"] = blocks.geometry.centroid.y
    fragments = pd.read_parquet(args.dataset / "fragments.parquet")
    area = fragments.groupby("block_id")["area_ha"].sum()
    age = fragments.groupby("block_id")["age"].min()
    sim = Simulator.from_dataset(args.dataset)
    route_path = args.routes or (
        ROOT / "runtime/operational_pilot/route_network" / f"route_distances_{args.label}_all.csv"
    )
    route_km: dict[tuple[int, str], float] = {}
    route_cost: dict[tuple[int, str], float] = {}
    if route_path.is_file():
        route_frame = pd.read_csv(route_path)
        for route in route_frame.itertuples(index=False):
            if pd.notna(route.total_km):
                route_km[(int(str(route.block_id)), str(route.destination))] = float(
                    str(route.total_km)
                )
            if hasattr(route, "total_cost_per_m3") and pd.notna(route.total_cost_per_m3):
                route_cost[(int(str(route.block_id)), str(route.destination))] = float(
                    str(route.total_cost_per_m3)
                )

    road_costs: dict[int, dict[str, Any]] = {}
    if args.road_costs is not None and args.road_costs.is_file():
        road_frame = pd.read_csv(args.road_costs)
        for road_row in road_frame.itertuples(index=False):
            road_costs[int(str(road_row.block_id))] = {
                "road_cost_5yr": float(str(road_row.road_cost_5yr)),
                "spur_build_5yr": float(str(road_row.spur_build_5yr)),
                "shared_maintenance_5yr": float(str(road_row.shared_maintenance_5yr)),
                "shared_upgrade_5yr": float(str(road_row.shared_upgrade_5yr)),
                "route_truck_legal": bool(road_row.route_truck_legal),
                "non_truck_km": float(str(road_row.non_truck_km)),
            }

    transformer = Transformer.from_crs(4326, 3005, always_xy=True)
    mills = {name: transformer.transform(lon, lat) for name, (lon, lat) in MILLS.items()}
    blocks = blocks[blocks.block_id.isin(operable)].copy()

    rows: list[dict[str, object]] = []
    for row in blocks.itertuples(index=False):
        block = int(row.block_id)
        sawlog, pulp = block_products(sim, block)
        volume = sawlog + pulp
        block_area = float(area.get(block, 0.0))
        if volume <= 0.0 or block_area <= 0.0:
            continue
        route_distances = [route_km.get((block, f"destination.{name}")) for name in mills]
        available = [value for value in route_distances if value is not None]
        if available:
            distance = min(available)
        else:
            distance = min(
                math.hypot(float(row.x) - mx, float(row.y) - my) / 1000.0
                for mx, my in mills.values()
            )
        route_costs = [route_cost.get((block, f"destination.{name}")) for name in mills]
        cost_values = [value for value in route_costs if value is not None]
        haul = min(cost_values) if cost_values else distance * ASSUMPTIONS["haul_per_m3_km"]
        if road_costs:
            road_entry = road_costs.get(block)
            if road_entry is None:
                continue
            road_cost = float(road_entry["road_cost_5yr"])
            spur_cost = float(road_entry["spur_build_5yr"])
            shared_maintenance = float(road_entry["shared_maintenance_5yr"])
            shared_upgrade = float(road_entry["shared_upgrade_5yr"])
            route_truck_legal = bool(road_entry["route_truck_legal"])
            non_truck_km = float(road_entry["non_truck_km"])
        else:
            road_cost = ASSUMPTIONS["road_build"] + 5.0 * ASSUMPTIONS["road_maintenance"]
            spur_cost = ASSUMPTIONS["road_build"]
            shared_maintenance = 5.0 * ASSUMPTIONS["road_maintenance"]
            shared_upgrade = 0.0
            route_truck_legal = True
            non_truck_km = 0.0
        fixed = (
            ASSUMPTIONS["fixed_planning"]
            + ASSUMPTIONS["fixed_layout"]
            + ASSUMPTIONS["fixed_move"]
            + road_cost
        )
        variable = sum(
            ASSUMPTIONS[key]
            for key in (
                "harvest",
                "planning",
                "layout",
                "stumpage",
                "loading",
                "unloading",
                "contingency",
            )
        )
        revenue = (
            sawlog * ASSUMPTIONS["sawlog_price"] + pulp * ASSUMPTIONS["pulp_price"]
        ) * args.price_factor
        cost = (volume * (variable + haul) + fixed) * args.cost_factor
        margin = revenue - cost
        rows.append(
            {
                "block_id": block,
                "area_ha": block_area,
                "age": int(age.get(block, 0)),
                "sawlog_m3": sawlog,
                "pulp_m3": pulp,
                "volume_m3": volume,
                "distance_km": distance,
                "haul_per_m3": haul,
                "road_cost_5yr": road_cost,
                "road_cost_per_m3": road_cost / volume,
                "spur_build_5yr": spur_cost,
                "shared_maintenance_5yr": shared_maintenance,
                "shared_upgrade_5yr": shared_upgrade,
                "route_truck_legal": route_truck_legal,
                "non_truck_km": non_truck_km,
                "revenue": revenue,
                "cost": cost,
                "margin": margin,
                "margin_per_m3": margin / volume,
            }
        )

    frame = pd.DataFrame(rows).sort_values("margin_per_m3", ascending=False)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / f"screen_{args.label}.csv", index=False)

    positive = frame[frame.margin > 0.0].copy()
    annual_cap = 225000.0
    period_cap = annual_cap * 5.0  # five-year pilot-equivalent envelope
    cumulative = positive["volume_m3"].cumsum()
    selected = positive[cumulative <= period_cap].copy()
    summary = {
        "label": args.label,
        "route_source": str(route_path),
        "price_factor": args.price_factor,
        "cost_factor": args.cost_factor,
        "dataset": str(args.dataset),
        "road_cost_source": str(args.road_costs) if args.road_costs else "placeholder",
        "operable_blocks": len(frame),
        "total_volume_m3": round(float(frame.volume_m3.sum()), 1),
        "positive_margin_blocks": len(positive),
        "positive_margin_volume_m3": round(float(positive.volume_m3.sum()), 1),
        "positive_margin_share": round(float(positive.volume_m3.sum() / frame.volume_m3.sum()), 3),
        "five_year_aac_envelope_m3": period_cap,
        "selected_within_envelope_m3": round(float(selected.volume_m3.sum()), 1),
        "median_delivered_cost_per_m3": round(
            float((positive.cost / positive.volume_m3).median()), 2
        ),
        "median_margin_per_m3": round(float(positive.margin_per_m3.median()), 2),
        "p10_margin_per_m3": round(float(positive.margin_per_m3.quantile(0.1)), 2),
        "p90_margin_per_m3": round(float(positive.margin_per_m3.quantile(0.9)), 2),
    }
    with (out / f"screen_{args.label}_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary))
        writer.writeheader()
        writer.writerow(summary)
    print(summary)


if __name__ == "__main__":
    main()
