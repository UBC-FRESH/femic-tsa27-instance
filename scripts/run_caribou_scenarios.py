#!/usr/bin/env python3
"""Run the supported caribou scenarios from the registry.

Only scenarios with ``status: supported`` are executed. ``proxy`` and ``unavailable``
scenarios are reported, not fabricated.

Command-line usage::

    python scripts/run_caribou_scenarios.py --check
    python scripts/run_caribou_scenarios.py --run s3_tsr5_base,s6_no_caribou
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import yaml

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY: Path = ROOT / "config" / "ws4" / "scenario_registry.yaml"
DEFAULT_RUNS: Path = ROOT / "runs"
DEFAULT_RECORD: Path = ROOT / "metadata" / "ws4" / "scenario_runs.json"


def load_registry(path: Path) -> dict[str, object]:
    """Load the scenario registry.

    Parameters
    ----------
    path : Path
        Registry YAML path.

    Returns
    -------
    dict
        Parsed registry.

    Raises
    ------
    ValueError
        When the registry has no scenarios mapping.
    """
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("scenarios"), dict):
        raise ValueError(f"{path} has no scenarios mapping")
    return payload


def portable_path(path: Path) -> str:
    """Return a repo-relative path when possible, else the file name.

    Parameters
    ----------
    path : Path
        Path to render.

    Returns
    -------
    str
        Repo-relative path or file name.
    """
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def build_command(dataset: Path, schedule: Path, out: Path, years: int) -> list[str]:
    """Build the ws4 simulate command.

    Parameters
    ----------
    dataset : Path
        Compiled dataset.
    schedule : Path
        Scenario schedule.
    out : Path
        Run output directory.
    years : int
        Simulation horizon.

    Returns
    -------
    list of str
        Command vector.
    """
    return [
        "ws4",
        "simulate",
        "--dataset",
        str(dataset),
        "--schedule",
        str(schedule),
        "--years",
        str(years),
        "--out",
        str(out),
    ]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the supported scenarios.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` on success, ``1`` on a check/simulation failure.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--years", type=int, default=250)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--run", type=str, default="")
    args = parser.parse_args(argv)
    registry = load_registry(args.registry)
    scenarios_raw = registry["scenarios"]
    assert isinstance(scenarios_raw, dict)
    scenarios = scenarios_raw
    dataset = ROOT / str(registry.get("dataset", "build/compiled"))
    selected = [name for name in str(args.run).split(",") if name] or [
        name for name, spec in scenarios.items() if spec.get("status") == "supported"
    ]
    records: list[dict[str, object]] = []
    for name in selected:
        spec = scenarios.get(name)
        if not isinstance(spec, dict):
            print(f"ERROR unknown scenario {name}", file=sys.stderr)
            return 1
        status = str(spec.get("status"))
        schedule = ROOT / str(spec.get("schedule", ""))
        if status != "supported":
            records.append(
                {
                    "scenario": name,
                    "status": status,
                    "note": spec.get("reason", spec.get("note", "")),
                }
            )
            continue
        if not schedule.is_file():
            print(f"ERROR missing schedule {schedule}", file=sys.stderr)
            return 1
        out = args.runs / name
        command = build_command(dataset, schedule, out, args.years)
        records.append(
            {
                "scenario": name,
                "status": status,
                "schedule": portable_path(schedule),
                "out": portable_path(out),
                "command": [portable_path(Path(part)) if "/" in part else part for part in command],
            }
        )
        if args.check:
            continue
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            print(completed.stdout[-2000:], file=sys.stderr)
            print(completed.stderr[-2000:], file=sys.stderr)
            return 1
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps({"scenarios": records}, indent=2), encoding="utf-8")
    for record in records:
        print(f"{record['scenario']:<36} {record['status']}")
    print(f"wrote {args.record}")
    if args.check:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
