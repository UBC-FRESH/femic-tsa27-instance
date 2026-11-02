"""Tests for the TSA 27 ALS feasibility helpers."""

from __future__ import annotations

import pytest
from shapely.geometry import Point

pytest.importorskip("geopandas")

import audit_als_inventory_feasibility


def test_distance_summary_handles_empty_and_odd_counts() -> None:
    """The summary handles an empty list and an odd count."""
    assert audit_als_inventory_feasibility.distance_summary([]) is None
    assert audit_als_inventory_feasibility.distance_summary([3.0, 1.0, 2.0]) == {
        "min": 1.0,
        "median": 2.0,
        "max": 3.0,
    }


def test_distance_summary_uses_midpoint_for_even_counts() -> None:
    """An even count uses the mean of the two middle values."""
    assert audit_als_inventory_feasibility.distance_summary([1.0, 2.0, 3.0, 4.0]) == {
        "min": 1.0,
        "median": 2.5,
        "max": 4.0,
    }


def test_tile_hit_years_and_nearest_distance() -> None:
    """Tile membership and distance use the tile bounding boxes."""
    tiles = [
        {"bbox_epsg3005": [0.0, 0.0, 10.0, 10.0], "acquisition_year": 2019},
        {"bbox_epsg3005": [20.0, 0.0, 30.0, 10.0], "acquisition_year": 2021},
    ]
    assert audit_als_inventory_feasibility.tile_hit_years(Point(5.0, 5.0), tiles) == [2019]
    assert audit_als_inventory_feasibility.tile_hit_years(Point(25.0, 5.0), tiles) == [2021]
    assert audit_als_inventory_feasibility.tile_hit_years(Point(15.0, 5.0), tiles) == []
    assert audit_als_inventory_feasibility.nearest_distance(Point(15.0, 5.0), tiles) == 5.0


def test_request_table_flags_point_cloud_and_offsets() -> None:
    """The request table carries priority, offset, and a 2 km bbox."""
    import geopandas as gpd

    inside = gpd.GeoDataFrame(
        {
            "SITE_IDENTIFIER": [1, 2],
            "TSA": [27.0, 27.0],
            "BEC_ZONE": ["ICH", "ICH"],
            "BEC_SBZ": ["mw", "mw"],
            "SAMPLE_ESTABLISHMENT_TYPE": ["PSP_G", "PSP_G"],
            "last_year": [1992, 2001],
            "visits": [2, 3],
            "BC_ALBERS_X": [1_500_000.0, 1_500_000.0],
            "BC_ALBERS_Y": [700_000.0, 720_000.0],
            "pc_years": [[2019], []],
            "nearest_pc_m": [0.0, 9000.0],
        },
        geometry=[Point(1_500_000.0, 700_000.0), Point(1_500_000.0, 720_000.0)],
        crs=3005,
    )
    table = audit_als_inventory_feasibility.request_table(inside, 2000.0).set_index(
        "site_identifier"
    )
    assert table.loc["1", "request_priority"] == "high"
    assert table.loc["1", "offset_years"] == "27"
    assert table.loc["1", "request_bbox_area_ha"] == pytest.approx(1600.0)
    assert table.loc["2", "request_priority"] == "secondary"
    assert table.loc["2", "offset_years"] == ""
