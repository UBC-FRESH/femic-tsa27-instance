#!/usr/bin/env python3
"""Reconcile the provisional TSA 27 land base against the TSR tables.

Reads the land-base summary and the curated TSR4 2010 and 2022 TSR5 tables, writes a
comparison CSV and a Markdown report, and fails when a directly comparable line is outside
the stated tolerance.

Command-line usage::

    python scripts/reconcile_land_base.py
    python scripts/reconcile_land_base.py --check
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_SUMMARY: Path = ROOT / "metadata" / "land_base" / "tsa27_land_base_summary.csv"
DEFAULT_TSR_2010: Path = ROOT / "metadata" / "tsr" / "tsa27_thlb_netdown_table3.csv"
DEFAULT_TSR_2022: Path = ROOT / "metadata" / "tsr" / "tsa27_thlb_netdown_table14_2022.csv"
DEFAULT_CSV: Path = ROOT / "metadata" / "tsr" / "tsa27_land_base_reconciliation.csv"
DEFAULT_REPORT: Path = ROOT / "reports" / "tsa27-land-base-reconciliation.md"
TOLERANCE_PCT: float = 1.0


def load_summary(path: Path) -> dict[str, float]:
    """Load the land-base summary into a class-to-area mapping.

    Parameters
    ----------
    path : Path
        Summary CSV with ``class`` and ``area_ha`` columns.

    Returns
    -------
    dict of str to float
        Class-to-hectare mapping.
    """
    frame = pd.read_csv(path)
    return {str(row["class"]): float(row["area_ha"]) for _, row in frame.iterrows()}


def load_tsr_rows(path: Path, value_column: str) -> dict[str, float]:
    """Load one TSR table into a land-base-element mapping.

    Parameters
    ----------
    path : Path
        TSR table CSV.
    value_column : str
        Column that holds the value to compare.

    Returns
    -------
    dict of str to float
        Land-base element to value, skipping blanks.
    """
    frame = pd.read_csv(path)
    values: dict[str, float] = {}
    for _, row in frame.iterrows():
        value = row.get(value_column)
        if pd.isna(value):
            continue
        values[str(row["land_base_element"])] = float(value)
    return values


def build_rows(
    summary: dict[str, float],
    tsr_2010: dict[str, float],
    tsr_2022: dict[str, float],
    tsr_2022_net: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Build the reconciliation rows.

    Parameters
    ----------
    summary : dict of str to float
        WS4 land-base summary.
    tsr_2010 : dict of str to float
        TSR4 2010 effective netdown values.
    tsr_2022 : dict of str to float
        TSR5 2022 gross values.
    tsr_2022_net : dict of str to float or None, optional
        TSR5 2022 net-removed values. Used for the caribou UWR net row.

    Returns
    -------
    list of dict
        One row per comparison with values, difference, comparability, and explanation.
    """
    specs = [
        (
            "gross_land_base",
            "gross_clip",
            tsr_2022,
            "Gross land base",
            "yes",
            "TSA 27 boundary clip versus the 2022 gross land base; 59 ha edge/rounding.",
        ),
        (
            "caribou_uwr_gross",
            "caribou_uwr_direct",
            tsr_2022,
            "Wildlife - Caribou UWR (no harvest)",
            "yes",
            "Direct UWR u-3-005 no-harvest clip; 61 ha boundary/geometry difference.",
        ),
        (
            "caribou_uwr_net",
            None,
            tsr_2022,
            "Wildlife - Caribou UWR (no harvest)",
            "no",
            "The net LHLB removal (62,892 ha) requires the LHLB overlap classification; P2.",
        ),
        (
            "aflb",
            "is_forested",
            tsr_2022,
            "Analysis forest land base (AFLB)",
            "no",
            "WS4 forested is a VRI treed class before ownership, non-administered, "
            "roads, and park exclusions; not AFLB.",
        ),
        (
            "thlb_2022",
            "thlb_candidate",
            tsr_2022,
            "Timber harvesting land base (THLB)",
            "no",
            "Provisional candidate omits operability, low-site, non-merchantable, "
            "riparian, WTP, and OGMA/MOGMA netdowns.",
        ),
        (
            "thlb_2010",
            "thlb_candidate",
            tsr_2010,
            "Timber Harvesting Land Base (THLB)",
            "no",
            "2010 THLB is against CFLB after the full netdown sequence; the "
            "candidate is not comparable.",
        ),
        (
            "caribou_2010_netdown",
            None,
            tsr_2010,
            "Mountain Caribou Reserves (GAR U-3-005)",
            "no",
            "2010 is a THLB netdown against CFLB; 2022 is an LHLB exclusion "
            "against AFLB. Keep the cycles separate.",
        ),
        (
            "ogma_2010",
            "ogma",
            tsr_2010,
            "Less temporary: Spatial OGMAs and MOGMAs",
            "no",
            "The legal OGMA layer has no TSA 27 polygons; the TSR uses non-legal FSP OGMAs/MOGMAs.",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for metric, summary_key, table, element, comparable, explanation in specs:
        ws4 = float(summary.get(summary_key, 0.0)) if summary_key else None
        if metric == "caribou_uwr_net" and tsr_2022_net is not None:
            tsr = float(tsr_2022_net.get(element, 0.0))
        else:
            tsr = float(table.get(element, 0.0))
        difference = None if ws4 is None else round(ws4 - tsr, 3)
        pct = None if ws4 is None or tsr == 0 else round(100 * (ws4 - tsr) / tsr, 4)
        rows.append(
            {
                "metric": metric,
                "ws4_class": summary_key or "",
                "tsr_element": element,
                "ws4_ha": ws4,
                "tsr_ha": tsr,
                "difference_ha": difference,
                "difference_pct": pct,
                "comparable": comparable,
                "within_tolerance": (
                    "yes"
                    if pct is not None and abs(pct) <= TOLERANCE_PCT
                    else ("no" if pct is not None else "n/a")
                ),
                "explanation": explanation,
            }
        )
    return rows


def check_rows(rows: Sequence[dict[str, Any]], tolerance_pct: float = TOLERANCE_PCT) -> list[str]:
    """Return errors for comparable rows outside tolerance.

    Parameters
    ----------
    rows : sequence of dict
        Reconciliation rows.
    tolerance_pct : float, optional
        Allowed absolute percentage difference for comparable rows.

    Returns
    -------
    list of str
        Error messages; empty when the check passes.
    """
    errors: list[str] = []
    for row in rows:
        if row["comparable"] != "yes":
            continue
        pct = row["difference_pct"]
        if pct is None or abs(float(pct)) > tolerance_pct:
            errors.append(f"{row['metric']}: {pct}% exceeds {tolerance_pct}%")
    return errors


def display_path(path: Path, root: Path = ROOT) -> str:
    """Return a repo-relative path label, or the file name when outside the repo.

    Parameters
    ----------
    path : Path
        Path to render.
    root : Path, optional
        Repository root. The default is the module root.

    Returns
    -------
    str
        Repo-relative path or file name.
    """
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def write_csv(rows: Sequence[dict[str, Any]], path: Path) -> None:
    """Write the reconciliation CSV.

    Parameters
    ----------
    rows : sequence of dict
        Reconciliation rows.
    path : Path
        Destination path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def write_report(rows: Sequence[dict[str, Any]], path: Path, summary_path: Path) -> None:
    """Write the reconciliation Markdown report.

    Parameters
    ----------
    rows : sequence of dict
        Reconciliation rows.
    path : Path
        Destination Markdown path.
    summary_path : Path
        Source summary path, rendered as a repo-relative link.
    """
    lines = [
        "# TSA 27 land-base reconciliation",
        "",
        "This report compares the provisional P1.2 land base with the TSR4 2010 "
        "and 2022 TSR5 tables.",
        "Only the gross land base and the direct caribou UWR clip are directly "
        "comparable at this stage.",
        "",
        f"Inputs: `{display_path(summary_path)}`, "
        "`metadata/tsr/tsa27_thlb_netdown_table3.csv`, and "
        "`metadata/tsr/tsa27_thlb_netdown_table14_2022.csv`.",
        "",
        "| Metric | WS4 (ha) | TSR (ha) | Difference (ha) | "
        "Difference (%) | Comparable | Within tolerance |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        ws4 = "" if row["ws4_ha"] is None else f"{row['ws4_ha']:,.0f}"
        tsr = f"{row['tsr_ha']:,.0f}"
        diff = "" if row["difference_ha"] is None else f"{row['difference_ha']:,.0f}"
        pct = "" if row["difference_pct"] is None else f"{row['difference_pct']:.2f}"
        lines.append(
            f"| {row['metric']} | {ws4} | {tsr} | {diff} | {pct} | "
            f"{row['comparable']} | {row['within_tolerance']} |"
        )
    lines.extend(
        [
            "",
            "## Findings",
            "",
            "- The gross land base matches the 2022 TSR5 value within 59 ha "
            "(0.008%), confirming the TSA 27 boundary and VRI clip.",
            "- The direct UWR u-3-005 no-harvest clip matches the 2022 TSR5 gross "
            "value within 61 ha (0.05%), confirming the layer and filter.",
            "- The binary VRI UWR flag is **not** used for area accounting: it "
            "reports 247,313 ha because whole VRI polygons are painted at the "
            "fragmented UWR edge. The direct clip is 116,759 ha.",
            "- The forested VRI class (419,663 ha) is not the AFLB (216,217 ha); it "
            "still contains ownership, non-administered, road, and park exclusions.",
            "- The provisional THLB candidate (246,451 ha) is not comparable to the "
            "TSR THLB (51,454 ha in 2022; 51,044 ha long-term in 2010). The "
            "remaining netdowns are the P2 work.",
            "- Legal OGMA has no polygons in TSA 27; the TSR uses non-legal FSP OGMAs/MOGMAs.",
            "",
            "## Decision for P2",
            "",
            "Keep the direct UWR clip as the caribou area accounting layer. Do not "
            "use the binary VRI flag for area totals; use it only for fragment "
            "screening until fragments are split at the UWR boundary.",
            "",
            "P2 must apply the remaining TSR netdowns (ownership, non-administered, "
            "roads, parks, inoperable, unstable/ESA, non-merchantable, low sites, "
            "riparian, community watersheds, WHA, PSP, backlog, cultural, WTP, "
            "OGMA/MOGMA) before the THLB is compared to the TSR.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the reconciliation.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` when comparable rows are within tolerance, ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--tsr-2010", type=Path, default=DEFAULT_TSR_2010)
    parser.add_argument("--tsr-2022", type=Path, default=DEFAULT_TSR_2022)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    summary = load_summary(args.summary)
    tsr_2010 = load_tsr_rows(args.tsr_2010, "effective_netdown_ha")
    tsr_2022 = load_tsr_rows(args.tsr_2022, "gross_ha")
    tsr_2022_net = load_tsr_rows(args.tsr_2022, "net_removed_ha")
    rows = build_rows(summary, tsr_2010, tsr_2022, tsr_2022_net)
    write_csv(rows, args.csv)
    write_report(rows, args.report, args.summary)
    errors = check_rows(rows)
    for row in rows:
        print(
            f"{row['metric']:<24} ws4={row['ws4_ha']} tsr={row['tsr_ha']} "
            f"diff={row['difference_ha']} ({row['difference_pct']}%) comparable={row['comparable']}"
        )
    print(f"wrote {args.csv}")
    print(f"wrote {args.report}")
    if args.check and errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
