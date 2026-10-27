#!/usr/bin/env python3
"""Build TSA 27 analysis units and strata from the P1 land-base layer.

The rule set is deterministic:

- species group from ``SPECIES_CD_1``;
- BEC zone + subzone from the VRI attributes;
- site-index class from ``SITE_INDEX``;
- managed/natural from ``OPENING_IND`` and ``last_harvest_year``.

Forested polygons with a missing species, site index, or age are marked ``UNASSIGNED`` with
an explicit reason. Non-forested polygons are marked ``NONFOREST``.

Command-line usage::

    python scripts/build_analysis_units.py
    python scripts/build_analysis_units.py --check
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_LAND_BASE: Path = ROOT / "data" / "land_base" / "tsa27_land_base.gpkg"
DEFAULT_GPKG: Path = ROOT / "data" / "analysis_units" / "tsa27_analysis_units.gpkg"
DEFAULT_SUMMARY: Path = ROOT / "metadata" / "analysis_units" / "tsa27_analysis_units.csv"

SPECIES_GROUPS: dict[str, str] = {
    "BL": "BL",
    "BA": "BL",
    "CW": "CW",
    "YC": "CW",
    "HW": "HW",
    "HM": "HW",
    "H": "HW",
    "SE": "SX",
    "SX": "SX",
    "SS": "SX",
    "SW": "SX",
    "FDI": "FDI",
    "FD": "FDI",
    "PLI": "PL",
    "PL": "PL",
    "AT": "AT",
    "ACT": "AT",
}


def species_group(code: object) -> str:
    """Return the species group for a leading-species code.

    Parameters
    ----------
    code : object
        VRI leading-species code, possibly missing.

    Returns
    -------
    str
        Species group, or ``OTHER`` for an unknown non-empty code.
    """
    if code is None or (isinstance(code, float) and pd.isna(code)):
        return "UNK"
    return SPECIES_GROUPS.get(str(code).strip().upper(), "OTHER")


def site_index_class(value: object) -> str:
    """Return the site-index class for a site index in metres.

    Parameters
    ----------
    value : object
        Site index, possibly missing.

    Returns
    -------
    str
        ``SI1`` (<10), ``SI2`` (10-15), ``SI3`` (15-20), ``SI4`` (>=20), or ``SI0``.
    """
    if not isinstance(value, (int, float)) or pd.isna(value):
        return "SI0"
    site = float(value)
    if site < 10:
        return "SI1"
    if site < 15:
        return "SI2"
    if site < 20:
        return "SI3"
    return "SI4"


def origin(opening_ind: object, last_harvest_year: object) -> str:
    """Return ``managed`` or ``natural`` from the opening and harvest signals.

    Parameters
    ----------
    opening_ind : object
        VRI ``OPENING_IND`` value.
    last_harvest_year : object
        Last harvest year from the cutblock join, or -1.

    Returns
    -------
    str
        ``managed`` when the polygon has an opening or a harvest year, else ``natural``.
    """
    opened = str(opening_ind).strip().upper() == "Y"
    harvested = isinstance(last_harvest_year, (int, float)) and float(last_harvest_year) > 0
    return "managed" if opened or harvested else "natural"


def select_base_vri(layer: gpd.GeoDataFrame, project: str = "REVELSTOKE_VRI") -> gpd.GeoDataFrame:
    """Select the TSA 27 base VRI project and exclude TFL/update overlays.

    Parameters
    ----------
    layer : geopandas.GeoDataFrame
        P1 land-base layer with a ``PROJECT`` column.
    project : str, optional
        Base VRI project name. The default is ``REVELSTOKE_VRI``.

    Returns
    -------
    geopandas.GeoDataFrame
        The selected project, or the input when the column is absent.
    """
    if "PROJECT" not in layer.columns:
        return layer
    return layer[layer["PROJECT"].astype(str) == project].copy()


def assign_analysis_units(layer: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Assign an AU ID and stratum fields to every land-base polygon.

    Parameters
    ----------
    layer : geopandas.GeoDataFrame
        P1 land-base layer.

    Returns
    -------
    geopandas.GeoDataFrame
        A copy with ``au_id``, ``au_species``, ``au_bec``, ``au_si``, ``au_origin``, and
        ``au_reason`` columns.
    """
    out = layer.copy()
    out["au_species"] = out["SPECIES_CD_1"].map(species_group)
    out["au_si"] = out["SITE_INDEX"].map(site_index_class)
    out["au_origin"] = [
        origin(opening, year)
        for opening, year in zip(out["OPENING_IND"], out["last_harvest_year"], strict=False)
    ]
    out["au_bec"] = out["BEC_ZONE_CODE"].fillna("UNK").astype(str) + out["BEC_SUBZONE"].fillna(
        ""
    ).astype(str)
    missing = out["au_species"].eq("UNK") | out["au_si"].eq("SI0") | out["PROJ_AGE_1"].isna()
    forested = out["is_forested"].astype(bool)
    out["au_id"] = (
        out["au_species"] + "-" + out["au_bec"] + "-" + out["au_si"] + "-" + out["au_origin"]
    )
    out.loc[~forested, "au_id"] = "NONFOREST"
    out.loc[forested & missing, "au_id"] = "UNASSIGNED"
    out["au_reason"] = ""
    out.loc[~forested, "au_reason"] = "not forested"
    out.loc[forested & missing, "au_reason"] = "missing species, site index, or age"
    return out


def summarize_analysis_units(layer: gpd.GeoDataFrame) -> pd.DataFrame:
    """Summarize area and polygon count by AU.

    Parameters
    ----------
    layer : geopandas.GeoDataFrame
        Layer with ``au_id`` and ``thlb_candidate``.

    Returns
    -------
    pandas.DataFrame
        One row per AU with union area, THLB-candidate union area, polygon count, and
        reason.
    """
    rows: list[dict[str, object]] = []
    for au_id, group in layer.groupby("au_id", dropna=False, sort=True):
        thlb = group["thlb_candidate"].astype(bool)
        thlb_group = group[thlb]
        rows.append(
            {
                "au_id": au_id,
                "au_species": group["au_species"].iloc[0],
                "au_bec": group["au_bec"].iloc[0],
                "au_si": group["au_si"].iloc[0],
                "au_origin": group["au_origin"].iloc[0],
                "area_ha": float(group.geometry.union_all().area / 10_000),
                "thlb_area_ha": float(thlb_group.geometry.union_all().area / 10_000)
                if len(thlb_group)
                else 0.0,
                "polygons": len(group),
                "reason": group["au_reason"].iloc[0],
            }
        )
    return pd.DataFrame(rows).sort_values("area_ha", ascending=False)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the AU build.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` on success.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--land-base", type=Path, default=DEFAULT_LAND_BASE)
    parser.add_argument("--gpkg", type=Path, default=DEFAULT_GPKG)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    layer = select_base_vri(gpd.read_file(args.land_base))
    assigned = assign_analysis_units(layer)
    summary = summarize_analysis_units(assigned)
    args.gpkg.parent.mkdir(parents=True, exist_ok=True)
    assigned.to_file(args.gpkg, driver="GPKG")
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.summary, index=False)
    print(summary.head(15).to_string(index=False))
    print(f"analysis_units={len(summary)} polygons={len(assigned)}")
    print(f"wrote {args.gpkg}")
    print(f"wrote {args.summary}")
    if args.check and (assigned["au_id"] == "").any():
        print("ERROR: empty au_id", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
