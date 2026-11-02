#!/usr/bin/env python3
"""Build a persisted WS4 GPU effect table for a TSA 27 even-flow target.

The table is the sparse exact effect cache used by ``ws4 gpu-run`` and ``ws4 gpu-watch``.
It is built once per dataset/target/seed combination and reused across GPU runs.

Usage:
    python scripts/build_gpu_effect_table.py \
        --dataset build/compiled_uwr \
        --targets config/ws4/targets/evenflow_caribou.yaml \
        --seed-schedule runtime/seed_oldest_first_s7.csv \
        --candidates-cache runtime/gpu-cache/s7/candidates.pkl \
        --simulator-cache runtime/gpu-cache/s7/simulator.pkl \
        --out runtime/gpu-effects/effects-s7.pt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from ws4.opt.candidate_cache import load_or_build_candidates, load_or_build_simulator  # type: ignore[import-not-found]  # local WS4 checkout is not a typed package
from ws4.opt.engine import OptimizeConfig, Optimizer, load_schedule_csv  # type: ignore[import-not-found]  # local WS4 checkout is not a typed package
from ws4.opt.gpu_effects import EffectTable, watchable_cells  # type: ignore[import-not-found]  # local WS4 checkout is not a typed package
from ws4.opt.incremental import IncrementalObjective  # type: ignore[import-not-found]  # local WS4 checkout is not a typed package
from ws4.opt.objective import load_targets  # type: ignore[import-not-found]  # local WS4 checkout is not a typed package

ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    """Return command-line options.

    Returns
    -------
    argparse.Namespace
        Parsed command-line options.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "build/compiled")
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--seed-schedule", type=Path, required=True)
    parser.add_argument("--candidates-cache", type=Path, required=True)
    parser.add_argument("--simulator-cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--years", type=int, default=200)
    parser.add_argument(
        "--cell-accounts",
        default="",
        help="Extra comma-separated accounts for the target-independent cell basis",
    )
    parser.add_argument(
        "--rebuild-caches",
        action="store_true",
        help="Rebuild simulator and candidate caches before building the table",
    )
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    """Return the SHA-256 of a file.

    Parameters
    ----------
    path : Path
        Input file.

    Returns
    -------
    str
        Hex digest.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """Build and persist the effect table plus a manifest."""
    args = parse_args()
    started = time.perf_counter()
    optimizer = Optimizer.from_dataset(
        args.dataset,
        OptimizeConfig(
            years=args.years,
            targets_path=str(args.targets),
            iterations=1,
            threads=1,
        ),
    )
    targets = load_targets(args.targets)
    seed_schedule = load_schedule_csv(args.seed_schedule)
    load_or_build_simulator(optimizer, args.simulator_cache, rebuild=args.rebuild_caches)
    candidates = load_or_build_candidates(
        optimizer, args.candidates_cache, rebuild=args.rebuild_caches
    )
    target_accounts = {target.account for target in targets}
    extra_accounts = {value.strip() for value in args.cell_accounts.split(",") if value.strip()}
    cell_accounts = tuple(sorted(target_accounts | extra_accounts))
    evaluator = IncrementalObjective(optimizer, targets, extra_accounts=cell_accounts)
    cells = watchable_cells(cell_accounts, args.years)
    print(
        f"building table: accounts={len(cell_accounts)} cells={len(cells)} dataset={args.dataset}",
        flush=True,
    )
    table = EffectTable.build(
        optimizer,
        evaluator,
        candidates=candidates,
        extra_pairs=list(seed_schedule.items()),
        cells=cells,
    )
    table.save(args.out, include_row_index=False, candidates=candidates)
    manifest = {
        "dataset": str(args.dataset),
        "targets": str(args.targets),
        "targets_sha256": file_sha256(args.targets),
        "seed_schedule": str(args.seed_schedule),
        "seed_schedule_sha256": file_sha256(args.seed_schedule),
        "table": str(args.out),
        "years": args.years,
        "cell_accounts": list(cell_accounts),
        "cells": len(table.cells),
        "rows": table.rows,
        "nnz": table.nnz,
        "bytes": table.nbytes(),
        "build_seconds": round(time.perf_counter() - started, 3),
    }
    args.out.with_suffix(args.out.suffix + ".json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(
        f"wrote {args.out}: rows={table.rows} nnz={table.nnz} "
        f"bytes={table.nbytes()} seconds={time.perf_counter() - started:.1f}"
    )


if __name__ == "__main__":
    main()
