#!/usr/bin/env python3
"""Build actual DRA haul distances for the TSA 27 pilot and query them with WS4 routing.

The source is the BC Digital Road Atlas (DRA) WFS, clipped to the TSA 27 bounding box.
The script nodes the DRA linework, keeps the largest connected component, snaps the pilot
blocks and two mill points to that graph, writes the four WS4 route tables, and calls WS4's
RouteNetwork to get least-length paths.

Usage:
    python scripts/build_ws4_route_distances.py
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
import requests
import yaml
from pyproj import Transformer
from scipy.sparse import coo_matrix  # type: ignore[import-untyped]  # optional local/model dependency is not installed with stubs
from scipy.sparse.csgraph import connected_components  # type: ignore[import-untyped]  # optional local/model dependency is not installed with stubs
from scipy.spatial import cKDTree  # type: ignore[import-untyped]  # optional local/model dependency is not installed with stubs
from shapely.ops import nearest_points, unary_union
from ws4.roads.network import RouteNetwork  # type: ignore[import-not-found]  # optional local/model dependency is not installed with stubs

ROOT = Path(__file__).resolve().parents[1]
BBOX = (1481038, 655622, 1582172, 819973)
WFS = "https://openmaps.gov.bc.ca/geo/pub/WHSE_BASEMAPPING.DRA_DGTL_ROAD_ATLAS_MPAR_SP/ows"
MILLS = {"destination.revelstoke": (-118.2, 51.0), "destination.malakwa": (-118.74, 50.96)}


def haul_rate(road_class: object, surface: object) -> float:
    """Return a documented route haul rate in CAD/m3/km by DRA class/surface.

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
    if road in {"trail", "skid"} or surf in {"overgrown", "decommissioned"}:
        return 0.50
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
        "--out", type=Path, default=ROOT / "runtime/operational_pilot/route_network"
    )
    parser.add_argument(
        "--scenario", type=Path, default=ROOT / "runtime/operational_pilot/scenario.yaml"
    )
    return parser.parse_args()


def fetch_pages(out: Path) -> list[Path]:
    """Download all DRA pages in the TSA bbox, cached under the output directory.

    Parameters
    ----------
    out : Path
        Output directory for the cached WFS pages.

    Returns
    -------
    list of Path
        Paths to the cached page files.
    """
    source = out / "source"
    source.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    start = 0
    while True:
        path = source / f"dra_{start:05d}.json"
        if not path.exists():
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeName": "WHSE_BASEMAPPING.DRA_DGTL_ROAD_ATLAS_MPAR_SP",
                "outputFormat": "application/json",
                "count": "10000",
                "startIndex": str(start),
                "bbox": f"{BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]},urn:ogc:def:crs:EPSG::3005",
            }
            response = requests.get(WFS, params=params, timeout=180)
            response.raise_for_status()
            path.write_bytes(response.content)
        payload = json.loads(path.read_text())
        features = payload.get("features", [])
        paths.append(path)
        if len(features) < 10000:
            break
        start += 10000
    return paths


