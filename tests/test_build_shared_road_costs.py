"""Tests for the shared-road cost allocator."""

from __future__ import annotations

import pandas as pd
import pytest

pytest.importorskip("scipy")

import build_shared_road_costs


def test_capital_recovery_factor() -> None:
    """The factor matches the annuity formula and handles a zero rate."""
    assert build_shared_road_costs.capital_recovery_factor(0.0, 10) == 0.1
    factor = build_shared_road_costs.capital_recovery_factor(0.05, 20)
    assert 0.0802 < factor < 0.0803


def test_segment_class_from_haul_rate() -> None:
    """Segment classes follow the class-based haul rates."""
    assert build_shared_road_costs.segment_class(0.06, 1000.0) == "highway"
    assert build_shared_road_costs.segment_class(0.10, 1000.0) == "paved"
    assert build_shared_road_costs.segment_class(0.16, 1000.0) == "resource"
    assert build_shared_road_costs.segment_class(0.50, 1000.0) == "non_truck"


def test_shortest_path_and_reconstruction() -> None:
    """Dijkstra finds the least-haul route and reconstructs its segments."""
    segments = pd.DataFrame(
        {
            "segment_id": [0, 1, 2],
            "from_vertex": [0, 1, 0],
            "to_vertex": [1, 2, 2],
            "length_m": [1000.0, 1000.0, 3000.0],
            "haul_cost": [0.10, 0.10, 0.30],
        }
    )
    adjacency = build_shared_road_costs.build_adjacency(segments)
    distance, previous = build_shared_road_costs.shortest_paths(adjacency, 2)
    assert distance[0] == 0.2
    path = build_shared_road_costs.reconstruct_path(previous, 0)
    assert path is not None
    segment_ids, haul, length = path
    assert sorted(segment_ids) == [0, 1]
    assert haul == 0.2
    assert length == 2000.0


def test_reconstruct_disconnected() -> None:
    """A vertex absent from the predecessor map has no route."""
    assert build_shared_road_costs.reconstruct_path({}, 0) is None
