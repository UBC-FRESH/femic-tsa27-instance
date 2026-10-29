#!/usr/bin/env python3
"""Fetch BC interior lumber AMVs and build a TSA 27 price index.

The source is the monthly BC Timber Pricing Branch "Stumpage Appraisal Parameters
(Interior)" memorandum. Each PDF carries a zone 7 (Southern Interior) lumber AMV table in
dollars per thousand board feet. This script extracts the zone 7 row, builds a
spruce-pine-fir composite, and averages it by year.

Usage:
    python scripts/fetch_bc_interior_amv.py
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd
import pypdf  # type: ignore[import-not-found, unused-ignore]  # optional PDF dependency
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT_MONTHLY = ROOT / "config/operational/bc_interior_amv_monthly.csv"
OUT_ANNUAL = ROOT / "config/operational/bc_interior_amv_index.csv"
BASE_URL = (
    "https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/"
    "forestry/timber-pricing/interior-timber-pricing/interior-parameters/"
)
PAGE_URL = (
    "https://www2.gov.bc.ca/gov/content/industry/forestry/competitive-forest-industry/"
    "timber-pricing/interior-timber-pricing/interior-appraisal-parameters"
)
YEARS = range(2017, 2027)
SPECIES = (
    "balsam",
    "larch",
    "cedar",
    "fir_hemlock",
    "lodgepole_pine",
    "white_pine",
    "yellow_pine",
    "spruce",
)
COMPOSITE = ("balsam", "fir_hemlock", "lodgepole_pine", "white_pine", "yellow_pine", "spruce")
HEADERS = {"User-Agent": "Mozilla/5.0"}


def links_for_year(year: int) -> list[str]:
    """Return candidate PDF links for a year.

    Parameters
    ----------
    year : int
        Calendar year.

    Returns
    -------
    list of str
        Absolute PDF URLs.
    """
    if year == 2017:
        months = ("feb", "mar", "may", "july", "aug", "sept", "oct", "nov", "dec")
        return [f"{BASE_URL}mps_{month}_17_interior.pdf" for month in months]
    url = f"{PAGE_URL}/{year}" if year < 2026 else PAGE_URL
    response = requests.get(url, timeout=120, headers=HEADERS)
    response.raise_for_status()
    found = re.findall(r'href="([^"]+\.pdf)"', response.text)
    links = [link for link in found if "mps_" in link and "interior" in link]
    return sorted(set(links))


def parse_pdf(payload: bytes) -> dict[str, object] | None:
    """Parse one appraisal-parameters PDF.

    Parameters
    ----------
    payload : bytes
        PDF bytes.

    Returns
    -------
    dict or None
        Zone 7 AMV row and effective date, or ``None`` when parsing fails.
    """
    reader = pypdf.PdfReader(io.BytesIO(payload))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    header = re.search(
        r"CALCULATIONS BETWEEN ([A-Z]+) \d+ - \d+, (\d{4})", text, flags=re.IGNORECASE
    )
    if header is None:
        return None
    month, year = header.group(1).title(), int(header.group(2))
    zone = None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 9 and parts[0] == "7" and all(part.isdigit() for part in parts[1:9]):
            zone = [float(part) for part in parts[1:9]]
            break
    if zone is None:
        return None
    row: dict[str, object] = {"year": year, "month": month}
    row.update(dict(zip(SPECIES, zone, strict=True)))
    row["spf_composite"] = sum(zone[SPECIES.index(key)] for key in COMPOSITE) / len(COMPOSITE)
    return row


def main() -> None:
    """Fetch monthly AMVs and write monthly and annual indices."""
    rows = []
    for year in YEARS:
        for link in links_for_year(year):
            try:
                response = requests.get(link, timeout=120, headers=HEADERS)
                response.raise_for_status()
                parsed = parse_pdf(response.content)
            except Exception as error:
                print(f"skip {link}: {error}")
                continue
            if parsed is None:
                print(f"skip unparsed {link}")
                continue
            parsed["source_url"] = link
            rows.append(parsed)
    monthly = pd.DataFrame(rows).sort_values(["year", "month"]).reset_index(drop=True)
    monthly.to_csv(OUT_MONTHLY, index=False)

    annual = monthly.groupby("year").agg(
        months=("spf_composite", "count"),
        spf_composite=("spf_composite", "mean"),
    )
    base = float(str(annual.loc[2026, "spf_composite"]))
    annual["factor_vs_2026"] = (annual.spf_composite / base).round(4)
    annual["spf_composite"] = annual.spf_composite.round(2)
    annual.reset_index().to_csv(OUT_ANNUAL, index=False)
    print(annual.reset_index().to_string(index=False))
    print(f"wrote {OUT_MONTHLY} and {OUT_ANNUAL}")


if __name__ == "__main__":
    main()
