#!/usr/bin/env python3
"""Compare the supported WS4 caribou scenarios.

Reads the run account values recorded in ``metadata/ws4/scenario_runs.json``, extracts the
first-period harvest and treated area, and writes a comparison CSV and Markdown table.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_RECORD: Path = ROOT / "metadata" / "ws4" / "scenario_runs.json"
DEFAULT_CSV: Path = ROOT / "metadata" / "ws4" / "scenario_comparison.csv"
DEFAULT_REPORT: Path = ROOT / "reports" / "tsa27-caribou-scenario-comparison.md"
HARVEST = "product.HarvestedVolume.managed.Total.CC"
TREATED = "product.Treated.managed.CC"


def extract_metrics(path: Path) -> dict[str, float]:
    """Extract first-period harvest and treated area from one run.

    Parameters
    ----------
    path : Path
        ``account_values.csv`` path.

    Returns
    -------
    dict of str to float
        Harvest in m³ and treated area in ha.
    """
    frame = pd.read_csv(path)
    harvest = frame[(frame["offset"] == 0) & (frame["account"] == HARVEST)]["value"].sum()
    treated = frame[(frame["offset"] == 0) & (frame["account"] == TREATED)]["value"].sum()
    return {"harvest_m3": float(harvest), "treated_ha": float(treated)}


def compare(record_path: Path) -> pd.DataFrame:
    """Build the scenario comparison table.

    Parameters
    ----------
    record_path : Path
        Scenario run record.

    Returns
    -------
    pandas.DataFrame
        One row per scenario with deltas against the no-caribou run.
    """
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for item in payload["scenarios"]:
        if item.get("status") != "supported":
            continue
        run = ROOT / str(item["out"]) / "account_values.csv"
        metrics = extract_metrics(run)
        rows.append({"scenario": item["scenario"], **metrics})
    frame = pd.DataFrame(rows)
    baseline = frame.loc[frame["scenario"] == "s6_no_caribou"]
    base_harvest = float(baseline["harvest_m3"].iloc[0]) if len(baseline) else 0.0
    base_treated = float(baseline["treated_ha"].iloc[0]) if len(baseline) else 0.0
    frame["harvest_delta_m3"] = frame["harvest_m3"] - base_harvest
    frame["harvest_delta_pct"] = (
        100 * frame["harvest_delta_m3"] / base_harvest if base_harvest else 0.0
    )
    frame["treated_delta_ha"] = frame["treated_ha"] - base_treated
    frame["treated_delta_pct"] = (
        100 * frame["treated_delta_ha"] / base_treated if base_treated else 0.0
    )
    return frame


def write_report(frame: pd.DataFrame, path: Path) -> None:
    """Write the comparison Markdown.

    Parameters
    ----------
    frame : pandas.DataFrame
        Comparison table.
    path : Path
        Destination report.
    """
    lines = [
        "# TSA 27 caribou scenario comparison",
        "",
        "First-period capacity comparison, not an AAC determination.",
        "",
        "| Scenario | Harvest (m³) | Δ harvest | Δ % | Treated (ha) | Δ treated | Δ % |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in frame.iterrows():
        lines.append(
            f"| {row['scenario']} | {row['harvest_m3']:,.0f} | "
            f"{row['harvest_delta_m3']:,.0f} | {row['harvest_delta_pct']:.1f} | "
            f"{row['treated_ha']:,.0f} | {row['treated_delta_ha']:,.0f} | "
            f"{row['treated_delta_pct']:.1f} |"
        )
    lines.extend(
        [
            "",
            "The baseline is `s6_no_caribou`. `s3_tsr5_base` applies the UWR "
            "u-3-005 no-harvest filter.",
            "",
            "This compares first-period harvest capacity from the current WS4 dataset. "
            "It is not a multi-rotation AAC forecast; the TSR4 validation and the "
            "unsupported scenario matrix are in the P4 attribution report.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the comparison.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` when every supported run has positive harvest, ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    frame = compare(args.record)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.csv, index=False)
    write_report(frame, args.report)
    print(frame.to_string(index=False))
    print(f"wrote {args.csv}")
    print(f"wrote {args.report}")
    if args.check and (frame["harvest_m3"] <= 0).any():
        print("ERROR: a supported scenario has no harvest", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
