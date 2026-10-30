"""Tests for the caribou zone/LU-BEC dataset partition."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import partition_caribou_zones as partition


def _tables() -> partition.DatasetTables:
    """Return a minimal compiled dataset with one treatment transition."""
    fragments = pd.DataFrame(
        {
            "fragment_id": [1, 2],
            "block_id": [1, 2],
            "area_ha": [10.0, 20.0],
            "age": [50, 60],
            "track_id": [1, 2],
        }
    )
    blocks = pd.DataFrame(
        {"block_id": [1, 2], "track_id": [1, 2], "offset": [50, 60], "area_ha": [10.0, 20.0]}
    )
    tracks = pd.DataFrame({"track_id": [1, 2], "name": ["T1", "T2"]})
    strata = pd.DataFrame(
        {"track_id": [1, 2], "offset": [0, 0], "next_age": [300, 300], "cycle": [0, 0]}
    )
    treatments = pd.DataFrame(
        {
            "track_id": [1],
            "begin": [0],
            "end": [1000],
            "treatment": ["CC"],
            "new_track": [2],
            "offset": [0],
            "retain": [0],
        }
    )
    curves = pd.DataFrame(
        {
            "curve_id": [1, 1, 2, 2, 2, 2],
            "x": [0.0, 1000.0, 139.0, 140.0, 249.0, 250.0],
            "y": [1.0, 1.0, 0.0, 1.0, 1.0, 0.0],
        }
    )
    features = pd.DataFrame(
        {
            "track_id": [1, 2, 1, 2],
            "label": [
                "feature.Seral.mature",
                "feature.Seral.mature",
                "feature.Seral.overmature",
                "feature.Seral.overmature",
            ],
            "curve_id": [2, 2, 2, 2],
        }
    )
    products = pd.DataFrame(
        {
            "track_id": [1, 2],
            "treatment": ["CC", "CC"],
            "label": [
                "product.HarvestedVolume.managed.Total.CC",
                "product.HarvestedVolume.managed.Total.CC",
            ],
            "curve_id": [1, 1],
        }
    )
    accounts = pd.DataFrame(
        {
            "group": ["_ALL_", "_MANAGED_"],
            "attribute": [
                "feature.Seral.mature",
                "product.HarvestedVolume.managed.Total.CC",
            ],
            "account": [
                "feature.Seral.mature",
                "product.HarvestedVolume.managed.Total.CC",
            ],
            "sum": [1.0, 1.0],
        }
    )
    return partition.DatasetTables(
        fragments=fragments,
        blocks=blocks,
        tracks=tracks,
        strata=strata,
        treatments=treatments,
        curves=curves,
        features=features,
        products=products,
        accounts=accounts,
        protoaccounts=accounts.copy(),
        groups=pd.DataFrame({"block_id": [1, 2], "group": ["forest", "forest"]}),
        messages=pd.DataFrame({"severity": ["info"], "message": ["source"]}),
        manifest={
            "schema_version": "0.1",
            "tables": {},
            "sources": [],
            "options": {},
            "metadata": {},
        },
    )


def _partition() -> pd.DataFrame:
    """Return the two-block partition used by the tests."""
    return pd.DataFrame(
        {"block_id": [1, 2], "zone": ["uwr", "other"], "lubec": ["A|ESSF", "B|ICH"]}
    )


def test_token_and_qualify_label() -> None:
    """Labels are qualified in the expected positions."""
    token = partition.partition_token("uwr", "A|ESSF")
    assert token == "uwr__A_ESSF"
    assert (
        partition.qualify_label("product.HarvestedVolume.managed.Total.CC", token)
        == "product.HarvestedVolume.uwr__A_ESSF.managed.Total.CC"
    )
    assert partition.qualify_label("feature.Seral.mature", token) == (
        "feature.Seral.mature.uwr__A_ESSF"
    )
    assert partition.qualify_label("feature.Other", token) == "feature.Other"


def test_derive_domain_is_mutually_exclusive() -> None:
    """UWR wins over the other flags; other is the default."""
    frame = pd.DataFrame(
        {
            "caribou_uwr": [1, 0, 0, 0],
            "caribou_core": [1, 1, 0, 0],
            "caribou_matrix": [1, 1, 1, 0],
            "caribou_zone": [1, 1, 1, 1],
        }
    )
    assert partition.derive_domain(frame).tolist() == ["uwr", "core", "matrix", "hlp"]


def test_partition_dataset_clones_tracks_and_labels() -> None:
    """The used tracks and treatment targets are cloned per partition."""
    result, summary = partition.partition_dataset(_tables(), _partition())
    assert summary["cloned_tracks"] == 3
    assert summary["source_area_ha"] == summary["output_area_ha"] == 30.0
    assert len(result.fragments) == 2
    assert result.fragments["track_id"].nunique() == 2
    assert len(result.tracks) == 3
    labels = set(result.features["label"].astype(str))
    assert "feature.Seral.mature" in labels
    assert "feature.Seral.mature.uwr__A_ESSF" in labels
    assert "feature.Area.uwr" in labels
    assert "feature.Area.other__B_ICH" in labels
    assert "feature.Seral.mature_old.uwr__A_ESSF" in labels
    assert "feature.Seral.mature_old.A_ESSF" in labels
    assert "feature.Seral.overmature.A_ESSF" in labels
    assert "feature.Area.A_ESSF" in labels
    products = set(result.products["label"].astype(str))
    assert "product.HarvestedVolume.uwr__A_ESSF.managed.Total.CC" in products
    accounts = set(result.accounts["account"].astype(str))
    assert "feature.Seral.mature.uwr__A_ESSF" in accounts
    assert "product.HarvestedVolume.uwr__A_ESSF.managed.Total.CC" in accounts
    for table in (result.treatments, result.products):
        assert table["track_id"].dtype == "int64"
    assert result.treatments["new_track"].dtype == "int64"


def test_partition_no_harvest_zone_drops_treatments() -> None:
    """A no-harvest zone keeps its tracks but loses its treatment rows."""
    result, summary = partition.partition_dataset(
        _tables(), _partition(), no_harvest_zones=("uwr",)
    )
    uwr_tracks = result.tracks.loc[result.tracks["name"].str.contains("ZONE\\(uwr\\)"), "track_id"]
    assert len(uwr_tracks) > 0
    assert result.treatments.loc[result.treatments["track_id"].isin(uwr_tracks)].empty
    assert int(str(summary["inoperable_tracks"])) > 0


def test_mature_old_curve_starts_at_140() -> None:
    """The combined mature+old curve is one from age 140."""
    curves = pd.DataFrame({"curve_id": [1, 1], "x": [0.0, 1.0], "y": [0.0, 1.0]})
    extended, curve_id = partition._mature_old_curve(curves)
    points = extended[extended["curve_id"] == curve_id].set_index("x")["y"]
    assert points.loc[139.0] == 0.0
    assert points.loc[140.0] == 1.0


def test_partition_treatment_target_stays_in_partition() -> None:
    """A cloned source track transitions to the cloned target in the same zone."""
    result, _ = partition.partition_dataset(_tables(), _partition())
    track_name = result.tracks.set_index("track_id")["name"]
    source = int(result.tracks.loc[result.tracks["name"].str.startswith("T1+"), "track_id"].iloc[0])
    target = int(
        result.treatments.loc[result.treatments["track_id"] == source, "new_track"].iloc[0]
    )
    assert "T2+" in track_name.loc[target]
    assert "+ZONE(uwr)+LUBEC(uwr__A_ESSF)" in track_name.loc[source]


def test_unity_curve_is_added_when_missing() -> None:
    """A constant curve is created when the source has no unity curve."""
    curves = pd.DataFrame({"curve_id": [1, 1], "x": [0.0, 1.0], "y": [0.0, 1.0]})
    extended, curve_id = partition._unity_curve(curves)
    assert curve_id == 2
    assert set(extended.loc[extended["curve_id"] == curve_id, "y"]) == {1.0}


def test_build_partition_table_uses_overrides() -> None:
    """The override resolves the duplicate key to the chosen fragment."""
    export = pd.DataFrame(
        {"BLOCK": [1, 2], "AU": [1, 1], "AREA_HA": [10.0, 10.0], "F_AGE": [50.0, 50.0]}
    )
    fragments = pd.DataFrame(
        {
            "FEATURE_ID": [101, 102],
            "au": [1, 1],
            "area_ha": [10.0, 10.0],
            "PROJ_AGE_1": [50.0, 50.0],
            "caribou_uwr": [1, 0],
            "caribou_core": [0, 0],
            "caribou_matrix": [0, 0],
            "caribou_zone": [0, 0],
            "lu_bec": ["A|ESSF", "B|ICH"],
        }
    )
    overrides = pd.DataFrame({"block_id": [1, 2], "fragment_id": [102, 101]})
    table = partition.build_partition_table(export, fragments, overrides)
    assert table.set_index("block_id")["zone"].to_dict() == {1: "other", 2: "uwr"}


def test_build_partition_table_rejects_unresolved_duplicate() -> None:
    """A duplicate key without an override is an error, not a silent choice."""
    export = pd.DataFrame({"BLOCK": [1], "AU": [1], "AREA_HA": [10.0], "F_AGE": [50.0]})
    fragments = pd.DataFrame(
        {
            "FEATURE_ID": [101, 102],
            "au": [1, 1],
            "area_ha": [10.0, 10.0],
            "PROJ_AGE_1": [50.0, 50.0],
            "caribou_uwr": [1, 0],
            "caribou_core": [0, 0],
            "caribou_matrix": [0, 0],
            "caribou_zone": [0, 0],
            "lu_bec": ["A|ESSF", "B|ICH"],
        }
    )
    with pytest.raises(ValueError, match="do not resolve"):
        partition.build_partition_table(export, fragments, None)


def _write_source(root: Path) -> Path:
    """Write the synthetic source dataset and return its directory."""
    path = root / "compiled"
    partition.write_dataset(_tables(), path)
    return path


def test_main_writes_and_checks(tmp_path: Path) -> None:
    """The CLI writes the partitioned dataset and the summary."""
    source = _write_source(tmp_path)
    partition_csv = tmp_path / "partition.csv"
    _partition().to_csv(partition_csv, index=False)
    out = tmp_path / "compiled_zone"
    summary = tmp_path / "summary.csv"
    args = [
        "--dataset",
        str(source),
        "--partition-csv",
        str(partition_csv),
        "--out",
        str(out),
        "--summary",
        str(summary),
    ]
    assert partition.main(args) == 0
    assert (out / "manifest.json").is_file()
    assert (out / "partition_manifest.json").is_file()
    assert summary.is_file()
    assert partition.main([*args, "--check"]) == 0
    manifest = json.loads((out / "partition_manifest.json").read_text(encoding="utf-8"))
    manifest["cloned_tracks"] = 999
    (out / "partition_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert partition.main([*args, "--check"]) == 1
