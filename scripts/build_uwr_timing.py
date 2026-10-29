#!/usr/bin/env python3
"""Build the 2019 UWR expansion block list and the pre/post timing counterfactual.

The current WS4 UWR dataset removes the full u-3-005 footprint. The 2019 approval added
about 10,600 ha. This script identifies the blocks affected by that addition and compares the
operational screen with and without those blocks.

Usage:
    python scripts/build_uwr_timing.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "data/downloads/bc"
OUT = ROOT / "runtime/annual_snapshots"
SCREEN = ROOT / "runtime/operational_screen"
CAP = 1_125_000.0


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    return parser.parse_args()


def summarize(frame: pd.DataFrame) -> dict[str, object]:
    """Summarise positive-margin volume and the five-year envelope.

    Parameters
    ----------
    frame : pandas.DataFrame
        Screen rows with ``margin``, ``volume_m3``, and ``margin_per_m3``.

    Returns
    -------
    dict
        Summary metrics.
    """
    positive = frame[frame.margin > 0.0].copy().sort_values("margin_per_m3", ascending=False)
    selected = positive[positive.volume_m3.cumsum() <= CAP]
    total = float(frame.volume_m3.sum())
    return {
        "blocks": len(frame),
        "total_volume_m3": round(total, 1),
        "positive_blocks": len(positive),
        "positive_volume_m3": round(float(positive.volume_m3.sum()), 1),
        "positive_share": round(float(positive.volume_m3.sum() / total), 3) if total else 0.0,
        "selected_m3": round(float(selected.volume_m3.sum()), 1),
        "median_margin_per_m3": round(float(positive.margin_per_m3.median()), 2)
        if not positive.empty
        else 0.0,
    }


def main() -> None:
    """Write the expansion block list and timing counterfactual."""
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    boundary = gpd.read_file(ROOT / "data/ws4/land_base.geojson").to_crs(3005)
    blocks = gpd.read_file(ROOT / "data/ws4/blocks.geojson").to_crs(3005)
    blocks["area_ha"] = blocks.geometry.area / 10_000.0
    uwr = gpd.read_file((DOWNLOADS / "uwr.geojson").resolve()).to_crs(3005)
    uwr = uwr[(uwr.UWR_NUMBER == "u-3-005") & uwr.TIMBER_HARVEST_CODE.notna()].copy()
    uwr = gpd.clip(uwr, boundary)
    uwr["approval_year"] = pd.to_datetime(uwr.APPROVAL_DATE, errors="coerce").dt.year
    pre_union = uwr[uwr.approval_year <= 2018].geometry.union_all()
    post_union = uwr[uwr.approval_year >= 2019].geometry.union_all()
    blocks["uwr_pre_ha"] = blocks.geometry.intersection(pre_union).area / 10_000.0
    blocks["uwr_post_ha"] = blocks.geometry.intersection(post_union).area / 10_000.0
    blocks["uwr_expansion_ha"] = (blocks.uwr_post_ha - blocks.uwr_pre_ha).clip(lower=0.0)
    expansion = blocks[blocks.uwr_expansion_ha > 0.01].copy()
    expansion[["block_id", "area_ha", "uwr_pre_ha", "uwr_post_ha", "uwr_expansion_ha"]].to_csv(
        args.out / "uwr_expansion_blocks.csv", index=False
    )

    full = pd.read_csv(SCREEN / "screen_full_shared.csv")
    current = pd.read_csv(SCREEN / "screen_uwr_shared.csv")
    current_ids = set(current.block_id.astype(int))
    expansion_ids = set(expansion.block_id.astype(int)) - current_ids
    add_back = full[full.block_id.isin(expansion_ids)].copy()
    pre2019 = pd.concat([current, add_back], ignore_index=True)
    pre2019 = pre2019.drop_duplicates("block_id")

    rows = []
    for label, frame in (
        ("pre_2019_u3_005", pre2019),
        ("post_2019_u3_005", current),
        ("expansion_blocks_only", add_back),
    ):
        summary = summarize(frame)
        summary["label"] = label
        rows.append(summary)
    summary_frame = pd.DataFrame(rows)[
        [
            "label",
            "blocks",
            "total_volume_m3",
            "positive_blocks",
            "positive_volume_m3",
            "positive_share",
            "selected_m3",
            "median_margin_per_m3",
        ]
    ]
    summary_frame.to_csv(args.out / "uwr_timing_summary.csv", index=False)
    print(f"expansion blocks: {len(expansion):,} ({expansion.uwr_expansion_ha.sum():,.0f} ha)")
    print(summary_frame.to_string(index=False))
    print(f"wrote {args.out / 'uwr_timing_summary.csv'}")
    print(f"wrote {args.out / 'uwr_expansion_blocks.csv'}")


if __name__ == "__main__":
    main()
