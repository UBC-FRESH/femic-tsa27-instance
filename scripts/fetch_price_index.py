#!/usr/bin/env python3
"""Fetch a public softwood-lumber price index and build annual factors.

The series is the U.S. Bureau of Labor Statistics producer price index for softwood lumber
(FRED ``WPU0811``). It is a market proxy, not a BC interior mill-gate log price.

Usage:
    python scripts/fetch_price_index.py
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config/operational/softwood_lumber_price_index.csv"
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=WPU0811"
YEARS = range(2015, 2027)


def main() -> None:
    """Fetch the monthly index, average by year, and write factors."""
    response = requests.get(URL, timeout=120)
    response.raise_for_status()
    frame = pd.read_csv(io.StringIO(response.text))
    frame.columns = ["month", "ppi"]
    frame["month"] = pd.to_datetime(frame["month"])
    frame["year"] = frame["month"].dt.year
    annual = frame.groupby("year")["ppi"].mean()
    base = float(annual.loc[2026])
    rows = []
    for year in YEARS:
        if year not in annual.index:
            continue
        value = float(annual.loc[year])
        rows.append(
            {
                "year": year,
                "softwood_lumber_ppi": round(value, 2),
                "factor_vs_2026": round(value / base, 4),
                "source": "BLS PPI WPU0811 via FRED",
                "note": "2026 is year-to-date" if year == 2026 else "",
            }
        )
    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
