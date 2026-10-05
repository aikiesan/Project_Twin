"""Tests for the manifest-driven local importer (synthetic folders only)."""

import pytest

from engine.ingest.local_import import DeniedPathError, is_denied, plan, run


def _write(path, data: bytes = b"x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _manifest(root, include, base="src", sid="demo"):
    return {
        "roots": {"r": str(root)},
        "sources": [{"id": sid, "root": "r", "base": base, "include": include}],
    }


def test_copies_keeps_subfolders_skips_junk_and_logs(tmp_path):
    _write(tmp_path / "src" / "a.csv", b"1")
    _write(tmp_path / "src" / "sub" / "b.csv", b"22")
    _write(tmp_path / "src" / "sub" / "Thumbs.db")
    raw, log = tmp_path / "raw", tmp_path / "interim" / "log.tsv"
    res = run(_manifest(tmp_path, ["*.csv", "sub/*"]), raw, log)
    assert (res.copied, res.skipped, res.missing) == (2, 0, 0)
    assert (raw / "demo" / "sub" / "b.csv").read_bytes() == b"22"
    assert not (raw / "demo" / "sub" / "Thumbs.db").exists()
    assert len(log.read_text(encoding="utf-8").splitlines()) == 3  # header + 2


def test_never_overwrites_and_dry_run_writes_nothing(tmp_path):
    _write(tmp_path / "src" / "a.csv", b"new")
    raw = tmp_path / "raw"
    _write(raw / "demo" / "a.csv", b"old")
    res = run(_manifest(tmp_path, ["a.csv"]), raw, tmp_path / "log.tsv")
    assert res.skipped == 1 and (raw / "demo" / "a.csv").read_bytes() == b"old"
    _write(tmp_path / "src" / "c.csv")
    res = run(_manifest(tmp_path, ["c.csv"]), raw, tmp_path / "log2.tsv", dry_run=True)
    assert res.copied == 1 and not (raw / "demo" / "c.csv").exists()
    assert not (tmp_path / "log2.tsv").exists()


def test_missing_pattern_is_reported(tmp_path):
    (tmp_path / "src").mkdir()
    res = run(_manifest(tmp_path, ["nope.csv"]), tmp_path / "raw", tmp_path / "log.tsv")
    assert res.missing == 1


@pytest.mark.parametrize(
    "path",
    [
        "A:/CP2B_Maps_V3/x.csv",
        "A:/Project_Twin/materiais/05_parceiros_NDA/a.pdf",
        r"A:\Validacao\Relatorio_granjas_sui.csv",
        "D/empreendimento-geracao-distribuida.parquet",
        "A:/ILUC_NIPE/Indicadores_HARVEX.xlsx",
        "C:/Downloads/dados_Joel/matriz.csv",
        r"C:\Docs\CP2B\Relatorio_granjas_aves_X.xlsx",
        "C:/Docs/CP2B/_DATA_FILES/farms_for_gee.csv",
        "C:/Docs/CP2B/x/sao_paulo_pig_farms.shp",
        "C:/Docs/Mapa_Amasa_Artigo_01/a.csv",
        "C:/Docs/40_Pesquisa/Produto_4_CEPAL/t.zip",
        "C:/Docs/x/ListaParticipante_18-12-2025.xlsx",
        "C:/Docs/ILUC/05_SERASA_CREDITO/a.csv",
    ],
)
def test_deny_list(path):
    assert is_denied(path)


def test_denied_base_or_file_refuses_whole_plan(tmp_path):
    _write(tmp_path / "CP2B_Maps_V3" / "od.csv")
    with pytest.raises(DeniedPathError):
        plan(_manifest(tmp_path, ["*"], base="CP2B_Maps_V3"))
    _write(tmp_path / "src" / "granjas_sui.csv")
    with pytest.raises(DeniedPathError):
        plan(_manifest(tmp_path, ["*"]))


def test_env_overrides_root(tmp_path, monkeypatch):
    _write(tmp_path / "other" / "src" / "a.csv")
    monkeypatch.setenv("LOCAL_ROOT_R", str(tmp_path / "other"))
    items = plan(_manifest(tmp_path / "nowhere", ["a.csv"]))
    assert items[0][1].is_file()
