"""Tests for the generated seral target table."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

import build_seral_targets as targets


def _presim() -> pd.DataFrame:
    """Return pre-simulation accounts for one LU/BEC."""
    return pd.DataFrame(
        {
            "account": [
                "feature.Area.Akolkolex_ESSFwc",
                "feature.Seral.mature_old.Akolkolex_ESSFwc",
                "feature.Seral.overmature.Akolkolex_ESSFwc",
            ],
            "value": [100.0, 60.0, 15.0],
        }
    )


def test_token() -> None:
    """The label token matches the partition labels."""
    assert targets.token("Akolkolex|ESSFwc") == "Akolkolex_ESSFwc"


def test_build_targets_bounds() -> None:
    """The absolute bounds are 40% and 10% of the LU/BEC area."""
    frame = targets.build_targets(_presim(), ["Akolkolex|ESSFwc"], periods=2)
    assert len(frame) == 4
    assert set(frame["account"]) == {
        "feature.Seral.mature_old.Akolkolex_ESSFwc",
        "feature.Seral.overmature.Akolkolex_ESSFwc",
    }
    mature = frame[frame["account"].str.contains("mature_old")]
    old = frame[frame["account"].str.contains("overmature")]
    assert mature["minimum"].tolist() == [40.0, 40.0]
    assert old["minimum"].tolist() == [10.0, 10.0]
    assert frame["period"].tolist() == [1, 2, 1, 2]


def test_build_targets_missing_account_raises() -> None:
    """A missing seral account is an error, not a silent zero."""
    with pytest.raises(ValueError, match="missing account"):
        targets.build_targets(_presim().iloc[0:1], ["Akolkolex|ESSFwc"])


def test_render_targets_parses() -> None:
    """The rendered text is valid YAML with the expected header and rows."""
    frame = targets.build_targets(_presim(), ["Akolkolex|ESSFwc"], periods=1)
    text = targets.render_targets(frame, ["dataset: build/compiled_zone_uwr"])
    assert text.startswith("# dataset: build/compiled_zone_uwr")
    parsed = yaml.safe_load(text)
    assert len(parsed["targets"]) == 2
    assert parsed["targets"][0]["period_width"] == 10


def test_summarise_targets() -> None:
    """The summary reports the area and the derived bounds."""
    summary = targets.summarise_targets(_presim(), ["Akolkolex|ESSFwc"], 0.40, 0.10)
    row = summary.iloc[0]
    assert row["area_ha"] == 100.0
    assert row["mature_old_ha"] == 60.0
    assert row["old_ha"] == 15.0
    assert row["min_mature_old_ha"] == 40.0
    assert row["min_old_ha"] == 10.0


def test_manifest_hash(tmp_path: Path) -> None:
    """A missing manifest returns a sentinel; a present one returns a digest."""
    assert targets._manifest_hash(tmp_path) == "missing"
    (tmp_path / "manifest.json").write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert len(targets._manifest_hash(tmp_path)) == 64


def test_main_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI writes a target file and ``--check`` compares it literally."""
    summary = tmp_path / "summary.csv"
    pd.DataFrame({"lubec": ["Akolkolex|ESSFwc"]}).to_csv(summary, index=False)
    dataset = tmp_path / "compiled"
    dataset.mkdir()
    (dataset / "manifest.json").write_text(json.dumps({"a": 1}), encoding="utf-8")
    monkeypatch.setattr(targets, "run_presim", lambda path, years=1: _presim())
    out = tmp_path / "targets.yaml"
    target_summary = tmp_path / "targets_summary.csv"
    args = [
        "--dataset",
        str(dataset),
        "--summary",
        str(summary),
        "--out",
        str(out),
        "--target-summary",
        str(target_summary),
        "--periods",
        "1",
    ]
    assert targets.main(args) == 0
    assert out.is_file()
    assert target_summary.is_file()
    assert targets.main([*args, "--check"]) == 0
    out.write_text("# stale\n", encoding="utf-8")
    assert targets.main([*args, "--check"]) == 1
