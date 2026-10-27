"""Tests for the provisional land-base builder."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

import build_land_base


def make_inputs() -> tuple[
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
]:
    """Build small synthetic inputs in EPSG:3005.

    Returns
    -------
    tuple of geopandas.GeoDataFrame
        TSA, VRI, LU, UWR, OGMA, and cutblocks.
    """
    tsa = gpd.GeoDataFrame({"TSA_NUMBER": ["27"]}, geometry=[box(0, 0, 20, 10)], crs=3005)
    vri = gpd.GeoDataFrame(
        {
            "BCLCS_LEVEL_1": ["V", "N"],
            "BCLCS_LEVEL_2": ["T", "N"],
            "BEC_ZONE_CODE": ["ICH", "ESSF"],
            "BEC_SUBZONE": ["mw", "wc"],
            "BEC_VARIANT": ["3", "2"],
        },
        geometry=[box(0, 0, 10, 10), box(10, 0, 20, 10)],
        crs=3005,
    )
    lu = gpd.GeoDataFrame(
        {
            "LANDSCAPE_UNIT_NAME": ["Test LU"],
            "BIODIVERSITY_EMPHASIS_OPTION": ["Intermediate"],
        },
        geometry=[box(0, 0, 20, 10)],
        crs=3005,
    )
    uwr = gpd.GeoDataFrame(
        {"UWR_NUMBER": ["u-3-005"], "TIMBER_HARVEST_CODE": ["NO HARVEST ZONE"]},
        geometry=[box(0, 0, 5, 10)],
        crs=3005,
    )
    ogma = gpd.GeoDataFrame(
        {"OGMA_TYPE": ["1"]},
        geometry=[box(15, 0, 20, 10)],
        crs=3005,
    )
    cutblocks = gpd.GeoDataFrame(
        {"HARVEST_MID_YEAR_CALENDAR": [2020]},
        geometry=[box(0, 0, 9, 10)],
        crs=3005,
    )
    return tsa, vri, lu, uwr, ogma, cutblocks


def test_classify_forested() -> None:
    """Only vegetated, treed polygons are forested."""
    _, vri, *_ = make_inputs()
    assert build_land_base.classify_forested(vri).tolist() == [True, False]


def test_caribou_uwr_mask() -> None:
    """Only the u-3-005 no-harvest polygons are selected."""
    _, _, _, uwr, _, _ = make_inputs()
    mask = build_land_base.caribou_uwr_mask(uwr)
    assert mask.tolist() == [True]


def test_build_land_base_flags() -> None:
    """The build attaches forest, LU, caribou, OGMA, and cutblock attributes."""
    tsa, vri, lu, uwr, ogma, cutblocks = make_inputs()
    layer = build_land_base.build_land_base(vri, tsa, lu, uwr, ogma, cutblocks)
    assert len(layer) == 2
    assert set(layer["caribou_uwr"].tolist()) == {1, 0}
    assert set(layer["ogma"].tolist()) == {0, 1}
    assert layer["is_forested"].tolist() == [True, False]
    assert layer["thlb_candidate"].tolist() == [False, False]
    assert layer["bec_label"].tolist() == ["ICH/mw/3", "ESSF/wc/2"]
    assert layer["last_harvest_year"].tolist() == [2020, -1]
    assert set(layer["LANDSCAPE_UNIT_NAME"].tolist()) == {"Test LU"}


def test_summarize() -> None:
    """The summary reports gross area and each flag."""
    tsa, vri, lu, uwr, ogma, cutblocks = make_inputs()
    layer = build_land_base.build_land_base(vri, tsa, lu, uwr, ogma, cutblocks)
    summary = build_land_base.summarize(layer)
    rows = summary.set_index("class")
    assert rows.loc["gross_clip", "polygons"] == 2
    assert rows.loc["is_forested", "polygons"] == 1
    assert rows.loc["caribou_uwr", "polygons"] == 1
    assert rows.loc["ogma", "polygons"] == 1
    assert rows.loc["thlb_candidate", "polygons"] == 0


def test_load_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loader returns the six inputs in the documented order."""
    inputs = make_inputs()
    tsa, vri, lu, uwr, ogma, cutblocks = inputs

    def fake_read_file(path: object, **kwargs: object) -> gpd.GeoDataFrame:
        text = str(path)
        if "FADM_TSA" in text:
            return tsa
        if "VEG_COMP" in text:
            return vri
        if text.endswith("lu.geojson"):
            return lu
        if text.endswith("uwr.geojson"):
            return uwr
        if text.endswith("ogma.geojson"):
            return ogma
        return cutblocks

    monkeypatch.setattr(gpd, "read_file", fake_read_file)
    loaded = build_land_base.load_inputs(Path("/data"), Path("/downloads"))
    assert len(loaded) == 6
    assert "TSA_NUMBER" in loaded[0].columns


def test_main_missing_environment(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI fails clearly when the external data root is unset."""
    monkeypatch.delenv("FEMIC_EXTERNAL_DATA_ROOT", raising=False)
    assert build_land_base.main([]) == 1
    assert "FEMIC_EXTERNAL_DATA_ROOT" in capsys.readouterr().err


def test_main_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI writes the GeoPackage and the summary."""
    monkeypatch.setenv("FEMIC_EXTERNAL_DATA_ROOT", str(tmp_path))
    inputs = make_inputs()
    monkeypatch.setattr(build_land_base, "load_inputs", lambda root, downloads: inputs)
    out = tmp_path / "land_base.gpkg"
    summary = tmp_path / "summary.csv"
    code = build_land_base.main(
        ["--out", str(out), "--summary", str(summary), "--downloads", str(tmp_path)]
    )
    assert code == 0
    assert out.is_file()
    assert summary.is_file()
