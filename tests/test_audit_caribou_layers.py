"""Tests for the caribou layer accounting audit."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

import audit_caribou_layers as audit


def _fragments() -> pd.DataFrame:
    """Return a small P3.1 fragment frame with one ambiguous key."""
    return pd.DataFrame(
        {
            "FEATURE_ID": [101, 102, 103, 104],
            "au": [1, 1, 1, 2],
            "area_ha": [100.0, 50.0, 100.0, 25.0],
            "PROJ_AGE_1": [80.0, 90.0, 80.0, 100.0],
            "thlb_area_ha": [100.0, 50.0, 0.0, 0.0],
            "caribou_uwr": [1, 1, 0, 0],
            "caribou_uwr_frac": [1.0, 0.2, 0.0, 0.0],
            "caribou_core": [0, 0, 0, 0],
            "caribou_matrix": [0, 0, 0, 0],
            "caribou_zone": [0, 0, 0, 0],
            "caribou_immature": [0, 0, 0, 0],
            "ogma": [0, 0, 0, 0],
            "lu_bec": ["LU1|ESSFvc", "LU1|ESSFvc", "LU1|ESSFvc", "LU2|ICHwk"],
        }
    )


def _export() -> pd.DataFrame:
    """Return a Patchworks-like export matching ``_fragments``."""
    return pd.DataFrame(
        {
            "BLOCK": [10, 20, 30],
            "AU": [1, 1, 2],
            "AREA_HA": [100.0, 50.0, 25.0],
            "F_AGE": [80.0, 90.0, 100.0],
        }
    )


def _features() -> pd.DataFrame:
    """Return og1, og2, and non-seral feature labels."""
    return pd.DataFrame(
        {
            "label": [
                "feature.Area.og1.ICH_CW_M",
                "feature.Area.og1.total",
                "feature.Area.og2.ICH_CW_M",
                "feature.Area.managed",
            ],
            "curve_id": [1, 1, 2, 3],
        }
    )


def _curves() -> pd.DataFrame:
    """Return the curves for ``_features``."""
    return pd.DataFrame(
        {
            "curve_id": [1, 1, 2, 2, 3],
            "x": [90.0, 190.0, 249.0, 250.0, 0.0],
            "y": [0.0, 1.0, 0.0, 1.0, 1.0],
        }
    )


def test_read_frame_csv_parquet_and_unsupported(tmp_path: Path) -> None:
    """CSV and Parquet read, and an unknown suffix raises."""
    csv = tmp_path / "frame.csv"
    pd.DataFrame({"a": [1, 2]}).to_csv(csv, index=False)
    assert audit.read_frame(csv)["a"].tolist() == [1, 2]
    parquet = tmp_path / "frame.parquet"
    pd.DataFrame({"a": [3]}).to_parquet(parquet)
    assert audit.read_frame(parquet)["a"].tolist() == [3]
    with pytest.raises(ValueError, match="unsupported table suffix"):
        audit.read_frame(tmp_path / "frame.xlsx")


def test_read_frame_gpkg(tmp_path: Path) -> None:
    """A GeoPackage reads as a plain frame without geometry."""
    path = tmp_path / "frame.gpkg"
    frame = gpd.GeoDataFrame({"value": [7]}, geometry=[box(0, 0, 1, 1)], crs=3005)
    frame.to_file(path, driver="GPKG")
    result = audit.read_frame(path)
    assert result["value"].tolist() == [7]
    assert "geometry" not in result.columns


def test_load_mapping_yaml_json_and_error(tmp_path: Path) -> None:
    """YAML and JSON mappings load; a list payload raises."""
    yaml_path = tmp_path / "payload.yaml"
    yaml_path.write_text("a: 1\n", encoding="utf-8")
    assert audit.load_mapping(yaml_path)["a"] == 1
    json_path = tmp_path / "payload.json"
    json_path.write_text(json.dumps({"b": 2}), encoding="utf-8")
    assert audit.load_mapping(json_path)["b"] == 2
    bad = tmp_path / "bad.yaml"
    bad.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ValueError, match="does not contain a mapping"):
        audit.load_mapping(bad)


def test_attribute_status_marks_presence_and_area() -> None:
    """A present flag reports its fragments and area; a missing one reports zero."""
    status = audit.attribute_status(_fragments(), ["caribou_uwr", "caribou_core", "lu_bec"])
    rows = {row["attribute"]: row for row in status.to_dict("records")}
    assert rows["caribou_uwr"]["present"] is True
    assert rows["caribou_uwr"]["flagged_fragments"] == 2
    assert rows["caribou_uwr"]["flagged_area_ha"] == 150.0
    assert rows["caribou_core"]["present"] is True
    assert rows["caribou_core"]["flagged_fragments"] == 0
    assert rows["lu_bec"]["flagged_fragments"] == 4


def test_missing_account_keys_finds_none_and_some() -> None:
    """Substring matching distinguishes present from missing account keys."""
    accounts = pd.DataFrame({"account": ["feature.Area.og1.total"]})
    features = pd.DataFrame({"label": ["feature.Area.og1.total"]})
    expected = (("og1", "seral"), ("caribou_uwr", "UWR"))
    assert audit.missing_account_keys(accounts, features, expected) == ["caribou_uwr"]
    present = pd.DataFrame({"account": ["caribou_uwr_ha"]})
    assert audit.missing_account_keys(present, features, (("caribou_uwr", "UWR"),)) == []
    seral = pd.DataFrame({"account": ["feature.Seral.mature"]})
    assert audit.missing_account_keys(seral, features, (("seral", "seral"),)) == []


def test_flag_inventory_counts_and_zero_flags() -> None:
    """The inventory reports counts and all-zero flags."""
    inventory = audit.flag_inventory(_fragments(), ["caribou_uwr", "caribou_core"])
    rows = {row["flag"]: row for row in inventory.to_dict("records")}
    assert rows["caribou_uwr"]["fragments"] == 2
    assert rows["caribou_uwr"]["area_ha"] == 150.0
    assert rows["caribou_core"]["fragments"] == 0


def test_uwr_area_accounting_overstatement() -> None:
    """The binary flag overstates the area-weighted intersection."""
    result = audit.uwr_area_accounting(_fragments())
    assert result["flagged_area_ha"] == 150.0
    assert result["intersection_area_ha"] == 110.0
    assert result["overstatement_ha"] == 40.0
    assert result["flagged_thlb_area_ha"] == 150.0


def test_uwr_area_accounting_requires_columns() -> None:
    """A fragment frame without the UWR columns raises."""
    with pytest.raises(ValueError, match="fragments missing columns"):
        audit.uwr_area_accounting(pd.DataFrame({"area_ha": [1.0]}))


def test_block_flag_reconciliation_detects_ambiguity() -> None:
    """The duplicate key makes block 10 ambiguous and conflicting."""
    result = audit.block_flag_reconciliation(_export(), _fragments())
    assert result["export_blocks"] == 3.0
    assert result["duplicate_fragment_keys"] == 1.0
    assert result["ambiguous_blocks"] == 1.0
    assert result["conflicting_blocks"] == 1.0
    assert result["conflicting_area_ha"] == 100.0
    assert result["flagged_blocks_max"] == 2.0
    assert result["flagged_blocks_min"] == 1.0
    resolved = audit.block_flag_reconciliation(
        _export(),
        _fragments(),
        pd.DataFrame({"block_id": [10], "fragment_id": [101], "iou": [1.0]}),
    )
    assert resolved["resolved_overrides"] == 1.0
    assert resolved["unresolved_blocks"] == 0.0
    assert resolved["flagged_blocks_exact"] == 2.0


def test_schedule_audit_counts_flagged_rows() -> None:
    """Only the flagged block's row counts as a violation."""
    flags = pd.DataFrame({"block_id": [10, 20, 30], "caribou_uwr": [1, 0, 0]})
    schedule = pd.DataFrame({"block_id": [10, 20, 30], "treatment": ["CC"] * 3})
    result = audit.schedule_audit(schedule, flags)
    assert result == {"rows": 3, "blocks": 3, "flagged_rows": 1}


