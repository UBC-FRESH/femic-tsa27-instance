#!/usr/bin/env python3
"""Build 2017-2026 annual land-base, fire, road, and UWR snapshots for TSA 27.

The snapshots are annual overlays of public layers, not a historical reconstruction of the
compiled inventory. They answer a narrower question: how much cutblock area, fire overlap,
active road length, and approved ungulate winter range existed in each year, and how do those
compare with the HBS harvest series?

Usage:
    python scripts/build_annual_snapshots.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "data/downloads/bc"
OUT = ROOT / "runtime/annual_snapshots"
YEARS = range(2017, 2027)
AAC = 225_000.0


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    return parser.parse_args()


def clip_area_ha(frame: gpd.GeoDataFrame, boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Clip a layer to the TSA boundary and add an area column in hectares.

    Parameters
    ----------
    frame : geopandas.GeoDataFrame
        Input layer in EPSG:3005.
    boundary : geopandas.GeoDataFrame
        TSA boundary polygon in EPSG:3005.

    Returns
    -------
    geopandas.GeoDataFrame
        Clipped layer with ``area_ha``.
    """
    clipped = gpd.clip(frame, boundary)
    clipped = clipped[~clipped.geometry.is_empty].copy()
    clipped["area_ha"] = clipped.geometry.area / 10_000.0
    return clipped


def hbs_series() -> pd.DataFrame:
    """Return the recovered HBS annual harvest series.

    Returns
    -------
    pandas.DataFrame
        Columns ``year`` and ``hbs_m3``.
    """
    old = pd.read_csv(ROOT / "runtime/document_ingestion/tsa27-dp2022-fig4/figure4_recovered.csv")
    old = old[["year", "volume_harvested_m3"]].rename(columns={"volume_harvested_m3": "hbs_m3"})
    new = pd.read_csv(
        ROOT / "runtime/document_ingestion/tsa27-dp2022-fig4/hbs_annual_scaled_volume_2022_2026.csv"
    )
    new = new[["year", "scaled_volume_m3"]].rename(columns={"scaled_volume_m3": "hbs_m3"})
    combined = pd.concat([old, new], ignore_index=True)
    combined = combined[combined.year.between(min(YEARS), max(YEARS))].copy()
    return combined.sort_values("year").reset_index(drop=True)


def cutblock_series(boundary: gpd.GeoDataFrame) -> pd.DataFrame:
    """Return annual and cumulative cutblock area inside TSA 27.

    Parameters
    ----------
    boundary : geopandas.GeoDataFrame
        TSA boundary polygon in EPSG:3005.

    Returns
    -------
    pandas.DataFrame
        Columns ``year``, ``cutblock_area_ha``, and ``cutblock_cumulative_ha``.
    """
    cutblocks = gpd.read_file((DOWNLOADS / "cutblocks_tsa_bbox.geojson").resolve())
    cutblocks = cutblocks.set_crs(3005, allow_override=True)
    cutblocks = clip_area_ha(cutblocks, boundary)
    cutblocks["harvest_year"] = pd.to_numeric(
        cutblocks["HARVEST_START_YEAR_CALENDAR"], errors="coerce"
    )
    missing = cutblocks["harvest_year"].isna()
    if missing.any():
        cutblocks.loc[missing, "harvest_year"] = pd.to_datetime(
            cutblocks.loc[missing, "HARVEST_START_DATE"], errors="coerce"
        ).dt.year
    cutblocks = cutblocks[cutblocks.harvest_year.between(min(YEARS), max(YEARS))].copy()
    annual = cutblocks.groupby("harvest_year")["area_ha"].sum()
    rows = []
    cumulative = 0.0
    for year in YEARS:
        value = float(annual.get(year, 0.0))
        cumulative += value
        rows.append(
            {
                "year": year,
                "cutblock_area_ha": round(value, 1),
                "cutblock_cumulative_ha": round(cumulative, 1),
            }
        )
    return pd.DataFrame(rows)


