"""Tests for the TSA 27 seral-stage configuration."""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parent.parent / "config" / "seral.tsa27.yaml"


def test_seral_boundaries_match_tsr_age_classes() -> None:
    """The mature/overmature boundaries are the TSR 140 and 250 year classes."""
    payload = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    stages = payload["default"]
    assert stages["mature"] == {"min_age": 140, "max_age": 249}
    assert stages["overmature"] == {"min_age": 250, "max_age": None}
    assert stages["immature"]["max_age"] == 139


def test_seral_stages_are_contiguous() -> None:
    """Every stage ends one year before the next stage starts."""
    payload = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    stages = payload["default"]
    order = ["regenerating", "young", "immature", "mature", "overmature"]
    for previous, current in pairwise(order):
        assert stages[previous]["max_age"] + 1 == stages[current]["min_age"]
    assert stages["regenerating"]["min_age"] == 0
