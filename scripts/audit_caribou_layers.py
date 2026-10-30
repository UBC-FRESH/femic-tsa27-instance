#!/usr/bin/env python3
"""Audit the caribou layer accounting in the TSA 27 WS4 instance.

The audit reads the built artifacts and reports, check by check, whether the
caribou policy layers are represented, accounted, enforced, and reconciled.
It does not change any data.

Status values:

- ``PASS``: the check was evaluated and the expected state holds.
- ``GAP``: known missing accounting, input, or enforcement. Reported, not hidden.
- ``FAIL``: an integrity failure (for example a UWR-flagged block in a filtered
  schedule, or a variant that does not match its manifest).

The command exits ``1`` when any check is ``FAIL``. With ``--strict`` it also
exits ``1`` when any check is ``GAP``, so it can serve as a gate once the gaps
are closed.

Command-line usage::

    python scripts/audit_caribou_layers.py
    python scripts/audit_caribou_layers.py --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import geopandas as gpd
import pandas as pd
import yaml

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_FRAGMENTS: Path = ROOT / "data" / "ws4" / "fragments.gpkg"
DEFAULT_COMPILED: Path = ROOT / "build" / "compiled"
DEFAULT_VARIANT: Path = ROOT / "build" / "compiled_uwr"
DEFAULT_EXPORT: Path = ROOT / "output" / "patchworks" / "fragments" / "fragments.shp"
DEFAULT_SCENARIOS: Path = ROOT / "scenarios"
DEFAULT_CONSTRAINTS: Path = ROOT / "config" / "ws4" / "caribou_constraints.yaml"
DEFAULT_REGISTRY: Path = ROOT / "config" / "ws4" / "scenario_registry.yaml"
DEFAULT_TABLE14: Path = ROOT / "metadata" / "tsr" / "tsa27_thlb_netdown_table14_2022.csv"
DEFAULT_TABLE3: Path = ROOT / "metadata" / "tsr" / "tsa27_thlb_netdown_table3.csv"
DEFAULT_LAND_BASE: Path = ROOT / "metadata" / "tsr" / "tsa27_land_base_reconciliation.csv"
DEFAULT_COMPARISON: Path = ROOT / "metadata" / "ws4" / "scenario_comparison.csv"
DEFAULT_OVERRIDES: Path = ROOT / "metadata" / "ws4" / "block_fragment_overrides.csv"
DEFAULT_ZONE_INVARIANTS: Path = ROOT / "metadata" / "ws4" / "zone_partition_invariants.csv"
DEFAULT_OUT: Path = ROOT / "runtime" / "caribou_audit"

Status = Literal["PASS", "GAP", "FAIL"]

FRAGMENT_ATTRIBUTES: tuple[str, ...] = (
    "caribou_uwr",
    "caribou_core",
    "caribou_matrix",
    "caribou_zone",
    "caribou_immature",
    "ogma",
    "lu_bec",
)

CARIBOU_ACCOUNT_KEYS: tuple[tuple[str, str], ...] = (
    ("caribou_uwr", "UWR area account"),
    ("caribou_core", "core area account"),
    ("caribou_matrix", "matrix area account"),
    ("lt_40", "matrix age <40 account"),
    ("seral", "mature/old seral account by LU/BEC"),
)

FLAGS: tuple[str, ...] = (
    "caribou_uwr",
    "caribou_core",
    "caribou_matrix",
    "caribou_zone",
    "caribou_immature",
    "ogma",
)


@dataclass(frozen=True)
class Check:
    """One audit finding.

    Parameters
    ----------
    check : str
        Stable identifier for the check.
    status : {"PASS", "GAP", "FAIL"}
        The finding status.
    detail : str
        One sentence with the evidence or the gap.
    """

    check: str
    status: Status
    detail: str


@dataclass(frozen=True)
class AuditInputs:
    """The frames and tables the audit evaluates.

    Parameters
    ----------
    fragments : pandas.DataFrame
        The P3.1 fragment attributes.
    compiled_fragments : pandas.DataFrame
        The compiled dataset's ``fragments`` table.
    accounts : pandas.DataFrame
        The compiled dataset's ``accounts`` table.
    features : pandas.DataFrame
        The compiled dataset's ``features`` table.
    curves : pandas.DataFrame
        The compiled dataset's ``curves`` table.
    blocks : pandas.DataFrame
        The compiled dataset's ``blocks`` table.
    variant_blocks : pandas.DataFrame
        The UWR variant's ``blocks`` table.
    export : pandas.DataFrame
        The Patchworks fragment export.
    schedules : mapping of str to pandas.DataFrame
        Schedule name to schedule frame.
    constraints : mapping of str to object
        Parsed ``caribou_constraints.yaml``.
    registry : mapping of str to object
        Parsed ``scenario_registry.yaml``.
    tsr5 : pandas.DataFrame
        TSR5 netdown table 14.
    tsr4 : pandas.DataFrame
        TSR4 netdown table 3.
    land_base : pandas.DataFrame
        The land-base reconciliation table.
    comparison : pandas.DataFrame
        The scenario comparison table.
    variant_manifest : mapping of str to object
        Parsed variant manifest.
    overrides : pandas.DataFrame
        Geometry-resolved ``block_id``/``fragment_id`` overrides.
    zone_invariants : pandas.DataFrame
        Zone-partition invariant checks.
    """

    fragments: pd.DataFrame
    compiled_fragments: pd.DataFrame
    accounts: pd.DataFrame
    features: pd.DataFrame
    curves: pd.DataFrame
    blocks: pd.DataFrame
    variant_blocks: pd.DataFrame
    export: pd.DataFrame
    schedules: Mapping[str, pd.DataFrame]
    constraints: Mapping[str, object]
    registry: Mapping[str, object]
    tsr5: pd.DataFrame
    tsr4: pd.DataFrame
    land_base: pd.DataFrame
    comparison: pd.DataFrame
    variant_manifest: Mapping[str, object]
    overrides: pd.DataFrame
    zone_invariants: pd.DataFrame


def read_frame(path: Path) -> pd.DataFrame:
    """Read a CSV, Parquet, GeoPackage, or shapefile as a plain frame.

    Parameters
    ----------
    path : pathlib.Path
        File to read.

    Returns
    -------
    pandas.DataFrame
        The tabular content, without geometry when the source has geometry.

    Raises
    ------
    ValueError
        When the suffix is not supported.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".gpkg", ".shp", ".geojson"}:
        return pd.DataFrame(gpd.read_file(path, ignore_geometry=True))
    raise ValueError(f"unsupported table suffix: {path.suffix}")