def test_variant_counts_matches_manifest() -> None:
    """The removed block count equals the manifest and extra blocks are zero."""
    compiled = pd.DataFrame({"block_id": [1, 2, 3]})
    variant = pd.DataFrame({"block_id": [3]})
    result = audit.variant_counts(compiled, variant, 2)
    assert result["removed_blocks"] == 2
    assert result["manifest_removed_blocks"] == 2
    assert result["extra_blocks"] == 0


def test_variant_removed_blocks_nested_and_missing() -> None:
    """Only an integer under ``metadata`` is accepted."""
    assert audit.variant_removed_blocks({"metadata": {"removed_blocks": 5}}) == 5
    assert audit.variant_removed_blocks({}) == -1
    assert audit.variant_removed_blocks({"metadata": {"removed_blocks": "5"}}) == -1


def test_og_profile_excludes_totals() -> None:
    """Only the specific og1/og2 labels are profiled."""
    profile = audit.og_profile(_features(), _curves())
    assert profile["label"].tolist() == [
        "feature.Area.og1.ICH_CW_M",
        "feature.Area.og2.ICH_CW_M",
    ]
    assert profile["low"].tolist() == [90.0, 249.0]
    assert profile["high"].tolist() == [190.0, 250.0]


def test_tsr_caribou_areas_and_missing_row() -> None:
    """The TSR caribou rows are read; an absent row raises."""
    table14 = pd.DataFrame(
        {
            "land_base_element": ["Wildlife - Caribou UWR (no harvest)"],
            "gross_ha": [116820.0],
            "net_removed_ha": [62892.0],
            "pct_of_aflb": [29.1],
        }
    )
    table3 = pd.DataFrame(
        {
            "land_base_element": ["Mountain Caribou Reserves (GAR U-3-005)"],
            "total_area_ha": [66098.0],
            "effective_netdown_ha": [18909.0],
        }
    )
    result = audit.tsr_caribou_areas(table14, table3)
    assert result["tsr5_gross_ha"] == 116820.0
    assert result["tsr4_net_ha"] == 18909.0
    with pytest.raises(ValueError, match="caribou row missing"):
        audit.tsr_caribou_areas(table14.iloc[0:0], table3)


