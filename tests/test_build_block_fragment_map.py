"""Tests for the geometry-resolved block-to-fragment map."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

import build_block_fragment_map as mapping


def _export() -> gpd.GeoDataFrame:
    """Return a two-block export frame with one ambiguous key."""
    return gpd.GeoDataFrame(
        {
            "FRAGMENT_I": [1, 2],
            "BLOCK": [10, 20],
            "AU": [1, 1],
            "AREA_HA": [100.0, 100.0],
            "F_AGE": [80.0, 80.0],
        },
        geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1)],
        crs=3005,
    )


def _fragments() -> gpd.GeoDataFrame:
    """Return two fragments that share a key but have distinct geometry."""
    return gpd.GeoDataFrame(
        {
            "FEATURE_ID": [101, 102],
            "au": [1, 1],
            "area_ha": [100.0, 100.0],
            "PROJ_AGE_1": [80.0, 80.0],
            "caribou_uwr": [1, 0],
        },
        geometry=[box(0, 0, 1, 1), box(2, 0, 3, 1)],
        crs=3005,
    )


def test_add_keys() -> None:
    """The join key is rounded consistently."""
    frame = mapping.add_keys(_export(), au_col="AU", area_col="AREA_HA", age_col="F_AGE")
    assert frame["area_key"].tolist() == [100.0, 100.0]
    assert frame["age_key"].tolist() == [80.0, 80.0]


def test_candidate_pairs_and_resolve() -> None:
    """Two ambiguous blocks resolve to the geometry-identical fragment."""
    pairs = mapping.candidate_pairs(_export(), _fragments())
    assert len(pairs) == 4
    overrides, summary = mapping.resolve_overrides(pairs)
    assert summary["ambiguous_blocks"] == 2
    assert summary["override_blocks"] == 2
    assert summary["min_override_iou"] == 1.0
    assert overrides.set_index("block_id")["fragment_id"].to_dict() == {10: 101, 20: 102}


def test_resolve_tie_raises() -> None:
    """Two candidates with identical geometry cannot be disambiguated."""
    fragments = _fragments()
    fragments.loc[1, "geometry"] = box(0, 0, 1, 1)
    pairs = mapping.candidate_pairs(_export(), fragments)
    with pytest.raises(ValueError, match="tied at IoU"):
        mapping.resolve_overrides(pairs)


def test_resolve_below_threshold_raises() -> None:
    """A candidate that does not overlap cannot be accepted."""
    fragments = _fragments()
    fragments.loc[1, "geometry"] = box(10, 10, 11, 11)
    pairs = mapping.candidate_pairs(_export(), fragments)
    with pytest.raises(ValueError, match="no candidate above IoU"):
        mapping.resolve_overrides(pairs)


def _write_inputs(root: Path) -> tuple[Path, Path]:
    """Write the export shapefile and fragment GeoPackage."""
    export = _export()
    fragments = _fragments()
    export_path = root / "fragments.shp"
    fragments_path = root / "fragments.gpkg"
    export.to_file(export_path)
    fragments.to_file(fragments_path, driver="GPKG")
    return export_path, fragments_path


def test_main_writes_and_checks(tmp_path: Path) -> None:
    """The CLI writes the overrides and ``--check`` accepts the current file."""
    export_path, fragments_path = _write_inputs(tmp_path)
    overrides = tmp_path / "overrides.csv"
    summary = tmp_path / "summary.csv"
    args = [
        "--export",
        str(export_path),
        "--fragments",
        str(fragments_path),
        "--overrides",
        str(overrides),
        "--summary",
        str(summary),
    ]
    assert mapping.main(args) == 0
    assert overrides.is_file()
    assert summary.is_file()
    assert mapping.main([*args, "--check"]) == 0
    changed = pd.read_csv(overrides)
    changed.loc[0, "fragment_id"] = 999
    changed.to_csv(overrides, index=False)
    assert mapping.main([*args, "--check"]) == 1
