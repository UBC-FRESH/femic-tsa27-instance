#!/usr/bin/env python3
"""Build a provisional TSA 27 land-base layer with caribou policy flags.

The layer is a first-pass overlay of VRI 2025, the TSA boundary, landscape units,
UWR u-3-005, legal OGMAs, and consolidated cutblocks. It is deliberately labelled
provisional: the 2022 core/matrix caribou layer, the historical HLP zone, and the
operability/ownership layers are still `to_fetch` in the data manifest.

Command-line usage::

    export FEMIC_EXTERNAL_DATA_ROOT=../femic/external/femic-public-data/data
    python scripts/build_land_base.py
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_OUT: Path = ROOT / "data" / "land_base" / "tsa27_land_base.gpkg"
DEFAULT_SUMMARY: Path = ROOT / "metadata" / "land_base" / "tsa27_land_base_summary.csv"
TSA_CODE = "27"


def classify_forested(vri: gpd.GeoDataFrame) -> pd.Series:
    """Return a boolean series for vegetated, treed VRI polygons.

    Parameters
    ----------
    vri : geopandas.GeoDataFrame
        VRI polygons with ``BCLCS_LEVEL_1`` and ``BCLCS_LEVEL_2``.

    Returns
    -------
    pandas.Series
        True where the polygon is vegetated and treed.
    """
    return pd.Series((vri["BCLCS_LEVEL_1"] == "V") & (vri["BCLCS_LEVEL_2"] == "T"))


def caribou_uwr_mask(uwr: gpd.GeoDataFrame) -> pd.Series:
    """Return a boolean series for the u-3-005 no-harvest caribou UWR.

    Parameters
    ----------
    uwr : geopandas.GeoDataFrame
        Ungulate winter range polygons with ``UWR_NUMBER`` and
        ``TIMBER_HARVEST_CODE``.

    Returns
    -------
    pandas.Series
        True for the caribou no-harvest polygons.
    """
    return pd.Series(
        uwr["UWR_NUMBER"].astype(str).str.lower().str.startswith("u-3-005")
        & (uwr["TIMBER_HARVEST_CODE"].astype(str).str.upper() == "NO HARVEST ZONE")
    )


def build_land_base(
    vri: gpd.GeoDataFrame,
    tsa: gpd.GeoDataFrame,
    lu: gpd.GeoDataFrame,
    uwr: gpd.GeoDataFrame,
    ogma: gpd.GeoDataFrame,
    cutblocks: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Clip VRI to TSA 27 and attach land-base and caribou flags.

    Parameters
    ----------
    vri : geopandas.GeoDataFrame
        VRI polygons in EPSG:3005.
    tsa : geopandas.GeoDataFrame
        TSA polygons in EPSG:3005.
    lu : geopandas.GeoDataFrame
        Landscape units in any CRS.
    uwr : geopandas.GeoDataFrame
        Ungulate winter range polygons in any CRS.
    ogma : geopandas.GeoDataFrame
        Legal OGMA polygons in any CRS.
    cutblocks : geopandas.GeoDataFrame
        Consolidated cutblocks in any CRS.

    Returns
    -------
    geopandas.GeoDataFrame
        The clipped VRI with flags and a provisional ``thlb_candidate`` field.
    """
    tsa_geom = tsa.union_all()
    clipped = vri[vri.geometry.intersects(tsa_geom)].copy()
    clipped["geometry"] = clipped.geometry.intersection(tsa_geom)
    clipped = clipped[~clipped.geometry.is_empty].copy()
    clipped["is_forested"] = classify_forested(clipped)
    clipped["is_non_productive"] = ~clipped["is_forested"]
    clipped["bec_label"] = (
        clipped["BEC_ZONE_CODE"].fillna("")
        + "/"
        + clipped["BEC_SUBZONE"].fillna("")
        + "/"
        + clipped["BEC_VARIANT"].fillna("")
    ).str.strip("/")

    lu_3005 = lu.to_crs(3005)[["LANDSCAPE_UNIT_NAME", "BIODIVERSITY_EMPHASIS_OPTION", "geometry"]]
    joined = gpd.sjoin(clipped, lu_3005, how="left", predicate="intersects")
    joined = joined[~joined.index.duplicated(keep="first")].drop(
        columns=["index_right"], errors="ignore"
    )

    caribou = uwr[caribou_uwr_mask(uwr)].to_crs(3005)[["UWR_NUMBER", "geometry"]]
    caribou["caribou_uwr"] = 1
    joined = gpd.sjoin(joined, caribou, how="left", predicate="intersects")
    joined["caribou_uwr"] = joined["caribou_uwr"].fillna(0).astype(int)
    joined = (
        joined.sort_values("caribou_uwr")
        .drop_duplicates(keep="last")
        .drop(columns=["index_right"], errors="ignore")
    )

    ogma_3005 = ogma.to_crs(3005)[["OGMA_TYPE", "geometry"]]
    ogma_3005["ogma"] = 1
    joined = gpd.sjoin(joined, ogma_3005, how="left", predicate="intersects")
    joined["ogma"] = joined["ogma"].fillna(0).astype(int)
    joined = (
        joined.sort_values("ogma")
        .drop_duplicates(keep="last")
        .drop(columns=["index_right"], errors="ignore")
    )

    cut_3005 = cutblocks.to_crs(3005)[["HARVEST_MID_YEAR_CALENDAR", "geometry"]]
    joined = gpd.sjoin(joined, cut_3005, how="left", predicate="intersects")
    joined["last_harvest_year"] = joined["HARVEST_MID_YEAR_CALENDAR"].fillna(-1)
    joined = (
        joined.sort_values("last_harvest_year")
        .drop_duplicates(keep="last")
        .drop(columns=["index_right"], errors="ignore")
    )

    for column in ("caribou_core", "caribou_matrix", "caribou_zone", "caribou_immature"):
        joined[column] = 0
    joined["thlb_candidate"] = (
        joined["is_forested"] & (joined["caribou_uwr"] == 0) & (joined["ogma"] == 0)
    )
    return joined.sort_index().reset_index(drop=True)


