"""Tests for the analysis-unit builder."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

import build_analysis_units


def make_layer() -> gpd.GeoDataFrame:
    """Build a small land-base layer for the tests.

    Returns
    -------
    geopandas.GeoDataFrame
        Three polygons: assigned, missing site, and non-forested.
    """
    return gpd.GeoDataFrame(
        {
            "SPECIES_CD_1": ["BL", "CW", None],
            "SITE_INDEX": [12.0, None, None],
            "PROJ_AGE_1": [80.0, 120.0, None],
            "BEC_ZONE_CODE": ["ESSF", "ICH", "ESSF"],
            "BEC_SUBZONE": ["vc", "wk", "vc"],
            "OPENING_IND": ["N", "Y", "N"],
            "last_harvest_year": [-1, 2010, -1],
            "is_forested": [True, True, False],
            "thlb_candidate": [True, False, False],
        },
        geometry=[box(0, 0, 1000, 1000), box(1000, 0, 2000, 1000), box(2000, 0, 3000, 1000)],
        crs=3005,
    )


def test_species_group() -> None:
    """Species codes map to the documented groups."""
    assert build_analysis_units.species_group("BL") == "BL"
    assert build_analysis_units.species_group("SX") == "SX"
    assert build_analysis_units.species_group("FDI") == "FDI"
    assert build_analysis_units.species_group("ZZ") == "OTHER"
    assert build_analysis_units.species_group(None) == "UNK"


def test_site_index_class() -> None:
    """Site index bins follow the documented thresholds."""
    assert build_analysis_units.site_index_class(8) == "SI1"
    assert build_analysis_units.site_index_class(12) == "SI2"
    assert build_analysis_units.site_index_class(17) == "SI3"
    assert build_analysis_units.site_index_class(25) == "SI4"
    assert build_analysis_units.site_index_class(None) == "SI0"


def test_origin() -> None:
    """Opening or harvest signals mark a polygon as managed."""
    assert build_analysis_units.origin("Y", -1) == "managed"
    assert build_analysis_units.origin("N", 2010) == "managed"
    assert build_analysis_units.origin("N", -1) == "natural"


def test_assign_analysis_units() -> None:
    """Every polygon gets an AU ID or an explicit reason."""
    assigned = build_analysis_units.assign_analysis_units(make_layer())
    assert assigned["au_id"].tolist() == [
        "BL-ESSFvc-SI2-natural",
        "UNASSIGNED",
        "NONFOREST",
    ]
    assert assigned["au_reason"].tolist() == [
        "",
        "missing species, site index, or age",
        "not forested",
    ]
    assert assigned["au_origin"].tolist() == ["natural", "managed", "natural"]


def test_summarize_analysis_units() -> None:
    """The summary reports area, THLB area, and polygons by AU."""
    assigned = build_analysis_units.assign_analysis_units(make_layer())
    summary = build_analysis_units.summarize_analysis_units(assigned)
    rows = summary.set_index("au_id")
    assert rows.loc["BL-ESSFvc-SI2-natural", "area_ha"] == 100.0
    assert rows.loc["BL-ESSFvc-SI2-natural", "thlb_area_ha"] == 100.0
    assert rows.loc["UNASSIGNED", "area_ha"] == 100.0
    assert rows.loc["NONFOREST", "area_ha"] == 100.0
    assert rows.loc["BL-ESSFvc-SI2-natural", "polygons"] == 1


def test_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI writes the AU GeoPackage and summary."""
    layer = make_layer()
    monkeypatch.setattr(gpd, "read_file", lambda path: layer)
    gpkg = tmp_path / "au.gpkg"
    summary = tmp_path / "au.csv"
    code = build_analysis_units.main(
        ["--land-base", str(tmp_path / "x.gpkg"), "--gpkg", str(gpkg), "--summary", str(summary)]
    )
    assert code == 0
    assert gpkg.is_file()
    assert summary.is_file()


def test_main_check_fails_on_empty_au(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The check fails when an AU id is empty."""
    layer = make_layer()
    layer["au_id"] = ""
    layer["au_species"] = "BL"
    layer["au_bec"] = "ESSFvc"
    layer["au_si"] = "SI2"
    layer["au_origin"] = "natural"
    layer["au_reason"] = ""
    monkeypatch.setattr(gpd, "read_file", lambda path: make_layer())
    monkeypatch.setattr(build_analysis_units, "assign_analysis_units", lambda value: layer)
    code = build_analysis_units.main(
        [
            "--land-base",
            str(tmp_path / "x.gpkg"),
            "--gpkg",
            str(tmp_path / "au.gpkg"),
            "--summary",
            str(tmp_path / "au.csv"),
            "--check",
        ]
    )
    assert code == 1


def test_select_base_vri_without_project() -> None:
    """A layer without a PROJECT column is returned unchanged."""
    layer = make_layer()
    assert build_analysis_units.select_base_vri(layer) is layer


def test_select_base_vri_with_project() -> None:
    """The TSA base project is selected and other projects are dropped."""
    layer = make_layer()
    layer["PROJECT"] = ["REVELSTOKE_VRI", "OTHER", "REVELSTOKE_VRI"]
    selected = build_analysis_units.select_base_vri(layer)
    assert len(selected) == 2
