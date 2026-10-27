#!/usr/bin/env python3
"""Build the WS4 fragment layer for TSA 27.

The fragments come from the P2 stand checkpoint. The build attaches the AU/curve/THLB
attributes, the caribou UWR intersection fraction, the landscape unit, and zero-valued
core/matrix/historical flags until those layers arrive.

Command-line usage::

    python scripts/build_ws4_fragments.py
    python scripts/build_ws4_fragments.py --check
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import wkb

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_CHECKPOINT: Path = ROOT / "data" / "vri_vclr1p_checkpoint8.feather"
DEFAULT_UWR: Path = ROOT / "data" / "downloads" / "bc" / "uwr.geojson"
DEFAULT_LU: Path = ROOT / "data" / "downloads" / "bc" / "lu.geojson"
DEFAULT_OGMA: Path = ROOT / "data" / "downloads" / "bc" / "ogma.geojson"
DEFAULT_OUT: Path = ROOT / "data" / "ws4" / "fragments.gpkg"
DEFAULT_SUMMARY: Path = ROOT / "metadata" / "ws4" / "tsa27_fragments_summary.csv"
DEFAULT_TSA: Path = ROOT / "data" / "tsa_boundaries.feather"


def load_fragments(path: Path) -> gpd.GeoDataFrame:
    """Load the P2 checkpoint and convert WKB geometry to EPSG:3005.

    Parameters
    ----------
    path : Path
        Feather checkpoint with a WKB ``geometry`` column.

    Returns
    -------
    geopandas.GeoDataFrame
        The stand checkpoint as a GeoDataFrame.
    """
    frame = pd.read_feather(path)
    geometry = [wkb.loads(value) for value in frame["geometry"]]
    return gpd.GeoDataFrame(frame.drop(columns=["geometry"]), geometry=geometry, crs=3005)


def caribou_uwr_fraction(fragments: gpd.GeoDataFrame, uwr: gpd.GeoDataFrame) -> pd.Series:
    """Return the fraction of each fragment covered by UWR u-3-005 no-harvest.

    Parameters
    ----------
    fragments : geopandas.GeoDataFrame
        Fragment polygons in EPSG:3005.
    uwr : geopandas.GeoDataFrame
        Ungulate winter range polygons.

    Returns
    -------
    pandas.Series
        Coverage fraction from 0 to 1, indexed like ``fragments``.
    """
    caribou = uwr[
        uwr["UWR_NUMBER"].astype(str).str.lower().str.startswith("u-3-005")
        & (uwr["TIMBER_HARVEST_CODE"].astype(str).str.upper() == "NO HARVEST ZONE")
    ].to_crs(3005)
    if caribou.empty:
        return pd.Series(0.0, index=fragments.index)
    clipped = gpd.clip(fragments[["geometry"]], caribou.union_all())
    if clipped.empty:
        return pd.Series(0.0, index=fragments.index)
    inter_area = clipped.geometry.area.groupby(clipped.index).sum()
    fraction = inter_area / fragments.geometry.area
    return pd.Series(fraction.reindex(fragments.index).fillna(0.0).clip(0.0, 1.0))


def attach_landscape_unit(fragments: gpd.GeoDataFrame, lu: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Attach the landscape-unit name by spatial join.

    Parameters
    ----------
    fragments : geopandas.GeoDataFrame
        Fragment polygons.
    lu : geopandas.GeoDataFrame
        Landscape-unit polygons.

    Returns
    -------
    geopandas.GeoDataFrame
        Fragments with a ``lu_name`` column.
    """
    lu_3005 = lu.to_crs(3005)[["LANDSCAPE_UNIT_NAME", "geometry"]]
    joined = gpd.sjoin(fragments, lu_3005, how="left", predicate="intersects").drop(
        columns=["index_right"], errors="ignore"
    )
    joined = joined[~joined.index.duplicated(keep="first")]
    return joined.rename(columns={"LANDSCAPE_UNIT_NAME": "lu_name"})


def build_fragments(
    fragments: gpd.GeoDataFrame, uwr: gpd.GeoDataFrame, lu: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """Attach the fragment attributes and caribou flags.

    Parameters
    ----------
    fragments : geopandas.GeoDataFrame
        Stand checkpoint.
    uwr : geopandas.GeoDataFrame
        Ungulate winter range.
    lu : geopandas.GeoDataFrame
        Landscape units.

    Returns
    -------
    geopandas.GeoDataFrame
        WS4 fragments with area, AU, curve, caribou, and LU attributes.
    """
    out = attach_landscape_unit(fragments.copy(), lu)
    out["fragment_id"] = out["FEATURE_ID"].astype(str)
    out["area_ha"] = out.geometry.area / 10_000
    out["thlb_area_ha"] = out["thlb_area"].fillna(0.0)
    out["caribou_uwr_frac"] = caribou_uwr_fraction(fragments, uwr)
    out["caribou_uwr"] = (out["caribou_uwr_frac"] >= 0.5).astype(int)
    out["caribou_core"] = 0
    out["caribou_matrix"] = 0
    out["caribou_zone"] = 0
    out["caribou_immature"] = 0
    out["ogma"] = 0
    out["lu_bec"] = (
        out["lu_name"].fillna("UNK").astype(str)
        + "|"
        + out["BEC_ZONE_CODE"].fillna("UNK").astype(str)
        + out["BEC_SUBZONE"].fillna("").astype(str)
    )
    return out


def summarize_fragments(fragments: gpd.GeoDataFrame) -> pd.DataFrame:
    """Summarize the fragment land base.

    Parameters
    ----------
    fragments : geopandas.GeoDataFrame
        Fragments with ``area_ha``, ``thlb_area_ha``, and ``caribou_uwr``.

    Returns
    -------
    pandas.DataFrame
        One row per class with area and fragment count.
    """
    rows = [
        {
            "class": "all_fragments",
            "area_ha": float(fragments["area_ha"].sum()),
            "fragments": len(fragments),
        },
        {
            "class": "thlb",
            "area_ha": float(fragments["thlb_area_ha"].sum()),
            "fragments": int((fragments["thlb_area_ha"] > 0).sum()),
        },
        {
            "class": "caribou_uwr",
            "area_ha": float(fragments.loc[fragments["caribou_uwr"] == 1, "area_ha"].sum()),
            "fragments": int((fragments["caribou_uwr"] == 1).sum()),
        },
    ]
    return pd.DataFrame(rows)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the fragment build.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` on success, ``1`` when the check fails.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--uwr", type=Path, default=DEFAULT_UWR)
    parser.add_argument("--lu", type=Path, default=DEFAULT_LU)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    fragments = load_fragments(args.checkpoint)
    uwr = gpd.read_file(args.uwr)
    lu = gpd.read_file(args.lu)
    built = build_fragments(fragments, uwr, lu)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    built.to_file(args.out, driver="GPKG")
    summary = summarize_fragments(built)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary, index=False)
    print(summary.to_string(index=False))
    print(f"fragments={len(built)}")
    print(f"wrote {args.out}")
    print(f"wrote {args.summary}")
    if args.check and (built["au"].isna().any() or built["curve1"].isna().any() or len(built) == 0):
        print("ERROR: missing AU/curve assignment or empty fragment layer", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
