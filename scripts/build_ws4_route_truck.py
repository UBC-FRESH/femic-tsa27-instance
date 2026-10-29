#!/usr/bin/env python3
"""Build a truck-legal DRA route network for the TSA 27 pilot.

Drops trail/skid/overgrown/decommissioned linework, keeps the connected component that
contains the pilot blocks, snaps blocks and mills to that component, and writes WS4 route
tables plus class-based haul distances/costs.

Usage:
    python scripts/build_ws4_route_truck.py
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.sparse import coo_matrix  # type: ignore[import-untyped]  # optional local/model dependency is not installed with stubs
from scipy.sparse.csgraph import connected_components  # type: ignore[import-untyped]  # optional local/model dependency is not installed with stubs
from scipy.spatial import cKDTree  # type: ignore[import-untyped]  # optional local/model dependency is not installed with stubs
from shapely.ops import nearest_points, unary_union
from ws4.roads.network import RouteNetwork  # type: ignore[import-not-found]  # optional local/model dependency is not installed with stubs

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runtime/operational_pilot/route_network/source"
OUT = ROOT / "runtime/operational_pilot/route_network_truck"
MILLS = {
    "destination.revelstoke": (-118.2, 51.0),
    "destination.malakwa": (-118.74, 50.96),
}
EXCLUDED_CLASSES = {"trail", "skid", "water", "ferry", "runway", "alleyway"}
EXCLUDED_SURFACES = {"decommissioned", "overgrown"}


def haul_rate(road_class: object, surface: object) -> float:
    """Return a class-based haul rate in CAD/m3/km.

    Parameters
    ----------
    road_class : object
        DRA road class value.
    surface : object
        DRA road surface value.

    Returns
    -------
    float
        Haul rate in CAD per cubic metre per kilometre.
    """
    road = str(road_class or "").lower()
    surf = str(surface or "").lower()
    if road in {"highway", "freeway", "arterial", "collector"}:
        return 0.06
    if surf == "paved":
        return 0.10
    if road in {"resource", "restricted", "strata", "recreation", "yield"} or surf in {
        "rough",
        "loose",
        "seasonal",
        "unknown",
    }:
        return 0.16
    return 0.16


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", type=Path, default=ROOT / "runtime/operational_pilot/scenario.yaml"
    )
    parser.add_argument("--out", type=Path, default=OUT)
    return parser.parse_args()


def main() -> None:
    """Build the filtered network and route the pilot blocks."""
    import yaml

    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    pages = sorted(SOURCE.glob("dra_*.json"))
    frames = [gpd.read_file(path) for path in pages]
    roads = gpd.GeoDataFrame(
        pd.concat(frames, ignore_index=True),
        geometry="geometry",
        crs=frames[0].crs,
    ).to_crs(3005)
    roads = roads[
        (roads["FEATURE_TYPE"] == "Road")
        & (~roads["ROAD_CLASS"].isin(EXCLUDED_CLASSES))
        & (~roads["ROAD_SURFACE"].isin(EXCLUDED_SURFACES))
    ].copy()
    print(f"truck-legal DRA features: {len(roads):,}")
    union = unary_union(roads.geometry.tolist())

    nodes: dict[tuple[int, int], int] = {}
    edges: list[tuple[int, int, float, float]] = []
    for road in roads.itertuples(index=False):
        rate = haul_rate(road.ROAD_CLASS, road.ROAD_SURFACE)
        lines = (
            list(road.geometry.geoms)
            if road.geometry.geom_type == "MultiLineString"
            else [road.geometry]
        )
        for line in lines:
            for a, c in itertools.pairwise(line.coords):
                ka = (round(a[0]), round(a[1]))
                kc = (round(c[0]), round(c[1]))
                if ka == kc:
                    continue
                nodes.setdefault(ka, len(nodes))
                nodes.setdefault(kc, len(nodes))
                edges.append(
                    (
                        nodes[ka],
                        nodes[kc],
                        float(np.hypot(a[0] - c[0], a[1] - c[1])),
                        rate,
                    )
                )
    n = len(nodes)
    rows = [edge[0] for edge in edges] + [edge[1] for edge in edges]
    cols = [edge[1] for edge in edges] + [edge[0] for edge in edges]
    data = [edge[2] for edge in edges] * 2
    graph = coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
    count, labels = connected_components(graph, directed=False)
    coords = np.array(list(nodes.keys()))
    tree = cKDTree(coords)

    scenario = yaml.safe_load(args.scenario.read_text())
    block_ids = [int(item["block_id"].removeprefix("B")) for item in scenario["planning_units"]]
    blocks = gpd.read_file(ROOT / "data/ws4/blocks.geojson").to_crs(3005)
    blocks = blocks[blocks.block_id.isin(block_ids)].copy()
    blocks["centroid"] = blocks.geometry.centroid

    block_nodes = []
    for row in blocks.itertuples(index=False):
        point = nearest_points(row.centroid, union)[1]
        _distance, index = tree.query([point.x, point.y])
        block_nodes.append(int(index))
    component = Counter(int(labels[index]) for index in block_nodes).most_common(1)[0][0]
    keep_nodes = np.where(labels == component)[0]
    keep_coords = coords[keep_nodes]
    keep_tree = cKDTree(keep_coords)
    remap = {int(node): index for index, node in enumerate(keep_nodes)}
    segments = [
        {
            "segment_id": index,
            "from_vertex": remap[a],
            "to_vertex": remap[c],
            "length_m": length,
            "haul_cost": length * rate / 1000.0,
            "build_cost": 0.0,
            "maintain_cost": 0.0,
        }
        for index, (a, c, length, rate) in enumerate(edges)
        if a in remap and c in remap
    ]
    vertices = pd.DataFrame(
        {
            "vertex_id": [remap[int(node)] for node in keep_nodes],
            "X": keep_coords[:, 0],
            "Y": keep_coords[:, 1],
        }
    )
    segments_frame = pd.DataFrame(segments)
    print(
        f"component {component}: {len(vertices):,} vertices; {len(segments_frame):,} segments; "
        f"graph components {count}"
    )

    linkages = []
    connectors = {}
    for row in blocks.itertuples(index=False):
        point = nearest_points(row.centroid, union)[1]
        _distance, index = keep_tree.query([point.x, point.y])
        node = int(keep_nodes[index])
        connector = float(
            np.hypot(coords[node][0] - row.centroid.x, coords[node][1] - row.centroid.y)
        )
        linkages.append({"block_id": int(row.block_id), "vertex_id": remap[node]})
        connectors[int(row.block_id)] = connector
    linkages_frame = pd.DataFrame(linkages)

    transformer = Transformer.from_crs(4326, 3005, always_xy=True)
    destinations = []
    for name, (lon, lat) in MILLS.items():
        x, y = transformer.transform(lon, lat)
        _d, index = keep_tree.query([x, y])
        destinations.append({"name": name, "vertex_id": remap[int(keep_nodes[index])]})
    destinations_frame = pd.DataFrame(destinations)

    vertices.to_csv(args.out / "vertices.csv", index=False)
    segments_frame.to_csv(args.out / "segments.csv", index=False)
    destinations_frame.to_csv(args.out / "destinations.csv", index=False)
    linkages_frame.to_csv(args.out / "linkages.csv", index=False)
    network = RouteNetwork.from_tables(
        segments_frame,
        destinations_frame,
        linkages_frame,
        vertices=vertices,
    )
    rows_out = []
    for row in blocks.itertuples(index=False):
        block = int(row.block_id)
        for name in MILLS:
            route = network.route(block, name)
            if route is None:
                rows_out.append(
                    {
                        "block_id": block,
                        "destination": name,
                        "route_km": None,
                        "connector_km": connectors[block] / 1000.0,
                        "total_km": None,
                        "route_cost_per_m3": None,
                        "connector_cost_per_m3": None,
                        "total_cost_per_m3": None,
                    }
                )
                continue
            connector_cost = connectors[block] * 0.12 / 1000.0
            rows_out.append(
                {
                    "block_id": block,
                    "destination": name,
                    "route_km": route.length_m / 1000.0,
                    "connector_km": connectors[block] / 1000.0,
                    "total_km": (route.length_m + connectors[block]) / 1000.0,
                    "route_cost_per_m3": route.haul_cost,
                    "connector_cost_per_m3": connector_cost,
                    "total_cost_per_m3": route.haul_cost + connector_cost,
                }
            )
    routes_frame = pd.DataFrame(rows_out)
    routes_frame.to_csv(args.out / "route_distances_ws4_truck.csv", index=False)
    manifest = {
        "source": "BC Digital Road Atlas, truck-legal filter",
        "excluded_classes": sorted(EXCLUDED_CLASSES),
        "excluded_surfaces": sorted(EXCLUDED_SURFACES),
        "features": len(roads),
        "component": component,
        "components": count,
        "vertices": len(vertices),
        "segments": len(segments_frame),
        "blocks": len(blocks),
        "routed": int(routes_frame.total_km.notna().sum()),
        "note": (
            "Trail/skid/overgrown/decommissioned features removed; blocks and mills "
            "snapped to one connected truck component."
        ),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(routes_frame.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
