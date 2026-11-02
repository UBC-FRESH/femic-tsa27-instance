"""Tests for the finite-number helper used by the operational scripts."""

from __future__ import annotations

from collections.abc import Callable

import pytest

pytest.importorskip("ws4")

from build_operational_pilot import finite_float as pilot_finite_float
from build_operational_screen import finite_float as screen_finite_float

HELPERS = [pilot_finite_float, screen_finite_float]


@pytest.mark.parametrize("helper", HELPERS)
def test_finite_float_accepts_numbers(helper: Callable[[object], float | None]) -> None:
    """Numeric strings and numbers are converted."""
    assert helper(2.5) == 2.5
    assert helper("3.25") == 3.25


@pytest.mark.parametrize("helper", HELPERS)
def test_finite_float_rejects_missing_and_non_finite(
    helper: Callable[[object], float | None],
) -> None:
    """Missing, non-numeric, NaN, and infinite values return None."""
    assert helper(None) is None
    assert helper("missing") is None
    assert helper(float("nan")) is None
    assert helper(float("inf")) is None
