"""Tests for the engine -> PILAR-2b release bundle (engine.export.bundle).

Every DataFrame, CNPJ, source id, commit sha and number below is SYNTHETIC test data (drawn from
a seeded generator or typed by hand); none of it is a model result or registry value.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pytest
from jsonschema import Draft202012Validator

from engine.export import bundle as bundle_mod
from engine.export.__main__ import main as export_main
from engine.export.bundle import (
    CONTRACT_TABLES,
    MANIFEST_SCHEMA_PATH,
    BundleError,
    BundleWarning,
    build_bundle,
    column_unit_ok,
    load_manifest_schema,
    manifest_schema_errors,
    release_dir,
    verify_bundle,
)

SYN_COMMIT = "0123456789abcdef0123456789abcdef01234567"  # synthetic 40-hex sha
SYN_CREATED_AT = "2026-10-04T12:00:00+00:00"
SYN_PARAMS_HASH = "abcdef012345"

SYN_SOURCES_YAML = """\
schema_version: 0.1
updated: 2026-10-04
sources:
  - id: syn_cane_stats
    name: Synthetic cane statistics
    publisher: Synthetic
    url: https://example.org/cane
    module: supply
    status: have
    confidence: S
    access: open
    license: synthetic
    accessed: 2026-01-15
    sha256: 1111111111111111111111111111111111111111111111111111111111111111
  - id: syn_partner_feed
    name: Synthetic partner dataset
    publisher: Synthetic partner
    url: confidential
    module: supply
    status: have
    confidence: S
    access: confidential
    license: NDA
