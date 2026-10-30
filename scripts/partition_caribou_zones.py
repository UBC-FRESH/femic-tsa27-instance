#!/usr/bin/env python3
"""Partition a compiled WS4 dataset by caribou zone and LU/BEC.

The partition is a post-compile track split. Every used ``(track, zone, lu_bec)``
combination becomes a clone of the source track, with zone-qualified area, seral,
and harvest labels. The source tables are not modified; the output is a separate
dataset directory.

Why a post-compile split: the ForestModelXML recipe has fixed define fields, so a
zone or LU/BEC partition cannot be expressed without a FEMIC change. The WS4
compiler already resolves a track from its define fields; cloning after compile
reuses the validated recipe and keeps the source dataset intact.

Command-line usage::

    python scripts/partition_caribou_zones.py
    python scripts/partition_caribou_zones.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_DATASET: Path = ROOT / "build" / "compiled"
DEFAULT_EXPORT: Path = ROOT / "output" / "patchworks" / "fragments" / "fragments.shp"
DEFAULT_FRAGMENTS: Path = ROOT / "data" / "ws4" / "fragments.gpkg"
DEFAULT_OVERRIDES: Path = ROOT / "metadata" / "ws4" / "block_fragment_overrides.csv"
DEFAULT_OUT: Path = ROOT / "build" / "compiled_zone"
DEFAULT_SUMMARY: Path = ROOT / "metadata" / "ws4" / "zone_partition_summary.csv"
DEFAULT_MANIFEST: Path = ROOT / "build" / "compiled_zone" / "partition_manifest.json"


def _as_int(value: object) -> int:
    """Convert a scalar to an integer.

    Parameters
    ----------
    value : object
        A numeric or numeric string.

    Returns
    -------
    int
        The integer value.
    """
    return int(float(str(value)))


def _as_float(value: object) -> float:
    """Convert a scalar to a float.

    Parameters
    ----------
    value : object
        A numeric or numeric string.

    Returns
    -------
    float
        The float value.
    """
    return float(str(value))


TABLES: tuple[str, ...] = (
    "fragments",
    "blocks",
    "tracks",
    "strata",
    "treatments",
    "curves",
    "features",
    "products",
    "accounts",
    "protoaccounts",
    "groups",
    "messages",
)


@dataclass(frozen=True)
class DatasetTables:
    """The compiled WS4 tables and their manifest.

    Parameters
    ----------
    fragments, blocks, tracks, strata, treatments, curves, features, products,
    accounts, protoaccounts, groups, messages : pandas.DataFrame
        The compiled dataset tables.
    manifest : dict
        The parsed ``manifest.json``.
    """

    fragments: pd.DataFrame
    blocks: pd.DataFrame
    tracks: pd.DataFrame
    strata: pd.DataFrame
    treatments: pd.DataFrame
    curves: pd.DataFrame
    features: pd.DataFrame
    products: pd.DataFrame
    accounts: pd.DataFrame
    protoaccounts: pd.DataFrame
    groups: pd.DataFrame
    messages: pd.DataFrame
    manifest: dict[str, object]


def load_dataset(path: Path) -> DatasetTables:
    """Load a compiled dataset directory.

    Parameters
    ----------
    path : pathlib.Path
        Directory with the parquet tables and ``manifest.json``.

    Returns
    -------
    DatasetTables
        The loaded tables.
    """
    return DatasetTables(
        fragments=pd.read_parquet(path / "fragments.parquet"),
        blocks=pd.read_parquet(path / "blocks.parquet"),
        tracks=pd.read_parquet(path / "tracks.parquet"),
        strata=pd.read_parquet(path / "strata.parquet"),
        treatments=pd.read_parquet(path / "treatments.parquet"),
        curves=pd.read_parquet(path / "curves.parquet"),
        features=pd.read_parquet(path / "features.parquet"),
        products=pd.read_parquet(path / "products.parquet"),
        accounts=pd.read_parquet(path / "accounts.parquet"),
        protoaccounts=pd.read_parquet(path / "protoaccounts.parquet"),
        groups=pd.read_parquet(path / "groups.parquet"),
        messages=pd.read_parquet(path / "messages.parquet"),
        manifest=json.loads((path / "manifest.json").read_text(encoding="utf-8")),
    )


def write_dataset(tables: DatasetTables, path: Path) -> None:
    """Write a dataset directory.

    Parameters
    ----------
    tables : DatasetTables
        The tables to write.
    path : pathlib.Path
        Destination directory.
    """
    path.mkdir(parents=True, exist_ok=True)
    for name in TABLES:
        frame = getattr(tables, name)
        frame.to_parquet(path / f"{name}.parquet", index=False)
    (path / "manifest.json").write_text(json.dumps(tables.manifest, indent=2), encoding="utf-8")


def partition_token(zone: str, lubec: str) -> str:
    """Return a label-safe token for a zone and LU/BEC pair.

    Parameters
    ----------
    zone : str
        Caribou domain (``uwr``, ``core``, ``matrix``, ``hlp``, ``other``).
    lubec : str
        ``<landscape unit>|<BEC>`` string.

    Returns
    -------
    str
        A token with non-alphanumeric characters replaced by underscores.
    """
    return f"{zone}__{lubec_token(lubec)}"


def lubec_token(lubec: str) -> str:
    """Return a label-safe token for a LU/BEC value.

    Parameters
    ----------
    lubec : str
        ``<landscape unit>|<BEC>`` string.

    Returns
    -------
    str
        The token with non-alphanumeric characters replaced by underscores.
    """
    return "".join(character if character.isalnum() else "_" for character in lubec)


def qualify_label(label: str, token: str) -> str:
    """Return the zone-qualified version of a feature or product label.

    Parameters
    ----------
    label : str
        Source label.
    token : str
        Partition token from :func:`partition_token`.

    Returns
    -------
    str
        The qualified label, or the source label when it is not partitioned.
    """
    if label.startswith("product.HarvestedVolume."):
        return label.replace("product.HarvestedVolume.", f"product.HarvestedVolume.{token}.", 1)
    if label.startswith(("product.Treated.", "feature.Area.", "feature.Seral.")):
        return f"{label}.{token}"
    return label


def derive_domain(fragments: pd.DataFrame) -> pd.Series:
    """Derive a mutually exclusive caribou domain from the P3.1 flags.

    Parameters
    ----------
    fragments : pandas.DataFrame
        P3.1 fragments with ``caribou_uwr``, ``caribou_core``, ``caribou_matrix``,
        and ``caribou_zone``.

    Returns
    -------
    pandas.Series
        One domain per fragment: ``uwr``, ``core``, ``matrix``, ``hlp``, or
        ``other``.
    """
    uwr = fragments["caribou_uwr"].fillna(0).astype(int) > 0
    core = fragments["caribou_core"].fillna(0).astype(int) > 0
    matrix = fragments["caribou_matrix"].fillna(0).astype(int) > 0
    hlp = fragments["caribou_zone"].fillna(0).astype(int) > 0
    domain = np.select([uwr, core, matrix, hlp], ["uwr", "core", "matrix", "hlp"], "other")
    return pd.Series(domain, index=fragments.index, name="zone")


def build_partition_table(
    export: pd.DataFrame,
    fragments: pd.DataFrame,
    overrides: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Map each export block to one zone and LU/BEC.

    Parameters
    ----------
    export : pandas.DataFrame
        Patchworks export with ``BLOCK``, ``AU``, ``AREA_HA``, and ``F_AGE``.
    fragments : pandas.DataFrame
        P3.1 fragments with ``FEATURE_ID``, ``au``, ``area_ha``, ``PROJ_AGE_1``,
        ``caribou_uwr``, ``caribou_core``, ``caribou_matrix``, ``caribou_zone``,
        and ``lu_bec``.
    overrides : pandas.DataFrame or None, optional
        Geometry-resolved ``block_id``/``fragment_id`` pairs.

    Returns
    -------
    pandas.DataFrame
        One row per block with ``block_id``, ``zone``, and ``lubec``.

    Raises
    ------
    ValueError
        When a block has more than one key candidate and no override.
    """
    left = pd.DataFrame(
        {
            "block_id": export["BLOCK"].astype(int),
            "au": export["AU"].astype(int),
            "area_key": export["AREA_HA"].astype(float).round(3),
            "age_key": export["F_AGE"].astype(float).round(0),
        }
    )
    right = fragments.loc[
        :,
        [
            "FEATURE_ID",
            "au",
            "area_ha",
            "PROJ_AGE_1",
            "caribou_uwr",
            "caribou_core",
            "caribou_matrix",
            "caribou_zone",
            "lu_bec",
        ],
    ].copy()
    right["area_key"] = right["area_ha"].astype(float).round(3)
    right["age_key"] = right["PROJ_AGE_1"].astype(float).round(0)
    right["fragment_id"] = right["FEATURE_ID"].astype(int)
    right["zone"] = derive_domain(right)
    right["lubec"] = right["lu_bec"].fillna("UNK|UNK").astype(str)
    merged = left.merge(
        right[["fragment_id", "au", "area_key", "age_key", "zone", "lubec"]],
        on=["au", "area_key", "age_key"],
        how="left",
    )
    if overrides is not None and not overrides.empty:
        chosen = overrides.set_index("block_id")["fragment_id"].astype(int)
        in_override = merged["block_id"].isin(chosen.index)
        keep = (~in_override) | (merged["fragment_id"] == merged["block_id"].map(chosen))
        merged = merged.loc[keep]
    counts = merged.groupby("block_id")["fragment_id"].count()
    unresolved = counts[counts != 1]
    if not unresolved.empty:
        raise ValueError(f"{len(unresolved)} blocks do not resolve to one fragment; add overrides")
    merged = merged.loc[merged["zone"].notna() & merged["lubec"].notna()]
    return merged.loc[:, ["block_id", "zone", "lubec"]].sort_values("block_id")


