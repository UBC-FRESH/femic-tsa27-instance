#!/usr/bin/env python3
"""Allocate shared-road build and maintenance costs to TSA 27 blocks.

The current screen charges every block a synthetic one-road-per-block cost. This
script replaces that placeholder with:

- a new block-to-road spur, priced with a public road-build rate;
- maintenance on the existing resource-road segments the block actually uses;
- maintenance shared across all blocks that use the same segment, weighted by volume.

Public road-build anchor: FERIC TR-28 subgrade costs (CPI-adjusted to 2026) and the
FPInnovations Jade Road trial range of CAD 37,700-63,000/km for re-establishing a
resource road. The central rate adds a surfacing/culvert allowance above subgrade.
Maintenance is an explicit planning assumption because no TSA-27-specific public
per-kilometre rate was found.

Usage:
    python scripts/build_shared_road_costs.py \
        --screen runtime/operational_screen/screen_full_truck.csv \
        --routes runtime/operational_pilot/route_network_truck/route_distances_full_truck_all.csv \
        --label full_shared
"""

from __future__ import annotations

import argparse
import heapq
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
from scipy.spatial import cKDTree  # type: ignore[import-untyped]  # scipy-stubs is not installed

ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT / "runtime/operational_pilot/route_network"
DESTINATIONS = ("destination.revelstoke", "destination.malakwa")
PERIOD_YEARS = 5
SPUR_LIFE_YEARS = 20
DISCOUNT_RATE = 0.05
CONNECTOR_HAUL_RATE = 0.12
BUILD_RATE_CENTRAL = 60_000.0
BUILD_RATE_LOW = 38_000.0
BUILD_RATE_HIGH = 100_000.0
MAINTENANCE_RATE_CENTRAL = 1_500.0
MAINTENANCE_RATE_LOW = 750.0
MAINTENANCE_RATE_HIGH = 3_000.0


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--network", type=Path, default=NETWORK)
    parser.add_argument("--label", default="shared")
    parser.add_argument("--build-rate", type=float, default=BUILD_RATE_CENTRAL)
    parser.add_argument("--maintenance-rate", type=float, default=MAINTENANCE_RATE_CENTRAL)
    parser.add_argument("--out", type=Path, default=ROOT / "runtime/operational_screen")
    return parser.parse_args()


def capital_recovery_factor(rate: float, years: int) -> float:
    """Return the annual capital-recovery factor for a discount rate and life.

    Parameters
    ----------
    rate : float
        Annual discount rate, as a fraction.
    years : int
        Asset life in years.

    Returns
    -------
    float
        Annual payment per unit of initial capital.
    """
    if years <= 0:
        raise ValueError("years must be > 0")
    if rate == 0.0:
        return 1.0 / years
    growth = (1.0 + rate) ** years
    return rate * growth / (growth - 1.0)


def segment_class(haul_cost: float, length_m: float) -> str:
    """Return a road class from the segment haul rate.

    Parameters
    ----------
    haul_cost : float
        Segment haul cost in CAD per cubic metre.
    length_m : float
        Segment length in metres.

    Returns
    -------
    str
        ``highway``, ``paved``, or ``resource``.
    """
    if length_m <= 0.0:
        return "resource"
    rate = haul_cost / (length_m / 1000.0)
    if rate <= 0.065:
        return "highway"
    if rate <= 0.105:
        return "paved"
    if rate <= 0.305:
        return "resource"
    return "non_truck"


def build_linkages(
    blocks: gpd.GeoDataFrame, vertices: pd.DataFrame
) -> tuple[pd.DataFrame, dict[int, float]]:
    """Assign every block to its nearest route vertex.

    Parameters
    ----------
    blocks : geopandas.GeoDataFrame
        Block polygons with ``block_id``.
    vertices : pandas.DataFrame
        Route vertices with ``vertex_id``, ``X``, and ``Y``.

    Returns
    -------
    tuple of pandas.DataFrame and dict of int to float
        Linkage table and connector distance in kilometres by block.
    """
    centroids = blocks.geometry.centroid
    coords = vertices[["X", "Y"]].to_numpy()
    tree = cKDTree(coords)
    distances, indexes = tree.query([[point.x, point.y] for point in centroids])
    linkages = pd.DataFrame(
        {
            "block_id": blocks.block_id.astype(int).to_numpy(),
            "vertex_id": vertices.vertex_id.to_numpy()[indexes],
        }
    )
    connectors = {
        int(block): float(distance) / 1000.0
        for block, distance in zip(blocks.block_id.astype(int), distances, strict=True)
    }
    return linkages, connectors


