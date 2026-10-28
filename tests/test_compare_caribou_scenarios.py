"""Tests for the caribou scenario comparison."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import compare_caribou_scenarios


def test_extract_and_compare(tmp_path: Path) -> None:
    """The comparison extracts harvest/treated and computes deltas."""
    for name, harvest, treated in [("s3", 50.0, 10.0), ("s6_no_caribou", 100.0, 20.0)]:
        run = tmp_path / name
        run.mkdir()
        pd.DataFrame(
            {
                "offset": [0, 0],
                "account": [
                    compare_caribou_scenarios.HARVEST,
                    compare_caribou_scenarios.TREATED,
                ],
                "value": [harvest, treated],
            }
        ).to_csv(run / "account_values.csv", index=False)
    record = tmp_path / "record.json"
    record.write_text(
        json.dumps(
            {
                "scenarios": [
                    {"scenario": "s3", "status": "supported", "out": "s3"},
                    {"scenario": "s6_no_caribou", "status": "supported", "out": "s6_no_caribou"},
                ]
            }
        ),
        encoding="utf-8",
    )
    compare_caribou_scenarios.ROOT = tmp_path
    frame = compare_caribou_scenarios.compare(record)
    row = frame.set_index("scenario").loc["s3"]
    assert row["harvest_delta_pct"] == -50.0
    assert row["treated_delta_pct"] == -50.0


def test_main_check(tmp_path: Path) -> None:
    """The CLI writes the comparison CSV and report."""
    record = tmp_path / "record.json"
    for name, harvest in [("s3", 50.0), ("s6_no_caribou", 100.0)]:
        run = tmp_path / name
        run.mkdir()
        pd.DataFrame(
            {
                "offset": [0, 0],
                "account": [
                    compare_caribou_scenarios.HARVEST,
                    compare_caribou_scenarios.TREATED,
                ],
                "value": [harvest, 10.0],
            }
        ).to_csv(run / "account_values.csv", index=False)
    record.write_text(
        json.dumps(
            {
                "scenarios": [
                    {"scenario": "s3", "status": "supported", "out": "s3"},
                    {
                        "scenario": "s6_no_caribou",
                        "status": "supported",
                        "out": "s6_no_caribou",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    compare_caribou_scenarios.ROOT = tmp_path
    code = compare_caribou_scenarios.main(
        [
            "--record",
            str(record),
            "--csv",
            str(tmp_path / "out.csv"),
            "--report",
            str(tmp_path / "out.md"),
            "--check",
        ]
    )
    assert code == 0
    assert (tmp_path / "out.csv").is_file()
    assert (tmp_path / "out.md").is_file()