def _clone_frame(
    fragments: pd.DataFrame, partition: pd.DataFrame, treatments: pd.DataFrame
) -> pd.DataFrame:
    """Return one row per cloned ``(track, zone, lubec)`` combination.

    Parameters
    ----------
    fragments : pandas.DataFrame
        Compiled fragments with ``block_id`` and ``track_id``.
    partition : pandas.DataFrame
        ``block_id``, ``zone``, and ``lubec``.
    treatments : pandas.DataFrame
        Compiled treatments with ``track_id`` and ``new_track``.

    Returns
    -------
    pandas.DataFrame
        ``old_track``, ``zone``, ``lubec``, ``token``, and ``new_track``.
    """
    joined = fragments[["block_id", "track_id"]].merge(partition, on="block_id", how="left")
    if joined["zone"].isna().any():
        raise ValueError("some fragments have no partition")
    used = joined.loc[:, ["track_id", "zone", "lubec"]].drop_duplicates()
    targets: dict[int, set[int]] = {}
    for track, target in treatments.loc[:, ["track_id", "new_track"]].itertuples(index=False):
        targets.setdefault(_as_int(track), set()).add(_as_int(target))
    pending: list[tuple[int, str, str]] = [
        (_as_int(row.track_id), str(row.zone), str(row.lubec)) for row in used.itertuples()
    ]
    combos = set(pending)
    while pending:
        track, zone, lubec = pending.pop()
        for target in targets.get(track, set()):
            key = (target, zone, lubec)
            if key not in combos:
                combos.add(key)
                pending.append(key)
    start = int(treatments["track_id"].max()) + 1
    rows = [
        {
            "old_track": track,
            "zone": zone,
            "lubec": lubec,
            "token": partition_token(zone, lubec),
            "lubec_token": lubec_token(lubec),
            "new_track": start + index,
        }
        for index, (track, zone, lubec) in enumerate(sorted(combos))
    ]
    return pd.DataFrame(rows)


