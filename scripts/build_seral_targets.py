#!/usr/bin/env python3
"""Build absolute seral targets from a zone-partitioned WS4 dataset.

The TSR seral targets are ratios:

- mature + old (>=140 years) >= 40% of the forested area by LU/BEC below the caribou line;
- old (>=250 years) >= 10% of the same area.

WS4 targets are absolute bounds, not ratios. Because the LU/BEC and zone totals are
constant through the simulation, the ratio becomes a fixed bound computed from the
pre-simulation account values.

The caribou line is not in the instance. This builder applies the below-the-line
targets everywhere and says so in the file header; do not read it as a legal target.

Command-line usage::

    python scripts/build_seral_targets.py
    python scripts/build_seral_targets.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

import pandas as pd
import yaml

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_DATASET: Path = ROOT / "build" / "compiled_zone_uwr"
DEFAULT_SUMMARY: Path = ROOT / "metadata" / "ws4" / "zone_partition_uwr_summary.csv"
DEFAULT_OUT: Path = ROOT / "config" / "ws4" / "targets" / "s3_seral_40_10.yaml"
DEFAULT_TARGET_SUMMARY: Path = ROOT / "metadata" / "ws4" / "seral_targets_summary.csv"
DEFAULT_PERIODS: int = 20
DEFAULT_PERIOD_WIDTH: int = 10
DEFAULT_MATURE_OLD: float = 0.40
DEFAULT_OLD: float = 0.10
DEFAULT_WEIGHT: float = 10000.0


def _as_float(value: object) -> float:
    """Convert a scalar to a float.

    Parameters
    ----------
    value : object
        A numeric or numeric string.

    Returns
    -------
    float
        The float value.
    """
    return float(str(value))


def token(lubec: str) -> str:
    """Return the label token for a LU/BEC value.

    Parameters
    ----------
    lubec : str
        ``<landscape unit>|<BEC>`` string.

    Returns
    -------
    str
        The token used by ``feature.Area.<token>`` and the seral labels.
    """
    return "".join(character if character.isalnum() else "_" for character in lubec)


def run_presim(dataset: Path, years: int = 1) -> pd.DataFrame:
    """Run a one-year simulation and return the pre-simulation accounts.

    Parameters
    ----------
    dataset : pathlib.Path
        Compiled zone dataset.
    years : int, optional
        Simulation horizon. One year is enough for the offset ``-1`` snapshot.

    Returns
    -------
    pandas.DataFrame
        ``account`` and ``value`` at offset ``-1``.

    Raises
    ------
    RuntimeError
        When ``ws4 simulate`` fails.
    """
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        schedule = root / "empty.csv"
        schedule.write_text("block_id,treatment,offset\n", encoding="utf-8")
        out = root / "run"
        completed = subprocess.run(
            [
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
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr[-2000:])
        frame = pd.read_csv(out / "account_values.csv")
    return frame.loc[frame["offset"] == -1, ["account", "value"]]


def build_targets(
    presim: pd.DataFrame,
    lubecs: Sequence[str],
    *,
    mature_old_fraction: float = DEFAULT_MATURE_OLD,
    old_fraction: float = DEFAULT_OLD,
    periods: int = DEFAULT_PERIODS,
    period_width: int = DEFAULT_PERIOD_WIDTH,
    weight: float = DEFAULT_WEIGHT,
) -> pd.DataFrame:
    """Build the absolute mature+old and old targets for every LU/BEC.

    Parameters
    ----------
    presim : pandas.DataFrame
        Pre-simulation accounts with ``account`` and ``value``.
    lubecs : sequence of str
        LU/BEC values in the dataset.
    mature_old_fraction : float, optional
        Minimum mature+old share of the LU/BEC area.
    old_fraction : float, optional
        Minimum old share of the LU/BEC area.
    periods : int, optional
        Number of accounting periods.
    period_width : int, optional
        Years per accounting period.
    weight : float, optional
        Target weight.

    Returns
    -------
    pandas.DataFrame
        One row per account and period.

    Raises
    ------
    ValueError
        When a required area or seral account is missing.
    """
    values = presim.set_index("account")["value"]
    rows: list[dict[str, object]] = []
    for lubec in lubecs:
        label = token(lubec)
        area_key = f"feature.Area.{label}"
        mature_key = f"feature.Seral.mature_old.{label}"
        old_key = f"feature.Seral.overmature.{label}"
        for key in (area_key, mature_key, old_key):
            if key not in values.index:
                raise ValueError(f"missing account {key}")
        area = _as_float(values[area_key])
        bounds = (
            ("mature_old", mature_key, mature_old_fraction * area),
            ("old", old_key, old_fraction * area),
        )
        for _name, account, minimum in bounds:
            for period in range(1, periods + 1):
                rows.append(
                    {
                        "account": account,
                        "period": period,
                        "period_width": period_width,
                        "minimum": minimum,
                        "min_weight": weight,
                    }
                )
    return pd.DataFrame(rows)


def render_targets(frame: pd.DataFrame, header: Sequence[str]) -> str:
    """Render the target table as YAML text.

    Parameters
    ----------
    frame : pandas.DataFrame
        Target rows from :func:`build_targets`.
    header : sequence of str
        Comment lines for the file header.

    Returns
    -------
    str
        The YAML text.
    """
    lines = [f"# {line}" if line else "#" for line in header]
    lines.append("targets:")
    for row in frame.itertuples(index=False):
        lines.append(
            f"  - {{account: {row.account}, period: {row.period}, "
            f"period_width: {row.period_width}, minimum: {row.minimum:.6f}, "
            f"min_weight: {row.min_weight:.1f}, shape: non_linear, priority: 2}}"
        )
    return "\n".join(lines) + "\n"


def summarise_targets(
    presim: pd.DataFrame,
    lubecs: Sequence[str],
    mature_old_fraction: float,
    old_fraction: float,
) -> pd.DataFrame:
    """Return the area, initial seral values, and bounds per LU/BEC.

    Parameters
    ----------
    presim : pandas.DataFrame
        Pre-simulation accounts.
    lubecs : sequence of str
        LU/BEC values.
    mature_old_fraction : float
        Minimum mature+old share of the LU/BEC area.
    old_fraction : float
        Minimum old share of the LU/BEC area.

    Returns
    -------
    pandas.DataFrame
        One row per LU/BEC.
    """
    values = presim.set_index("account")["value"]
    rows: list[dict[str, object]] = []
    for lubec in lubecs:
        label = token(lubec)
        rows.append(
            {
                "lubec": lubec,
                "token": label,
                "area_ha": round(_as_float(values[f"feature.Area.{label}"]), 3),
                "mature_old_ha": round(_as_float(values[f"feature.Seral.mature_old.{label}"]), 3),
                "old_ha": round(_as_float(values[f"feature.Seral.overmature.{label}"]), 3),
            }
        )
    summary = pd.DataFrame(rows)
    summary["min_mature_old_ha"] = summary["area_ha"] * mature_old_fraction
    summary["min_old_ha"] = summary["area_ha"] * old_fraction
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    """Build or check the seral target table.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` on success, ``1`` when ``--check`` finds a difference.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--target-summary", type=Path, default=DEFAULT_TARGET_SUMMARY)
    parser.add_argument("--periods", type=int, default=DEFAULT_PERIODS)
    parser.add_argument("--period-width", type=int, default=DEFAULT_PERIOD_WIDTH)
    parser.add_argument("--mature-old", type=float, default=DEFAULT_MATURE_OLD)
    parser.add_argument("--old", type=float, default=DEFAULT_OLD)
    parser.add_argument("--weight", type=float, default=DEFAULT_WEIGHT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    summary = pd.read_csv(args.summary)
    lubecs = sorted(summary["lubec"].astype(str).unique())
    presim = run_presim(args.dataset)
    frame = build_targets(
        presim,
        lubecs,
        mature_old_fraction=args.mature_old,
        old_fraction=args.old,
        periods=args.periods,
        period_width=args.period_width,
        weight=args.weight,
    )
    resolved = args.dataset.resolve()
    dataset_label = (
        resolved.relative_to(ROOT.resolve()).as_posix()
        if resolved.is_relative_to(ROOT.resolve())
        else args.dataset.name
    )
    header = [
        "Generated by scripts/build_seral_targets.py; do not hand-edit.",
        f"dataset: {dataset_label}",
        f"dataset_manifest_sha256: {_manifest_hash(args.dataset)}",
        f"fractions: mature+old >= {args.mature_old:.2f}, old >= {args.old:.2f}",
        f"periods: {args.periods} x {args.period_width} years",
        "Basis: LU/BEC area from the zone-partitioned dataset. The caribou line is not",
        "in the instance, so the below-the-line targets are applied everywhere.",
    ]
    text = render_targets(frame, header)
    if args.check:
        existing = args.out.read_text(encoding="utf-8") if args.out.is_file() else ""
        if existing != text:
            print(f"ERROR: {args.out} is missing or out of date", file=sys.stderr)
            return 1
        print(f"checked {args.out}")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    target_summary = summarise_targets(presim, lubecs, args.mature_old, args.old)
    args.target_summary.parent.mkdir(parents=True, exist_ok=True)
    target_summary.to_csv(args.target_summary, index=False)
    parsed = yaml.safe_load(text)
    print(f"targets: {len(parsed['targets'])}")
    print(f"accounts: {frame['account'].nunique()}")
    print(f"wrote {args.out}")
    print(f"wrote {args.target_summary}")
    return 0


def _manifest_hash(dataset: Path) -> str:
    """Return the SHA-256 of the dataset manifest.

    Parameters
    ----------
    dataset : pathlib.Path
        Compiled dataset.

    Returns
    -------
    str
        Hex digest, or ``"missing"`` when the manifest is absent.
    """
    path = dataset / "manifest.json"
    if not path.is_file():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    sys.exit(main())
