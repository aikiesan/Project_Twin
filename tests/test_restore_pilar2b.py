"""Tests for engine.ingest.restore_pilar2b: what is left out of the PILAR-2b copy, and why.

Pure planning functions only; the docker/psql path is exercised by hand (docs/27).
"""

from __future__ import annotations

from engine.ingest import restore_pilar2b as rp

TABLES = {
    "municipalities": ["id", "ibge_code", "geometry"],
    "cp2b_parameters": ["id", "parametro", "valor_med"],
    "calculator_leads": ["id", "email", "ip_address"],
    "auth_users": ["id", "email", "password_hash"],
    "biogas_plants": ["id", "name", "address"],
    "plant_contacts": ["id", "telefone"],  # not listed: caught by its column
    "residuos_fde_backup_027": ["id", "fde"],
    "technology_cards": ["id", "name", "created_by"],
}
VIEWS = {
    "municipality_rankings": {"municipalities"},
    "plants_with_infra": {"municipalities", "biogas_plants"},
    "plants_summary": {"plants_with_infra"},  # transitive
    "unified_refs": {"cp2b_parameters"},
}


def test_listed_personal_backup_tables_are_excluded():
    out = rp.choose_exclusions(TABLES, VIEWS)
    assert "calculator_leads" in out and "auth_users" in out
    assert out["biogas_plants"].startswith("personal-looking column")
    assert "plant_contacts" in out
    assert out["residuos_fde_backup_027"] == "backup table"
    for kept in ("municipalities", "cp2b_parameters", "technology_cards"):
        assert kept not in out  # created_by is an opaque id, not a personal column


def test_views_over_excluded_relations_are_excluded_transitively():
    out = rp.choose_exclusions(TABLES, VIEWS)
    assert "plants_with_infra" in out and "plants_summary" in out
    assert "municipality_rankings" not in out


def test_views_calling_functions_and_their_dependents_are_excluded():
    views = {**VIEWS, "dashboard": {"unified_refs"}}
    out = rp.choose_exclusions(TABLES, views, {"unified_refs": {"normalize_doi"}})
    assert out["unified_refs"].endswith("normalize_doi")
    assert "dashboard" in out


def test_sequences_of_excluded_tables_are_excluded():
    owners = {
        "calculator_leads_id_seq": "calculator_leads",
        "municipalities_id_seq": "municipalities",
    }
    out = rp.choose_exclusions(TABLES, VIEWS, None, owners)
    assert "calculator_leads_id_seq" in out
    assert "municipalities_id_seq" not in out


def test_fks_to_relations_not_copied_are_dropped():
    fks = [
        ("ts_ingest_run_fkey", "staging", "ingest_runs"),
        ("cards_created_by_fkey", "public", "auth_users"),
        ("summary_mun_fkey", "public", "municipalities"),
    ]
    assert rp.fks_to_drop(fks, ["municipalities", "technology_cards"]) == [
        "cards_created_by_fkey",
        "ts_ingest_run_fkey",
    ]


def test_filter_toc_drops_behaviour_security_and_named_fks():
    toc = [
        ";",
        "; Archive created at 2026-10-05",
        "5; 2615 2200 SCHEMA - public pg_database_owner",
        "6; 3079 1 EXTENSION - postgis",
        "301; 1255 20001 FUNCTION public normalize_doi(text) postgres",
        "6100; 0 0 COMMENT public FUNCTION normalize_doi(text) postgres",
        "400; 1259 20100 TABLE public municipalities postgres",
        "401; 1259 20101 VIEW public municipality_rankings postgres",
        "402; 1259 20102 MATERIALIZED VIEW public mv postgres",
        "5900; 0 20100 TABLE DATA public municipalities postgres",
        "6001; 2606 20200 CONSTRAINT public municipalities municipalities_pkey postgres",
        "6002; 2606 20201 FK CONSTRAINT public technology_cards cards_created_by_fkey postgres",
        "6003; 2606 20202 FK CONSTRAINT public summary summary_mun_fkey postgres",
        "6004; 2620 20300 TRIGGER public municipalities audit_trigger postgres",
        "6005; 3256 20400 POLICY public municipalities read_all postgres",
        "6006; 0 20100 ROW SECURITY public municipalities postgres",
        "6007; 0 0 ACL public TABLE municipalities postgres",
        "6008; 0 0 COMMENT public TABLE municipalities postgres",
    ]
    kept = rp.filter_toc(toc, ["cards_created_by_fkey"])
    text = "\n".join(kept)
    for gone in ("SCHEMA -", "EXTENSION", "FUNCTION", "TRIGGER", "POLICY", "ROW SECURITY",
                 "ACL", "cards_created_by_fkey"):  # fmt: skip
        assert gone not in text, gone
    for stays in ("TABLE public municipalities", "VIEW public municipality_rankings",
                  "MATERIALIZED VIEW public mv", "TABLE DATA", "municipalities_pkey",
                  "summary_mun_fkey", "COMMENT public TABLE municipalities"):  # fmt: skip
        assert stays in text, stays
    assert kept[:2] == [";", "; Archive created at 2026-10-05"]


def test_move_sql_targets_pilar2b_and_skips_extension_objects():
    assert "SET SCHEMA pilar2b" in rp.MOVE_SQL
    assert "deptype = 'e'" in rp.MOVE_SQL
