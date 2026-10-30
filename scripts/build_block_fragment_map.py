#!/usr/bin/env python3
"""Resolve the Patchworks block-to-fragment join with geometry.

The Patchworks export has no stable fragment id: ``FRAGMENT_I`` is a sequential index
and ``BLOCK`` is regenerated. The only shared key with the P3.1 fragment layer is the
rounded ``(AU, area_ha, age)`` tuple, which is ambiguous for a small number of blocks.

This script finds those ambiguous blocks and resolves each one by geometry. The export
polygon and the P3.1 fragment polygon come from the same stand, so the correct candidate
has an intersection-over-union of 1.0. The resolved pairs are written as a small override
table; unique-key blocks need no override.

Command-line usage::

    python scripts/build_block_fragment_map.py
    python scripts/build_block_fragment_map.py --check
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry.base import BaseGeometry

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_EXPORT: Path = ROOT / "output" / "patchworks" / "fragments" / "fragments.shp"
DEFAULT_FRAGMENTS: Path = ROOT / "data" / "ws4" / "fragments.gpkg"
DEFAULT_OVERRIDES: Path = ROOT / "metadata" / "ws4" / "block_fragment_overrides.csv"
DEFAULT_SUMMARY: Path = ROOT / "metadata" / "ws4" / "block_fragment_join_summary.csv"
IOU_THRESHOLD: float = 0.999


def add_keys(
    frame: gpd.GeoDataFrame, *, au_col: str, area_col: str, age_col: str
) -> gpd.GeoDataFrame:
    """Add the rounded join key columns to an export or fragment frame.

    Parameters
    ----------
    frame : geopandas.GeoDataFrame
        Export or P3.1 fragment frame.
    au_col : str
        Analysis-unit column.
    area_col : str
        Area column, in hectares.
    age_col : str
        Age column.

    Returns
    -------
    geopandas.GeoDataFrame
        A copy with ``au``, ``area_key``, and ``age_key`` columns.
    """
    out = frame.copy()
    out["au"] = out[au_col].astype(int)
    out["area_key"] = out[area_col].astype(float).round(3)
    out["age_key"] = out[age_col].astype(float).round(0)
    return out


def candidate_pairs(export: gpd.GeoDataFrame, fragments: gpd.GeoDataFrame) -> pd.DataFrame:
    """Join export blocks to key-matched fragments and compute the overlap.

    Parameters
    ----------
    export : geopandas.GeoDataFrame
        Patchworks export with ``BLOCK``, ``AU``, ``AREA_HA``, ``F_AGE``, and geometry.
    fragments : geopandas.GeoDataFrame
        P3.1 fragments with ``FEATURE_ID``, ``au``, ``area_ha``, ``PROJ_AGE_1``, and geometry.

    Returns
    -------
    pandas.DataFrame
        One row per candidate pair with ``block_id``, ``fragment_id``,
        ``caribou_uwr``, and ``iou``.
    """
    left = add_keys(export, au_col="AU", area_col="AREA_HA", age_col="F_AGE")
    right = add_keys(fragments, au_col="au", area_col="area_ha", age_col="PROJ_AGE_1")
    left = left[["BLOCK", "au", "area_key", "age_key", "geometry"]].rename(
        columns={"BLOCK": "block_id", "geometry": "geometry_export"}
    )
    right = right[["FEATURE_ID", "au", "area_key", "age_key", "caribou_uwr", "geometry"]].rename(
        columns={"FEATURE_ID": "fragment_id", "geometry": "geometry_fragment"}
    )
    merged = left.merge(right, on=["au", "area_key", "age_key"], how="left")
    merged["fragment_id"] = merged["fragment_id"].astype("Int64")
    merged["iou"] = [
        _iou(row.geometry_export, row.geometry_fragment) for row in merged.itertuples()
    ]
    return pd.DataFrame(merged.drop(columns=["geometry_export", "geometry_fragment"]))


def _iou(left: BaseGeometry | None, right: BaseGeometry | None) -> float:
    """Return the intersection-over-union of two polygons.

    Parameters
    ----------
    left, right : shapely.geometry.base.BaseGeometry or None
        Polygons in the same CRS.

    Returns
    -------
    float
        The intersection area divided by the union area, or ``0.0``.
    """
    if not isinstance(left, BaseGeometry) or not isinstance(right, BaseGeometry):
        return 0.0
    intersection = left.intersection(right).area
    union = left.union(right).area
    return float(intersection / union) if union else 0.0


def resolve_overrides(
    pairs: pd.DataFrame, threshold: float = IOU_THRESHOLD
) -> tuple[pd.DataFrame, dict[str, int | float]]:
    """Resolve every ambiguous block to exactly one fragment by overlap.

    Parameters
    ----------
    pairs : pandas.DataFrame
        Candidate pairs from :func:`candidate_pairs`.
    threshold : float, optional
        Minimum intersection-over-union for a resolved pair.

    Returns
    -------
    tuple of pandas.DataFrame and dict
        The override rows and the join summary.

    Raises
    ------
    ValueError
        When an ambiguous block has no candidate above the threshold, or two
        candidates tie at the best overlap.
    """
    counts = pairs.groupby("block_id")["fragment_id"].count()
    ambiguous = counts[counts > 1].index
    overrides: list[dict[str, object]] = []
    for block_id in ambiguous:
        candidates = pairs[pairs["block_id"] == block_id].sort_values("iou", ascending=False)
        best = float(candidates["iou"].iloc[0])
        if best < threshold:
            raise ValueError(
                f"block {block_id} has no candidate above IoU {threshold} (best {best:.4f})"
            )
        tied = int((candidates["iou"] >= best - 1e-9).sum())
        if tied > 1:
            raise ValueError(f"block {block_id} has {tied} candidates tied at IoU {best:.4f}")
        overrides.append(
            {
                "block_id": int(block_id),
                "fragment_id": int(candidates["fragment_id"].iloc[0]),
                "iou": round(best, 6),
            }
        )
    frame = pd.DataFrame(overrides, columns=["block_id", "fragment_id", "iou"])
    summary: dict[str, int | float] = {
        "export_blocks": int(pairs["block_id"].nunique()),
        "key_matched_blocks": int((counts > 0).sum()),
        "unmatched_blocks": int((counts == 0).sum()),
        "ambiguous_blocks": len(ambiguous),
        "override_blocks": len(frame),
        "min_override_iou": float(frame["iou"].min()) if len(frame) else 1.0,
    }
    return frame, summary


def main(argv: Sequence[str] | None = None) -> int:
    """Build or check the block-to-fragment override table.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` on success, ``1`` when ``--check`` finds a difference.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--fragments", type=Path, default=DEFAULT_FRAGMENTS)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    export = gpd.read_file(args.export).to_crs(3005)
    fragments = gpd.read_file(args.fragments).to_crs(3005)
    pairs = candidate_pairs(export, fragments)
    overrides, summary = resolve_overrides(pairs)
    summary_frame = pd.DataFrame(
        [{"metric": key, "value": str(value)} for key, value in summary.items()]
    )
    if args.check:
        existing = pd.read_csv(args.overrides) if args.overrides.is_file() else None
        if existing is None or not existing.equals(overrides):
            print(f"ERROR: {args.overrides} is missing or out of date", file=sys.stderr)
            return 1
        print(summary_frame.to_string(index=False))
        print(f"checked {args.overrides}")
        return 0
    args.overrides.parent.mkdir(parents=True, exist_ok=True)
    overrides.to_csv(args.overrides, index=False)
    summary_frame.to_csv(args.summary, index=False)
    print(summary_frame.to_string(index=False))
    print(f"wrote {args.overrides}")
    print(f"wrote {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
