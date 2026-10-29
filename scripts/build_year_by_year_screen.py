#!/usr/bin/env python3
"""Run the operational screen year by year with UWR timing and fire no-salvage.

This is a reduced-form annual screen. It varies only the UWR eligibility timing and the
block-level fire overlap; prices, costs, and mill capacity remain static.

Usage:
    python scripts/build_year_by_year_screen.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from build_uwr_timing import summarize

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "runtime/operational_screen"
SNAPSHOTS = ROOT / "runtime/annual_snapshots"
OUT = SNAPSHOTS
YEARS = range(2017, 2027)
VARIABLE_COST_PER_M3 = 68.0
STUMPAGE_PER_M3 = 20.0
PRICE_INDEX = ROOT / "config/operational/bc_interior_amv_index.csv"
STUMPAGE_INDEX = ROOT / "config/operational/bc_interior_stumpage.csv"


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--price-index", type=Path, default=PRICE_INDEX)
    parser.add_argument("--stumpage-index", type=Path, default=STUMPAGE_INDEX)
    return parser.parse_args()


def pre2019_pool(full: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    """Return the pre-2019 UWR pool.

    Parameters
    ----------
    full : pandas.DataFrame
        Full-dataset screen.
    current : pandas.DataFrame
        Current UWR screen.

    Returns
    -------
    pandas.DataFrame
        Current UWR rows plus the blocks added by the 2019 expansion.
    """
    expansion = pd.read_csv(SNAPSHOTS / "uwr_expansion_blocks.csv")
    current_ids = set(current.block_id.astype(int))
    expansion_ids = set(expansion.block_id.astype(int)) - current_ids
    add_back = full[full.block_id.isin(expansion_ids)].copy()
    pool = pd.concat([current, add_back], ignore_index=True)
    return pool.drop_duplicates("block_id")


def fire_adjust(frame: pd.DataFrame, burn: dict[int, float]) -> pd.DataFrame:
    """Reduce block volume by burned volume with no salvage.

    Parameters
    ----------
    frame : pandas.DataFrame
        Screen rows.
    burn : dict of int to float
        Burned operable volume by block.

    Returns
    -------
    pandas.DataFrame
        Adjusted rows with recomputed cost and margin.
    """
    adjusted = frame.copy()
    burned = adjusted.block_id.map(burn).fillna(0.0).clip(lower=0.0)
    burned = burned.clip(upper=adjusted.volume_m3)
    ratio = 1.0 - burned / adjusted.volume_m3.replace(0.0, pd.NA)
    ratio = ratio.fillna(0.0)
    variable = VARIABLE_COST_PER_M3 + adjusted.haul_per_m3
    fixed = adjusted.cost - adjusted.volume_m3 * variable
    adjusted["burned_m3"] = burned
    adjusted["volume_m3"] = adjusted.volume_m3 * ratio
    adjusted["revenue"] = adjusted.revenue * ratio
    adjusted["cost"] = fixed + adjusted.volume_m3 * variable
    adjusted["margin"] = adjusted.revenue - adjusted.cost
    adjusted["margin_per_m3"] = adjusted.margin / adjusted.volume_m3.replace(0.0, pd.NA)
    adjusted["margin_per_m3"] = adjusted.margin_per_m3.fillna(-1e12)
    return adjusted


def price_adjust(frame: pd.DataFrame, factor: float, stumpage_rate: float | None) -> pd.DataFrame:
    """Scale revenue and optionally replace the flat stumpage assumption.

    Parameters
    ----------
    frame : pandas.DataFrame
        Screen rows.
    factor : float
        Price factor relative to the 2026 base.
    stumpage_rate : float or None
        Annual South East average stumpage rate. ``None`` keeps the flat CAD 20/m³.

    Returns
    -------
    pandas.DataFrame
        Adjusted rows.
    """
    adjusted = frame.copy()
    adjusted["revenue"] = adjusted.revenue * factor
    if stumpage_rate is not None:
        adjusted["cost"] = adjusted.cost + (stumpage_rate - STUMPAGE_PER_M3) * adjusted.volume_m3
    adjusted["margin"] = adjusted.revenue - adjusted.cost
    adjusted["margin_per_m3"] = adjusted.margin / adjusted.volume_m3
    return adjusted


def main() -> None:
    """Write the annual screen and the fire no-salvage comparison."""
    args = parse_args()
    full = pd.read_csv(SCREEN / "screen_full_shared.csv")
    current = pd.read_csv(SCREEN / "screen_uwr_shared.csv")
    pre2019 = pre2019_pool(full, current)
    hbs = pd.read_csv(SNAPSHOTS / "annual_snapshot_summary.csv")[
        ["year", "hbs_m3", "harvest_to_aac"]
    ]
    fire = pd.read_csv(SNAPSHOTS / "fire_block_overlap.csv")
    price_index = pd.read_csv(args.price_index).set_index("year")
    stumpage_index = pd.read_csv(args.stumpage_index).set_index("year")
    burn_by_year: dict[int, dict[int, float]] = {}
    for year, group in fire.groupby("year"):
        burn_by_year[int(str(year))] = {
            int(str(block)): float(str(value))
            for block, value in group.groupby("block_id")["volume_at_risk_m3"].sum().items()
        }

    rows = []
    for year in YEARS:
        pool = pre2019 if year < 2019 else current
        base = summarize(pool)
        burned = burn_by_year.get(year, {})
        adjusted = fire_adjust(pool, burned)
        after = summarize(adjusted)
        factor = float(str(price_index.loc[year, "factor_vs_2026"]))
        stumpage_rate = float(str(stumpage_index.loc[year, "south_east_avg_stumpage_per_m3"]))
        price_only = summarize(price_adjust(pool, factor, stumpage_rate=None))
        price_stumpage = summarize(price_adjust(pool, factor, stumpage_rate=stumpage_rate))
        hbs_row = hbs[hbs.year == year].iloc[0]
        rows.append(
            {
                "year": year,
                "uwr_pool": "pre_2019" if year < 2019 else "post_2019",
                "hbs_m3": round(float(hbs_row.hbs_m3), 1),
                "harvest_to_aac": round(float(hbs_row.harvest_to_aac), 4),
                "pool_volume_m3": base["total_volume_m3"],
                "base_positive_m3": base["positive_volume_m3"],
                "base_positive_share": base["positive_share"],
                "base_selected_m3": base["selected_m3"],
                "fire_volume_removed_m3": round(float(adjusted.burned_m3.sum()), 1),
                "fire_positive_m3": after["positive_volume_m3"],
                "fire_positive_share": after["positive_share"],
                "fire_selected_m3": after["selected_m3"],
                "price_factor_vs_2026": round(factor, 4),
                "price_positive_m3": price_only["positive_volume_m3"],
                "price_positive_share": price_only["positive_share"],
                "price_selected_m3": price_only["selected_m3"],
                "price_stumpage_positive_m3": price_stumpage["positive_volume_m3"],
                "price_stumpage_positive_share": price_stumpage["positive_share"],
                "price_stumpage_selected_m3": price_stumpage["selected_m3"],
                "south_east_stumpage_per_m3": round(stumpage_rate, 2),
            }
        )
    frame = pd.DataFrame(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out / "year_by_year_screen.csv", index=False)
    print(frame.to_string(index=False))
    print(f"wrote {args.out / 'year_by_year_screen.csv'}")


if __name__ == "__main__":
    main()
