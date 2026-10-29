"""Tests for the UWR timing and year-by-year screen helpers."""

from __future__ import annotations

import pandas as pd

import build_uwr_timing
import build_year_by_year_screen


def test_summarize_positive_and_selected() -> None:
    """The summary ranks positive rows and respects the five-year cap."""
    frame = pd.DataFrame(
        {
            "block_id": [1, 2],
            "volume_m3": [600_000.0, 600_000.0],
            "margin": [60_000.0, -1.0],
            "margin_per_m3": [0.1, -0.000001],
        }
    )
    summary = build_uwr_timing.summarize(frame)
    assert summary["positive_volume_m3"] == 600_000.0
    assert summary["positive_share"] == 0.5
    assert summary["selected_m3"] == 600_000.0


def test_fire_adjust_removes_volume_and_keeps_fixed_cost() -> None:
    """No-salvage adjustment scales revenue and variable cost, not fixed cost."""
    frame = pd.DataFrame(
        {
            "block_id": [1],
            "volume_m3": [10.0],
            "haul_per_m3": [2.0],
            "revenue": [1000.0],
            "cost": [800.0],
            "margin": [200.0],
            "margin_per_m3": [20.0],
        }
    )
    adjusted = build_year_by_year_screen.fire_adjust(frame, {1: 5.0})
    assert adjusted.volume_m3.iloc[0] == 5.0
    assert adjusted.burned_m3.iloc[0] == 5.0
    assert adjusted.revenue.iloc[0] == 500.0
    assert adjusted.cost.iloc[0] == 450.0
    assert adjusted.margin.iloc[0] == 50.0


def test_price_adjust_scales_revenue_and_optional_stumpage() -> None:
    """The price screen scales revenue and can index stumpage."""
    frame = pd.DataFrame(
        {
            "block_id": [1],
            "volume_m3": [10.0],
            "revenue": [1000.0],
            "cost": [800.0],
            "margin": [200.0],
            "margin_per_m3": [20.0],
        }
    )
    price_only = build_year_by_year_screen.price_adjust(frame, 0.5, stumpage_rate=None)
    assert price_only.revenue.iloc[0] == 500.0
    assert price_only.cost.iloc[0] == 800.0
    assert price_only.margin.iloc[0] == -300.0

    indexed = build_year_by_year_screen.price_adjust(frame, 0.5, stumpage_rate=10.0)
    assert indexed.cost.iloc[0] == 700.0
    assert indexed.margin.iloc[0] == -200.0
