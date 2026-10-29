"""Tests for the annual snapshot builder."""

from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import box

import build_annual_snapshots


def test_hbs_series_covers_snapshot_years() -> None:
    """The recovered HBS series covers every snapshot year."""
    path = (
        build_annual_snapshots.ROOT
        / "runtime/document_ingestion/tsa27-dp2022-fig4/figure4_recovered.csv"
    )
    if not path.exists():
        pytest.skip("HBS recovery artifact is not present in this checkout")
    frame = build_annual_snapshots.hbs_series()
    assert list(frame.year) == list(range(2017, 2027))
    assert frame.hbs_m3.notna().all()


def test_clip_area_ha_clips_and_measures() -> None:
    """Clipping returns hectares inside the boundary."""
    boundary = gpd.GeoDataFrame(geometry=[box(0, 0, 100, 100)], crs=3005)
    frame = gpd.GeoDataFrame(geometry=[box(50, 0, 150, 100)], crs=3005)
    clipped = build_annual_snapshots.clip_area_ha(frame, boundary)
    assert len(clipped) == 1
    assert clipped.area_ha.iloc[0] == 0.5
