"""Tests for the WS4 fragment builder."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely import wkb
from shapely.geometry import box

import build_ws4_fragments


def make_inputs() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Build small synthetic fragments, UWR, and LU layers.

    Returns
    -------
    tuple of geopandas.GeoDataFrame
        Fragments, UWR, and landscape units.
    """
    fragments = gpd.GeoDataFrame(
        {
            "FEATURE_ID": [1, 2],
            "au": [2701000, 2702000],
            "curve1": [2701000, 2702000],
            "curve2": [2721000, 2722000],
            "thlb": [1, 0],
            "thlb_area": [100.0, 0.0],
            "BEC_ZONE_CODE": ["ICH", "ESSF"],
            "BEC_SUBZONE": ["wk", "vc"],
        },
        geometry=[box(0, 0, 1000, 1000), box(2000, 0, 3000, 1000)],
        crs=3005,
    )
    uwr = gpd.GeoDataFrame(
        {"UWR_NUMBER": ["u-3-005"], "TIMBER_HARVEST_CODE": ["NO HARVEST ZONE"]},
        geometry=[box(0, 0, 500, 1000)],
        crs=3005,
    )
    lu = gpd.GeoDataFrame(
        {"LANDSCAPE_UNIT_NAME": ["Test LU"]},
        geometry=[box(0, 0, 3000, 1000)],
        crs=3005,
    )
    return fragments, uwr, lu


def test_load_fragments(tmp_path: Path) -> None:
    """The WKB checkpoint loads as a GeoDataFrame in EPSG:3005."""
    fragments, _, _ = make_inputs()
    path = tmp_path / "checkpoint.feather"
    frame = pd.DataFrame(
        {
            "FEATURE_ID": fragments["FEATURE_ID"],
            "au": fragments["au"],
            "curve1": fragments["curve1"],
            "thlb_area": fragments["thlb_area"],
            "geometry": [wkb.dumps(geom) for geom in fragments.geometry],
        }
    )
    frame.to_feather(path)
    loaded = build_ws4_fragments.load_fragments(path)
    assert loaded.crs.to_epsg() == 3005
    assert len(loaded) == 2


def test_caribou_uwr_fraction_empty() -> None:
    """An empty UWR or no intersection returns zero."""
    fragments, _, _ = make_inputs()
    empty = gpd.GeoDataFrame({"UWR_NUMBER": [], "TIMBER_HARVEST_CODE": []}, geometry=[], crs=3005)
    assert build_ws4_fragments.caribou_uwr_fraction(fragments, empty).tolist() == [0.0, 0.0]
    far = gpd.GeoDataFrame(
        {"UWR_NUMBER": ["u-3-005"], "TIMBER_HARVEST_CODE": ["NO HARVEST ZONE"]},
        geometry=[box(9000, 0, 9500, 1000)],
        crs=3005,
    )
    assert build_ws4_fragments.caribou_uwr_fraction(fragments, far).tolist() == [0.0, 0.0]


def test_caribou_uwr_fraction() -> None:
    """The fraction is one half for the polygon that overlaps UWR by half."""
    fragments, uwr, _ = make_inputs()
    fraction = build_ws4_fragments.caribou_uwr_fraction(fragments, uwr)
    assert fraction.tolist() == [0.5, 0.0]


def test_attach_landscape_unit() -> None:
    """The LU name is attached to each fragment."""
    fragments, _, lu = make_inputs()
    joined = build_ws4_fragments.attach_landscape_unit(fragments, lu)
    assert joined["lu_name"].tolist() == ["Test LU", "Test LU"]


def test_build_fragments_flags() -> None:
    """The UWR threshold and the zero-valued flags are applied."""
    fragments, uwr, lu = make_inputs()
    built = build_ws4_fragments.build_fragments(fragments, uwr, lu)
    assert built["caribou_uwr"].tolist() == [1, 0]
    assert built["caribou_core"].tolist() == [0, 0]
    assert built["caribou_matrix"].tolist() == [0, 0]
    assert built["area_ha"].tolist() == [100.0, 100.0]
    assert built["lu_bec"].tolist() == ["Test LU|ICHwk", "Test LU|ESSFvc"]


def test_summarize_fragments() -> None:
    """The summary reports all, THLB, and UWR areas."""
    fragments, uwr, lu = make_inputs()
    built = build_ws4_fragments.build_fragments(fragments, uwr, lu)
    summary = build_ws4_fragments.summarize_fragments(built).set_index("class")
    assert summary.loc["all_fragments", "area_ha"] == 200.0
    assert summary.loc["thlb", "area_ha"] == 100.0
    assert summary.loc["caribou_uwr", "area_ha"] == 100.0


def test_main_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI writes the fragments and summary and passes the check."""
    fragments, uwr, lu = make_inputs()
    monkeypatch.setattr(build_ws4_fragments, "load_fragments", lambda path: fragments)
    monkeypatch.setattr(
        gpd,
        "read_file",
        lambda path: uwr if str(path).endswith("uwr.geojson") else lu,
    )
    code = build_ws4_fragments.main(
        [
            "--checkpoint",
            str(tmp_path / "x.feather"),
            "--uwr",
            str(tmp_path / "uwr.geojson"),
            "--lu",
            str(tmp_path / "lu.geojson"),
            "--out",
            str(tmp_path / "fragments.gpkg"),
            "--summary",
            str(tmp_path / "summary.csv"),
            "--check",
        ]
    )
    assert code == 0
    assert (tmp_path / "fragments.gpkg").is_file()
    assert (tmp_path / "summary.csv").is_file()


def test_main_check_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The check fails when an AU is missing."""
    fragments, _, _ = make_inputs()
    broken = fragments.copy()
    broken["au"] = None
    monkeypatch.setattr(build_ws4_fragments, "load_fragments", lambda path: fragments)
    monkeypatch.setattr(build_ws4_fragments, "build_fragments", lambda f, u, l: broken)
    monkeypatch.setattr(
        build_ws4_fragments,
        "summarize_fragments",
        lambda f: pd.DataFrame([{"class": "x", "area_ha": 0.0, "fragments": 0}]),
    )
    monkeypatch.setattr(
        build_ws4_fragments.gpd,
        "read_file",
        lambda path: gpd.GeoDataFrame(geometry=[], crs=3005),
    )
    code = build_ws4_fragments.main(
        [
            "--checkpoint",
            str(tmp_path / "x.feather"),
            "--uwr",
            str(tmp_path / "uwr.geojson"),
            "--lu",
            str(tmp_path / "lu.geojson"),
            "--out",
            str(tmp_path / "fragments.gpkg"),
            "--summary",
            str(tmp_path / "summary.csv"),
            "--check",
        ]
    )
    assert code == 1
