"""Tests for engine.ingest.load_postgis: naming, private routing, registry check, idempotency.

No database is needed except for the last test, which runs only when DATABASE_URL is set.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from engine.ingest import load_postgis as lp

REGISTRY = {
    "open_src": {"id": "open_src", "access": "open"},
    "restricted_src": {"id": "restricted_src", "access": "restricted"},
    "farm_src": {"id": "farm_src", "access": "open"},
}


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------- naming
def test_table_name_basic_and_accents():
    assert lp.table_name("cp2b_redu_v2", "municipalities") == "raw_cp2b_redu_v2__municipalities"
    assert (
        lp.table_name("mapbiomas_infra", "Usinas_Termelétricas_UTE_Biomassa")
        == "raw_mapbiomas_infra__usinas_termeletricas_ute_biomassa"
    )
    assert lp.slug("Censo 2022 - Território - São Paulo") == "censo_2022_territorio_sao_paulo"


def test_table_name_long_is_cut_deterministically():
    a = lp.table_name("seade_geo_ambiente_transporte", "ambiente_unid_conservacao_estadual_pi")
    b = lp.table_name("seade_geo_ambiente_transporte", "ambiente_unid_conservacao_federal_pi")
    assert len(a.encode()) <= 63 and len(b.encode()) <= 63
    assert a != b
    assert a == lp.table_name(
        "seade_geo_ambiente_transporte", "ambiente_unid_conservacao_estadual_pi"
    )


def test_source_id_from_path():
    assert lp.source_id_from_path("data/raw/cp2b_redu_v2/a/b.csv") == "cp2b_redu_v2"
    assert lp.source_id_from_path("/vsizip/data/raw/cetesb_ictem_2023/x.zip") == "cetesb_ictem_2023"
    assert lp.source_id_from_path("data/private/cp2b_gee_exports/f.shp") == "cp2b_gee_exports"
    with pytest.raises(ValueError):
        lp.source_id_from_path("docs/whatever.csv")


# ---------------------------------------------------------------- private routing
def test_private_path_goes_to_private_schema():
    spec = lp.TableSpec("farm_src", "farms", "vector", ["data/private/farm_src/farms.shp"])
    assert lp.route_private(spec, REGISTRY).schema == "private"
    assert spec.qualified == "private.raw_farm_src__farms"


def test_restricted_source_goes_to_private_even_under_raw():
    spec = lp.TableSpec("restricted_src", "t", "csv", ["data/raw/restricted_src/t.csv"])
    assert lp.route_private(spec, REGISTRY).schema == "private"


def test_open_raw_source_stays_in_engine():
    spec = lp.TableSpec("open_src", "t", "csv", ["data/raw/open_src/t.csv"])
    assert lp.route_private(spec, REGISTRY).schema == "engine"


def test_dedupe_keeps_private_flag_and_rejects_name_clash():
    a = lp.TableSpec("farm_src", "f", "vector", ["data/private/farm_src/f.shp"])
    b = lp.TableSpec("farm_src", "f", "vector", ["data/private/farm_src/f.shp"], private=True)
    (only,) = lp.dedupe([a, b])
    assert only.private
    c = lp.TableSpec("open_src", "x", "csv", ["data/raw/open_src/x.csv"])
    d = lp.TableSpec("open_src", "x", "csv", ["data/raw/open_src/other/x.csv"])
    with pytest.raises(ValueError, match="same table name"):
        lp.dedupe([c, d])


# ---------------------------------------------------------------- registry check
def test_unregistered_source_is_refused():
    specs = [
        lp.TableSpec("open_src", "a", "csv", ["data/raw/open_src/a.csv"]),
        lp.TableSpec("ghost_src", "b", "csv", ["data/raw/ghost_src/b.csv"]),
    ]
    with pytest.raises(lp.UnregisteredSourceError, match="ghost_src"):
        lp.check_registered(specs, REGISTRY)
    lp.check_registered(specs[:1], REGISTRY)  # registered only: no error


def test_denied_paths():
    assert lp.is_denied("data/raw/harvex_matrices/x.xlsx")
    assert lp.is_denied("data/raw/JOEL_indicators/x.csv")
    assert not lp.is_denied("data/raw/cp2b_redu_v2/municipalities.csv")


# ---------------------------------------------------------------- config -> specs
def test_specs_from_tables_glob_and_layer(tmp_path: Path):
    _write(tmp_path / "data/raw/open_src/y=2020.csv", "a\n1\n")
    _write(tmp_path / "data/raw/open_src/y=2021.csv", "a\n2\n")
    cfg = {
        "tables": [
            {"kind": "csv", "layer": "series", "paths": ["data/raw/open_src/y=*.csv"]},
            {"kind": "csv", "paths": ["data/raw/open_src/y=*.csv"]},  # no layer: one per file
        ]
    }
    specs = lp.specs_from_tables(cfg, tmp_path)
    assert [s.table for s in specs] == [
        "raw_open_src__series",
        "raw_open_src__y_2020",
        "raw_open_src__y_2021",
    ]
    assert specs[0].relpath == "data/raw/open_src/y=*.csv"
    assert len(specs[0].paths) == 2


def test_specs_from_layers_choropleth_and_private():
    cfg = {
        "layers": [
            {
                "id": "c",
                "kind": "choropleth",
                "source_id": "open_src",
                "geometry": "data/raw/mesh_src/m.shp",
                "table": "data/raw/open_src/t.csv",
            },
            {
                "id": "f",
                "kind": "vector",
                "source_id": "farm_src",
                "path": "data/private/farm_src/f.shp",
                "encoding": "latin1",
                "private": True,
                "db_layer": "farms",
            },
        ]
    }
    specs = lp.specs_from_layers(cfg)
    assert [s.qualified for s in specs] == [
        "engine.raw_mesh_src__m",  # geometry keyed on its own folder, not the layer's source_id
        "engine.raw_open_src__t",
        "private.raw_farm_src__farms",
    ]
    assert specs[2].options["encoding"] == "latin1"


def test_needs_load_rules():
    assert lp.needs_load(None, "h", table_exists=False, force=False)
    assert not lp.needs_load("h", "h", table_exists=True, force=False)
    assert lp.needs_load("h", "h2", table_exists=True, force=False)
    assert lp.needs_load("h", "h", table_exists=False, force=False)
    assert lp.needs_load("h", "h", table_exists=True, force=True)


# ---------------------------------------------------------------- files
def test_shapefile_hash_includes_sidecars(tmp_path: Path):
    for ext in (".shp", ".shx", ".dbf", ".prj"):
        _write(tmp_path / f"data/raw/open_src/f{ext}", ext)
    spec = lp.TableSpec("open_src", "f", "vector", ["data/raw/open_src/f.shp"])
    before = lp.inputs_sha256(tmp_path, spec)
    _write(tmp_path / "data/raw/open_src/f.dbf", "changed")
    assert lp.inputs_sha256(tmp_path, spec) != before


def test_convert_decimal_comma_keeps_identifiers():
    df = pd.DataFrame(
        {
            "CNPJ": ["07903169001768", "11131464000587"],
            "cap": ["8000,00", "1.204.000,50"],
            "name": ["A", "B"],
            "code": ["07", "10"],
        }
    )
    out = lp.convert_decimal_comma(df, keep_text=["CNPJ"])
    assert out["cap"].tolist() == [8000.0, 1204000.5]
    assert out["CNPJ"].tolist() == ["07903169001768", "11131464000587"]
    assert out["code"].tolist() == ["07", "10"]  # leading zero -> identifier, stays text
    assert out["name"].tolist() == ["A", "B"]


def test_read_spec_csv_filter_int_and_source_file(tmp_path: Path):
    head = ",ano,uf,geocod_mun,area_past_ha\n"
    _write(
        tmp_path / "data/raw/open_src/y=2008.csv",
        head + "0,2008.0,SP,3500105.0,1.5\n1,2008.0,MT,5100201.0,2\n",
    )
    _write(tmp_path / "data/raw/open_src/y=2009.csv", head + "0,2009.0,SP,3500105.0,3\n")
    spec = lp.TableSpec(
        "open_src",
        "vigor_sp",
        "csv",
        ["data/raw/open_src/y=2008.csv", "data/raw/open_src/y=2009.csv"],
        options={
            "filter": {"uf": "SP"},
            "int_columns": ["geocod_mun"],
            "drop_columns": ["Unnamed: 0"],
        },
    )
    df = lp.read_spec(tmp_path, spec)
    assert len(df) == 2
    assert df["geocod_mun"].tolist() == [3500105, 3500105]
    assert "Unnamed: 0" not in df.columns
    assert df["_source_file"].tolist() == ["y=2008.csv", "y=2009.csv"]


def test_database_url_from_env_file(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    _write(tmp_path / ".env", "PGPASSWORD=x\nDATABASE_URL=postgresql://e:x@localhost:5433/engine\n")
    assert lp.database_url(tmp_path) == "postgresql://e:x@localhost:5433/engine"
    assert lp.database_url(tmp_path / "nowhere") is None


# ---------------------------------------------------------------- the real config
@pytest.mark.skipif(not (lp.PACKAGE_DIR.parents[2] / "data" / "raw").is_dir(), reason="no data/")
def test_real_plan_is_registered_and_private_routed(root: Path):
    from engine.registry import load_sources

    registry = {s["id"]: s for s in load_sources(root / "registry" / "sources.yaml")}
    specs = lp.plan(root, registry)
    assert specs, "empty plan"
    for s in specs:
        assert s.source_id in registry
        assert len(s.table.encode()) <= 63
        if any(p.removeprefix("/vsizip/").startswith("data/private/") for p in s.paths):
            assert s.schema == "private", s.qualified
    assert all(s.schema == "engine" for s in lp.plan(root, registry, include_private=False))


# ---------------------------------------------------------------- live database (optional)
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
def test_load_into_live_database(tmp_path: Path):
    from sqlalchemy import create_engine, inspect, text

    _write(tmp_path / "data/raw/pytest_open/t.csv", "a,b\n1,x\n2,y\n")
    _write(tmp_path / "data/private/pytest_priv/p.csv", "a\n1\n")
    specs = [
        lp.TableSpec("pytest_open", "t", "csv", ["data/raw/pytest_open/t.csv"]),
        lp.route_private(
            lp.TableSpec("pytest_priv", "p", "csv", ["data/private/pytest_priv/p.csv"]), {}
        ),
    ]
    db = create_engine(os.environ["DATABASE_URL"])
    try:
        first = lp.load_all(db, tmp_path, specs)
        assert [r.status for r in first] == ["loaded", "loaded"]
        assert [r.status for r in lp.load_all(db, tmp_path, specs)] == ["skipped", "skipped"]
        with db.connect() as conn:
            assert inspect(conn).has_table("raw_pytest_priv__p", schema="private")
            assert not inspect(conn).has_table("raw_pytest_priv__p", schema="engine")
    finally:
        with db.begin() as conn:
            for s in specs:
                conn.execute(text(f"DROP TABLE IF EXISTS {s.qualified}"))
                conn.execute(
                    text(f"DELETE FROM {lp.LOG_TABLE} WHERE table_name = :t"), {"t": s.qualified}
                )