def build_adjacency(
    segments: pd.DataFrame,
) -> dict[int, list[tuple[int, int, float, float]]]:
    """Build an undirected adjacency map from the segment table.

    Parameters
    ----------
    segments : pandas.DataFrame
        Segment table with ``segment_id``, ``from_vertex``, ``to_vertex``,
        ``haul_cost``, and ``length_m``.

    Returns
    -------
    dict of int to list of tuple
        ``vertex -> [(neighbour, segment_id, haul_cost, length_m), ...]``.
    """
    adjacency: dict[int, list[tuple[int, int, float, float]]] = defaultdict(list)
    for row in segments.itertuples(index=False):
        start = int(str(row.from_vertex))
        end = int(str(row.to_vertex))
        segment = int(str(row.segment_id))
        haul = float(str(row.haul_cost))
        length = float(str(row.length_m))
        adjacency[start].append((end, segment, haul, length))
        adjacency[end].append((start, segment, haul, length))
    return adjacency


def shortest_paths(
    adjacency: dict[int, list[tuple[int, int, float, float]]], source: int
) -> tuple[dict[int, float], dict[int, tuple[int, int, float, float]]]:
    """Run one Dijkstra search from a destination vertex.

    Parameters
    ----------
    adjacency : dict of int to list of tuple
        Undirected adjacency map from :func:`build_adjacency`.
    source : int
        Destination vertex identifier.

    Returns
    -------
    tuple of dict
        Distance by vertex and predecessor ``(vertex, segment, cost, length)`` by vertex.
    """
    distance: dict[int, float] = {source: 0.0}
    previous: dict[int, tuple[int, int, float, float]] = {}
    queue: list[tuple[float, int]] = [(0.0, source)]
    while queue:
        cost, vertex = heapq.heappop(queue)
        if cost > distance.get(vertex, float("inf")):
            continue
        for neighbour, segment, haul, length in adjacency.get(vertex, []):
            candidate = cost + haul
            if candidate < distance.get(neighbour, float("inf")):
                distance[neighbour] = candidate
                previous[neighbour] = (vertex, segment, haul, length)
                heapq.heappush(queue, (candidate, neighbour))
    return distance, previous


def reconstruct_path(
    previous: dict[int, tuple[int, int, float, float]], vertex: int
) -> tuple[list[int], float, float] | None:
    """Reconstruct a path from a block vertex back to the destination.

    Parameters
    ----------
    previous : dict of int to tuple
        Predecessor map from :func:`shortest_paths`.
    vertex : int
        Starting (block) vertex.

    Returns
    -------
    tuple or None
        ``(segment_ids, haul_cost, length_m)``, or ``None`` when disconnected.
    """
    if vertex not in previous:
        return None
    segment_ids: list[int] = []
    haul = 0.0
    length = 0.0
    current = vertex
    while current in previous:
        parent, segment, segment_haul, segment_length = previous[current]
        segment_ids.append(segment)
        haul += segment_haul
        length += segment_length
        current = parent
    return segment_ids, haul, length


