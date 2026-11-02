#!/usr/bin/env python3
"""Audit TSA 27 FAIB plots and LidarBC point-cloud coverage.

The audit reads a public FAIB plot header, an optional FAIB visit table, a TSA
boundary, and a LidarBC selection manifest. It reports plot composition, recent
plots, point-cloud footprint, plot-to-tile overlap, time offsets, and nearest
distances. It does not download tiles, fit a model, or change the TSA 27 model.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, box

DEFAULT_RECENT_SINCE = 2018


def distance_summary(values: list[float]) -> dict[str, float] | None:
    """Summarize a list of distances.

    Parameters
    ----------
    values : list[float]
        Distances in metres.

    Returns
    -------
    dict[str, float] or None
        Minimum, median, and maximum, or ``None`` for an empty list.
    """
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    median = (
        ordered[midpoint] if len(ordered) % 2 else (ordered[midpoint - 1] + ordered[midpoint]) / 2.0
    )
    return {"min": ordered[0], "median": median, "max": ordered[-1]}


def tile_hit_years(point: Point, tiles: list[dict[str, Any]]) -> list[int]:
    """Return the acquisition years of tiles that contain a point.

    Parameters
    ----------
    point : shapely.geometry.Point
        Plot location.
    tiles : list[dict[str, Any]]
        LidarBC point-cloud tiles.

    Returns
    -------
    list[int]
        Sorted, unique acquisition years.
    """
    years: set[int] = set()
    for tile in tiles:
        if box(*tile["bbox_epsg3005"]).contains(point):
            year = tile.get("acquisition_year")
            if year is not None:
                years.add(int(year))
    return sorted(years)


def nearest_distance(point: Point, tiles: list[dict[str, Any]]) -> float:
    """Return the distance to the nearest point-cloud tile.

    Parameters
    ----------
    point : shapely.geometry.Point
        Plot location.
    tiles : list[dict[str, Any]]
        LidarBC point-cloud tiles.

    Returns
    -------
    float
        Distance in metres.
    """
    return float(min(box(*tile["bbox_epsg3005"]).distance(point) for tile in tiles))


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary", type=Path, required=True)
    parser.add_argument("--plots", type=Path, required=True)
    parser.add_argument("--visits", type=Path)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--request-csv", type=Path)
    parser.add_argument("--request-buffer-m", type=float, default=2000.0)
    parser.add_argument("--recent-since", type=int, default=DEFAULT_RECENT_SINCE)
    return parser.parse_args()


def request_table(inside: pd.DataFrame, buffer_m: float) -> pd.DataFrame:
    """Return one acquisition-request row per plot.

    Parameters
    ----------
    inside : pandas.DataFrame
        Plot rows with point-cloud fields.
    buffer_m : float
        Request buffer around each plot, in metres.

    Returns
    -------
    pandas.DataFrame
        Request rows with a square bounding box in EPSG:3005.
    """
    rows: list[dict[str, Any]] = []
    for _, row in inside.iterrows():
        point = cast(Point, row["geometry"])
        bounds = point.buffer(buffer_m).bounds
        years = [int(year) for year in cast(list[int], row["pc_years"])]
        last_year = int(cast(float, row["last_year"]))
        offsets = [year - last_year for year in years] if years else []
        nearest = float(cast(float, row["nearest_pc_m"]))
        if years:
            priority = "high"
        elif nearest <= 5000:
            priority = "medium"
        else:
            priority = "secondary"
        rows.append(
            {
                "site_identifier": str(row["SITE_IDENTIFIER"]),
                "tsa": cast(float, row["TSA"]),
                "bec_zone": cast(str, row["BEC_ZONE"]),
                "bec_subzone": cast(str, row["BEC_SBZ"]),
                "establishment": cast(str, row["SAMPLE_ESTABLISHMENT_TYPE"]),
                "last_year": last_year,
                "visits": cast(int, row["visits"]),
                "x_epsg3005": float(cast(float, row["BC_ALBERS_X"])),
                "y_epsg3005": float(cast(float, row["BC_ALBERS_Y"])),
                "has_pointcloud": bool(years),
                "pc_years": ",".join(str(year) for year in years),
                "offset_years": ",".join(str(offset) for offset in offsets),
                "nearest_pc_m": nearest,
                "request_priority": priority,
                "request_bbox_minx": bounds[0],
                "request_bbox_miny": bounds[1],
                "request_bbox_maxx": bounds[2],
                "request_bbox_maxy": bounds[3],
                "request_bbox_area_ha": (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) / 10000.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["request_priority", "nearest_pc_m", "site_identifier"])


def main() -> None:
    """Run the audit and write its JSON summary."""
    args = parse_args()
    boundary = gpd.read_file(args.boundary)
    boundary_geometry = boundary.geometry.union_all()
    plots = pd.read_csv(args.plots)
    if args.visits is not None:
        visits = pd.read_csv(args.visits)
        visit_summary = (
            visits.groupby("SITE_IDENTIFIER")
            .agg(last_year=("MEAS_YR", "max"), visits=("VISIT_NUMBER", "count"))
            .reset_index()
        )
        plots = plots.merge(visit_summary, on="SITE_IDENTIFIER", how="left")
    else:
        plots["last_year"] = pd.NA
        plots["visits"] = pd.NA
    plots = plots.dropna(subset=["BC_ALBERS_X", "BC_ALBERS_Y"]).copy()
    points = gpd.GeoDataFrame(
        plots,
        geometry=gpd.points_from_xy(plots["BC_ALBERS_X"], plots["BC_ALBERS_Y"]),
        crs=3005,
    )
    inside = gpd.sjoin(points, boundary[["geometry"]], how="inner", predicate="within").drop(
        columns="index_right", errors="ignore"
    )

    selection = json.loads(args.selection.read_text(encoding="utf-8"))
    tiles = [tile for tile in selection.get("tiles", []) if tile.get("product") == "point_cloud"]
    footprint = (
        gpd.GeoSeries([box(*tile["bbox_epsg3005"]) for tile in tiles], crs=3005)
        .union_all()
        .intersection(boundary_geometry)
    )

    inside = inside.copy()
    inside["pc_years"] = inside.geometry.apply(lambda point: tile_hit_years(point, tiles))
    inside["nearest_pc_m"] = inside.geometry.apply(lambda point: nearest_distance(point, tiles))
    inside["recent"] = inside["last_year"].fillna(0) >= args.recent_since
    with_pc = inside[inside["pc_years"].apply(bool)]
    detail = []
    for row in with_pc.itertuples(index=False):
        years = list(row.pc_years)
        offsets = [year - int(row.last_year) for year in years]
        detail.append(
            {
                "site_identifier": str(row.SITE_IDENTIFIER),
                "last_year": int(row.last_year),
                "bec": str(row.BEC_ZONE),
                "bec_subzone": str(row.BEC_SBZ),
                "pc_years": years,
                "offset_years": offsets,
            }
        )

    summary = {
        "boundary_ha": float(boundary_geometry.area / 10000.0),
        "plot_count": len(inside),
        "plots_by_bec": dict(Counter(inside["BEC_ZONE"].fillna("unknown"))),
        "plots_by_establishment": dict(
            Counter(inside["SAMPLE_ESTABLISHMENT_TYPE"].fillna("unknown"))
        ),
        "recent_since": args.recent_since,
        "recent_plot_count": int(inside["recent"].sum()),
        "pointcloud_tile_count": len(tiles),
        "pointcloud_years": dict(Counter(tile.get("acquisition_year") for tile in tiles)),
        "pointcloud_footprint_ha": float(footprint.area / 10000.0),
        "pointcloud_footprint_pct": float(footprint.area / boundary_geometry.area * 100.0),
        "plots_with_pointcloud": len(with_pc),
        "plots_within_5km": int((inside["nearest_pc_m"] <= 5000).sum()),
        "plots_within_10km": int((inside["nearest_pc_m"] <= 10000).sum()),
        "nearest_distance_m": distance_summary(inside["nearest_pc_m"].tolist()),
        "recent_distance_m": distance_summary(
            inside.loc[inside["recent"], "nearest_pc_m"].tolist()
        ),
        "plots_with_pointcloud_detail": detail,
        "request_buffer_m": args.request_buffer_m,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.request_csv is not None:
        request_table(inside, args.request_buffer_m).to_csv(args.request_csv, index=False)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