def load_mapping(path: Path) -> Mapping[str, object]:
    """Load a YAML or JSON mapping from ``path``.

    Parameters
    ----------
    path : pathlib.Path
        YAML or JSON file.

    Returns
    -------
    collections.abc.Mapping
        The top-level mapping.

    Raises
    ------
    ValueError
        When the file does not contain a mapping.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload: object = json.loads(text)
    else:
        payload = yaml.safe_load(text)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} does not contain a mapping")
    return {str(key): value for key, value in payload.items()}


def attribute_status(fragments: pd.DataFrame, expected: Sequence[str]) -> pd.DataFrame:
    """Report which expected attributes exist and how much area they flag.

    Parameters
    ----------
    fragments : pandas.DataFrame
        Fragment table, with ``area_ha`` when area is available.
    expected : sequence of str
        Attribute names to check.

    Returns
    -------
    pandas.DataFrame
        One row per attribute with ``present``, ``flagged_fragments``, and
        ``flagged_area_ha``.
    """
    rows: list[dict[str, object]] = []
    for name in expected:
        present = name in fragments.columns
        flagged = 0
        area = 0.0
        if present and pd.api.types.is_numeric_dtype(fragments[name]):
            mask = fragments[name].fillna(0).astype(float) > 0
            flagged = int(mask.sum())
            if "area_ha" in fragments.columns:
                area = float(fragments.loc[mask, "area_ha"].sum())
        elif present:
            flagged = int(fragments[name].notna().sum())
        rows.append(
            {
                "attribute": name,
                "present": present,
                "flagged_fragments": flagged,
                "flagged_area_ha": round(area, 1),
            }
        )
    return pd.DataFrame(rows)


def missing_account_keys(
    accounts: pd.DataFrame, features: pd.DataFrame, expected: Sequence[tuple[str, str]]
) -> list[str]:
    """Return the expected account keys that no account or feature label carries.

    Parameters
    ----------
    accounts : pandas.DataFrame
        Compiled ``accounts`` table.
    features : pandas.DataFrame
        Compiled ``features`` table.
    expected : sequence of tuple of str
        ``(substring, description)`` pairs to look for.

    Returns
    -------
    list of str
        The missing substrings, in the order given.
    """
    labels = {str(value).lower() for value in accounts["account"]} | {
        str(value).lower() for value in features["label"]
    }
    return [
        key for key, _description in expected if not any(key.lower() in label for label in labels)
    ]


def flag_inventory(fragments: pd.DataFrame, flags: Sequence[str]) -> pd.DataFrame:
    """Summarize each caribou zone flag by fragment count and area.

    Parameters
    ----------
    fragments : pandas.DataFrame
        Fragment attributes with ``area_ha``.
    flags : sequence of str
        Flag column names.

    Returns
    -------
    pandas.DataFrame
        One row per flag with ``present``, ``fragments``, and ``area_ha``.
    """
    rows: list[dict[str, object]] = []
    for flag in flags:
        present = flag in fragments.columns
        count = 0
        area = 0.0
        if present:
            mask = fragments[flag].fillna(0).astype(float) > 0
            count = int(mask.sum())
            area = float(fragments.loc[mask, "area_ha"].sum())
        rows.append(
            {"flag": flag, "present": present, "fragments": count, "area_ha": round(area, 1)}
        )
    return pd.DataFrame(rows)


def uwr_area_accounting(fragments: pd.DataFrame) -> dict[str, float]:
    """Compare the binary UWR flag area with the area-weighted intersection.

    Parameters
    ----------
    fragments : pandas.DataFrame
        Fragment attributes with ``area_ha``, ``caribou_uwr``, and
        ``caribou_uwr_frac``.

    Returns
    -------
    dict of str to float
        Flagged area, intersection area, overstatement in hectares and
        percent, and flagged THLB area.

    Raises
    ------
    ValueError
        When a required column is missing.
    """
    required = {"area_ha", "caribou_uwr", "caribou_uwr_frac", "thlb_area_ha"}
    missing = required - set(fragments.columns)
    if missing:
        raise ValueError(f"fragments missing columns: {sorted(missing)}")
    flagged = fragments["caribou_uwr"].fillna(0).astype(float) > 0
    flagged_area = float(fragments.loc[flagged, "area_ha"].sum())
    intersection = float(
        (fragments["area_ha"] * fragments["caribou_uwr_frac"].fillna(0.0).clip(0.0, 1.0)).sum()
    )
    overstatement = flagged_area - intersection
    percent = 100.0 * overstatement / intersection if intersection else 0.0
    thlb_flagged = float(fragments.loc[flagged, "thlb_area_ha"].fillna(0.0).sum())
    return {
        "flagged_area_ha": round(flagged_area, 1),
        "intersection_area_ha": round(intersection, 1),
        "overstatement_ha": round(overstatement, 1),
        "overstatement_pct": round(percent, 2),
        "flagged_thlb_area_ha": round(thlb_flagged, 1),
    }


def block_flag_reconciliation(
    export: pd.DataFrame,
    fragments: pd.DataFrame,
    overrides: pd.DataFrame | None = None,
) -> dict[str, float]:
    """Re-derive block UWR flags from the rounded ``(AU, area, age)`` join.

    Parameters
    ----------
    export : pandas.DataFrame
        Patchworks export with ``BLOCK``, ``AU``, ``AREA_HA``, and ``F_AGE``.
    fragments : pandas.DataFrame
        P3.1 fragments with ``FEATURE_ID``, ``au``, ``area_ha``, ``PROJ_AGE_1``,
        and ``caribou_uwr``.
    overrides : pandas.DataFrame or None, optional
        Geometry-resolved ``block_id``/``fragment_id`` pairs.

    Returns
    -------
    dict of str to float
        Join counts, ambiguous and conflicting blocks, resolved overrides, and
        flagged blocks under the ``max``, ``min``, and exact rules.
    """
    left = pd.DataFrame(
        {
            "block_id": export["BLOCK"].astype(int),
            "area_ha": export["AREA_HA"].astype(float),
            "au": export["AU"].astype(int),
            "area_key": export["AREA_HA"].astype(float).round(3),
            "age_key": export["F_AGE"].astype(float).round(0),
        }
    )
    right = pd.DataFrame(
        {
            "fragment_id": fragments["FEATURE_ID"].astype(int),
            "au": fragments["au"].astype(int),
            "area_key": fragments["area_ha"].astype(float).round(3),
            "age_key": fragments["PROJ_AGE_1"].astype(float).round(0),
            "caribou_uwr": fragments["caribou_uwr"].astype(int),
        }
    )
    duplicate_keys = int(right.duplicated(["au", "area_key", "age_key"]).sum())
    merged = left.merge(right, on=["au", "area_key", "age_key"], how="left")
    merged["caribou_uwr"] = merged["caribou_uwr"].fillna(0).astype(int)
    grouped = merged.groupby("block_id", as_index=False).agg(
        matches=("caribou_uwr", "count"),
        distinct=("caribou_uwr", "nunique"),
        max_flag=("caribou_uwr", "max"),
        min_flag=("caribou_uwr", "min"),
        area_ha=("area_ha", "first"),
    )
    ambiguous = grouped[grouped["matches"] > 1]
    conflicting = ambiguous[ambiguous["distinct"] > 1]
    flags = dict(zip(grouped["block_id"].astype(int), grouped["max_flag"].astype(int), strict=True))
    resolved = 0
    ambiguous_ids = {int(value) for value in ambiguous["block_id"]}
    if overrides is not None and not overrides.empty:
        fragment_flag = dict(
            zip(right["fragment_id"].astype(int), right["caribou_uwr"].astype(int), strict=True)
        )
        for block_id, fragment_id in zip(
            overrides["block_id"].astype(int),
            overrides["fragment_id"].astype(int),
            strict=True,
        ):
            if int(block_id) in ambiguous_ids:
                resolved += 1
            flags[int(block_id)] = fragment_flag[int(fragment_id)]
    unresolved = len(ambiguous) - resolved
    return {
        "export_blocks": float(len(left)),
        "unmatched_blocks": float((grouped["matches"] == 0).sum()),
        "duplicate_fragment_keys": float(duplicate_keys),
        "ambiguous_blocks": float(len(ambiguous)),
        "conflicting_blocks": float(len(conflicting)),
        "conflicting_area_ha": round(float(conflicting["area_ha"].sum()), 1),
        "flagged_blocks_max": float(grouped["max_flag"].sum()),
        "flagged_blocks_min": float(grouped["min_flag"].sum()),
        "resolved_overrides": float(resolved),
        "unresolved_blocks": float(unresolved),
        "flagged_blocks_exact": float(sum(flags.values())),
    }


def schedule_audit(schedule: pd.DataFrame, flags: pd.DataFrame) -> dict[str, int]:
    """Count schedule rows that fall on a UWR-flagged block.

    Parameters
    ----------
    schedule : pandas.DataFrame
        Schedule with ``block_id``.
    flags : pandas.DataFrame
        Block flags with ``block_id`` and ``caribou_uwr``.

    Returns
    -------
    dict of str to int
        Schedule rows, unique blocks, and flagged rows.
    """
    merged = schedule.merge(flags[["block_id", "caribou_uwr"]], on="block_id", how="left")
    merged["caribou_uwr"] = merged["caribou_uwr"].fillna(0).astype(int)
    return {
        "rows": len(schedule),
        "blocks": int(schedule["block_id"].nunique()),
        "flagged_rows": int((merged["caribou_uwr"] > 0).sum()),
    }


def variant_counts(
    compiled_blocks: pd.DataFrame, variant_blocks: pd.DataFrame, manifest_removed: int
) -> dict[str, int]:
    """Compare the UWR variant with the compiled dataset and its manifest.

    Parameters
    ----------
    compiled_blocks : pandas.DataFrame
        Compiled ``blocks`` table.
    variant_blocks : pandas.DataFrame
        Variant ``blocks`` table.
    manifest_removed : int
        ``removed_blocks`` recorded in the variant manifest.

    Returns
    -------
    dict of str to int
        Row and unique-block counts, removed blocks, and any extra blocks.
    """
    compiled_ids = set(compiled_blocks["block_id"].astype(int))
    variant_ids = set(variant_blocks["block_id"].astype(int))
    removed = compiled_ids - variant_ids
    return {
        "compiled_rows": len(compiled_blocks),
        "compiled_blocks": len(compiled_ids),
        "variant_rows": len(variant_blocks),
        "variant_blocks": len(variant_ids),
        "removed_blocks": len(removed),
        "manifest_removed_blocks": manifest_removed,
        "extra_blocks": len(variant_ids - compiled_ids),
    }


def og_profile(features: pd.DataFrame, curves: pd.DataFrame) -> pd.DataFrame:
    """Profile the ``og1`` and ``og2`` seral feature curves.

    Parameters
    ----------
    features : pandas.DataFrame
        Compiled ``features`` table.
    curves : pandas.DataFrame
        Compiled ``curves`` table.

    Returns
    -------
    pandas.DataFrame
        One row per unique ``feature.Area.og1.*`` or ``og2.*`` label with its
        lower and upper age threshold.
    """
    rows: list[dict[str, object]] = []
    labels = features[["label", "curve_id"]].drop_duplicates()
    for label, curve_id in labels.itertuples(index=False):
        name = str(label)
        if not (name.startswith("feature.Area.og1.") or name.startswith("feature.Area.og2.")):
            continue
        if name.endswith(".total"):
            continue
        points = curves.loc[curves["curve_id"] == curve_id, "x"]
        if points.empty:
            continue
        rows.append(
            {
                "og": "og1" if name.startswith("feature.Area.og1.") else "og2",
                "label": name,
                "low": float(points.min()),
                "high": float(points.max()),
            }
        )
    return pd.DataFrame(rows)


def tsr_caribou_areas(table14: pd.DataFrame, table3: pd.DataFrame) -> dict[str, float]:
    """Read the caribou rows from the TSR5 and TSR4 netdown tables.

    Parameters
    ----------
    table14 : pandas.DataFrame
        TSR5 netdown table 14.
    table3 : pandas.DataFrame
        TSR4 netdown table 3.

    Returns
    -------
    dict of str to float
        Gross and net areas and the TSR5 share of AFLB.

    Raises
    ------
    ValueError
        When either caribou row is absent.
    """
    row5 = table14[table14["land_base_element"].astype(str).str.contains("Caribou UWR")]
    row4 = table3[table3["land_base_element"].astype(str).str.contains("Mountain Caribou")]
    if row5.empty or row4.empty:
        raise ValueError("caribou row missing from a TSR netdown table")
    first5 = row5.iloc[0]
    first4 = row4.iloc[0]
    return {
        "tsr5_gross_ha": float(first5["gross_ha"]),
        "tsr5_net_ha": float(first5["net_removed_ha"]),
        "tsr5_pct_aflb": float(first5["pct_of_aflb"]),
        "tsr4_gross_ha": float(first4["total_area_ha"]),
        "tsr4_net_ha": float(first4["effective_netdown_ha"]),
    }


def enforcement_rows(payload: Mapping[str, object]) -> list[dict[str, str]]:
    """Collect the layer/enforcement pairs from the constraints mapping.

    Parameters
    ----------
    payload : collections.abc.Mapping
        Parsed ``caribou_constraints.yaml``.

    Returns
    -------
    list of dict
        One row per layer with an ``enforcement`` key.
    """
    rows: list[dict[str, str]] = []
    for key, value in payload.items():
        if isinstance(value, Mapping):
            if "enforcement" in value:
                rows.append(
                    {
                        "layer": key,
                        "enforcement": str(value.get("enforcement", "")),
                        "status": str(value.get("status", "")),
                    }
                )
            else:
                rows.extend(enforcement_rows(value))
    return rows


def supported_scenarios(registry: Mapping[str, object]) -> dict[str, str]:
    """Return scenario id to status for every registry entry.

    Parameters
    ----------
    registry : collections.abc.Mapping
        Parsed ``scenario_registry.yaml``.

    Returns
    -------
    dict of str to str
        Scenario id to status.

    Raises
    ------
    ValueError
        When the registry has no scenarios mapping.
    """
    scenarios = registry.get("scenarios")
    if not isinstance(scenarios, Mapping):
        raise ValueError("scenario registry has no scenarios mapping")
    result: dict[str, str] = {}
    for name, spec in scenarios.items():
        if isinstance(spec, Mapping):
            result[str(name)] = str(spec.get("status", "unknown"))
    return result


def build_checks(inputs: AuditInputs) -> list[Check]:
    """Run every caribou accounting check.

    Parameters
    ----------
    inputs : AuditInputs
        The loaded frames and tables.

    Returns
    -------
    list of Check
        The findings, in a stable order.
    """
    checks: list[Check] = []

    attributes = attribute_status(inputs.compiled_fragments, FRAGMENT_ATTRIBUTES)
    missing_attributes = [
        str(row.attribute) for row in attributes.itertuples() if not bool(row.present)
    ]
    checks.append(
        Check(
            "compiled_fragment_attributes",
            "GAP" if missing_attributes else "PASS",
            "compiled dataset carries no caribou/LU attributes: " + ", ".join(missing_attributes)
            if missing_attributes
            else "every expected caribou/LU attribute is present",
        )
    )

    missing_keys = missing_account_keys(inputs.accounts, inputs.features, CARIBOU_ACCOUNT_KEYS)
    checks.append(
        Check(
            "caribou_accounts",
            "GAP" if missing_keys else "PASS",
            "no account or feature label for: " + ", ".join(missing_keys)
            if missing_keys
            else "every expected caribou account is present",
        )
    )

    inventory = flag_inventory(inputs.fragments, FLAGS)
    empty_flags = inventory[inventory["fragments"].astype(int) == 0]
    zero_flags = [str(value) for value in empty_flags["flag"]]
    checks.append(
        Check(
            "p31_zone_flags",
            "GAP" if zero_flags else "PASS",
            "zone flags with no fragments: " + ", ".join(zero_flags)
            if zero_flags
            else "every zone flag has fragments",
        )
    )

    area = uwr_area_accounting(inputs.fragments)
    checks.append(
        Check(
            "uwr_area_accounting",
            "GAP" if abs(area["overstatement_pct"]) > 1.0 else "PASS",
            f"flag {area['flagged_area_ha']:,.0f} ha vs weighted intersection "
            f"{area['intersection_area_ha']:,.0f} ha "
            f"({area['overstatement_ha']:+,.0f} ha, {area['overstatement_pct']:+.2f}%)",
        )
    )

    join = block_flag_reconciliation(inputs.export, inputs.fragments, inputs.overrides)
    checks.append(
        Check(
            "uwr_block_join",
            "GAP" if join["unresolved_blocks"] > 0 or join["unmatched_blocks"] > 0 else "PASS",
            f"{join['ambiguous_blocks']:.0f} ambiguous blocks, "
            f"{join['resolved_overrides']:.0f} resolved by geometry, "
            f"{join['unresolved_blocks']:.0f} unresolved; "
            f"exact flags {join['flagged_blocks_exact']:.0f}",
        )
    )

    flags = _block_flags(inputs.export, inputs.fragments, inputs.overrides)
    base_rows = 0
    base_flagged = 0
    filtered_rows = 0
    filtered_flagged = 0
    for name, schedule in inputs.schedules.items():
        result = schedule_audit(schedule, flags)
        if name == "s3_base":
            base_rows = result["rows"]
            base_flagged = result["flagged_rows"]
        if "uwr_excluded" in name:
            filtered_rows = result["rows"]
            filtered_flagged = result["flagged_rows"]
    added_up = base_rows == filtered_rows + base_flagged
    checks.append(
        Check(
            "schedule_uwr_filter",
            "FAIL" if filtered_flagged > 0 or not added_up else "PASS",
            f"base {base_rows:,} rows, {base_flagged:,} flagged; "
            f"filtered {filtered_rows:,} rows, {filtered_flagged:,} flagged; "
            + ("row counts add up" if added_up else "row counts do not add up"),
        )
    )

    variant = variant_counts(
        inputs.blocks,
        inputs.variant_blocks,
        variant_removed_blocks(inputs.variant_manifest),
    )
    variant_ok = (
        variant["removed_blocks"] == variant["manifest_removed_blocks"]
        and variant["extra_blocks"] == 0
    )
    checks.append(
        Check(
            "uwr_variant_manifest",
            "PASS" if variant_ok else "FAIL",
            f"removed {variant['removed_blocks']:,} blocks vs manifest "
            f"{variant['manifest_removed_blocks']:,}; "
            f"{variant['extra_blocks']:,} extra blocks in the variant",
        )
    )

    tsr = tsr_caribou_areas(inputs.tsr5, inputs.tsr4)
    p1_clip = _p1_uwr_clip(inputs.land_base)
    checks.append(
        Check(
            "tsr_gross_reconciliation",
            "PASS" if abs(p1_clip - tsr["tsr5_gross_ha"]) / tsr["tsr5_gross_ha"] <= 0.01 else "GAP",
            f"P1 direct clip {p1_clip:,.0f} ha vs TSR5 gross {tsr['tsr5_gross_ha']:,.0f} ha; "
            f"compiled flag {area['flagged_area_ha']:,.0f} ha is on the P2 checkpoint, "
            "not the P1 land base",
        )
    )

    flagged_thlb = area["flagged_thlb_area_ha"]
    treated_delta = _treated_delta(inputs.comparison)
    treat_ok = treated_delta > 0 and abs(flagged_thlb - treated_delta) / treated_delta <= 0.01
    checks.append(
        Check(
            "uwr_treated_area",
            "PASS" if treat_ok else "GAP",
            f"flagged THLB {flagged_thlb:,.0f} ha vs treated-area delta {treated_delta:,.0f} ha",
        )
    )

    labels = {str(value) for value in inputs.features["label"]}
    has_seral = {"feature.Seral.mature", "feature.Seral.overmature"} <= labels
    checks.append(
        Check(
            "seral_thresholds",
            "PASS" if has_seral else "GAP",
            "feature.Seral.mature/overmature present (140/250)"
            if has_seral
            else "no feature.Seral.mature/overmature labels",
        )
    )
    profile = og_profile(inputs.features, inputs.curves)
    if has_seral:
        basis_detail = "feature.Seral.* is AU-level; no LU/BEC partition"
    elif profile.empty:
        basis_detail = "no og1/og2 or feature.Seral curves found"
    else:
        og1 = profile[profile["og"] == "og1"]
        crosses = int(((og1["low"] <= 140) & (og1["high"] >= 140)).sum())
        basis_detail = (
            f"og1 is an AU ramp ({crosses}/{len(og1)} cross age 140); "
            "no feature.Seral labels; no LU/BEC partition"
        )
    checks.append(Check("seral_account_basis", "GAP", basis_detail))

    if inputs.zone_invariants.empty:
        zone_status: Status = "GAP"
        zone_detail = "no zone-partition invariants recorded"
    else:
        zone_ok = bool(inputs.zone_invariants["pass"].astype(bool).all())
        zone_status = "PASS" if zone_ok else "FAIL"
        passed = int(inputs.zone_invariants["pass"].astype(bool).sum())
        zone_detail = (
            f"{passed}/{len(inputs.zone_invariants)} invariants pass; "
            f"max |delta| {float(inputs.zone_invariants['delta'].abs().max()):.3f}"
        )
    checks.append(Check("zone_partition", zone_status, zone_detail))

    layers = enforcement_rows(inputs.constraints)
    unenforced = [
        row["layer"] for row in layers if row["enforcement"] not in {"schedule_filter", "enforced"}
    ]
    checks.append(
        Check(
            "layer_enforcement",
            "GAP" if unenforced else "PASS",
            "mapped but not enforced: " + ", ".join(unenforced)
            if unenforced
            else "every layer is enforced",
        )
    )

    scenarios = supported_scenarios(inputs.registry)
    unimplemented = [name for name, status in scenarios.items() if status != "supported"]
    checks.append(
        Check(
            "scenario_coverage",
            "GAP" if unimplemented else "PASS",
            "not fully implemented: " + ", ".join(unimplemented)
            if unimplemented
            else "every scenario is supported",
        )
    )

    scripts = [ROOT / "scripts" / "build_compiled_uwr.py", ROOT / "scripts" / "max_flow.py"]
    absent = [path.name for path in scripts if not path.is_file()]
    checks.append(
        Check(
            "reproducibility_inputs",
            "GAP" if absent else "PASS",
            "missing build/analysis scripts: " + ", ".join(absent)
            if absent
            else "variant build and level search scripts are present",
        )
    )

    return checks


def variant_removed_blocks(manifest: Mapping[str, object]) -> int:
    """Read ``metadata.removed_blocks`` from a variant manifest.

    Parameters
    ----------
    manifest : collections.abc.Mapping
        Parsed variant manifest.

    Returns
    -------
    int
        The recorded removed-block count, or ``-1`` when absent.
    """
    metadata = manifest.get("metadata")
    if isinstance(metadata, Mapping):
        value = metadata.get("removed_blocks", -1)
        if isinstance(value, int):
            return value
    return -1


def _block_flags(
    export: pd.DataFrame,
    fragments: pd.DataFrame,
    overrides: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return one UWR flag per export block.

    Parameters
    ----------
    export : pandas.DataFrame
        Patchworks export.
    fragments : pandas.DataFrame
        P3.1 fragments.
    overrides : pandas.DataFrame or None, optional
        Geometry-resolved ``block_id``/``fragment_id`` pairs.

    Returns
    -------
    pandas.DataFrame
        ``block_id`` and ``caribou_uwr`` columns.
    """
    left = pd.DataFrame(
        {
            "block_id": export["BLOCK"].astype(int),
            "au": export["AU"].astype(int),
            "area_key": export["AREA_HA"].astype(float).round(3),
            "age_key": export["F_AGE"].astype(float).round(0),
        }
    )
    right = pd.DataFrame(
        {
            "fragment_id": fragments["FEATURE_ID"].astype(int),
            "au": fragments["au"].astype(int),
            "area_key": fragments["area_ha"].astype(float).round(3),
            "age_key": fragments["PROJ_AGE_1"].astype(float).round(0),
            "caribou_uwr": fragments["caribou_uwr"].astype(int),
        }
    )
    merged = left.merge(right, on=["au", "area_key", "age_key"], how="left")
    if overrides is not None and not overrides.empty:
        chosen = overrides.set_index("block_id")["fragment_id"].astype(int)
        in_override = merged["block_id"].isin(chosen.index)
        keep = (~in_override) | (merged["fragment_id"] == merged["block_id"].map(chosen))
        merged = merged.loc[keep]
    merged["caribou_uwr"] = merged["caribou_uwr"].fillna(0).astype(int)
    flags = merged.groupby("block_id", as_index=False).agg(caribou_uwr=("caribou_uwr", "max"))
    return pd.DataFrame(flags).sort_values("block_id").reset_index(drop=True)


