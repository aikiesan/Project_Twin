"""Tests for the local dataset inventory (synthetic files only)."""

import hashlib

import yaml

from engine.ingest.inventory import scan, sha256_file, write_inventory_csv, yaml_stubs


def _write(path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_sha256_matches_hashlib(tmp_path):
    p = _write(tmp_path / "a.csv", b"x,y\n1,2\n")
    assert sha256_file(p) == hashlib.sha256(b"x,y\n1,2\n").hexdigest()


def test_shapefile_sidecars_grouped(tmp_path):
    for ext in (".shp", ".shx", ".dbf", ".prj"):
        _write(tmp_path / "infra" / f"gasodutos{ext}", ext.encode())
    _write(tmp_path / "infra" / "readme.txt", b"hello")
    entries = scan(tmp_path)
    by_path = {e.path: e for e in entries}
    assert set(by_path) == {"infra/gasodutos.shp", "infra/readme.txt"}
    shp = by_path["infra/gasodutos.shp"]
    assert shp.n_files == 4
    assert shp.sidecars == [".dbf", ".prj", ".shx"]
    assert shp.format == "ESRI Shapefile"
    assert shp.size_bytes == sum(len(e.encode()) for e in (".shp", ".shx", ".dbf", ".prj"))


def test_private_flag_and_yaml_skips_private(tmp_path):
    _write(tmp_path / "partner_sao_martinho" / "vinasse.xlsx", b"secret")
    _write(tmp_path / "public" / "ibge_pam.csv", b"a")
    entries = scan(tmp_path, private_substrings=("partner",))
    priv = {e.path: e.private for e in entries}
    assert priv == {"partner_sao_martinho/vinasse.xlsx": True, "public/ibge_pam.csv": False}
    stubs = yaml.safe_load(yaml_stubs(entries, "supply", "2026-10-04"))
    assert [s["id"] for s in stubs] == ["held_public_ibge_pam"]
    assert stubs[0]["status"] == "have"
    assert stubs[0]["local_path"] == "data/raw/public/ibge_pam.csv"


def test_inventory_csv_roundtrip(tmp_path):
    _write(tmp_path / "d" / "x.parquet", b"PAR1")
    entries = scan(tmp_path / "d")
    out = tmp_path / "inv.csv"
    write_inventory_csv(entries, out)
    text = out.read_text(encoding="utf-8").splitlines()
    assert text[0].startswith("id,path,format,size_bytes,sha256")
    assert len(text) == 2