"""


@pytest.fixture
def sources_yaml(tmp_path: Path) -> Path:
    path = tmp_path / "sources.yaml"
    path.write_text(SYN_SOURCES_YAML, encoding="utf-8")
    return path


def synthetic_tables(seed: int = 20261004) -> dict[str, pd.DataFrame]:
    """Small SYNTHETIC tables shaped like the contract (docs/18 §2)."""
    rng = np.random.default_rng(seed)
    cell_a = h3.latlng_to_cell(-22.80, -47.00, 8)  # synthetic points in SP
    cell_b = h3.latlng_to_cell(-21.50, -48.50, 8)
    p50 = rng.uniform(100.0, 200.0, size=2)
    return {
        "facilities": pd.DataFrame(
            {
                "cnpj": ["00000000000001", "00000000000002"],
                "name": ["Synthetic mill A", "Synthetic mill B"],
                "type": ["mill", "mill"],
                "capacity_nm3_d": rng.uniform(1_000.0, 5_000.0, size=2).round(1),
                "geom": ["POINT (-47.0 -22.8)", "POINT (-48.5 -21.5)"],
            }
        ),
        "hex_supply": pd.DataFrame(
            {
                "h3_index": [cell_a, cell_b],
                "month": [1, 2],
                "residue": ["vinasse", "vinasse"],
                "p05": (p50 * 0.5).round(2),
                "p50": p50.round(2),
                "p95": (p50 * 1.5).round(2),
                "unit": ["m3", "m3"],
            }
        ),
        "lcob_results": pd.DataFrame(
            {
                "site_id": ["syn_site_1", "syn_site_1"],
                "scenario": ["base", "high_cbio"],
                "strategy": ["vinasse_only", "vinasse_only"],
                "lcob_brl_nm3_p50": rng.uniform(1.0, 4.0, size=2).round(3),
                "npv_brl_2025": rng.uniform(-1e6, 1e6, size=2).round(0),
                "irr_frac": rng.uniform(0.0, 0.2, size=2).round(4),
            }
        ),
        "supply_curve": pd.DataFrame(
            {
                "scenario": ["base", "base"],
                "cum_nm3_d": [1_000.0, 3_000.0],
                "lcob_brl_nm3": [2.0, 3.0],
            }
        ),
    }


def _build(out_dir: Path, sources_yaml: Path, tables=None, **overrides):
    kwargs = {
        "version": "0.1.0",
        "run_id": "syn-run-001",
        "params_hash": SYN_PARAMS_HASH,
        "sources_used": ["syn_cane_stats"],
        "scenarios": ["base", "high_cbio"],
        "created_at": SYN_CREATED_AT,
        "git_commit": SYN_COMMIT,
        "crs": "EPSG:4674",
        "sources_path": sources_yaml,
    }
    kwargs.update(overrides)
    return build_bundle(synthetic_tables() if tables is None else tables, out_dir, **kwargs)


# ---------------------------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------------------------


def test_build_bundle_writes_parquet_csv_and_manifest(tmp_path: Path, sources_yaml: Path) -> None:
    out = tmp_path / "exports" / "v0.1.0"
    manifest = _build(out, sources_yaml)

    names = sorted(p.name for p in out.iterdir())
    tables = ["facilities", "hex_supply", "lcob_results", "supply_curve"]
    expected = [f"{t}.{ext}" for t in tables for ext in ("csv", "parquet")] + ["manifest.json"]
    assert names == sorted(expected)
    on_disk = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert on_disk == manifest
    assert manifest_schema_errors(manifest) == []
    assert manifest["version"] == "0.1.0"
    assert manifest["git_commit"] == SYN_COMMIT
    assert manifest["crs"] == "EPSG:4674"
    assert manifest["source_versions"] == {
        "syn_cane_stats": {
            "accessed": "2026-01-15",
            "sha256": "1111111111111111111111111111111111111111111111111111111111111111",
        }
    }
    assert len(manifest["files"]) == 2 * len(tables)  # one parquet + one csv per table

    for entry in manifest["files"]:
        path = out / entry["path"]
        assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert entry["bytes"] == path.stat().st_size
        assert entry["rows"] == 2  # every synthetic table has 2 rows
    fac = next(e for e in manifest["files"] if e["path"] == "facilities.parquet")
    assert [c["name"] for c in fac["columns"]] == [
        "cnpj",
        "name",
        "type",
        "capacity_nm3_d",
        "geom",
    ]
    assert fac["geometry_columns"] == ["geom"]
    assert pd.read_parquet(out / "facilities.parquet")["cnpj"].tolist() == [
        "00000000000001",
        "00000000000002",
    ]
    assert verify_bundle(out) == []
    # no temp folders left next to the bundle
    assert [p.name for p in out.parent.iterdir()] == ["v0.1.0"]


def test_bundle_is_byte_reproducible(tmp_path: Path, sources_yaml: Path) -> None:
    first = _build(tmp_path / "a" / "v0.1.0", sources_yaml)
    second = _build(tmp_path / "b" / "v0.1.0", sources_yaml)
    assert first == second
    assert (tmp_path / "a" / "v0.1.0" / "manifest.json").read_bytes() == (
        tmp_path / "b" / "v0.1.0" / "manifest.json"
    ).read_bytes()


def test_release_dir_and_contract_tables() -> None:
    assert release_dir("0.2.0", "/tmp/x") == Path("/tmp/x/v0.2.0")
    assert CONTRACT_TABLES == (
        "facilities",
        "hex_supply",
        "mill_month",
        "lcob_results",
        "sites",
        "supply_curve",
    )


def test_manifest_schema_is_valid_draft_2020_12() -> None:
    schema = load_manifest_schema(MANIFEST_SCHEMA_PATH)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)


def test_schema_requires_crs_when_geometry_present(tmp_path: Path, sources_yaml: Path) -> None:
    manifest = _build(tmp_path / "v0.1.0", sources_yaml)
    broken = dict(manifest, crs=None)
    assert any(e.startswith("crs:") for e in manifest_schema_errors(broken))


# ---------------------------------------------------------------------------------------------
# Metadata gates
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("version", ["0.1", "v0.1.0", "01.0.0", "1.0.0.0", "", "1.0.0-"])
def test_version_must_be_semver(tmp_path: Path, sources_yaml: Path, version: str) -> None:
    with pytest.raises(BundleError, match="Semantic Versioning"):
        _build(tmp_path / "out", sources_yaml, version=version)
    assert not (tmp_path / "out").exists()


def test_semver_prerelease_and_build_metadata_accepted(tmp_path: Path, sources_yaml) -> None:
    manifest = _build(tmp_path / "out", sources_yaml, version="1.2.3-rc.1+build.5")
    assert manifest["version"] == "1.2.3-rc.1+build.5"


@pytest.mark.parametrize(
    ("override", "fragment"),
    [
        ({"run_id": "bad run id"}, "run_id"),
        ({"params_hash": "NOT-HEX"}, "params_hash"),
        ({"git_commit": "xyz"}, "git_commit"),
        ({"created_at": "2026-10-04T12:00:00"}, "UTC offset"),  # naive
        ({"created_at": "2026-10-04"}, "UTC offset"),  # date only
        ({"created_at": "yesterday"}, "ISO 8601"),
        ({"created_at": "20261004T120000Z"}, "UTC offset"),  # basic format: not in schema
        ({"scenarios": ["base", "base", "high_cbio"]}, "duplicates"),
        ({"sources_used": "syn_cane_stats"}, "sources_used must be a list"),
        ({"sources_used": ["syn_unknown"]}, "not registered"),
        ({"crs": "EPSG:4326"}, "contract CRS"),
    ],
)
def test_metadata_gates(tmp_path: Path, sources_yaml: Path, override: dict, fragment: str) -> None:
    with pytest.raises(BundleError, match=fragment):
        _build(tmp_path / "out", sources_yaml, **override)
    assert not (tmp_path / "out").exists()


def test_created_at_defaults_to_now_utc(tmp_path: Path, sources_yaml: Path) -> None:
    before = datetime.now(UTC).replace(microsecond=0)
    manifest = _build(tmp_path / "out", sources_yaml, created_at=None)
    stamp = datetime.fromisoformat(manifest["created_at"])
    assert stamp.tzinfo is not None
    assert before <= stamp <= datetime.now(UTC)


def test_git_commit_lookup_when_not_given(tmp_path: Path, sources_yaml: Path, monkeypatch) -> None:
    monkeypatch.setattr(bundle_mod, "_git_head_commit", lambda: SYN_COMMIT)
    assert _build(tmp_path / "a", sources_yaml, git_commit=None)["git_commit"] == SYN_COMMIT
    monkeypatch.setattr(bundle_mod, "_git_head_commit", lambda: None)
    assert _build(tmp_path / "b", sources_yaml, git_commit=None)["git_commit"] is None


def test_real_git_lookup_is_hex_or_none() -> None:
    commit = bundle_mod._git_head_commit()
    assert commit is None or (len(commit) == 40 and int(commit, 16) >= 0)


def test_confidential_source_is_flagged(tmp_path: Path, sources_yaml: Path) -> None:
    with pytest.warns(BundleWarning, match="confidential"):
        manifest = _build(
            tmp_path / "out", sources_yaml, sources_used=["syn_cane_stats", "syn_partner_feed"]
        )
    assert any("syn_partner_feed" in w for w in manifest["warnings"])
    assert manifest["source_versions"]["syn_partner_feed"] == {"accessed": None, "sha256": None}


# ---------------------------------------------------------------------------------------------
# Table gates
# ---------------------------------------------------------------------------------------------


def test_unknown_table_refused_unless_allow_extra(tmp_path: Path, sources_yaml: Path) -> None:
    tables = synthetic_tables()
    tables["debug_table"] = pd.DataFrame({"site_id": ["s"], "value_t": [1.0]})
    with pytest.raises(BundleError, match="not in the contract"):
        _build(tmp_path / "a", sources_yaml, tables=tables)
    manifest = _build(tmp_path / "b", sources_yaml, tables=tables, allow_extra=True)
    assert manifest["extra_tables"] == ["debug_table"]
    with pytest.raises(BundleError, match="snake_case"):
        _build(tmp_path / "c", sources_yaml, tables={"../evil": tables["facilities"]})


@pytest.mark.parametrize(
    "column", ["partner_cost_brl", "nda_volume_m3", "Confidential_note", "private_cane_t"]
)
def test_private_columns_refused(tmp_path: Path, sources_yaml: Path, column: str) -> None:
    tables = synthetic_tables()
    tables["supply_curve"][column] = 1.0
    with pytest.raises(BundleError, match="confidentiality pattern"):
        _build(tmp_path / "out", sources_yaml, tables=tables)
    assert not (tmp_path / "out").exists()


def test_private_table_name_refused(tmp_path: Path, sources_yaml: Path) -> None:
    tables = {"partner_mills": pd.DataFrame({"cnpj": ["00000000000001"]})}
    with pytest.raises(BundleError, match="table name 'partner_mills' matches"):
        _build(tmp_path / "out", sources_yaml, tables=tables, allow_extra=True)


def test_blocklist_has_no_substring_false_positives(tmp_path: Path, sources_yaml: Path) -> None:
    tables = synthetic_tables()
    # 'calendar' and 'mandate' contain the letters 'nda' but are not the token 'nda'
    tables["supply_curve"]["calendar_month"] = 1
    tables["supply_curve"]["mandate_volume_nm3"] = 2.0
    manifest = _build(tmp_path / "out", sources_yaml, tables=tables)
    assert manifest["warnings"] == []


def test_custom_blocklist(tmp_path: Path, sources_yaml: Path) -> None:
    with pytest.raises(BundleError, match="'lcob'"):
        _build(tmp_path / "out", sources_yaml, private_columns_blocklist=[r"lcob"])
    with pytest.raises(BundleError, match="invalid private_columns_blocklist"):
        _build(tmp_path / "out", sources_yaml, private_columns_blocklist=[r"("])


@pytest.mark.parametrize("flag", ["private", "confidential"])
def test_private_attrs_flag_refused(tmp_path: Path, sources_yaml: Path, flag: str) -> None:
    tables = synthetic_tables()
    tables["facilities"].attrs[flag] = True
    with pytest.raises(BundleError, match=f"attrs\\['{flag}'\\]=True"):
        _build(tmp_path / "out", sources_yaml, tables=tables)


def test_geometry_requires_contract_crs(tmp_path: Path, sources_yaml: Path) -> None:
    with pytest.raises(BundleError, match="pass crs='EPSG:4674'"):
        _build(tmp_path / "a", sources_yaml, crs=None)
    tables = synthetic_tables()
    tables["facilities"].attrs["crs"] = "EPSG:31983"
    with pytest.raises(BundleError, match="reproject to EPSG:4674"):
        _build(tmp_path / "b", sources_yaml, tables=tables)
    # no geometry anywhere -> crs may be omitted and is null in the manifest
    no_geom = {"supply_curve": synthetic_tables()["supply_curve"]}
    manifest = _build(tmp_path / "c", sources_yaml, tables=no_geom, crs=None)
    assert manifest["crs"] is None


def test_wkb_geometry_is_hex_in_csv(tmp_path: Path, sources_yaml: Path) -> None:
    tables = synthetic_tables()
    tables["facilities"]["geom"] = [b"\x01\x02\xab", b"\x01\x02\xcd"]  # synthetic bytes
    out = tmp_path / "out"
    manifest = _build(out, sources_yaml, tables=tables)
    assert (out / "facilities.csv").read_text().splitlines()[1].endswith(",0102ab")
    fac = next(e for e in manifest["files"] if e["path"] == "facilities.parquet")
    assert fac["columns"][-1]["arrow_type"] == "binary"


def test_unit_suffix_warnings_and_strict_mode(tmp_path: Path, sources_yaml: Path) -> None:
    tables = synthetic_tables()
    tables["lcob_results"]["npv"] = 0.0  # no unit suffix
    with pytest.warns(BundleWarning, match="'npv' has no recognised unit suffix"):
        manifest = _build(tmp_path / "a", sources_yaml, tables=tables)
    assert manifest["warnings"] == [
        "table 'lcob_results': column 'npv' has no recognised unit suffix (e.g. _t, _nm3_d, "
        "_brl_2025, _frac) and is not a known id column"
    ]
    with pytest.raises(BundleError, match=r"\[strict\]"):
        _build(tmp_path / "b", sources_yaml, tables=tables, strict=True)


@pytest.mark.parametrize(
    ("column", "has_unit_column", "expected"),
    [
        ("cane_t", False, True),
        ("ch4_nm3_d", False, True),
        ("capex_brl_2025", False, True),
        ("lcob_brl_nm3_p95", False, True),
        ("olr_kgvs_m3d", False, True),
        ("irr_frac", False, True),
        ("site_id", False, True),
        ("is_operating", False, True),
        ("h3_index", False, True),
        ("npv", False, False),
        ("capacity", False, False),
        ("t_start", False, False),  # first token is not treated as a unit
        ("p50", False, False),
        ("p50", True, True),  # long format: the 'unit' column carries the unit
    ],
)
def test_column_unit_ok(column: str, has_unit_column: bool, expected: bool) -> None:
    assert column_unit_ok(column, has_unit_column) is expected


def test_scenario_values_must_be_declared(tmp_path: Path, sources_yaml: Path) -> None:
    with pytest.raises(BundleError, match="'high_cbio'"):
        _build(tmp_path / "out", sources_yaml, scenarios=["base"])


def test_invalid_h3_refused(tmp_path: Path, sources_yaml: Path) -> None:
    tables = synthetic_tables()
    tables["hex_supply"].loc[1, "h3_index"] = "not-a-cell"
    with pytest.raises(BundleError, match="invalid/missing H3 cell"):
        _build(tmp_path / "out", sources_yaml, tables=tables)


def test_integer_h3_cells_accepted(tmp_path: Path, sources_yaml: Path) -> None:
    tables = synthetic_tables()
    hexes = tables["hex_supply"]
    hexes["h3_index"] = np.array([h3.str_to_int(c) for c in hexes["h3_index"]], dtype=np.int64)
    manifest = _build(tmp_path / "out", sources_yaml, tables={"hex_supply": hexes}, crs=None)
    entry = next(e for e in manifest["files"] if e["path"] == "hex_supply.parquet")
    assert entry["columns"][0] == {"name": "h3_index", "dtype": "int64", "arrow_type": "int64"}


def test_names_with_trailing_newline_refused(tmp_path: Path, sources_yaml: Path) -> None:
    tables = {"supply_curve\n": synthetic_tables()["supply_curve"]}
    with pytest.raises(BundleError, match="must be snake_case"):
        _build(tmp_path / "a", sources_yaml, tables=tables)
    with pytest.raises(BundleError, match="run_id"):
        _build(tmp_path / "b", sources_yaml, run_id="syn-run\n")


def test_cnpj_and_contract_columns_warn(tmp_path: Path, sources_yaml: Path) -> None:
    tables = {"mill_month": pd.DataFrame({"cnpj": [1, 2], "cane_t": [10.0, 20.0]})}
    with pytest.warns(BundleWarning):
        manifest = _build(tmp_path / "out", sources_yaml, tables=tables)
    assert manifest["warnings"] == [
        "table 'mill_month': contract column(s) missing: month",
        "table 'mill_month': 2 cnpj value(s) are not 14-digit strings (store zero-padded text), "
        "e.g. 1",
    ]


def test_named_index_and_bad_columns_refused(tmp_path: Path, sources_yaml: Path) -> None:
    tables = synthetic_tables()
    tables["supply_curve"] = tables["supply_curve"].set_index("scenario")
    with pytest.raises(BundleError, match="named index"):
        _build(tmp_path / "a", sources_yaml, tables=tables)
    dup = pd.DataFrame([[1.0, 2.0]], columns=["cum_nm3_d", "cum_nm3_d"])
    with pytest.raises(BundleError, match="duplicate column"):
        _build(tmp_path / "b", sources_yaml, tables={"supply_curve": dup})
    with pytest.raises(BundleError, match="non-empty mapping"):
        _build(tmp_path / "c", sources_yaml, tables={})


# ---------------------------------------------------------------------------------------------
# Output folder handling and failure cleanup
# ---------------------------------------------------------------------------------------------


def test_existing_bundle_is_immutable_unless_overwrite(tmp_path: Path, sources_yaml) -> None:
    out = tmp_path / "v0.1.0"
    _build(out, sources_yaml)
    with pytest.raises(BundleError, match="already exists"):
        _build(out, sources_yaml)
    smaller = {"supply_curve": synthetic_tables()["supply_curve"]}
    manifest = _build(out, sources_yaml, tables=smaller, overwrite=True)
    assert sorted(p.name for p in out.iterdir()) == [
        "manifest.json",
        "supply_curve.csv",
        "supply_curve.parquet",
    ]
    assert verify_bundle(out) == [] and len(manifest["files"]) == 2

    other = tmp_path / "not_a_bundle"
    other.mkdir()
    (other / "keep.txt").write_text("synthetic user file")
    with pytest.raises(BundleError, match="refusing to overwrite"):
        _build(other, sources_yaml, overwrite=True)
    assert (other / "keep.txt").exists()


def test_schema_failure_leaves_no_partial_bundle(tmp_path: Path, sources_yaml: Path) -> None:
    strict_schema = load_manifest_schema()
    strict_schema["properties"]["run_id"] = {"const": "only-this-run"}  # synthetic constraint
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(strict_schema), encoding="utf-8")
    parent = tmp_path / "exports"
    with pytest.raises(BundleError, match="manifest does not match the schema"):
        _build(parent / "v0.1.0", sources_yaml, schema_path=schema_path)
    assert list(parent.iterdir()) == []  # temp folder removed, nothing renamed into place


# ---------------------------------------------------------------------------------------------
# verify_bundle and CLI
# ---------------------------------------------------------------------------------------------


def test_verify_detects_tampering(tmp_path: Path, sources_yaml: Path) -> None:
    out = tmp_path / "v0.1.0"
    _build(out, sources_yaml)
    with open(out / "supply_curve.csv", "a", encoding="utf-8") as fh:
        fh.write("base,9000.0,9.0\n")  # extra synthetic row
    (out / "hex_supply.parquet").unlink()
    (out / "notes.txt").write_text("unlisted")
    problems = verify_bundle(out)
    assert "supply_curve.csv: sha256 mismatch" in problems
    assert "supply_curve.csv: 3 rows != manifest 2" in problems
    assert any(p.startswith("supply_curve.csv: size") for p in problems)
    assert "hex_supply.parquet: missing" in problems
    assert "unlisted file(s) in bundle: notes.txt" in problems

    (out / "manifest.json").write_text("{not json")
    (problem,) = verify_bundle(out)
    assert "manifest.json is not valid JSON" in problem
    assert verify_bundle(tmp_path / "nowhere") == [
        f"{tmp_path / 'nowhere' / 'manifest.json'} not found"
    ]


def test_cli_verify(tmp_path: Path, sources_yaml: Path, capsys: pytest.CaptureFixture) -> None:
    out = tmp_path / "v0.1.0"
    _build(out, sources_yaml)
    assert export_main(["verify", str(out)]) == 0
    assert capsys.readouterr().out.strip().endswith(": OK")
    (out / "sites.csv").write_text("synthetic")
    assert export_main(["verify", str(out)]) == 1
    assert "unlisted file(s) in bundle: sites.csv" in capsys.readouterr().out
