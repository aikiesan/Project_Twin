"""SEMIL Anuário per-municipality table parser on verbatim lines (no PDF, no network)."""

import pandas as pd

from engine.ingest.semil_anuario import br_int, check_tables, find_rows, match_ibge, parse_pages

ELEC = (
    "Campinas 490.729 1.267.769.850 35.845 1.237.972.041 720 13.663.597 1.851 609.866.012 127 "
    "96.126.513 2.187 141.811.792 196 25.888.768 50 9.814.712 531.705 3.402.913.285"
)
GAS_HEADER = "RESIDENCIAL COMERCIAL INDUSTRIAL AUTOMOTIVO COGERAÇÃO TERMOGERAÇÃO TOTAL Municipios"
GAS = [
    "Aguaí 0 0 0 0 1 1.712.078 0 0 0 0 0 0 1 1.712.078",
    "Agudos 0 0 0 0 1 28.447 0 0 0 0 0 0 1 28.447",
    "Total do Estado 0 0 0 0 2 1.740.525 0 0 0 0 0 0 2 1.740.526",
]
PETRO = [
    "Litros Litros Litros Quilos Litros Litros Quilos Quilos Litros Quilos",
    "Adamantina 6.121.500 5.000 11.746.002 0 53.084 0 745.315 0 16.759.500 127.690",
    "Jeriquara 594.500 0 1.763.000 0 -3.252 0 2.753 0 806.800 600",
    "Mirandópolis 3.075.000 0 7.051.000 0 0 0 674.728 0 5.691.000 228.140 "
    "Mirante do Paranapanema 1.544.000 0 15.616.900 0 0 0 651.685 0 2.469.000 0",
    "Anhumas 260.000 544.000 0 0 0 12.931 0 335.000 0",
]


def pages():
    p1 = "\n".join(["MUNICÍPIO", "N.C. kWh N.C. kWh", ELEC, "16 Secretaria de Meio Ambiente"])
    p2 = "\n".join(
        [
            "TABELA Nº 4 – GÁS NATURAL – OS 15 MAIORES",
            "Cubatão 2.584 175.969 1 156.568 7 352.633.722 1 397.597 0 0 0 0 "
            "2.593 353.363.857 7,39",
            GAS_HEADER,
            *GAS,
        ]
    )
    p3 = "\n".join(["TABELA Nº 6 – OS 15 MAIORES", *PETRO])
    return [p1, p2, p3]


def test_br_int():
    assert br_int("1.267.769.850") == 1267769850
    assert br_int("-3.252") == -3252
    assert br_int("0") == 0


def test_find_rows_exact_count_and_two_per_line():
    assert find_rows(ELEC, 18)[0][0] == "Campinas"
    assert find_rows(ELEC, 14) == []
    two = find_rows(PETRO[3], 10)
    assert [n for n, _ in two] == ["Mirandópolis", "Mirante do Paranapanema"]
    assert find_rows("Cubatão 1 2 3 4 5 6 7 8 9 10 11 12 13 14 7,39", 14) == []


def test_parse_pages_sections_pages_and_skipped():
    t = parse_pages(pages())
    e = t["electricity"].iloc[0]
    assert e["municipio_pdf"] == "Campinas" and e["pdf_page"] == 1
    assert e["elec_total_kwh"] == 3402913285 and e["elec_residencial_nc"] == 490729
    g = t["natural_gas"]
    assert list(g["municipio_pdf"]) == ["Aguaí", "Agudos", "Total do Estado"]  # not Cubatão
    assert g["is_total"].tolist() == [False, False, True]
    p = t["petroleum"].set_index("municipio_pdf")
    assert len(p) == 4 and p.loc["Jeriquara", "querosene_aviacao_l"] == -3252
    assert p.loc["Adamantina", "glp_kg"] == 745315
    assert t["skipped"]["line"].str.startswith("Anhumas").tolist() == [True]


def test_check_tables_total_difference():
    c = check_tables(parse_pages(pages()))
    assert c["natural_gas"]["rows"] == 2
    assert c["natural_gas"]["sum_minus_total"] == {"gas_total_m3": -1}
    assert c["skipped"]["lines"] == 1


def test_match_ibge_normalises_and_uses_aliases():
    ibge = pd.DataFrame(
        {"ibge_code": [3530706, 3538808, 3548104], "name": ["Mogi Guaçu", "Piraju", "Florínea"]}
    )
    got = match_ibge(
        pd.Series(["Mogi-Guaçu", "Pirajú", "Florínia", "Nowhere"]), ibge, {"Florínia": "Florínea"}
    )
    assert got.tolist()[:3] == [3530706, 3538808, 3548104]
    assert pd.isna(got.iloc[3])
