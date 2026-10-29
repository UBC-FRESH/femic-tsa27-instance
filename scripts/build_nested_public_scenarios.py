#!/usr/bin/env python3
"""Run the nested public-data scenario grid.

Dimensions:

- year and UWR pool (pre/post-2019);
- BC interior AMV price factor;
- six public stumpage anchors;
- cost factor 1.0 or 1.2;
- fire no-salvage on or off.

The output is a range, not a single attribution.

Usage:
    python scripts/build_nested_public_scenarios.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from build_uwr_timing import summarize
from build_year_by_year_screen import fire_adjust, pre2019_pool, price_adjust

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "runtime/operational_screen"
SNAPSHOTS = ROOT / "runtime/annual_snapshots"
PRICE_INDEX = ROOT / "config/operational/bc_interior_amv_index.csv"
STUMPAGE_ANCHORS = (12.76, 20.00, 32.53, 47.10, 55.22, 60.53)
COST_FACTORS = (1.0, 1.2)
YEARS = range(2017, 2027)


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=SNAPSHOTS)
    return parser.parse_args()


def main() -> None:
    """Write the nested grid and annual envelope."""
    args = parse_args()
    full = pd.read_csv(SCREEN / "screen_full_shared.csv")
    current = pd.read_csv(SCREEN / "screen_uwr_shared.csv")
    pre2019 = pre2019_pool(full, current)
    price = pd.read_csv(PRICE_INDEX).set_index("year")
    hbs = pd.read_csv(SNAPSHOTS / "annual_snapshot_summary.csv").set_index("year")
    fire = pd.read_csv(SNAPSHOTS / "fire_block_overlap.csv")
    burn_by_year: dict[int, dict[int, float]] = {}
    for year, group in fire.groupby("year"):
        burn_by_year[int(str(year))] = {
            int(str(block)): float(str(value))
            for block, value in group.groupby("block_id")["volume_at_risk_m3"].sum().items()
        }

    rows = []
    for year in YEARS:
        pool = pre2019 if year < 2019 else current
        factor = float(str(price.loc[year, "factor_vs_2026"]))
        for stumpage in STUMPAGE_ANCHORS:
            priced = price_adjust(pool, factor, stumpage_rate=stumpage)
            for cost_factor in COST_FACTORS:
                for no_salvage in (False, True):
                    adjusted = priced.copy()
                    if no_salvage:
                        adjusted = fire_adjust(adjusted, burn_by_year.get(year, {}))
                    adjusted["cost"] = adjusted.cost * cost_factor
                    adjusted["margin"] = adjusted.revenue - adjusted.cost
                    adjusted["margin_per_m3"] = adjusted.margin / adjusted.volume_m3.replace(
                        0.0, pd.NA
                    )
                    adjusted["margin_per_m3"] = adjusted.margin_per_m3.fillna(-1e12)
                    result = summarize(adjusted)
                    rows.append(
                        {
                            "year": year,
                            "uwr_pool": "pre_2019" if year < 2019 else "post_2019",
                            "price_factor_vs_2026": round(factor, 4),
                            "stumpage_per_m3": stumpage,
                            "cost_factor": cost_factor,
                            "fire_no_salvage": no_salvage,
                            "positive_volume_m3": result["positive_volume_m3"],
                            "positive_share": result["positive_share"],
                            "selected_m3": result["selected_m3"],
                            "hbs_m3": round(float(str(hbs.loc[year, "hbs_m3"])), 1),
                            "harvest_to_aac": round(float(str(hbs.loc[year, "harvest_to_aac"])), 4),
                        }
                    )
    frame = pd.DataFrame(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out / "nested_public_scenarios.csv", index=False)

    summary = (
        frame.groupby("year")
        .agg(
            price_factor=("price_factor_vs_2026", "first"),
            min_positive_share=("positive_share", "min"),
            median_positive_share=("positive_share", "median"),
            max_positive_share=("positive_share", "max"),
            min_selected_m3=("selected_m3", "min"),
            median_selected_m3=("selected_m3", "median"),
            max_selected_m3=("selected_m3", "max"),
            hbs_m3=("hbs_m3", "first"),
            harvest_to_aac=("harvest_to_aac", "first"),
        )
        .reset_index()
    )
    summary.to_csv(args.out / "nested_public_scenarios_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(f"wrote {args.out / 'nested_public_scenarios.csv'}")
    print(f"wrote {args.out / 'nested_public_scenarios_summary.csv'}")


if __name__ == "__main__":
    main()
