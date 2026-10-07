"""SEMIL-SP *Anuário de Energéticos por Município* (2025, ano base 2024): per-municipality tables.

Registry id ``semil_anuario_energeticos_2025``. Three long tables, one row per municipality,
identified by **name only** (no IBGE code), Brazilian integers (``1.267.769.850``):

- electricity: count of consumers (``nc``) and kWh for 8 classes + total (18 numbers per row);
- natural gas: count of consumers and m³ for 6 classes + total (14 numbers); only the
  municipalities with piped gas are listed. The PDF prints "m³" with no reference conditions;
  columns keep ``m3`` (not ``nm3``) until the base is confirmed (docs/21);
- petroleum derivatives and hydrated ethanol: 10 numbers, litres or kilograms per product
  (unit row "Litros Litros Litros Quilos …"). The Anuário states that anhydrous ethanol is
  inside "gasolina automotiva" at 27 %.

Parsing is line based and works on ``pdftotext -layout`` or pypdf text
(:mod:`engine.ingest.pdftext`):
a section starts at its table's own header line (below) and ends at the next ``TABELA Nº``
heading (the regional and top-15 summary tables). A data row is a name followed by **exactly**
the section's number of integer tokens; summary rows fail this (they end in a percentage or
start with a rank). Each row keeps its 1-based PDF page for provenance.

Names are matched to IBGE codes after removing accents, case, hyphens and apostrophes
("Mogi-Guaçu" = "Mogi Guaçu"); remaining mismatches go to an explicit alias table, never to
fuzzy guessing.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pandas as pd

ELEC_CLASSES = (
    "residencial",
    "comercial",
    "rural",
    "industrial",
    "iluminacao_publica",
    "poder_publico",
    "servico_publico",
    "consumo_proprio",
    "total",
)
GAS_CLASSES = (
    "residencial",
    "comercial",
    "industrial",
    "automotivo",
    "cogeracao",
    "termogeracao",
    "total",
)
#: Product columns in PDF order, unit from the PDF's unit row (Litros / Quilos).
PETRO_COLUMNS = (
    "gasolina_automotiva_l",
    "gasolina_aviacao_l",
    "oleo_diesel_l",
    "oleo_combustivel_kg",
    "querosene_aviacao_l",
    "querosene_iluminacao_l",
    "glp_kg",
    "coque_kg",
    "etanol_hidratado_l",
    "asfalto_kg",
)


@dataclass(frozen=True)
class Section:
    """One per-municipality table: how it starts and what its row holds."""

    key: str
    start: re.Pattern[str]
    columns: tuple[str, ...]


SECTIONS = (
    Section(
        "electricity",
        re.compile(r"N\.C\.\s+kWh"),
        tuple(f"elec_{c}_{u}" for c in ELEC_CLASSES for u in ("nc", "kwh")),
    ),
    Section(
        "natural_gas",
        re.compile(r"COGERA\S*\s+TERMOGERA\S*\s+TOTAL\s+Munic", re.IGNORECASE),
        tuple(f"gas_{c}_{u}" for c in GAS_CLASSES for u in ("nc", "m3")),
    ),
    Section("petroleum", re.compile(r"^\s*Litros\s+Litros\s+Litros\s+Quilos"), PETRO_COLUMNS),
)
END = re.compile(r"TABELA\s+N", re.IGNORECASE)
BR_INT = re.compile(r"^-?\d{1,3}(?:\.\d{3})*$")
TOTAL_NAMES = ("total do estado", "estado de sao paulo", "total")


def br_int(tok: str) -> int:
    """Brazilian integer ``"1.267.769.850"`` -> ``1267769850`` (a leading ``-`` is kept)."""
    if not BR_INT.match(tok):
        raise ValueError(f"not a Brazilian integer: {tok!r}")
    return int(tok.replace(".", ""))


def find_rows(line: str, n: int) -> list[tuple[str, list[int]]]:
    """Rows in ``line``: one or more ``name`` + exactly ``n`` integers, back to back.

    Text extraction sometimes puts two table rows on one line. The whole line must decompose
    into such segments, otherwise nothing is returned (summary rows end in a percentage).
    """
    toks, out, i = line.split(), [], 0
    while i < len(toks):
        j = i
        while j < len(toks) and not BR_INT.match(toks[j]):
            j += 1
        k = j
        while k < len(toks) and BR_INT.match(toks[k]):
            k += 1
        name = " ".join(toks[i:j])
        if not name or any(ch.isdigit() for ch in name) or k - j != n:
            return []
        out.append((name, [br_int(t) for t in toks[j:k]]))
        i = k
    return out


def parse_pages(pages: Sequence[str]) -> dict[str, pd.DataFrame]:
    """Per-section tables from page texts (``pages[0]`` = PDF page 1).

    Returns ``{section_key: DataFrame}`` with ``municipio_pdf``, ``pdf_page`` and the section's
    columns; rows whose name is a state total have ``is_total=True``. Key ``"skipped"`` lists
    row-like lines that were not parsed. Repeated rows (same name
    in one section) keep the first and are reported by :func:`check_tables`.
    """
    rows: dict[str, list[dict]] = {s.key: [] for s in SECTIONS}
    skipped: list[dict] = []
    current: Section | None = None
    for pno, text in enumerate(pages, start=1):
        for line in text.splitlines():
            if END.search(line):
                current = None
                continue
            for s in SECTIONS:
                if s.start.search(line):
                    current = s
                    break
            if current is None:
                continue
            got = find_rows(line, len(current.columns))
            if not got:
                if _looks_like_row(line, len(current.columns)):
                    skipped.append({"section": current.key, "pdf_page": pno, "line": line.strip()})
                continue
            for name, vals in got:
                rec = {"municipio_pdf": name, "pdf_page": pno}
                rec.update(zip(current.columns, vals, strict=True))
                rec["is_total"] = norm_name(name) in TOTAL_NAMES
                rows[current.key].append(rec)
    out = {}
    for s in SECTIONS:
        cols = ["municipio_pdf", "pdf_page", "is_total", *s.columns]
        out[s.key] = pd.DataFrame(rows[s.key], columns=cols)
    out["skipped"] = pd.DataFrame(skipped, columns=["section", "pdf_page", "line"])
    return out


def _looks_like_row(line: str, n: int) -> bool:
    """A name then mostly integers, but not exactly ``n`` of them: report it, never guess."""
    toks = line.split()
    ints = sum(bool(BR_INT.match(t)) for t in toks)
    return ints >= n // 2 and not any(re.match(r"^\d+,\d+$", t) for t in toks)


def norm_name(name: str) -> str:
    """Accent-, case-, hyphen- and apostrophe-insensitive municipality key."""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"[-'’`´]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def match_ibge(
    names: pd.Series, ibge: pd.DataFrame, aliases: Mapping[str, str] | None = None
) -> pd.Series:
    """IBGE 7-digit code per PDF name (``<NA>`` when unmatched).

    Args:
        names: municipality names as printed in the PDF.
        ibge: ``ibge_code`` and ``name`` columns (official names, e.g. IBGE mesh ``NM_MUN``).
        aliases: PDF name -> official name, for spellings the normalisation does not bridge.
    """
    key = {norm_name(n): int(c) for c, n in zip(ibge["ibge_code"], ibge["name"], strict=True)}
    al = {norm_name(k): norm_name(v) for k, v in (aliases or {}).items()}
    return names.map(lambda n: key.get(al.get(norm_name(n), norm_name(n)))).astype("Int64")


def check_tables(tables: Mapping[str, pd.DataFrame]) -> dict[str, dict]:
    """Row counts, duplicate names and, where the PDF prints one, the state total vs the row sum."""
    out = {}
    for key, df in tables.items():
        if key == "skipped":
            out[key] = {"lines": int(len(df))}
            continue
        body, tot = df[~df["is_total"]], df[df["is_total"]]
        cols = [
            c for c in df.columns if c not in ("municipio_pdf", "ibge_code", "pdf_page", "is_total")
        ]
        rec: dict = {
            "rows": int(len(body)),
            "duplicate_names": sorted(
                body.loc[body["municipio_pdf"].duplicated(), "municipio_pdf"]
            ),
            "pages": (
                [int(body["pdf_page"].min()), int(body["pdf_page"].max())] if len(body) else []
            ),
        }
        if len(tot):
            first = body.drop_duplicates("municipio_pdf")
            diff = {c: int(first[c].sum() - tot.iloc[0][c]) for c in cols}
            rec["total_row_page"] = int(tot.iloc[0]["pdf_page"])
            rec["sum_minus_total"] = {c: d for c, d in diff.items() if d}
        out[key] = rec
    return out