def _unity_curve(curves: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Return the curves table and a curve id whose value is always one.

    Parameters
    ----------
    curves : pandas.DataFrame
        Compiled curves with ``curve_id``, ``x``, and ``y``.

    Returns
    -------
    tuple of pandas.DataFrame and int
        The curves table (extended when needed) and the unity curve id.
    """
    for curve_id, group in curves.groupby("curve_id"):
        if bool((group["y"].astype(float) == 1.0).all()):
            return curves, _as_int(curve_id)
    new_id = _as_int(curves["curve_id"].max()) + 1
    addition = pd.DataFrame({"curve_id": [new_id, new_id], "x": [0.0, 1000.0], "y": [1.0, 1.0]})
    return pd.concat([curves, addition], ignore_index=True), new_id


def _mature_old_curve(curves: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Return the curves table and a curve that is one at age 140 and older.

    Parameters
    ----------
    curves : pandas.DataFrame
        Compiled curves with ``curve_id``, ``x``, and ``y``.

    Returns
    -------
    tuple of pandas.DataFrame and int
        The curves table (extended) and the mature+old curve id.
    """
    new_id = _as_int(curves["curve_id"].max()) + 1
    addition = pd.DataFrame(
        {"curve_id": [new_id, new_id, new_id], "x": [0.0, 139.0, 140.0], "y": [0.0, 0.0, 1.0]}
    )
    return pd.concat([curves, addition], ignore_index=True), new_id


def _expand_accounts(
    source: pd.DataFrame,
    feature_labels: Sequence[str],
    product_labels: Sequence[str],
    additions: Sequence[tuple[str, str]],
) -> pd.DataFrame:
    """Add account rows for the qualified feature and product labels.

    Parameters
    ----------
    source : pandas.DataFrame
        Source accounts table.
    feature_labels : sequence of str
        Qualified feature labels to add.
    product_labels : sequence of str
        Qualified product labels to add.
    additions : sequence of tuple of str
        Extra ``(label, group)`` pairs with no source account.

    Returns
    -------
    pandas.DataFrame
        The expanded accounts table.
    """
    by_attribute = {str(row.attribute): row for row in source.itertuples(index=False)}
    rows: list[dict[str, object]] = [
        {
            "group": str(row.group),
            "attribute": str(row.attribute),
            "account": str(row.account),
            "sum": _as_float(row.sum),
        }
        for row in source.itertuples(index=False)
    ]
    existing = {str(row.account) for row in source.itertuples(index=False)}
    for label in [*feature_labels, *product_labels]:
        if label in existing:
            continue
        source_label = label.rsplit(".", 1)[0]
        match = by_attribute.get(label) or by_attribute.get(source_label)
        rows.append(
            {
                "group": str(match.group) if match is not None else "_ALL_",
                "attribute": label,
                "account": label,
                "sum": _as_float(match.sum) if match is not None else 1.0,
            }
        )
        existing.add(label)
    for label, group in additions:
        if label in existing:
            continue
        rows.append({"group": group, "attribute": label, "account": label, "sum": 1.0})
        existing.add(label)
    return pd.DataFrame(rows, columns=["group", "attribute", "account", "sum"])


def partition_dataset(
    tables: DatasetTables,
    partition: pd.DataFrame,
    no_harvest_zones: Sequence[str] = (),
) -> tuple[DatasetTables, dict[str, object]]:
    """Clone every used track by zone and LU/BEC.

    Parameters
    ----------
    tables : DatasetTables
        Source compiled dataset.
    partition : pandas.DataFrame
        One row per block with ``block_id``, ``zone``, and ``lubec``.
    no_harvest_zones : sequence of str, optional
        Zones whose cloned tracks carry no treatment rows.

    Returns
    -------
    tuple of DatasetTables and dict
        The partitioned dataset and its summary counts.
    """
    clone = _clone_frame(tables.fragments, partition, tables.treatments)

    tracks = clone.merge(
        tables.tracks.rename(columns={"track_id": "old_track"}), on="old_track", how="left"
    )
    tracks["track_id"] = tracks["new_track"].astype(int)
    tracks["name"] = (
        tracks["name"].astype(str)
        + "+ZONE("
        + tracks["zone"].astype(str)
        + ")+LUBEC("
        + tracks["token"].astype(str)
        + ")"
    )
    tracks = tracks.loc[:, ["track_id", "name"]]

    strata = clone.merge(
        tables.strata.rename(columns={"track_id": "old_track"}), on="old_track", how="left"
    ).dropna(subset=["offset"])
    strata["track_id"] = strata["new_track"].astype(int)
    strata = strata.loc[:, ["track_id", "offset", "next_age", "cycle"]]

    clone_for_merge = clone.rename(columns={"new_track": "clone_track"})
    treatments = clone_for_merge.merge(
        tables.treatments.rename(columns={"track_id": "old_track"}), on="old_track", how="left"
    ).dropna(subset=["treatment"])
    treatments["track_id"] = treatments["clone_track"].astype(int)
    target_map = {
        (_as_int(row.old_track), str(row.zone), str(row.lubec)): _as_int(row.clone_track)
        for row in clone_for_merge.itertuples()
    }
    treatments["new_track"] = [
        target_map[(_as_int(target), str(zone), str(lubec))]
        for target, zone, lubec in zip(
            treatments["new_track"], treatments["zone"], treatments["lubec"], strict=True
        )
    ]
    treatments = treatments.loc[
        :, ["track_id", "begin", "end", "treatment", "new_track", "offset", "retain", "zone"]
    ]
    if no_harvest_zones:
        treatments = treatments.loc[~treatments["zone"].isin(list(no_harvest_zones))]
    for column in ("track_id", "begin", "end", "new_track", "offset", "retain"):
        treatments[column] = treatments[column].astype(int)
    treatments = treatments.loc[
        :, ["track_id", "begin", "end", "treatment", "new_track", "offset", "retain"]
    ]

    features = clone.merge(
        tables.features.rename(columns={"track_id": "old_track"}), on="old_track", how="left"
    ).dropna(subset=["label"])
    features["track_id"] = features["new_track"].astype(int)
    base = features.loc[:, ["track_id", "label", "curve_id"]].copy()
    qualified = base.copy()
    qualified["label"] = [
        qualify_label(str(label), str(token))
        for label, token in zip(qualified["label"], features["token"], strict=True)
    ]
    qualified = qualified[qualified["label"] != base["label"]]
    curves, unity = _unity_curve(tables.curves)
    curves, mature_old = _mature_old_curve(curves)
    area = clone.loc[:, ["new_track", "zone", "token", "lubec_token"]].drop_duplicates()
    area_rows = pd.concat(
        [
            pd.DataFrame(
                {
                    "track_id": area["new_track"].astype(int),
                    "label": "feature.Area." + area["zone"].astype(str),
                    "curve_id": unity,
                }
            ),
            pd.DataFrame(
                {
                    "track_id": area["new_track"].astype(int),
                    "label": "feature.Area." + area["token"].astype(str),
                    "curve_id": unity,
                }
            ),
            pd.DataFrame(
                {
                    "track_id": area["new_track"].astype(int),
                    "label": "feature.Area." + area["lubec_token"].astype(str),
                    "curve_id": unity,
                }
            ),
        ],
        ignore_index=True,
    )
    mature_old_rows = pd.concat(
        [
            pd.DataFrame(
                {
                    "track_id": area["new_track"].astype(int),
                    "label": "feature.Seral.mature_old",
                    "curve_id": mature_old,
                }
            ),
            pd.DataFrame(
                {
                    "track_id": area["new_track"].astype(int),
                    "label": "feature.Seral.mature_old." + area["token"].astype(str),
                    "curve_id": mature_old,
                }
            ),
            pd.DataFrame(
                {
                    "track_id": area["new_track"].astype(int),
                    "label": "feature.Seral.mature_old." + area["lubec_token"].astype(str),
                    "curve_id": mature_old,
                }
            ),
        ],
        ignore_index=True,
    )
    overmature_rows = features.loc[
        features["label"] == "feature.Seral.overmature",
        ["new_track", "lubec_token", "curve_id"],
    ].copy()
    overmature_rows = pd.DataFrame(
        {
            "track_id": overmature_rows["new_track"].astype(int),
            "label": "feature.Seral.overmature." + overmature_rows["lubec_token"].astype(str),
            "curve_id": overmature_rows["curve_id"].astype(int),
        }
    )
    features = pd.concat(
        [base, qualified, area_rows, mature_old_rows, overmature_rows], ignore_index=True
    )

    products = clone.merge(
        tables.products.rename(columns={"track_id": "old_track"}), on="old_track", how="left"
    ).dropna(subset=["label"])
    products["track_id"] = products["new_track"].astype(int)
    product_base = products.loc[:, ["track_id", "treatment", "label", "curve_id"]].copy()
    product_qualified = product_base.copy()
    product_qualified["label"] = [
        qualify_label(str(label), str(token))
        for label, token in zip(product_qualified["label"], products["token"], strict=True)
    ]
    product_qualified = product_qualified[product_qualified["label"] != product_base["label"]]
    products = pd.concat([product_base, product_qualified], ignore_index=True)
    products["track_id"] = products["track_id"].astype(int)
    products["curve_id"] = products["curve_id"].astype(int)

    fragments = tables.fragments.merge(partition, on="block_id", how="left")
    fragments = fragments.merge(
        clone.loc[:, ["old_track", "zone", "lubec", "new_track"]],
        left_on=["track_id", "zone", "lubec"],
        right_on=["old_track", "zone", "lubec"],
        how="left",
    )
    if fragments["new_track"].isna().any():
        raise ValueError("some fragments have no cloned track")
    fragments["track_id"] = fragments["new_track"].astype(int)
    fragments = fragments.loc[:, ["fragment_id", "block_id", "area_ha", "age", "track_id"]]
    blocks = (
        fragments.groupby(["block_id", "track_id"], as_index=False)
        .agg(offset=("age", "min"), area_ha=("area_ha", "sum"))
        .loc[:, ["block_id", "track_id", "offset", "area_ha"]]
    )

    feature_labels = sorted(
        set(features["label"].astype(str)) - set(tables.features["label"].astype(str))
    )
    product_labels = sorted(
        set(products["label"].astype(str)) - set(tables.products["label"].astype(str))
    )
    tokens = sorted(
        {
            partition_token(str(zone), str(lubec))
            for zone, lubec in partition[["zone", "lubec"]].itertuples(index=False)
        }
    )
    additions = [
        (f"feature.Area.{zone}", "_ALL_") for zone in sorted(partition["zone"].unique())
    ] + [(f"feature.Area.{token}", "_ALL_") for token in tokens]
    accounts = _expand_accounts(tables.accounts, feature_labels, product_labels, additions)
    protoaccounts = _expand_accounts(
        tables.protoaccounts, feature_labels, product_labels, additions
    )

    manifest = dict(tables.manifest)
    base_metadata = manifest.get("metadata")
    metadata: dict[str, object] = (
        {str(key): value for key, value in base_metadata.items()}
        if isinstance(base_metadata, dict)
        else {}
    )
    metadata.update(
        {
            "variant": "zone_partition",
            "source_dataset": "build/compiled",
            "partition": {
                "zones": sorted(partition["zone"].unique().tolist()),
                "lubec_count": int(partition["lubec"].nunique()),
                "cloned_tracks": len(clone),
                "no_harvest_zones": list(no_harvest_zones),
            },
        }
    )
    manifest["metadata"] = metadata
    result = DatasetTables(
        fragments=fragments,
        blocks=blocks,
        tracks=tracks,
        strata=strata,
        treatments=treatments,
        curves=curves,
        features=features,
        products=products,
        accounts=accounts,
        protoaccounts=protoaccounts,
        groups=tables.groups,
        messages=pd.concat(
            [
                tables.messages,
                pd.DataFrame(
                    {
                        "severity": ["info"],
                        "message": [
                            f"zone partition: {len(clone)} cloned tracks across "
                            f"{partition['lubec'].nunique()} LU/BEC values"
                        ],
                    }
                ),
            ],
            ignore_index=True,
        ),
        manifest=manifest,
    )
    summary: dict[str, object] = {
        "source_fragments": len(tables.fragments),
        "output_fragments": len(fragments),
        "source_area_ha": round(float(tables.fragments["area_ha"].sum()), 3),
        "output_area_ha": round(float(fragments["area_ha"].sum()), 3),
        "source_tracks_used": int(tables.fragments["track_id"].nunique()),
        "cloned_tracks": len(clone),
        "zones": sorted(partition["zone"].unique().tolist()),
        "lubec_count": int(partition["lubec"].nunique()),
        "qualified_features": len(feature_labels),
        "qualified_products": len(product_labels),
        "no_harvest_zones": list(no_harvest_zones),
        "inoperable_tracks": len(clone.loc[clone["zone"].isin(list(no_harvest_zones))]),
    }
    return result, summary


def summarise_partitions(
    fragments: pd.DataFrame, partition: pd.DataFrame, clone: pd.DataFrame
) -> pd.DataFrame:
    """Summarise fragments, area, and cloned tracks by partition.

    Parameters
    ----------
    fragments : pandas.DataFrame
        Output fragments with ``block_id`` and ``area_ha``.
    partition : pandas.DataFrame
        ``block_id``, ``zone``, and ``lubec``.
    clone : pandas.DataFrame
        Cloned track table with ``zone``, ``lubec``, and ``new_track``.

    Returns
    -------
    pandas.DataFrame
        One row per zone/LU-BEC with ``fragments``, ``area_ha``, and ``tracks``.
    """
    joined = fragments.merge(partition, on="block_id", how="left")
    grouped = (
        joined.groupby(["zone", "lubec"], as_index=False)
        .agg(fragments=("fragment_id", "count"), area_ha=("area_ha", "sum"))
        .sort_values(["zone", "lubec"])
    )
    tracks = clone.groupby(["zone", "lubec"], as_index=False).agg(tracks=("new_track", "count"))
    grouped = grouped.merge(tracks, on=["zone", "lubec"], how="left")
    grouped["area_ha"] = grouped["area_ha"].round(3)
    return grouped


def _read_partition(path: Path) -> pd.DataFrame:
    """Read a partition table from CSV.

    Parameters
    ----------
    path : pathlib.Path
        CSV with ``block_id``, ``zone``, and ``lubec``.

    Returns
    -------
    pandas.DataFrame
        The partition table.
    """
    return pd.read_csv(path)


def main(argv: Sequence[str] | None = None) -> int:
    """Build or check the zone-partitioned dataset.

    Parameters
    ----------
    argv : sequence of str or None, optional
        Command-line arguments.

    Returns
    -------
    int
        ``0`` on success, ``1`` when ``--check`` finds a difference.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--fragments", type=Path, default=DEFAULT_FRAGMENTS)
    parser.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--partition-csv", type=Path, default=None)
    parser.add_argument("--no-harvest-zones", type=str, default="")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.partition_csv is not None:
        partition = _read_partition(args.partition_csv)
    else:
        export = gpd.read_file(args.export, ignore_geometry=True)
        fragments = gpd.read_file(args.fragments, ignore_geometry=True)
        overrides = pd.read_csv(args.overrides) if args.overrides.is_file() else None
        partition = build_partition_table(pd.DataFrame(export), pd.DataFrame(fragments), overrides)
    tables = load_dataset(args.dataset)
    no_harvest = tuple(zone.strip() for zone in args.no_harvest_zones.split(",") if zone.strip())
    result, summary = partition_dataset(tables, partition, no_harvest)
    if args.check:
        if not (args.out / "partition_manifest.json").is_file():
            print(f"ERROR: {args.out} has no partition manifest", file=sys.stderr)
            return 1
        existing = json.loads((args.out / "partition_manifest.json").read_text(encoding="utf-8"))
        if existing != summary:
            print(f"ERROR: {args.out} is out of date", file=sys.stderr)
            return 1
        print(json.dumps(summary, indent=2))
        return 0
    write_dataset(result, args.out)
    (args.out / "partition_manifest.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    clone = _clone_frame(tables.fragments, partition, tables.treatments)
    summary_frame = summarise_partitions(result.fragments, partition, clone)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary_frame.to_csv(args.summary, index=False)
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.out}")
    print(f"wrote {args.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
