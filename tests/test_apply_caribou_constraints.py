"""Tests for the UWR schedule filter."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

import apply_caribou_constraints


def test_block_flags_and_filter() -> None:
    """A flagged block is removed and an unflagged block is retained."""
    export = gpd.GeoDataFrame(
        {
            "FRAGMENT_I": [1, 2],
            "BLOCK": [10, 20],
            "AU": [2701000, 2701000],
            "AREA_HA": [100.0, 200.0],
            "F_AGE": [80.0, 90.0],
        },
        geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1)],
        crs=3005,
    )
    fragments = gpd.GeoDataFrame(
        {
            "au": [2701000, 2701000],
            "area_ha": [100.0, 200.0],
            "PROJ_AGE_1": [80.0, 90.0],
            "caribou_uwr": [1, 0],
        },
        geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1)],
        crs=3005,
    )
    flags = apply_caribou_constraints.block_flags(export, fragments)
    assert flags.set_index("block_id")["caribou_uwr"].to_dict() == {10: 1, 20: 0}
    schedule = pd.DataFrame({"block_id": [10, 20], "treatment": ["CC", "CC"], "offset": [0, 0]})
    filtered = apply_caribou_constraints.filter_schedule(schedule, flags)
    assert filtered["block_id"].tolist() == [20]


def test_main_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI writes the filtered schedule and the summary."""
    schedule = tmp_path / "schedule.csv"
    schedule.write_text("block_id,treatment,offset\n10,CC,0\n20,CC,0\n", encoding="utf-8")
    export = gpd.GeoDataFrame(
        {
            "FRAGMENT_I": [1, 2],
            "BLOCK": [10, 20],
            "AU": [2701000, 2701000],
            "AREA_HA": [100.0, 200.0],
            "F_AGE": [80.0, 90.0],
        },
        geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1)],
        crs=3005,
    )
    fragments = gpd.GeoDataFrame(
        {
            "au": [2701000, 2701000],
            "area_ha": [100.0, 200.0],
            "PROJ_AGE_1": [80.0, 90.0],
            "caribou_uwr": [1, 0],
        },
        geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1)],
        crs=3005,
    )
    monkeypatch.setattr(
        gpd,
        "read_file",
        lambda path: export if str(path).endswith(".shp") else fragments,
    )
    code = apply_caribou_constraints.main(
        [
            "--schedule",
            str(schedule),
            "--fragments",
            str(tmp_path / "fragments.gpkg"),
            "--export",
            str(tmp_path / "export.shp"),
            "--out",
            str(tmp_path / "out.csv"),
            "--summary",
            str(tmp_path / "summary.csv"),
        ]
    )
    assert code == 0
    assert (tmp_path / "out.csv").is_file()
    assert (tmp_path / "summary.csv").is_file()