def fire_series(
    boundary: gpd.GeoDataFrame, blocks: gpd.GeoDataFrame, volumes: dict[int, float]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return annual fire area, per-fire overlap, and block-level volume at risk.

    Parameters
    ----------
    boundary : geopandas.GeoDataFrame
        TSA boundary polygon in EPSG:3005.
    blocks : geopandas.GeoDataFrame
        WS4 block polygons with ``block_id`` and ``area_ha``.
    volumes : dict of int to float
        Operable year-0 volume by block.

    Returns
    -------
    tuple of pandas.DataFrame
        Annual summary, per-fire overlap, and block-level overlap tables.
    """
    fires = gpd.read_file((DOWNLOADS / "fire_perimeters_tsa_bbox.geojson").resolve())
    fires = fires.set_crs(3005, allow_override=True)
    fires["FIRE_YEAR"] = pd.to_numeric(fires["FIRE_YEAR"], errors="coerce")
    fires = fires[fires.FIRE_YEAR.between(min(YEARS), max(YEARS))].copy()
    fires = clip_area_ha(fires, boundary)
    fires = fires[fires.area_ha > 0.0].copy()
    rows = []
    fire_rows = []
    fire_block_rows = []
    for year in YEARS:
        year_fires = fires[fires["FIRE_YEAR"].eq(year)]
        burned = float(year_fires.area_ha.sum())
        block_overlap = 0.0
        volume_at_risk = 0.0
        for fire in year_fires.itertuples(index=False):
            overlap = gpd.overlay(
                blocks[["block_id", "area_ha", "geometry"]],
                gpd.GeoDataFrame(
                    {"FIRE_NUMBER": [fire.FIRE_NUMBER]},
                    geometry=[fire.geometry],
                    crs=blocks.crs,
                ),
                how="intersection",
                keep_geom_type=True,
            )
            if overlap.empty:
                continue
            overlap["overlap_ha"] = overlap.geometry.area / 10_000.0
            fire_overlap = float(overlap.overlap_ha.sum())
            fire_volume = float(
                sum(
                    volumes.get(int(row.block_id), 0.0)
                    * min(float(row.overlap_ha) / float(row.area_ha), 1.0)
                    for row in overlap.itertuples(index=False)
                )
            )
            block_overlap += fire_overlap
            volume_at_risk += fire_volume
            for row in overlap.itertuples(index=False):
                fire_block_rows.append(
                    {
                        "year": year,
                        "fire_number": fire.FIRE_NUMBER,
                        "block_id": int(row.block_id),
                        "overlap_ha": round(float(row.overlap_ha), 4),
                        "volume_at_risk_m3": round(
                            volumes.get(int(row.block_id), 0.0)
                            * min(float(row.overlap_ha) / float(row.area_ha), 1.0),
                            2,
                        ),
                    }
                )
            fire_rows.append(
                {
                    "year": year,
                    "fire_number": fire.FIRE_NUMBER,
                    "fire_area_ha": round(float(fire.area_ha), 1),
                    "block_overlap_ha": round(fire_overlap, 1),
                    "operable_volume_at_risk_m3": round(fire_volume, 1),
                }
            )
        rows.append(
            {
                "year": year,
                "fire_area_ha": round(burned, 1),
                "fire_block_overlap_ha": round(block_overlap, 1),
                "operable_volume_at_risk_m3": round(volume_at_risk, 1),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(fire_rows), pd.DataFrame(fire_block_rows)


def road_series(boundary: gpd.GeoDataFrame) -> pd.DataFrame:
    """Return active FTEN road length by year.

    Parameters
    ----------
    boundary : geopandas.GeoDataFrame
        TSA boundary polygon in EPSG:3005.

    Returns
    -------
    pandas.DataFrame
        Columns ``year`` and ``active_road_km``.
    """
    roads = gpd.read_file((DOWNLOADS / "roads.geojson").resolve()).to_crs(3005)
    roads = clip_area_ha(roads, boundary)
    roads["retirement"] = pd.to_datetime(roads["RETIREMENT_DATE"], errors="coerce")
    rows = []
    for year in YEARS:
        end = pd.Timestamp(f"{year}-12-31")
        active = roads[roads["retirement"].isna() | (roads["retirement"] > end)]
        rows.append({"year": year, "active_road_km": round(float(active.length.sum()) / 1000.0, 1)})
    return pd.DataFrame(rows)


def uwr_series(boundary: gpd.GeoDataFrame) -> pd.DataFrame:
    """Return approved UWR area by year from current boundaries and approval dates.

    Parameters
    ----------
    boundary : geopandas.GeoDataFrame
        TSA boundary polygon in EPSG:3005.

    Returns
    -------
    pandas.DataFrame
        Columns ``year`` and ``uwr_area_ha``.
    """
    uwr = gpd.read_file((DOWNLOADS / "uwr.geojson").resolve()).to_crs(3005)
    uwr = uwr[(uwr.UWR_NUMBER == "u-3-005") & uwr.TIMBER_HARVEST_CODE.notna()].copy()
    uwr["approval_year"] = pd.to_datetime(uwr["APPROVAL_DATE"], errors="coerce").dt.year
    rows = []
    for year in YEARS:
        approved = uwr[uwr.approval_year <= year]
        if approved.empty:
            area = 0.0
        else:
            union = approved.geometry.union_all()
            area = float(boundary.geometry.intersection(union).area.sum()) / 10_000.0
        rows.append({"year": year, "uwr_area_ha": round(area, 1)})
    return pd.DataFrame(rows)


def main() -> None:
    """Build and write the annual snapshot tables."""
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    boundary = gpd.read_file(ROOT / "data/ws4/land_base.geojson").to_crs(3005)
    blocks = gpd.read_file(ROOT / "data/ws4/blocks.geojson").to_crs(3005)
    blocks["area_ha"] = blocks.geometry.area / 10_000.0
    screen = pd.read_csv(ROOT / "runtime/operational_screen/screen_full_shared.csv")
    volumes = {
        int(str(row.block_id)): float(str(row.volume_m3)) for row in screen.itertuples(index=False)
    }

    cutblocks = cutblock_series(boundary)
    fires, fire_rows, fire_block_rows = fire_series(boundary, blocks, volumes)
    roads = road_series(boundary)
    uwr = uwr_series(boundary)
    hbs = hbs_series()

    summary = hbs.merge(cutblocks, on="year", how="outer")
    summary = summary.merge(fires, on="year", how="outer")
    summary = summary.merge(roads, on="year", how="outer")
    summary = summary.merge(uwr, on="year", how="outer")
    summary["harvest_to_aac"] = summary.hbs_m3 / AAC
    operable_area = float(screen["area_ha"].sum())
    summary["fire_overlap_over_cutblock_area"] = (
        summary.fire_block_overlap_ha / summary.cutblock_area_ha.replace(0.0, pd.NA)
    )
    summary["fire_overlap_share_of_operable_area"] = summary.fire_block_overlap_ha / operable_area
    summary["cutblock_ha_per_1000m3"] = summary.cutblock_area_ha / (summary.hbs_m3 / 1000.0)
    summary = summary.sort_values("year").reset_index(drop=True)
    summary.to_csv(args.out / "annual_snapshot_summary.csv", index=False)
    fire_rows.to_csv(args.out / "fire_overlap_by_year.csv", index=False)
    fire_block_rows.to_csv(args.out / "fire_block_overlap.csv", index=False)

    print(summary.to_string(index=False))
    print(f"wrote {args.out / 'annual_snapshot_summary.csv'}")
    print(f"wrote {args.out / 'fire_overlap_by_year.csv'}")
    print(f"wrote {args.out / 'fire_block_overlap.csv'}")


if __name__ == "__main__":
    main()
