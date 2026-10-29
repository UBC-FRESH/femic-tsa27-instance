#!/usr/bin/env python3
"""Build an oldest-first seed schedule for a WS4 even-flow run.

The heuristic walks the horizon one year at a time. For each year it takes the oldest
manageable blocks that have a clear-cut candidate in that year until the annual area
target is met, then records the block's candidate chain. The default area target spreads
one pass over the whole horizon; ``--rotation-age`` instead uses one rotation pass.

Usage:
    python scripts/build_oldest_first_seed.py --dataset build/compiled \
        --targets config/ws4/targets/evenflow_no_caribou.yaml \
        --out runtime/seed_oldest_first_s8.csv

    python scripts/build_oldest_first_seed.py --dataset build/compiled \
        --targets config/ws4/targets/evenflow_caribou.yaml \
        --out runtime/seed_oldest_first_s7.csv --rotation-age 140
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd
from ws4.opt.engine import OptimizeConfig, Optimizer  # type: ignore[import-not-found]  # optional local/model dependency is not installed with stubs


def parse_args() -> argparse.Namespace:
    """Return the command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=root / "build/compiled")
    parser.add_argument(
        "--targets",
        type=Path,
        default=root / "config/ws4/targets/evenflow_no_caribou.yaml",
    )
    parser.add_argument("--out", type=Path, default=root / "runtime/seed_oldest_first.csv")
    parser.add_argument("--years", type=int, default=200)
    parser.add_argument("--period-width", type=int, default=10)
    parser.add_argument(
        "--rotation-age",
        type=int,
        default=None,
        help="area target = candidate area / rotation age; default spreads one pass over --years",
    )
    return parser.parse_args()


def main() -> None:
    """Write the seed schedule."""
    args = parse_args()
    optimizer = Optimizer.from_dataset(
        args.dataset,
        OptimizeConfig(
            years=args.years,
            targets_path=str(args.targets),
            iterations=1,
            seed=1,
        ),
    )
    candidates = optimizer.candidates()
    fragments = pd.read_parquet(args.dataset / "fragments.parquet")
    area = fragments.groupby("block_id")["area_ha"].sum()
    age = fragments.groupby("block_id")["age"].min()

    by_year: dict[int, list[tuple[int, int, float, tuple[tuple[str, int], ...]]]] = defaultdict(
        list
    )
    candidate_area = 0.0
    for raw_block, chains in candidates.items():
        if not chains:
            continue
        block = int(raw_block)
        candidate_area += float(area.get(block, 0.0))
        # A block may be operable in several years. Keep the longest chain for each first
        # year so a block with a second rotation contributes to the late periods too.
        best: dict[int, tuple[tuple[str, int], ...]] = {}
        for chain in chains:
            if not chain or chain[0][0] != "CC":
                continue
            year = int(chain[0][1])
            if 0 <= year < args.years and (year not in best or len(chain) > len(best[year])):
                best[year] = chain
        for year, chain in best.items():
            by_year[year].append(
                (int(age.get(block, 0)), block, float(area.get(block, 0.0)), chain)
            )
    for entries in by_year.values():
        entries.sort(reverse=True)

    span = args.rotation_age if args.rotation_age is not None else args.years
    area_per_year = candidate_area / max(1, span)
    used: set[int] = set()
    rows: list[tuple[int, str, int]] = []
    for year in range(args.years):
        taken = 0.0
        for _age, block, block_area, chain in by_year.get(year, []):
            if block in used:
                continue
            for treatment, offset in chain:
                rows.append((block, treatment, offset))
            used.add(block)
            taken += block_area
            if taken >= area_per_year:
                break

    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["block_id", "treatment", "offset"]).sort_values(
        ["offset", "block_id"]
    ).to_csv(out, index=False)
    scheduled_area = sum(float(area.get(block, 0.0)) for block in used)
    print(
        f"wrote {out}: {len(used)} blocks, {scheduled_area:.1f} ha, "
        f"area/year {area_per_year:.1f} ha"
    )


if __name__ == "__main__":
    main()