def test_enforcement_rows_nested() -> None:
    """Nested layer mappings are flattened."""
    payload = {
        "uwr": {"enforcement": "schedule_filter"},
        "matrix": {"enforcement": "mapped_not_enforced", "status": "to_fetch"},
        "core": {"nested": {"enforcement": "pending_layer"}},
    }
    rows = audit.enforcement_rows(payload)
    assert {row["layer"] for row in rows} == {"uwr", "matrix", "nested"}
    assert {row["enforcement"] for row in rows} == {
        "schedule_filter",
        "mapped_not_enforced",
        "pending_layer",
    }


def test_supported_scenarios_and_error() -> None:
    """The registry returns id/status pairs and rejects a missing mapping."""
    registry = {"scenarios": {"s3": {"status": "supported"}, "s4": {"status": "unavailable"}}}
    assert audit.supported_scenarios(registry) == {"s3": "supported", "s4": "unavailable"}
    with pytest.raises(ValueError, match="no scenarios mapping"):
        audit.supported_scenarios({})


def _inputs() -> audit.AuditInputs:
    """Return a fully populated input set with no integrity failures."""
    fragments = _fragments()
    compiled = fragments[["area_ha", "caribou_uwr", "caribou_core", "caribou_matrix"]].copy()
    compiled["caribou_zone"] = 0
    compiled["caribou_immature"] = 0
    compiled["ogma"] = 0
    compiled["lu_bec"] = ""
    accounts = pd.DataFrame(
        {
            "account": [
                "caribou_uwr_ha",
                "caribou_core_ha",
                "caribou_matrix_ha",
                "matrix_area_lt_40",
                "old_seral_ha",
            ]
        }
    )
    return audit.AuditInputs(
        fragments=fragments,
        compiled_fragments=compiled,
        accounts=accounts,
        features=_features(),
        curves=_curves(),
        blocks=pd.DataFrame({"block_id": [10, 20, 30]}),
        variant_blocks=pd.DataFrame({"block_id": [30]}),
        export=_export(),
        schedules={
            "s3_base": pd.DataFrame({"block_id": [10, 30]}),
            "s3_base_caribou_uwr_excluded": pd.DataFrame({"block_id": [30]}),
        },
        constraints={"uwr": {"enforcement": "schedule_filter"}},
        registry={"scenarios": {"s3": {"status": "supported"}}},
        tsr5=pd.DataFrame(
            {
                "land_base_element": ["Wildlife - Caribou UWR (no harvest)"],
                "gross_ha": [116820.0],
                "net_removed_ha": [62892.0],
                "pct_of_aflb": [29.1],
            }
        ),
        tsr4=pd.DataFrame(
            {
                "land_base_element": ["Mountain Caribou Reserves (GAR U-3-005)"],
                "total_area_ha": [66098.0],
                "effective_netdown_ha": [18909.0],
            }
        ),
        land_base=pd.DataFrame({"metric": ["caribou_uwr_gross"], "ws4_ha": [116759.0]}),
        comparison=pd.DataFrame({"scenario": ["s3_tsr5_base"], "treated_delta_ha": [-150.0]}),
        variant_manifest={"metadata": {"removed_blocks": 2}},
        overrides=pd.DataFrame({"block_id": [10], "fragment_id": [101], "iou": [1.0]}),
        zone_invariants=pd.DataFrame({"invariant": ["area"], "delta": [0.0], "pass": [True]}),
    )


