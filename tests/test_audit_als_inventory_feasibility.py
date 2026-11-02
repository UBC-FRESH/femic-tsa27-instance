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