def _p1_uwr_clip(land_base: pd.DataFrame) -> float:
    """Read the P1 direct UWR clip from the land-base reconciliation table.

    Parameters
    ----------
    land_base : pandas.DataFrame
        Reconciliation table with ``metric`` and ``ws4_ha``.

    Returns
    -------
    float
        The P1 clip area in hectares.

    Raises
    ------
    ValueError
        When the row is absent.
    """
    row = land_base[land_base["metric"] == "caribou_uwr_gross"]
    if row.empty:
        raise ValueError("caribou_uwr_gross row missing from the reconciliation table")
    return float(row.iloc[0]["ws4_ha"])


def _treated_delta(comparison: pd.DataFrame) -> float:
    """Return the treated-area reduction for the UWR scenario.

    Parameters
    ----------
    comparison : pandas.DataFrame
        Scenario comparison with ``scenario`` and ``treated_delta_ha``.

    Returns
    -------
    float
        The absolute treated-area delta in hectares, or ``0.0`` when absent.
    """
    row = comparison[comparison["scenario"] == "s3_tsr5_base"]
    if row.empty:
        return 0.0
    return abs(float(row.iloc[0]["treated_delta_ha"]))


def load_inputs(
    fragments_path: Path,
    compiled_dir: Path,
    variant_dir: Path,
    export_path: Path,
    scenarios_dir: Path,
    constraints_path: Path,
    registry_path: Path,
    table14_path: Path,
    table3_path: Path,
    land_base_path: Path,
    comparison_path: Path,
    overrides_path: Path,
    zone_invariants_path: Path,
) -> AuditInputs:
    """Load every audit input from disk.

    Parameters
    ----------
    fragments_path : pathlib.Path
        P3.1 fragment attributes.
    compiled_dir : pathlib.Path
        Compiled dataset directory.
    variant_dir : pathlib.Path
        UWR variant directory.
    export_path : pathlib.Path
        Patchworks fragment export.
    scenarios_dir : pathlib.Path
        Directory of ``*.schedule.csv`` files.
    constraints_path : pathlib.Path
        ``caribou_constraints.yaml``.
    registry_path : pathlib.Path
        ``scenario_registry.yaml``.
    table14_path : pathlib.Path
        TSR5 netdown table 14.
    table3_path : pathlib.Path
        TSR4 netdown table 3.
    land_base_path : pathlib.Path
        Land-base reconciliation table.
    comparison_path : pathlib.Path
        Scenario comparison table.
    overrides_path : pathlib.Path
        Geometry-resolved block-to-fragment overrides.
    zone_invariants_path : pathlib.Path
        Zone-partition invariant checks.

    Returns
    -------
    AuditInputs
        The loaded inputs.
    """
    schedules = {
        path.name.removesuffix(".schedule.csv"): read_frame(path)
        for path in sorted(scenarios_dir.glob("*.schedule.csv"))
    }
    return AuditInputs(
        fragments=read_frame(fragments_path),
        compiled_fragments=read_frame(compiled_dir / "fragments.parquet"),
        accounts=read_frame(compiled_dir / "accounts.parquet"),
        features=read_frame(compiled_dir / "features.parquet"),
        curves=read_frame(compiled_dir / "curves.parquet"),
        blocks=read_frame(compiled_dir / "blocks.parquet"),
        variant_blocks=read_frame(variant_dir / "blocks.parquet"),
        export=read_frame(export_path),
        schedules=schedules,
        constraints=load_mapping(constraints_path),
        registry=load_mapping(registry_path),
        tsr5=read_frame(table14_path),
        tsr4=read_frame(table3_path),
        land_base=read_frame(land_base_path),
        comparison=read_frame(comparison_path),
        variant_manifest=load_mapping(variant_dir / "manifest.json"),
        overrides=(
            read_frame(overrides_path)
            if overrides_path.is_file()
            else pd.DataFrame({"block_id": [], "fragment_id": []})
        ),
        zone_invariants=(
            read_frame(zone_invariants_path)
            if zone_invariants_path.is_file()
            else pd.DataFrame({"invariant": [], "pass": []})
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the caribou accounting audit.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` when every check passes or only gaps remain, ``1`` on a failure
        (or on any gap with ``--strict``).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=Path, default=DEFAULT_FRAGMENTS)
    parser.add_argument("--compiled", type=Path, default=DEFAULT_COMPILED)
    parser.add_argument("--variant", type=Path, default=DEFAULT_VARIANT)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--constraints", type=Path, default=DEFAULT_CONSTRAINTS)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--table14", type=Path, default=DEFAULT_TABLE14)
    parser.add_argument("--table3", type=Path, default=DEFAULT_TABLE3)
    parser.add_argument("--land-base", type=Path, default=DEFAULT_LAND_BASE)
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARISON)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--zone-invariants", type=Path, default=DEFAULT_ZONE_INVARIANTS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    inputs = load_inputs(
        args.fragments,
        args.compiled,
        args.variant,
        args.export,
        args.scenarios,
        args.constraints,
        args.registry,
        args.table14,
        args.table3,
        args.land_base,
        args.comparison,
        args.overrides,
        args.zone_invariants,
    )
    checks = build_checks(inputs)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame([asdict(check) for check in checks])
    summary.to_csv(args.out_dir / "summary.csv", index=False)
    (args.out_dir / "summary.json").write_text(
        json.dumps({"checks": [asdict(check) for check in checks]}, indent=2),
        encoding="utf-8",
    )
    flag_inventory(inputs.fragments, FLAGS).to_csv(args.out_dir / "flag_inventory.csv", index=False)
    og_profile(inputs.features, inputs.curves).to_csv(args.out_dir / "og_profile.csv", index=False)
    for check in checks:
        print(f"{check.status:<4}  {check.check:<28}  {check.detail}")
    failures = sum(check.status == "FAIL" for check in checks)
    gaps = sum(check.status == "GAP" for check in checks)
    passed = len(checks) - failures - gaps
    print(f"\n{len(checks)} checks: {passed} pass, {gaps} gap, {failures} fail")
    print(f"wrote {args.out_dir}")
    if failures:
        return 1
    if args.strict and gaps:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