def test_build_checks_pass_gap_and_fail() -> None:
    """The audit separates pass, gap, and fail."""
    checks = {check.check: check for check in audit.build_checks(_inputs())}
    assert checks["schedule_uwr_filter"].status == "PASS"
    assert checks["uwr_variant_manifest"].status == "PASS"
    assert checks["seral_thresholds"].status == "GAP"
    assert checks["seral_account_basis"].status == "GAP"
    assert checks["zone_partition"].status == "PASS"
    polluted = replace(
        _inputs(),
        schedules={
            "s3_base": pd.DataFrame({"block_id": [10, 30]}),
            "s3_base_caribou_uwr_excluded": pd.DataFrame({"block_id": [10, 30]}),
        },
    )
    failed = {check.check: check for check in audit.build_checks(polluted)}
    assert failed["schedule_uwr_filter"].status == "FAIL"


def test_seral_thresholds_pass_with_labels() -> None:
    """The threshold check passes when the seral feature labels are present."""
    extra = pd.DataFrame(
        {
            "label": ["feature.Seral.mature", "feature.Seral.overmature"],
            "curve_id": [4, 5],
        }
    )
    curves = pd.concat(
        [
            _curves(),
            pd.DataFrame(
                {
                    "curve_id": [4, 4, 5, 5],
                    "x": [139.0, 140.0, 249.0, 250.0],
                    "y": [0.0, 1.0, 0.0, 1.0],
                }
            ),
        ],
        ignore_index=True,
    )
    inputs = replace(
        _inputs(),
        features=pd.concat([_features(), extra], ignore_index=True),
        curves=curves,
    )
    checks = {check.check: check for check in audit.build_checks(inputs)}
    assert checks["seral_thresholds"].status == "PASS"
    assert checks["seral_account_basis"].status == "GAP"
    assert checks["zone_partition"].status == "PASS"