def main() -> None:
    """Build tables, query WS4 routes, and write the distance table."""
    args = parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    pages = fetch_pages(out)
    frames = [gpd.read_file(path) for path in pages]
    roads = gpd.GeoDataFrame(
        pd.concat(frames, ignore_index=True),
        geometry="geometry",
        crs=frames[0].crs,
    ).to_crs(3005)
    union = unary_union(roads.geometry.tolist())
    print(f"DRA road features: {len(roads):,}; noded lines: {len(union.geoms):,}")

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
    largest = Counter(int(label) for label in labels).most_common(1)[0][0]
    print(f"graph nodes: {n:,}; edges: {len(edges):,}; components: {count}; largest: {largest}")

    coords = np.array(list(nodes.keys()))
    tree = cKDTree(coords)
    keep_nodes = np.where(labels == largest)[0]
    keep_set = {int(node) for node in keep_nodes}
    remap = {node: index for index, node in enumerate(sorted(keep_set))}
    segments = []
    for index, (a, c, length, rate) in enumerate(edges):
        if a in keep_set and c in keep_set:
            segments.append(
                {
                    "segment_id": index,
                    "from_vertex": remap[a],
                    "to_vertex": remap[c],
                    "length_m": length,
                    "haul_cost": length * rate / 1000.0,
                    "build_cost": 0.0,
                    "maintain_cost": 0.0,
                }
            )
    vertices = pd.DataFrame(
        {
            "vertex_id": [remap[node] for node in sorted(keep_set)],
            "X": [coords[node][0] for node in sorted(keep_set)],
            "Y": [coords[node][1] for node in sorted(keep_set)],
        }
    )
    segments_frame = pd.DataFrame(segments)
    print(f"largest component: {len(vertices):,} vertices; {len(segments_frame):,} segments")

    scenario = yaml.safe_load(args.scenario.read_text())
    block_ids = [int(item["block_id"].removeprefix("B")) for item in scenario["planning_units"]]
    blocks = gpd.read_file(ROOT / "data/ws4/blocks.geojson").to_crs(3005)
    blocks = blocks[blocks.block_id.isin(block_ids)].copy()
    blocks["centroid"] = blocks.geometry.centroid

    linkages = []
    connectors = {}
    for row in blocks.itertuples(index=False):
        point = nearest_points(row.centroid, union)[1]
        _distance, index = tree.query([point.x, point.y])
        node = int(index)
        if node not in keep_set:
            nearest = min(
                keep_set,
                key=lambda candidate: (
                    (coords[candidate][0] - point.x) ** 2 + (coords[candidate][1] - point.y) ** 2
                ),
            )
            node = nearest
        connector = float(
            np.hypot(coords[node][0] - row.centroid.x, coords[node][1] - row.centroid.y)
        )
        linkages.append({"block_id": int(row.block_id), "vertex_id": remap[node]})
        connectors[int(row.block_id)] = connector
    linkages_frame = pd.DataFrame(linkages)

    transformer = Transformer.from_crs(4326, 3005, always_xy=True)
    destinations = []
    destination_nodes = {}
    for name, (lon, lat) in MILLS.items():
        x, y = transformer.transform(lon, lat)
        _distance, index = tree.query([x, y])
        node = int(index)
        if node not in keep_set:
            node = min(
                keep_set,
                key=lambda candidate: (
                    (coords[candidate][0] - x) ** 2 + (coords[candidate][1] - y) ** 2
                ),
            )
        destinations.append({"name": name, "vertex_id": remap[node]})
        destination_nodes[name] = remap[node]
    destinations_frame = pd.DataFrame(destinations)

    vertices.to_csv(out / "vertices.csv", index=False)
    segments_frame.to_csv(out / "segments.csv", index=False)
    destinations_frame.to_csv(out / "destinations.csv", index=False)
    linkages_frame.to_csv(out / "linkages.csv", index=False)
    network = RouteNetwork.from_tables(
        segments_frame,
        destinations_frame,
        linkages_frame,
        vertices=vertices,
    )
    route_rows = []
    for row in blocks.itertuples(index=False):
        block = int(row.block_id)
        for name in MILLS:
            route = network.route(block, name)
            if route is None:
                route_rows.append(
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
            total = route.length_m + connectors[block]
            connector_cost = connectors[block] * 0.12 / 1000.0
            route_rows.append(
                {
                    "block_id": block,
                    "destination": name,
                    "route_km": route.length_m / 1000.0,
                    "connector_km": connectors[block] / 1000.0,
                    "total_km": total / 1000.0,
                    "route_cost_per_m3": route.haul_cost,
                    "connector_cost_per_m3": connector_cost,
                    "total_cost_per_m3": route.haul_cost + connector_cost,
                }
            )
    routes_frame = pd.DataFrame(route_rows)
    routes_frame.to_csv(out / "route_distances_ws4.csv", index=False)
    manifest = {
        "source": "BC Digital Road Atlas WFS",
        "type_name": "WHSE_BASEMAPPING.DRA_DGTL_ROAD_ATLAS_MPAR_SP",
        "bbox_epsg3005": BBOX,
        "pages": [str(path.relative_to(ROOT)) for path in pages],
        "vertices": len(vertices),
        "segments": len(segments_frame),
        "components": count,
        "largest_component": largest,
        "blocks": len(blocks),
        "mills": MILLS,
        "route_table": "route_distances_ws4.csv",
        "note": (
            "Route lengths and class-based haul costs use the DRA line graph; "
            "connectors are straight-line."
        ),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(routes_frame.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
