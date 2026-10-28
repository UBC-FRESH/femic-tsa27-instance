"""Tests for the caribou scenario runner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

import run_caribou_scenarios


def write_registry(tmp_path: Path) -> Path:
    """Write a small registry with one supported and one unavailable scenario.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory.

    Returns
    -------
    Path
        Registry path.
    """
    schedule = tmp_path / "schedule.csv"
    schedule.write_text("block_id,treatment,offset\n1,CC,0\n", encoding="utf-8")
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        yaml.safe_dump(
            {
                "dataset": str(tmp_path / "dataset"),
                "scenarios": {
                    "s3": {"status": "supported", "schedule": str(schedule)},
                    "s4": {"status": "unavailable", "reason": "missing layer"},
                },
            }
        ),
        encoding="utf-8",
    )
    return registry


def test_load_registry_rejects_empty(tmp_path: Path) -> None:
    """A registry without scenarios is rejected."""
    path = tmp_path / "r.yaml"
    path.write_text("schema_version: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="scenarios"):
        run_caribou_scenarios.load_registry(path)


def test_build_command(tmp_path: Path) -> None:
    """The simulate command carries dataset, schedule, years, and out."""
    command = run_caribou_scenarios.build_command(
        tmp_path / "dataset", tmp_path / "s.csv", tmp_path / "out", 250
    )
    assert command[:2] == ["ws4", "simulate"]
    assert "--years" in command


def test_main_check(tmp_path: Path) -> None:
    """The check writes the record without running the simulation."""
    registry = write_registry(tmp_path)
    record = tmp_path / "record.json"
    code = run_caribou_scenarios.main(
        [
            "--registry",
            str(registry),
            "--runs",
            str(tmp_path / "runs"),
            "--record",
            str(record),
            "--check",
        ]
    )
    assert code == 0
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["scenarios"][0]["scenario"] == "s3"
    assert payload["scenarios"][0]["status"] == "supported"


def test_main_unknown(tmp_path: Path) -> None:
    """An unknown scenario is an error."""
    registry = write_registry(tmp_path)
    code = run_caribou_scenarios.main(
        ["--registry", str(registry), "--runs", str(tmp_path / "runs"), "--run", "nope", "--check"]
    )
    assert code == 1


def test_main_run_with_mock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The run path records the scenario and calls the simulator."""
    registry = write_registry(tmp_path)
    record = tmp_path / "record.json"
    calls: list[list[str]] = []

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command: list[str], **kwargs: object) -> Completed:
        calls.append(command)
        return Completed()

    monkeypatch.setattr(subprocess, "run", fake_run)
    code = run_caribou_scenarios.main(
        [
            "--registry",
            str(registry),
            "--runs",
            str(tmp_path / "runs"),
            "--record",
            str(record),
            "--run",
            "s3",
        ]
    )
    assert code == 0
    assert calls
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["scenarios"][0]["status"] == "supported"


def test_main_unsupported(tmp_path: Path) -> None:
    """An unsupported scenario is recorded, not run."""
    registry = write_registry(tmp_path)
    record = tmp_path / "record.json"
    code = run_caribou_scenarios.main(
        [
            "--registry",
            str(registry),
            "--runs",
            str(tmp_path / "runs"),
            "--record",
            str(record),
            "--run",
            "s4",
        ]
    )
    assert code == 0
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["scenarios"][0]["status"] == "unavailable"


def test_main_missing_schedule(tmp_path: Path) -> None:
    """A supported scenario with a missing schedule is an error."""
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        yaml.safe_dump(
            {
                "dataset": str(tmp_path / "dataset"),
                "scenarios": {"s3": {"status": "supported", "schedule": "missing.csv"}},
            }
        ),
        encoding="utf-8",
    )
    code = run_caribou_scenarios.main(
        [
            "--registry",
            str(registry),
            "--runs",
            str(tmp_path / "runs"),
            "--record",
            str(tmp_path / "record.json"),
            "--run",
            "s3",
        ]
    )
    assert code == 1