def main() -> None:
    """Write block road-cost and shared-segment tables."""
    args = parse_args()
    print("reading screen", flush=True)
    screen = pd.read_csv(args.screen)
    screen = screen[screen.volume_m3 > 0.0].copy()
    volumes = {
        int(str(row.block_id)): float(str(row.volume_m3)) for row in screen.itertuples(index=False)
    }
    print("reading routes", flush=True)
    route_frame = pd.read_csv(args.routes)
    route_frame = route_frame[route_frame.block_id.isin(volumes)].copy()

    vertices = pd.read_csv(args.network / "vertices.csv")
    segments = pd.read_csv(args.network / "segments.csv")
    destinations = pd.read_csv(args.network / "destinations.csv")
    segments["length_km"] = segments.length_m / 1000.0
    segments["road_class"] = [
        segment_class(haul, length)
        for haul, length in zip(segments.haul_cost, segments.length_m, strict=True)
    ]
    segment_road_class = {
        int(str(row.segment_id)): str(row.road_class) for row in segments.itertuples(index=False)
    }
    segment_length_by_id = {
        int(str(row.segment_id)): float(str(row.length_km))
        for row in segments.itertuples(index=False)
    }

    print("reading blocks", flush=True)
    blocks = gpd.read_file(ROOT / "data/ws4/blocks.geojson").to_crs(3005)
    blocks = blocks[blocks.block_id.isin(volumes)].copy()
    linkages, connectors = build_linkages(blocks, vertices)
    print("building adjacency", flush=True)
    adjacency = build_adjacency(segments)
    destination_vertices = {
        str(row.name): int(str(row.vertex_id)) for row in destinations.itertuples(index=False)
    }
    print("running dijkstra", flush=True)
    path_trees = {
        name: shortest_paths(adjacency, vertex) for name, vertex in destination_vertices.items()
    }
    block_vertices = {
        int(str(row.block_id)): int(str(row.vertex_id)) for row in linkages.itertuples(index=False)
    }

    print("reconstructing paths", flush=True)
    users: dict[int, list[int]] = defaultdict(list)
    chosen: dict[int, dict[str, Any]] = {}
    for block in blocks.block_id.astype(int):
        best: tuple[float, str, list[int], float, float] | None = None
        for destination in DESTINATIONS:
            distance, previous = path_trees[destination]
            vertex = block_vertices[block]
            if vertex not in distance:
                continue
            path = reconstruct_path(previous, vertex)
            if path is None:
                continue
            segment_ids, haul, length = path
            score = haul + connectors[block] * CONNECTOR_HAUL_RATE
            if best is None or score < best[0]:
                best = (score, destination, segment_ids, haul, length)
        if best is None:
            continue
        _score, destination, segment_ids, haul, length = best
        chosen[block] = {
            "destination": destination,
            "segment_ids": segment_ids,
            "haul": haul,
            "length": length,
        }
        for segment_id in segment_ids:
            users[int(segment_id)].append(block)

    crf = capital_recovery_factor(DISCOUNT_RATE, SPUR_LIFE_YEARS)
    print("building segment costs", flush=True)
    segment_rows = []
    segment_cost: dict[int, float] = {}
    segment_upgrade: dict[int, float] = {}
    segment_user_volume: dict[int, float] = {}
    segment_non_truck: dict[int, bool] = {}
    segment_length_km: dict[int, float] = {}
    for segment_id, block_ids in users.items():
        road_class = segment_road_class[int(str(segment_id))]
        length_km = segment_length_by_id[int(str(segment_id))]
        if road_class in {"resource", "non_truck"}:
            maintenance = length_km * args.maintenance_rate * PERIOD_YEARS
            if road_class == "non_truck":
                maintenance *= 1.5
        else:
            maintenance = 0.0
        upgrade = (
            length_km * args.build_rate * crf * PERIOD_YEARS if road_class == "non_truck" else 0.0
        )
        user_volume = sum(volumes[block] for block in block_ids)
        segment_cost[int(str(segment_id))] = maintenance
        segment_upgrade[int(str(segment_id))] = upgrade
        segment_user_volume[int(str(segment_id))] = user_volume
        segment_non_truck[int(str(segment_id))] = road_class == "non_truck"
        segment_length_km[int(str(segment_id))] = length_km
        segment_rows.append(
            {
                "segment_id": int(str(segment_id)),
                "road_class": road_class,
                "length_km": length_km,
                "users": len(block_ids),
                "user_volume_m3": round(user_volume, 1),
                "maintenance_5yr": round(maintenance, 2),
                "upgrade_5yr": round(upgrade, 2),
            }
        )

    rows = []
    for block, entry in chosen.items():
        route_km = float(str(entry["length"])) / 1000.0
        connector_km = connectors[block]
        spur_build = connector_km * args.build_rate
        spur_5yr = spur_build * crf * PERIOD_YEARS
        shared_maintenance = 0.0
        dedicated_maintenance = 0.0
        shared_upgrade = 0.0
        non_truck_km = 0.0
        for segment_id in entry["segment_ids"]:
            cost = segment_cost[int(str(segment_id))]
            dedicated_maintenance += cost
            user_volume = segment_user_volume[int(str(segment_id))]
            if user_volume > 0.0:
                shared_maintenance += cost * volumes[block] / user_volume
                shared_upgrade += segment_upgrade[int(segment_id)] * volumes[block] / user_volume
            if segment_non_truck[int(str(segment_id))]:
                non_truck_km += segment_length_km[int(str(segment_id))]
        road_cost = spur_5yr + shared_maintenance + shared_upgrade
        rows.append(
            {
                "block_id": block,
                "destination": entry["destination"],
                "volume_m3": volumes[block],
                "connector_km": round(connector_km, 4),
                "route_km": round(route_km, 4),
                "spur_build_cost": round(spur_build, 2),
                "spur_build_5yr": round(spur_5yr, 2),
                "shared_maintenance_5yr": round(shared_maintenance, 2),
                "shared_upgrade_5yr": round(shared_upgrade, 2),
                "dedicated_maintenance_5yr": round(dedicated_maintenance, 2),
                "non_truck_km": round(non_truck_km, 3),
                "route_truck_legal": non_truck_km == 0.0,
                "road_cost_5yr": round(road_cost, 2),
                "road_cost_per_m3": round(road_cost / volumes[block], 3),
            }
        )

    frame = pd.DataFrame(rows).sort_values("block_id")
    args.out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out / f"road_costs_{args.label}.csv", index=False)
    segment_frame = pd.DataFrame(segment_rows).sort_values("segment_id")
    segment_frame.to_csv(args.out / f"road_segments_{args.label}.csv", index=False)

    connector_values = frame.connector_km
    summary = {
        "label": args.label,
        "screen": str(args.screen),
        "routes": str(args.routes),
        "blocks": len(frame),
        "unrouted": len(volumes) - len(frame),
        "build_rate_cad_per_km": args.build_rate,
        "maintenance_rate_cad_per_km_year": args.maintenance_rate,
        "discount_rate": DISCOUNT_RATE,
        "spur_life_years": SPUR_LIFE_YEARS,
        "period_years": PERIOD_YEARS,
        "capital_recovery_factor": round(crf, 6),
        "median_connector_km": round(float(connector_values.median()), 3),
        "p90_connector_km": round(float(connector_values.quantile(0.9)), 3),
        "max_connector_km": round(float(connector_values.max()), 3),
        "share_connector_over_2km": round(float((connector_values > 2.0).mean()), 3),
        "total_spur_build_m": round(float(connector_values.sum() * 1000.0), 0),
        "unique_segments_used": len(segment_frame),
        "unique_route_km": round(float(segment_frame.length_km.sum()), 1),
        "resource_segments": int((segment_frame.road_class == "resource").sum()),
        "non_truck_segments": int((segment_frame.road_class == "non_truck").sum()),
        "total_maintenance_5yr": round(float(segment_frame.maintenance_5yr.sum()), 0),
        "total_upgrade_5yr": round(float(segment_frame.upgrade_5yr.sum()), 0),
        "share_truck_legal_routes": round(float(frame.route_truck_legal.mean()), 3),
        "median_road_cost_per_m3": round(float(frame.road_cost_per_m3.median()), 2),
        "p90_road_cost_per_m3": round(float(frame.road_cost_per_m3.quantile(0.9)), 2),
        "median_spur_build_cost": round(float(frame.spur_build_cost.median()), 0),
    }
    (args.out / f"road_costs_{args.label}_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
