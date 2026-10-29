#!/usr/bin/env python3
"""Build a public-data price/stumpage envelope for the annual screen.

No proprietary billed-stumpage series is used. The envelope combines:

- the BC interior lumber AMV price factor for each year;
- five public stumpage anchors: 12.76, 20.00, 32.53, 47.10, and 55.22 $/m3;
- the pre/post-2019 UWR pool.

Usage:
    python scripts/build_public_data_envelope.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from build_uwr_timing import summarize
from build_year_by_year_screen import pre2019_pool, price_adjust

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "runtime/operational_screen"
SNAPSHOTS = ROOT / "runtime/annual_snapshots"
PRICE_INDEX = ROOT / "config/operational/bc_interior_amv_index.csv"
STUMPAGE_ANCHORS = (12.76, 20.00, 32.53, 47.10, 55.22, 60.53)
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
    """Write the public-data envelope and annual min/median/max table."""
    args = parse_args()
    full = pd.read_csv(SCREEN / "screen_full_shared.csv")
    current = pd.read_csv(SCREEN / "screen_uwr_shared.csv")
    pre2019 = pre2019_pool(full, current)
    price = pd.read_csv(PRICE_INDEX).set_index("year")
    hbs = pd.read_csv(SNAPSHOTS / "annual_snapshot_summary.csv").set_index("year")

    rows = []
    for year in YEARS:
        pool = pre2019 if year < 2019 else current
        factor = float(str(price.loc[year, "factor_vs_2026"]))
        for stumpage in STUMPAGE_ANCHORS:
            result = summarize(price_adjust(pool, factor, stumpage_rate=stumpage))
            rows.append(
                {
                    "year": year,
                    "uwr_pool": "pre_2019" if year < 2019 else "post_2019",
                    "price_factor_vs_2026": round(factor, 4),
                    "stumpage_per_m3": stumpage,
                    "positive_volume_m3": result["positive_volume_m3"],
                    "positive_share": result["positive_share"],
                    "selected_m3": result["selected_m3"],
                    "hbs_m3": round(float(str(hbs.loc[year, "hbs_m3"])), 1),
                    "harvest_to_aac": round(float(str(hbs.loc[year, "harvest_to_aac"])), 4),
                }
            )
    frame = pd.DataFrame(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out / "public_data_envelope.csv", index=False)

    summary = (
        frame.groupby("year")
        .agg(
            price_factor=("price_factor_vs_2026", "first"),
            min_positive_share=("positive_share", "min"),
            median_positive_share=("positive_share", "median"),
            max_positive_share=("positive_share", "max"),
            min_positive_m3=("positive_volume_m3", "min"),
            max_positive_m3=("positive_volume_m3", "max"),
            hbs_m3=("hbs_m3", "first"),
            harvest_to_aac=("harvest_to_aac", "first"),
        )
        .reset_index()
    )
    summary.to_csv(args.out / "public_data_envelope_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(f"wrote {args.out / 'public_data_envelope.csv'}")
    print(f"wrote {args.out / 'public_data_envelope_summary.csv'}")


if __name__ == "__main__":
    main()
