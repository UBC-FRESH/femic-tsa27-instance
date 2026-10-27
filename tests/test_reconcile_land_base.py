"""Tests for the land-base reconciliation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import reconcile_land_base


def write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Write a summary and two small TSR tables.

    Parameters
    ----------
    tmp_path : Path
        Temporary directory.

    Returns
    -------
    tuple of Path
        Summary, 2010 table, and 2022 table.
    """
    summary = tmp_path / "summary.csv"
    pd.DataFrame(
        {
            "class": ["gross_clip", "caribou_uwr_direct", "is_forested", "thlb_candidate", "ogma"],
            "area_ha": [758443, 116759, 419663, 246451, 0],
        }
    ).to_csv(summary, index=False)
    tsr_2010 = tmp_path / "tsr2010.csv"
    pd.DataFrame(
        {
            "land_base_element": [
                "Timber Harvesting Land Base (THLB)",
                "Mountain Caribou Reserves (GAR U-3-005)",
                "Less temporary: Spatial OGMAs and MOGMAs",
            ],
            "effective_netdown_ha": [57908, 18909, 5549],
        }
    ).to_csv(tsr_2010, index=False)
    tsr_2022 = tmp_path / "tsr2022.csv"
    pd.DataFrame(
        {
            "land_base_element": [
                "Gross land base",
                "Wildlife - Caribou UWR (no harvest)",
                "Analysis forest land base (AFLB)",
                "Timber harvesting land base (THLB)",
            ],
            "gross_ha": [758502, 116820, 216217, 51454],
            "net_removed_ha": [None, 62892, None, None],
        }
    ).to_csv(tsr_2022, index=False)
    return summary, tsr_2010, tsr_2022


def test_load_summary(tmp_path: Path) -> None:
    """The summary loads as a class-to-area mapping."""
    summary, _, _ = write_inputs(tmp_path)
    values = reconcile_land_base.load_summary(summary)
    assert values["gross_clip"] == 758443
    assert values["caribou_uwr_direct"] == 116759


def test_load_tsr_rows(tmp_path: Path) -> None:
    """The TSR loader skips blank values and keeps the requested column."""
    _, tsr_2010, _ = write_inputs(tmp_path)
    values = reconcile_land_base.load_tsr_rows(tsr_2010, "effective_netdown_ha")
    assert values["Timber Harvesting Land Base (THLB)"] == 57908
    assert values["Mountain Caribou Reserves (GAR U-3-005)"] == 18909


def test_load_tsr_rows_skips_blanks(tmp_path: Path) -> None:
    """Blank values are skipped rather than coerced to zero."""
    path = tmp_path / "tsr.csv"
    pd.DataFrame(
        {
            "land_base_element": ["A", "B"],
            "gross_ha": [10, None],
        }
    ).to_csv(path, index=False)
    values = reconcile_land_base.load_tsr_rows(path, "gross_ha")
    assert values == {"A": 10.0}


def test_build_rows(tmp_path: Path) -> None:
    """The reconciliation builds the documented metrics."""
    summary, tsr_2010, tsr_2022 = write_inputs(tmp_path)
    rows = reconcile_land_base.build_rows(
        reconcile_land_base.load_summary(summary),
        reconcile_land_base.load_tsr_rows(tsr_2010, "effective_netdown_ha"),
        reconcile_land_base.load_tsr_rows(tsr_2022, "gross_ha"),
        reconcile_land_base.load_tsr_rows(tsr_2022, "net_removed_ha"),
    )
    by_metric = {row["metric"]: row for row in rows}
    assert len(rows) == 8
    assert by_metric["gross_land_base"]["difference_ha"] == -59
    assert by_metric["caribou_uwr_gross"]["difference_ha"] == -61
    assert by_metric["caribou_uwr_net"]["tsr_ha"] == 62892
    assert by_metric["gross_land_base"]["within_tolerance"] == "yes"
    assert by_metric["thlb_2022"]["comparable"] == "no"


def test_check_rows_passes(tmp_path: Path) -> None:
    """Comparable rows within one percent pass."""
    summary, tsr_2010, tsr_2022 = write_inputs(tmp_path)
    rows = reconcile_land_base.build_rows(
        reconcile_land_base.load_summary(summary),
        reconcile_land_base.load_tsr_rows(tsr_2010, "effective_netdown_ha"),
        reconcile_land_base.load_tsr_rows(tsr_2022, "gross_ha"),
        reconcile_land_base.load_tsr_rows(tsr_2022, "net_removed_ha"),
    )
    assert reconcile_land_base.check_rows(rows) == []


def test_check_rows_fails_on_large_difference() -> None:
    """A comparable row outside tolerance fails the check."""
    rows = [
        {
            "metric": "gross_land_base",
            "difference_pct": 5.0,
            "comparable": "yes",
        }
    ]
    errors = reconcile_land_base.check_rows(rows)
    assert errors
    assert "gross_land_base" in errors[0]


def test_display_path(tmp_path: Path) -> None:
    """Repo-relative paths are rendered relative; outside paths keep the file name."""
    inside = tmp_path / "reports" / "report.md"
    inside.parent.mkdir()
    inside.write_text("x", encoding="utf-8")
    assert reconcile_land_base.display_path(inside, tmp_path) == "reports/report.md"
    assert reconcile_land_base.display_path(Path("relative.md"), tmp_path) == "relative.md"


def test_write_outputs(tmp_path: Path) -> None:
    """The CSV and Markdown report are written."""
    summary, tsr_2010, tsr_2022 = write_inputs(tmp_path)
    rows = reconcile_land_base.build_rows(
        reconcile_land_base.load_summary(summary),
        reconcile_land_base.load_tsr_rows(tsr_2010, "effective_netdown_ha"),
        reconcile_land_base.load_tsr_rows(tsr_2022, "gross_ha"),
        reconcile_land_base.load_tsr_rows(tsr_2022, "net_removed_ha"),
    )
    csv = tmp_path / "out.csv"
    report = tmp_path / "out.md"
    reconcile_land_base.write_csv(rows, csv)
    reconcile_land_base.write_report(rows, report, summary)
    assert csv.is_file()
    assert "TSA 27 land-base reconciliation" in report.read_text(encoding="utf-8")


def test_main_check(tmp_path: Path) -> None:
    """The CLI writes outputs and returns zero when comparable rows pass."""
    summary, tsr_2010, tsr_2022 = write_inputs(tmp_path)
    code = reconcile_land_base.main(
        [
            "--summary",
            str(summary),
            "--tsr-2010",
            str(tsr_2010),
            "--tsr-2022",
            str(tsr_2022),
            "--csv",
            str(tmp_path / "out.csv"),
            "--report",
            str(tmp_path / "out.md"),
            "--check",
        ]
    )
    assert code == 0


def test_main_check_fails(tmp_path: Path) -> None:
    """The CLI returns non-zero when a comparable row is outside tolerance."""
    summary, tsr_2010, tsr_2022 = write_inputs(tmp_path)
    frame = pd.read_csv(summary)
    frame.loc[frame["class"] == "gross_clip", "area_ha"] = 900000
    frame.to_csv(summary, index=False)
    code = reconcile_land_base.main(
        [
            "--summary",
            str(summary),
            "--tsr-2010",
            str(tsr_2010),
            "--tsr-2022",
            str(tsr_2022),
            "--csv",
            str(tmp_path / "out.csv"),
            "--report",
            str(tmp_path / "out.md"),
            "--check",
        ]
    )
    assert code == 1