def direct_uwr_area(tsa: gpd.GeoDataFrame, uwr: gpd.GeoDataFrame) -> float:
    """Return the direct UWR u-3-005 no-harvest area clipped to the TSA.

    Parameters
    ----------
    tsa : geopandas.GeoDataFrame
        TSA polygons in EPSG:3005.
    uwr : geopandas.GeoDataFrame
        Ungulate winter range polygons.

    Returns
    -------
    float
        Union area in hectares, or 0 when no caribou polygons intersect.
    """
    caribou = uwr[caribou_uwr_mask(uwr)].to_crs(3005)
    clipped = gpd.clip(caribou, tsa.union_all())
    if clipped.empty:
        return 0.0
    return float(clipped.union_all().area / 10_000)


def summarize(layer: gpd.GeoDataFrame, direct_uwr_ha: float | None = None) -> pd.DataFrame:
    """Summarize the provisional land-base areas.

    Parameters
    ----------
    layer : geopandas.GeoDataFrame
        The built land-base layer in EPSG:3005.
    direct_uwr_ha : float or None, optional
        Direct UWR u-3-005 clip area in hectares. When provided, a
        ``caribou_uwr_direct`` row is appended.

    Returns
    -------
    pandas.DataFrame
        One row per class with area in hectares and polygon count.
    """
    rows = [
        {
            "class": "gross_clip",
            "area_ha": float(layer.geometry.union_all().area / 10_000),
            "polygons": len(layer),
            "notes": "union area; VRI polygons overlap in the source layer",
        }
    ]
    for column, note in (
        ("is_forested", "union area of vegetated, treed VRI polygons"),
        (
            "caribou_uwr",
            "union area; binary flag can overstate the edge of fragmented UWR polygons",
        ),
        ("ogma", "union area of legal OGMA polygons"),
        ("thlb_candidate", "provisional: forested, outside UWR and OGMA only"),
        ("caribou_core", "to_fetch; currently zero"),
        ("caribou_matrix", "to_fetch; currently zero"),
    ):
        mask = layer[column].astype(bool)
        rows.append(
            {
                "class": column,
                "area_ha": float(layer[mask].geometry.union_all().area / 10_000)
                if mask.any()
                else 0.0,
                "polygons": int(mask.sum()),
                "notes": note,
            }
        )
    if direct_uwr_ha is not None:
        rows.append(
            {
                "class": "caribou_uwr_direct",
                "area_ha": float(direct_uwr_ha),
                "polygons": 0,
                "notes": "direct UWR u-3-005 no-harvest clip; use this for area accounting",
            }
        )
    return pd.DataFrame(rows)


def load_inputs(external_root: Path, downloads: Path) -> tuple[gpd.GeoDataFrame, ...]:
    """Load the build inputs.

    Parameters
    ----------
    external_root : Path
        ``FEMIC_EXTERNAL_DATA_ROOT``.
    downloads : Path
        Directory with the clipped BC layer GeoJSON files.

    Returns
    -------
    tuple of geopandas.GeoDataFrame
        TSA, VRI, LU, UWR, OGMA, and cutblocks.
    """
    tsa = gpd.read_file(external_root / "bc" / "tsa" / "FADM_TSA.gdb", engine="pyogrio")
    tsa = tsa[tsa["TSA_NUMBER"].astype(str).str.lstrip("0") == TSA_CODE].to_crs(3005)
    bounds = tsa.total_bounds
    vri = gpd.read_file(
        external_root / "bc" / "vri" / "2025" / "VEG_COMP_LYR_R1_POLY_2025.gdb",
        layer="VEG_COMP_LYR_R1_POLY",
        bbox=tuple(bounds),
        engine="pyogrio",
    )
    lu = gpd.read_file(downloads / "lu.geojson")
    uwr = gpd.read_file(downloads / "uwr.geojson")
    ogma = gpd.read_file(downloads / "ogma.geojson")
    cutblocks = gpd.read_file(downloads / "cutblocks.geojson")
    return tsa, vri, lu, uwr, ogma, cutblocks


def main(argv: Sequence[str] | None = None) -> int:
    """Run the land-base build.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` on success.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--downloads", type=Path, default=ROOT / "data" / "downloads" / "bc")
    args = parser.parse_args(argv)
    external = os.environ.get("FEMIC_EXTERNAL_DATA_ROOT")
    if not external:
        print("FEMIC_EXTERNAL_DATA_ROOT is not set", file=sys.stderr)
        return 1
    tsa, vri, lu, uwr, ogma, cutblocks = load_inputs(Path(external), args.downloads)
    layer = build_land_base(vri, tsa, lu, uwr, ogma, cutblocks)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    layer.to_file(args.out, driver="GPKG")
    summary = summarize(layer, direct_uwr_ha=direct_uwr_area(tsa, uwr))
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary, index=False)
    print(summary.to_string(index=False))
    print(f"wrote {args.out}")
    print(f"wrote {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