def _write_inputs(root: Path) -> dict[str, object]:
    """Write a minimal on-disk audit input set and return the CLI paths."""
    fragments = _fragments()
    fragments.to_csv(root / "fragments.csv", index=False)
    compiled = root / "compiled"
    compiled.mkdir()
    fragments[
        [
            "area_ha",
            "caribou_uwr",
            "caribou_core",
            "caribou_matrix",
            "caribou_zone",
            "caribou_immature",
            "ogma",
            "lu_bec",
        ]
    ].to_parquet(compiled / "fragments.parquet")
    pd.DataFrame(
        {
            "account": [
                "caribou_uwr_ha",
                "caribou_core_ha",
                "caribou_matrix_ha",
                "matrix_area_lt_40",
                "old_seral_ha",
            ]
        }
    ).to_parquet(compiled / "accounts.parquet")
    _features().to_parquet(compiled / "features.parquet")
    _curves().to_parquet(compiled / "curves.parquet")
    pd.DataFrame({"block_id": [10, 20, 30]}).to_parquet(compiled / "blocks.parquet")
    variant = root / "variant"
    variant.mkdir()
    pd.DataFrame({"block_id": [30]}).to_parquet(variant / "blocks.parquet")
    (variant / "manifest.json").write_text(
        json.dumps({"metadata": {"removed_blocks": 2}}), encoding="utf-8"
    )
    _export().to_csv(root / "export.csv", index=False)
    scenarios = root / "scenarios"
    scenarios.mkdir()
    pd.DataFrame({"block_id": [10, 30]}).to_csv(scenarios / "s3_base.schedule.csv", index=False)
    pd.DataFrame({"block_id": [30]}).to_csv(
        scenarios / "s3_base_caribou_uwr_excluded.schedule.csv", index=False
    )
    (root / "constraints.yaml").write_text(
        "uwr:\n  enforcement: schedule_filter\n", encoding="utf-8"
    )
    (root / "registry.yaml").write_text(
        "scenarios:\n  s3:\n    status: supported\n", encoding="utf-8"
    )
    pd.DataFrame(
        {
            "land_base_element": ["Wildlife - Caribou UWR (no harvest)"],
            "gross_ha": [116820.0],
            "net_removed_ha": [62892.0],
            "pct_of_aflb": [29.1],
        }
    ).to_csv(root / "table14.csv", index=False)
    pd.DataFrame(
        {
            "land_base_element": ["Mountain Caribou Reserves (GAR U-3-005)"],
            "total_area_ha": [66098.0],
            "effective_netdown_ha": [18909.0],
        }
    ).to_csv(root / "table3.csv", index=False)
    pd.DataFrame({"metric": ["caribou_uwr_gross"], "ws4_ha": [116759.0]}).to_csv(
        root / "land_base.csv", index=False
    )
    pd.DataFrame({"block_id": [10], "fragment_id": [101], "iou": [1.0]}).to_csv(
        root / "overrides.csv", index=False
    )
    pd.DataFrame(
        {"invariant": ["area"], "base": [1.0], "zone": [1.0], "delta": [0.0], "pass": [True]}
    ).to_csv(root / "zone_invariants.csv", index=False)
    pd.DataFrame({"scenario": ["s3_tsr5_base"], "treated_delta_ha": [-150.0]}).to_csv(
        root / "comparison.csv", index=False
    )
    return {
        "--fragments": str(root / "fragments.csv"),
        "--compiled": str(compiled),
        "--variant": str(variant),
        "--export": str(root / "export.csv"),
        "--scenarios": str(scenarios),
        "--constraints": str(root / "constraints.yaml"),
        "--registry": str(root / "registry.yaml"),
        "--table14": str(root / "table14.csv"),
        "--table3": str(root / "table3.csv"),
        "--land-base": str(root / "land_base.csv"),
        "--comparison": str(root / "comparison.csv"),
        "--overrides": str(root / "overrides.csv"),
        "--zone-invariants": str(root / "zone_invariants.csv"),
        "--out-dir": str(root / "audit"),
    }


def test_main_writes_outputs(tmp_path: Path) -> None:
    """The CLI writes the summary and detail tables and returns zero."""
    args: list[str] = []
    for key, value in _write_inputs(tmp_path).items():
        args.extend([key, str(value)])
    assert audit.main(args) == 0
    out = tmp_path / "audit"
    assert (out / "summary.csv").is_file()
    assert (out / "summary.json").is_file()
    assert (out / "flag_inventory.csv").is_file()
    assert (out / "og_profile.csv").is_file()
    assert len(pd.read_csv(out / "summary.csv")) == 15


def test_main_strict_returns_one_on_gap(tmp_path: Path) -> None:
    """``--strict`` turns a gap into a non-zero exit."""
    args: list[str] = []
    for key, value in _write_inputs(tmp_path).items():
        args.extend([key, str(value)])
    args.append("--strict")
    assert audit.main(args) == 1
