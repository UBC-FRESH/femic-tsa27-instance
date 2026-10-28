#!/usr/bin/env python3
"""Apply the UWR no-harvest constraint to a WS4 schedule.

The P3.1 fragment flags are keyed by FEATURE_ID; the Patchworks export uses FRAGMENT_I and
BLOCK. This script matches fragments by AU, area, and age, attaches the UWR flag to the
exported block ids, and drops blocks whose UWR flag is 1.

The matrix 13% and historical deferral are mapped in `config/ws4/caribou_constraints.yaml`
but are not enforced by this schedule filter.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_SCHEDULE: Path = ROOT / "scenarios" / "s3_base.schedule.csv"
DEFAULT_FRAGMENTS: Path = ROOT / "data" / "ws4" / "fragments.gpkg"
DEFAULT_EXPORT: Path = ROOT / "output" / "patchworks" / "fragments" / "fragments.shp"
DEFAULT_OUT: Path = ROOT / "scenarios" / "s3_base_caribou_uwr_excluded.schedule.csv"
DEFAULT_SUMMARY: Path = ROOT / "metadata" / "ws4" / "caribou_schedule_filter.csv"


def block_flags(export: gpd.GeoDataFrame, fragments: gpd.GeoDataFrame) -> pd.DataFrame:
    """Map exported block ids to the P3.1 UWR flag.

    Parameters
    ----------
    export : geopandas.GeoDataFrame
        Patchworks fragments with ``FRAGMENT_I``, ``BLOCK``, ``AU``, ``AREA_HA``, ``F_AGE``.
    fragments : geopandas.GeoDataFrame
        P3.1 fragments with ``au``, ``area_ha``, ``PROJ_AGE_1``, ``caribou_uwr``.

    Returns
    -------
    pandas.DataFrame
        One row per block with ``block_id`` and ``caribou_uwr``.
    """
    left = pd.DataFrame(
        {
            "block_id": export["BLOCK"].astype(int),
            "au": export["AU"].astype(int),
            "area_key": export["AREA_HA"].astype(float).round(3),
            "age_key": export["F_AGE"].astype(float).round(0),
        }
    )
    right = pd.DataFrame(
        {
            "au": fragments["au"].astype(int),
            "area_key": fragments["area_ha"].astype(float).round(3),
            "age_key": fragments["PROJ_AGE_1"].astype(float).round(0),
            "caribou_uwr": fragments["caribou_uwr"].astype(int),
        }
    )
    merged = left.merge(right, on=["au", "area_key", "age_key"], how="left")
    merged["caribou_uwr"] = merged["caribou_uwr"].fillna(0).astype(int)
    dataframe = pd.DataFrame(merged.groupby("block_id", as_index=False)[["caribou_uwr"]].max())
    return dataframe.sort_values("block_id").reset_index(drop=True)


def filter_schedule(schedule: pd.DataFrame, flags: pd.DataFrame) -> pd.DataFrame:
    """Drop schedule rows whose block is flagged as UWR no-harvest.

    Parameters
    ----------
    schedule : pandas.DataFrame
        Schedule with ``block_id``, ``treatment``, and ``offset``.
    flags : pandas.DataFrame
        Block flags with ``block_id`` and ``caribou_uwr``.

    Returns
    -------
    pandas.DataFrame
        The filtered schedule.
    """
    merged = schedule.merge(flags, on="block_id", how="left")
    merged["caribou_uwr"] = merged["caribou_uwr"].fillna(0).astype(int)
    return merged[merged["caribou_uwr"] == 0][["block_id", "treatment", "offset"]].copy()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the schedule filter.

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
    parser.add_argument("--schedule", type=Path, default=DEFAULT_SCHEDULE)
    parser.add_argument("--fragments", type=Path, default=DEFAULT_FRAGMENTS)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args(argv)
    schedule = pd.read_csv(args.schedule)
    export = gpd.read_file(args.export)
    fragments = gpd.read_file(args.fragments)
    flags = block_flags(export, fragments)
    filtered = filter_schedule(schedule, flags)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(args.out, index=False)
    summary = pd.DataFrame(
        [
            {"class": "schedule_rows", "value": len(schedule)},
            {"class": "uwr_flagged_blocks", "value": int(flags["caribou_uwr"].sum())},
            {"class": "excluded_rows", "value": len(schedule) - len(filtered)},
            {"class": "retained_rows", "value": len(filtered)},
        ]
    )
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary, index=False)
    print(summary.to_string(index=False))
    print(f"wrote {args.out}")
    print(f"wrote {args.summary}")
    if len(filtered) == 0:
        print("ERROR: no schedule rows remain", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
