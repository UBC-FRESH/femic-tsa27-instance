#!/usr/bin/env python3
"""Project WS4 road-network distances onto all operable TSA 27 blocks.

Uses the DRA route tables built by ``build_ws4_route_distances.py`` and WS4's
RouteNetwork to return least-length road routes from every operable block to the
two pilot mills. The connector from a block centroid to its nearest route vertex
is reported separately.

Usage:
    python scripts/build_ws4_route_all.py --dataset build/compiled --label full
    python scripts/build_ws4_route_all.py --dataset build/compiled_uwr --label uwr
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from scipy.spatial import cKDTree  # type: ignore[import-untyped]  # optional local/model dependency is not installed with stubs
from ws4.opt.engine import OptimizeConfig, Optimizer  # type: ignore[import-not-found]  # optional local/model dependency is not installed with stubs
from ws4.roads.network import RouteNetwork  # type: ignore[import-not-found]  # optional local/model dependency is not installed with stubs

ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT / "runtime/operational_pilot/route_network"
DESTINATIONS = ("destination.revelstoke", "destination.malakwa")


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "build/compiled")
    parser.add_argument("--label", default="full")
    parser.add_argument("--network", type=Path, default=NETWORK)
    parser.add_argument("--out", type=Path, default=NETWORK)
    return parser.parse_args()


def main() -> None:
    """Write block-to-mill road distances for all operable blocks."""
    args = parse_args()
    network_dir = args.network
    vertices = pd.read_csv(network_dir / "vertices.csv")
    segments = pd.read_csv(network_dir / "segments.csv")
    destinations = pd.read_csv(network_dir / "destinations.csv")
    blocks = gpd.read_file(ROOT / "data/ws4/blocks.geojson").to_crs(3005)
    blocks["x"] = blocks.geometry.centroid.x
    blocks["y"] = blocks.geometry.centroid.y
    optimizer = Optimizer.from_dataset(
        args.dataset,
        OptimizeConfig(years=200, iterations=1, seed=1),
    )
    candidates = optimizer.candidates()
    operable = {int(block) for block, chains in candidates.items() if chains}
    blocks = blocks[blocks.block_id.isin(operable)].copy()
    coords = vertices[["X", "Y"]].to_numpy()
    tree = cKDTree(coords)
    distances, indexes = tree.query(blocks[["x", "y"]].to_numpy())
    linkages = pd.DataFrame(
        {
            "block_id": blocks.block_id.astype(int).to_numpy(),
            "vertex_id": vertices.vertex_id.to_numpy()[indexes],
        }
    )
    network = RouteNetwork.from_tables(segments, destinations, linkages, vertices=vertices)
    rows = []
    for row, connector in zip(blocks.itertuples(index=False), distances, strict=True):
        block = int(row.block_id)
        for destination in DESTINATIONS:
            route = network.route(block, destination)
            if route is None:
                rows.append(
                    {
                        "block_id": block,
                        "destination": destination,
                        "route_km": None,
                        "connector_km": float(connector) / 1000.0,
                        "total_km": None,
                        "route_cost_per_m3": None,
                        "connector_cost_per_m3": None,
                        "total_cost_per_m3": None,
                    }
                )
            else:
                rows.append(
                    {
                        "block_id": block,
                        "destination": destination,
                        "route_km": route.length_m / 1000.0,
                        "connector_km": float(connector) / 1000.0,
                        "total_km": (route.length_m + float(connector)) / 1000.0,
                        "route_cost_per_m3": route.haul_cost,
                        "connector_cost_per_m3": float(connector) * 0.12 / 1000.0,
                        "total_cost_per_m3": route.haul_cost + float(connector) * 0.12 / 1000.0,
                    }
                )
    frame = pd.DataFrame(rows)
    out = args.out / f"route_distances_{args.label}_all.csv"
    frame.to_csv(out, index=False)
    summary = {
        "dataset": str(args.dataset),
        "blocks": len(blocks),
        "routes": len(frame),
        "routed": int(frame.total_km.notna().sum()),
        "unrouted": int(frame.total_km.isna().sum()),
        "median_revelstoke_km": float(
            frame[frame.destination == "destination.revelstoke"].total_km.median()
        ),
        "median_malakwa_km": float(
            frame[frame.destination == "destination.malakwa"].total_km.median()
        ),
    }
    (args.out / f"route_distances_{args.label}_all_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(out)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
