"""RenovaBio certification reports -> mill-year records (rule-based v0) + extraction verifier.

What this module does
---------------------
1. :func:`extract_mill_year` reads the per-page text of a RenovaBio *Relatório de Certificação*
   (layout of the Benri template "RQ 0607.1", route E1GC) and emits one record per data year in
   the shape of ``templates/extraction_schema_mill_year.json``. Every value carries the 1-based
   ``page`` and a ``quote``: a verbatim substring of that page with runs of whitespace collapsed
   to one space (layout padding from ``pdftotext -layout`` is not kept), at most 500 characters.
2. :func:`verify_record` checks any record in that schema against the page texts. It is written
   to be reused on **LLM-produced** extractions (CLAUDE.md §6, docs/08 §6): the quote must be
   found on the cited page, the value must be parseable from the quote, units must be
   dimensionally consistent with the variable, and plausibility ratios are computed and flagged.
3. Helpers: :func:`parse_br_number` (Brazilian number format), :func:`find_cnpj` and
   :func:`is_valid_cnpj` (official mod-11 check digits), :func:`find_br_numbers`.

Generated vs applied (CLAUDE.md rule 9)
---------------------------------------
Vinasse volumes are mapped to ``vinasse_applied`` or ``vinasse_generated`` only when the
page context says so (see :func:`classify_vinasse_context`); ambiguous context -> the value is
*not* emitted and a warning is written to ``record["extraction"]["warnings"]``.

Units
-----
``unit`` is stored **as written** in the document (e.g. ``"ton"``, ``"Litros"``, ``"L"``,
``"kWh"``, ``"gCO2eq/MJ"``, ``"%"``), as the schema asks. :func:`unit_info` maps a written unit to
(dimension, canonical unit, factor): mass -> t, volume -> L, energy -> kWh. Only exact unit
conversions are used (1 t = 1000 kg, 1 m3 = 1000 L, 1 MWh = 1000 kWh). Percentages are kept in
percent units (98.53, not 0.9853).

Plausibility screening thresholds
---------------------------------
``ETHANOL_YIELD_SCREEN_L_PER_T`` and ``VINASSE_APPLIED_SCREEN_L_PER_L`` are the QA screening
bands written in ``docs/06_DATA_ACQUISITION_PLAYBOOK.md`` §1.1 "Checks" (project rule, not a
registry parameter). They only raise ``flag`` problems, never errors, and never feed a model;
pass other bands (or ``None`` to disable) as keyword arguments. For ``vinasse_generated`` the
band is the registry row ``vin_gen`` (low/high, L per L ethanol) read with
:func:`engine.registry.get_param`.

CLI
---
``python -m engine.ingest.renovabio <pdf_or_txt> --source-id X --url Y [--verify]`` prints a
JSON array of records to stdout (``--verify`` also prints problems to stderr).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from engine import ROOT
from engine.ingest.pdftext import load_pages

__all__ = [
    "AmbiguousNumberError",
    "CnpjMatch",
    "ExtractionError",
    "NumberToken",
    "Problem",
    "SCHEMA_PATH",
    "classify_vinasse_context",
    "cnpj_check_digits",
    "extract_mill_year",
    "find_br_numbers",
    "find_cnpj",
    "format_cnpj",
    "is_valid_cnpj",
    "main",
    "normalize_text",
    "parse_br_number",
    "unit_info",
    "validate_record_schema",
    "verify_record",
]

#: JSON schema every record must satisfy.
SCHEMA_PATH = ROOT / "templates" / "extraction_schema_mill_year.json"

#: Identifier written to ``record["extraction"]["model"]`` by the rule-based extractor.
EXTRACTOR_ID = "rule-based:engine.ingest.renovabio v0"

#: Maximum quote length in characters (schema ``maxLength``).
QUOTE_MAX_CHARS = 500

#: QA screening band for (anhydrous + hydrated) ethanol per tonne of cane processed, L/t.
#: Source: docs/06_DATA_ACQUISITION_PLAYBOOK.md §1.1 "Checks" (project screening rule; a FLAG
#: only — sugar/ethanol mix legitimately moves mills outside it).
ETHANOL_YIELD_SCREEN_L_PER_T: tuple[float, float] = (70.0, 90.0)

#: QA screening band for vinasse APPLIED per litre of ethanol, L/L.
#: Source: docs/06_DATA_ACQUISITION_PLAYBOOK.md §1.1 "Checks" ("flagged if < 8 or > 16 L/L").
VINASSE_APPLIED_SCREEN_L_PER_L: tuple[float, float] = (8.0, 16.0)

#: Registry id whose low/high bound vinasse GENERATED per litre of ethanol (L/L).
VINASSE_GENERATED_PARAM_ID = "vin_gen"

#: Variables that describe the whole certification period, not one year.
PERIOD_LEVEL_VARIABLES = frozenset({"neea_anhydrous", "neea_hydrated", "eligible_fraction"})

#: Expected physical dimension for each schema variable.
VARIABLE_DIMENSION: dict[str, str] = {
    "cane_processed": "mass",
    "anhydrous_ethanol": "volume",
    "hydrated_ethanol": "volume",
    "sugar": "mass",
    "vinasse_generated": "volume",
    "vinasse_applied": "volume",
    "filter_cake": "mass",
    "straw_recovered": "mass",
    "bagasse_surplus": "mass",
    "electricity_exported": "energy",
    "neea_anhydrous": "ghg_intensity",
    "neea_hydrated": "ghg_intensity",
    "eligible_fraction": "percent",
}

# --------------------------------------------------------------------------------------------
# Text normalisation
# --------------------------------------------------------------------------------------------

_SPACE_RE = re.compile(r"\s+")
#: Layout glyphs dropped from quotes and from the comparison form: Unicode private-use
#: characters (e.g. U+F0B7, the Symbol-font bullet that pdftotext emits before list rows) and
#: common bullet characters. They carry no content.
_GLYPH_RE = re.compile("[\ue000-\uf8ff\u2022\u25aa\u25cf\u25e6]")


def collapse_ws(text: str) -> str:
    """Drop layout glyphs (private-use bullets) and collapse every whitespace run to one space."""
    return _SPACE_RE.sub(" ", _GLYPH_RE.sub(" ", text)).strip()


def normalize_text(text: str) -> str:
    """Unicode NFKC + :func:`collapse_ws`; the comparison form used by :func:`verify_record`.

    NFKC folds compatibility characters (``m³`` -> ``m3``, ``K₂O`` -> ``K2O``, math-italic letters
    -> plain letters, NBSP -> space) so that a quote typed with plain characters still matches.
    Private-use bullet glyphs are removed (see :func:`collapse_ws`).
    """
    return collapse_ws(unicodedata.normalize("NFKC", text))


# --------------------------------------------------------------------------------------------
# Brazilian number format
# --------------------------------------------------------------------------------------------


class AmbiguousNumberError(ValueError):
    """Token such as ``"1.234"``: Brazilian thousands (1234) or a dot decimal (1.234)?"""


_RE_THOUSANDS_DEC = re.compile(r"\d{1,3}(?:\.\d{3})+,\d+")
_RE_DEC = re.compile(r"\d+,\d+")
_RE_SPACE_GROUPS = re.compile(r"\d{1,3}(?: \d{3})+(?:,\d+)?")
_RE_INT = re.compile(r"\d+")
_RE_THOUSANDS_INT = re.compile(r"\d{1,3}(?:\.\d{3})+")
_MINUS_SIGNS = "-\u2212"


def parse_br_number(text: str, *, allow_ambiguous_thousands: bool = False) -> float:
    """Parse one number written in Brazilian format.

    Rules (applied after Unicode NFKC and whitespace collapsing; surrounding spaces ignored):

    - optional leading sign ``-``, ``−`` (U+2212) or ``+`` (spaces after the sign allowed);
    - optional trailing ``%`` (the value is returned **in percent units**: ``"98,53%"`` -> 98.53);
    - ``1.286.435.205,88`` -> dots are thousands separators *only* in groups of exactly three
      digits, the comma is the decimal mark;
    - ``62,34`` / ``1234,5`` -> comma decimal without thousands separators;
    - ``1 286 435 205,88`` -> spaces accepted as thousands separators in 3-digit groups;
    - ``2021`` -> plain integer;
    - ``1.234.567`` (two or more dot groups, no comma) -> unambiguous thousands -> 1234567;
    - ``1.234`` (one dot group, no comma) is **ambiguous** (1234 in Brazil, 1.234 in English):
      raises :class:`AmbiguousNumberError` unless ``allow_ambiguous_thousands=True`` (then 1234);
    - anything else (``"1.23"``, ``"1,234.56"``, ``"12.34,5"``, ``"-"``, ``""``, units) raises
      :class:`ValueError`. Accounting negatives ``(1.234,56)`` and currency symbols are not
      accepted; the caller must pass a single bare token.

    Args:
        text: the token, e.g. ``"2.329.621,65"``.
        allow_ambiguous_thousands: read a single-group ``"1.234"`` as Brazilian thousands.

    Returns:
        The value as ``float``.
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    s = collapse_ws(unicodedata.normalize("NFKC", text))
    if s.endswith("%"):
        s = s[:-1].rstrip()
    sign = 1.0
    if s[:1] and (s[0] in _MINUS_SIGNS or s[0] == "+"):
        sign = -1.0 if s[0] in _MINUS_SIGNS else 1.0
        s = s[1:].lstrip()
    if not s:
        raise ValueError(f"not a number: {text!r}")
    if _RE_THOUSANDS_DEC.fullmatch(s):
        canonical = s.replace(".", "").replace(",", ".")
    elif _RE_DEC.fullmatch(s):
        canonical = s.replace(",", ".")
    elif _RE_SPACE_GROUPS.fullmatch(s):
        canonical = s.replace(" ", "").replace(",", ".")
    elif _RE_INT.fullmatch(s):
        canonical = s
    elif _RE_THOUSANDS_INT.fullmatch(s):
        if s.count(".") >= 2 or allow_ambiguous_thousands:
            canonical = s.replace(".", "")
        else:
            raise AmbiguousNumberError(
                f"{text!r} is ambiguous (Brazilian thousands or dot decimal); "
                "pass allow_ambiguous_thousands=True to read it as thousands"
            )
    else:
        raise ValueError(f"not a Brazilian-formatted number: {text!r}")
    return sign * float(canonical)


@dataclass(frozen=True)
class NumberToken:
    """A number-like token found in text.

    Attributes:
        text: token as written (without a trailing ``%``).
        start, end: character offsets of ``text`` in the searched string.
        value: parsed value (Brazilian reading; percent sign ignored).
        ambiguous: True for single-dot-group tokens like ``"1.234"``.
        alt_value: the dot-decimal reading of an ambiguous token (e.g. 1.234), else ``None``.
        percent: True when the token is immediately followed by ``%``.
    """

    text: str
    start: int
    end: int
    value: float
    ambiguous: bool = False
    alt_value: float | None = None
    percent: bool = False


_NUM_TOKEN_RE = re.compile(
    r"(?<![\w.,\u2212-])"
    r"(?P<tok>[-\u2212]?\d+(?:\.\d{3})*(?:,\d+)?)"
    r"(?P<pct>[ ]?%)?"
    r"(?![\w]|[.,]\d)"
)


def find_br_numbers(text: str) -> list[NumberToken]:
    """Find every token that :func:`parse_br_number` can read (dates/versions yield fragments).

    Tokens glued to letters, dots or commas (``"12.1.2312"``, ``"K2O"``) are skipped.
    """
    out: list[NumberToken] = []
    for m in _NUM_TOKEN_RE.finditer(text):
        tok = m.group("tok")
        pct = m.group("pct") is not None
        try:
            value = parse_br_number(tok)
            out.append(NumberToken(tok, m.start("tok"), m.end("tok"), value, percent=pct))
        except AmbiguousNumberError:
            alt = float(tok.replace("\u2212", "-"))
            value = parse_br_number(tok, allow_ambiguous_thousands=True)
            out.append(NumberToken(tok, m.start("tok"), m.end("tok"), value, True, alt, pct))
        except ValueError:
            continue
    return out


def _decimals(token: str) -> int:
    return len(token.split(",", 1)[1]) if "," in token else 0


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


# --------------------------------------------------------------------------------------------
# CNPJ
# --------------------------------------------------------------------------------------------

_CNPJ_RE = re.compile(r"(?<!\d)(\d{2})\.?(\d{3})\.?(\d{3})/?(\d{4})-?(\d{2})(?!\d)")
_CNPJ_W1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_CNPJ_W2 = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def _mod11_digit(digits: Sequence[int], weights: Sequence[int]) -> int:
    remainder = sum(d * w for d, w in zip(digits, weights, strict=True)) % 11
    return 0 if remainder < 2 else 11 - remainder


def cnpj_check_digits(base12: str) -> str:
    """Return the two check digits of a CNPJ from its first 12 digits (official mod-11 rule).

    DV1 = mod-11 of the 12 digits with weights 5,4,3,2,9,8,7,6,5,4,3,2; DV2 = mod-11 of the 12
    digits + DV1 with weights 6,5,4,3,2,9,8,7,6,5,4,3,2; a remainder < 2 gives digit 0, otherwise
    11 - remainder. Non-digit characters in ``base12`` are ignored.
    """
    digits = [int(c) for c in re.sub(r"\D", "", base12)]
    if len(digits) != 12:
        raise ValueError(f"CNPJ base must have 12 digits, got {len(digits)}: {base12!r}")
    dv1 = _mod11_digit(digits, _CNPJ_W1)
    dv2 = _mod11_digit([*digits, dv1], _CNPJ_W2)
    return f"{dv1}{dv2}"


def is_valid_cnpj(cnpj: str) -> bool:
    """True when ``cnpj`` (formatted or not) has 14 digits and valid check digits.

    Strings of 14 identical digits (e.g. ``00000000000000``) pass the arithmetic but are
    rejected, as in the usual Receita Federal validators. The alphanumeric CNPJ format is not
    supported (the extraction schema requires 14 digits).
    """
    digits = re.sub(r"\D", "", cnpj or "")
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    return cnpj_check_digits(digits[:12]) == digits[12:]


def format_cnpj(cnpj: str) -> str:
    """``"50376938000936"`` -> ``"50.376.938/0009-36"``."""
    d = re.sub(r"\D", "", cnpj)
    if len(d) != 14:
        raise ValueError(f"CNPJ must have 14 digits: {cnpj!r}")
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


@dataclass(frozen=True)
class CnpjMatch:
    """A CNPJ found in text: 14-digit ``cnpj``, ``raw`` text, offsets and check-digit validity."""

    cnpj: str
    raw: str
    start: int
    end: int
    valid: bool


def find_cnpj(text: str, *, include_invalid: bool = False) -> list[CnpjMatch]:
    """Find CNPJs written formatted (``50.376.938/0009-36``) or as a bare 14-digit run.

    A match may not touch other digits, so the 44-digit NF-e access keys printed in RenovaBio
    reports (which embed the issuer CNPJ) do not produce matches. Only matches with valid check
    digits are returned unless ``include_invalid=True``. A bare 14-digit number that is not a
    CNPJ still passes the check with probability ~1/100; prefer formatted matches near a
    ``CNPJ`` label (as :func:`extract_mill_year` does).
    """
    out: list[CnpjMatch] = []
    for m in _CNPJ_RE.finditer(text):
        digits = "".join(m.groups())
        valid = is_valid_cnpj(digits)
        if valid or include_invalid:
            out.append(CnpjMatch(digits, m.group(0), m.start(), m.end(), valid))
    return out


# --------------------------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------------------------

_UNIT_TABLE: dict[str, tuple[str, str, float]] = {
    "t": ("mass", "t", 1.0),
    "ton": ("mass", "t", 1.0),
    "tons": ("mass", "t", 1.0),
    "tonelada": ("mass", "t", 1.0),
    "toneladas": ("mass", "t", 1.0),
    "kg": ("mass", "t", 1e-3),
    "l": ("volume", "L", 1.0),
    "litro": ("volume", "L", 1.0),
    "litros": ("volume", "L", 1.0),
    "m3": ("volume", "L", 1e3),
    "kwh": ("energy", "kWh", 1.0),
    "mwh": ("energy", "kWh", 1e3),
    "gco2eq/mj": ("ghg_intensity", "gCO2eq/MJ", 1.0),
    "gco2e/mj": ("ghg_intensity", "gCO2eq/MJ", 1.0),
    "%": ("percent", "%", 1.0),
}


def _unit_key(unit: str) -> str:
    return normalize_text(unit).replace(" ", "").lower().rstrip(".")


def unit_info(unit: str | None) -> tuple[str, str, float] | None:
    """Map a unit as written to ``(dimension, canonical_unit, factor_to_canonical)``.

    Examples: ``"ton"`` -> ``("mass", "t", 1.0)``, ``"Kg"`` -> ``("mass", "t", 0.001)``,
    ``"Litros"`` -> ``("volume", "L", 1.0)``, ``"m³"`` -> ``("volume", "L", 1000.0)``.
    Returns ``None`` for unknown units.
    """
    if not unit:
        return None
    return _UNIT_TABLE.get(_unit_key(unit))


def _same_scale(a: tuple[str, str, float], b: tuple[str, str, float]) -> bool:
    return a[0] == b[0] and _close(a[2], b[2])


_UNIT_AFTER_RE = re.compile(r"[ \t]*(?P<unit>%|[A-Za-z][A-Za-z0-9/³²₂]*)")


def _unit_after(text: str, pos: int) -> str | None:
    m = _UNIT_AFTER_RE.match(text, pos)
    return m.group("unit") if m else None


def _occurrences(pages: Sequence[str], token: str) -> list[tuple[int, str | None]]:
    """Pages (1-based) where ``token`` occurs as a whole number, with the unit word after it."""
    pat = re.compile(rf"(?<![\d.,]){re.escape(token)}(?![\d]|[.,]\d)")
    out: list[tuple[int, str | None]] = []
    for pno, text in enumerate(pages, 1):
        for m in pat.finditer(text):
            out.append((pno, _unit_after(text, m.end())))
    return out


# --------------------------------------------------------------------------------------------
# Layout helpers (Benri template RQ 0607.1, pdftotext -layout)
# --------------------------------------------------------------------------------------------

_NUM_PAT = r"-?\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+(?:,\d+)?"
_YEAR_PAT = r"(?:19|20)\d{2}"
_SECTION_LINE_RE = re.compile(r"^(?P<h>\d{1,2}\.?\s+[A-ZÀ-Ý][^\n]{4,110})$", re.M)
_FURNITURE_RES = tuple(
    re.compile(p)
    for p in (
        r"^\s*$",
        r"Relatório de Certificação da Produção Eficiente de",
        r"^\s*\d+\s*/\s*\d+\s*$",
        r"^\s*Biocombustíveis\s*$",
        r"Relatório de Auditoria",
        r"^\s*Rev\.\d+\s*$",
        r"^\s*RenovaBio\s+\d{2}/\d{2}/\d{2}\s*$",
        r"Pág\.\s*\d+/\d+",
        r"^Item\s+Questão",
        r"^\s*Correção/Esclareci",
        r"^\s*mento\s*$",
    )
)


def _is_furniture(line: str) -> bool:
    """Blank lines, page headers/footers and repeated table headers of the Benri template."""
    return any(r.search(line) for r in _FURNITURE_RES) or bool(_SECTION_LINE_RE.match(line))


def _lines(text: str) -> list[tuple[int, int, str]]:
    """``(start, end, line)`` for every line of ``text`` (``end`` excludes the newline)."""
    out: list[tuple[int, int, str]] = []
    pos = 0
    for line in text.split("\n"):
        out.append((pos, pos + len(line), line))
        pos += len(line) + 1
    return out


def _section_header_before(
    pages: Sequence[str], page_no: int, offset: int, lookback_pages: int = 2
) -> str | None:
    """Last numbered section heading before ``offset`` on ``page_no`` (or on earlier pages)."""
    for pno in range(page_no, max(0, page_no - lookback_pages - 1), -1):
        text = pages[pno - 1]
        limit = offset if pno == page_no else len(text)
        header = None
        for m in _SECTION_LINE_RE.finditer(text):
            if m.start() >= limit:
                break
            header = collapse_ws(m.group("h"))
        if header:
            return header
    return None


#: Optional list bullet before a row (private-use U+F0B7 from pdftotext, or common bullets).
_BULLET_PAT = r"(?:[\ue000-\uf8ff\u2022\u25aa\u25cf\u25e6\u00b7\u2013-]\s*)?"


def _eq_row_re(units: str) -> re.Pattern[str]:
    """Row like ``2021 = 2.329.621,65 Kg`` or ``• 2021: 2.329.621,65 ton`` (whole line)."""
    return re.compile(
        rf"^\s*{_BULLET_PAT}(?P<year>{_YEAR_PAT})\s*[=:]\s*(?P<num>{_NUM_PAT})\s*"
        rf"(?P<unit>{units})\s*$"
    )


_TABLE_ROW_RE = re.compile(rf"^\s*{_BULLET_PAT}(?P<year>{_YEAR_PAT})\s+(?P<num>{_NUM_PAT})\s*$")
_INTENSITY_ROW_RE = re.compile(
    rf"^\s*{_BULLET_PAT}(?P<year>{_YEAR_PAT}):\s*(?P<num>{_NUM_PAT})\s*L\s*/\s*t\s*cana\s*$"
)


@dataclass(frozen=True)
class _Row:
    page: int
    year: int
    num: str
    unit: str | None
    line_start: int
    line_end: int


def _find_row_block(
    pages: Sequence[str],
    page_no: int,
    offset: int,
    row_re: re.Pattern[str],
    *,
    max_lines_before: int = 40,
    max_pages_ahead: int = 1,
) -> list[_Row]:
    """First block of consecutive year rows after ``offset`` on ``page_no`` (may cross a page).

    Page furniture (headers, footers, blank lines) is skipped. Before the block starts at most
    ``max_lines_before`` content lines are skipped; after it starts, the first content line that
    is not a row, or a repeated year, ends the block.
    """
    rows: list[_Row] = []
    budget = max_lines_before
    last_page = min(len(pages), page_no + max_pages_ahead)
    for pno in range(page_no, last_page + 1):
        text = pages[pno - 1]
        for start, end, line in _lines(text):
            if pno == page_no and end < offset:
                continue
            if pno == page_no and start <= offset <= end:
                continue  # the anchor's own line
            m = row_re.search(line)
            if m:
                year = int(m.group("year"))
                if any(r.year == year for r in rows):
                    return rows
                unit = m.groupdict().get("unit")
                rows.append(_Row(pno, year, m.group("num"), unit, start, end))
                continue
            if _is_furniture(line):
                continue
            if rows:
                return rows
            budget -= 1
            if budget <= 0:
                return rows
    return rows


# --------------------------------------------------------------------------------------------
# Extraction rules
# --------------------------------------------------------------------------------------------

_MASS_UNITS = r"toneladas|ton|t|Kg|kg"
_VOLUME_UNITS = r"Litros|litros|L|m³|m3"
_ENERGY_UNITS = r"MWh|kWh"


@dataclass(frozen=True)
class _SeriesRule:
    variable: str  # schema enum value, or "vinasse" (classified from context)
    anchor: re.Pattern[str]
    row: re.Pattern[str]
    label: str
    quote_from_anchor: bool
    unit_group: str | None = None
    note: str = ""


_SERIES_RULES: tuple[_SeriesRule, ...] = (
    _SeriesRule(
        "cane_processed",
        re.compile(r"Cana\s+processada:"),
        _eq_row_re(_MASS_UNITS),
        "Cana processada (item 'cálculo do volume elegível')",
        True,
        note="Total cane processed (moagem), not only eligible cane.",
    ),
    _SeriesRule(
        "anhydrous_ethanol",
        re.compile(r"Rendimento\s+Etanol\s+Anidro"),
        _eq_row_re(_VOLUME_UNITS),
        "Etanol anidro (item 'rendimento de etanol anidro')",
        False,
        note="Anhydrous ethanol production volume declared in RenovaCalc.",
    ),
    _SeriesRule(
        "hydrated_ethanol",
        re.compile(r"Rendimento\s+Etanol\s+Hidratado"),
        _eq_row_re(_VOLUME_UNITS),
        "Etanol hidratado (item 'rendimento de etanol hidratado')",
        False,
        note="Hydrated ethanol production volume declared in RenovaCalc.",
    ),
    _SeriesRule(
        "vinasse",
        re.compile(r"Produto\s+Vinhaça\s*\((?P<unit>[^)\n]+)\)"),
        _TABLE_ROW_RE,
        "table 'Produto Vinhaça'",
        True,
        unit_group="unit",
    ),
    _SeriesRule(
        "electricity_exported",
        re.compile(r"Energia\s+Elétrica\s+Vendida"),
        _eq_row_re(_ENERGY_UNITS),
        "Energia elétrica vendida/comercializada",
        False,
        note="Electricity SOLD ('Energia Elétrica Comercializada'), mapped to "
        "electricity_exported; unit as written.",
    ),
    _SeriesRule(
        "bagasse_surplus",
        re.compile(r"Bagaço\s+Vendido"),
        _eq_row_re(_MASS_UNITS),
        "Bagaço comercializado",
        False,
        note="Bagasse SOLD ('Bagaço Comercializado'), mapped to bagasse_surplus as a LOWER "
        "BOUND: surplus bagasse that was stored or not sold is not reported.",
    ),
)

_PERIOD_NOTE = (
    "Certification-period value (RenovaCalc period {period}); repeated in each year record, "
    "NOT year-specific."
)

_NEEA_ANHYDROUS_RE = re.compile(
    rf"Etanol\s+Anidro:\s*(?P<num>{_NUM_PAT})\s*(?P<unit>gCO2e?q?/MJ)"
    r"(?:\s*Nota\s+de\s+Efici[eê]ncia\s+Energ[eé]tico-)?"
)
_NEEA_HYDRATED_RE = re.compile(
    rf"(?:Ambiental:\s*)?Etanol\s+Hidratado:\s*(?P<num>{_NUM_PAT})\s*(?P<unit>gCO2e?q?/MJ)"
)
_ELIGIBLE_RE = re.compile(
    rf"Fração\s+do\s+volume\s+de\s+(?P<num>{_NUM_PAT})\s*(?P<unit>%)"
    r"(?:[^\n]*\n\s*biocombust[ií]vel\s+eleg[ií]vel:)?"
)
_MOAGEM_TOTAL_RE = re.compile(rf"Moagem\s+de\s+cana\s+-\s+\(ton\)\s+(?P<num>{_NUM_PAT})")
_CANA_ELEGIVEL_RE = re.compile(rf"Cana\s+elegível\s+\(ton\)\s+(?P<num>{_NUM_PAT})")

_VINASSE_APPLIED_CUES = tuple(
    re.compile(p, re.I)
    for p in (
        r"CONSUMO\s+DE\s+VINHAÇA",
        r"Utilização\s+de\s+Fertilizantes\s+Orgânicos(?:/Organominerais)?",
        r"quantias\s+utilizadas\s+de\s+vinhaça",
        r"fertirriga\w*",
        r"vinhaça\s+aplicada",
        r"aplicação\s+de\s+vinhaça",
    )
)
_VINASSE_GENERATED_CUES = tuple(
    re.compile(p, re.I)
    for p in (
        r"vinhaça\s+gerada",
        r"geração\s+de\s+vinhaça",
        r"vinhaça\s+produzida",
        r"produção\s+de\s+vinhaça",
    )
)


class ExtractionError(RuntimeError):
    """The document does not look like a RenovaBio certification report this v0 can read."""


@dataclass
class _Hit:
    variable: str
    value: float
    unit: str
    page: int
    quote: str
    token: str
    year: int | None
    table_or_section: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_value(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "variable": self.variable,
            "value": self.value,
            "unit": self.unit,
            "page": self.page,
        }
        if self.table_or_section:
            out["table_or_section"] = self.table_or_section
        out["quote"] = self.quote
        if self.notes:
            out["notes"] = " ".join(self.notes)
        return out


def classify_vinasse_context(
    pages: Sequence[str], page_no: int, *, lookback_pages: int = 1
) -> tuple[str | None, list[str]]:
    """Decide whether a vinasse figure on ``page_no`` is APPLIED or GENERATED (CLAUDE.md rule 9).

    Looks for Portuguese cue phrases on the page and the ``lookback_pages`` before it
    (applied: "CONSUMO DE VINHAÇA", "Utilização de Fertilizantes Orgânicos", "quantias utilizadas
    de vinhaça", "fertirrigação", "vinhaça aplicada"; generated: "vinhaça gerada", "geração de
    vinhaça", "vinhaça produzida", "produção de vinhaça").

    Returns:
        ``("vinasse_applied" | "vinasse_generated" | None, evidence)``; ``None`` when there are
        no cues or cues of both kinds. ``evidence`` lists ``"p.N: '<verbatim cue>'"`` strings.
    """
    applied: list[str] = []
    generated: list[str] = []
    for pno in range(max(1, page_no - lookback_pages), page_no + 1):
        text = pages[pno - 1]
        for cue in _VINASSE_APPLIED_CUES:
            for m in cue.finditer(text):
                applied.append(f"p.{pno}: '{collapse_ws(m.group(0))}'")
        for cue in _VINASSE_GENERATED_CUES:
            for m in cue.finditer(text):
                generated.append(f"p.{pno}: '{collapse_ws(m.group(0))}'")
    applied, generated = list(dict.fromkeys(applied)), list(dict.fromkeys(generated))
    if applied and not generated:
        return "vinasse_applied", applied
    if generated and not applied:
        return "vinasse_generated", generated
    return None, applied + generated


def _label_above(text: str, offset: int, max_lines: int = 6) -> str | None:
    """Nearest non-blank line above ``offset`` that is not itself a year row."""
    before = text[:offset].split("\n")[:-1]
    for line in reversed(before[-max_lines:]):
        if line.strip() and not re.match(rf"^\s*{_YEAR_PAT}\s*[=:]", line):
            return collapse_ws(line)
    return None


def _line_at(text: str, offset: int) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    return collapse_ws(text[start : end if end >= 0 else len(text)])


@dataclass
class _SeriesResult:
    hits: list[_Hit]
    rows: list[_Row]
    anchor_page: int


def _extract_series(
    pages: Sequence[str], rule: _SeriesRule, warnings: list[str]
) -> _SeriesResult | None:
    for pno, text in enumerate(pages, 1):
        for am in rule.anchor.finditer(text):
            rows = _find_row_block(pages, pno, am.end(), rule.row)
            if not rows:
                continue
            anchor_unit = am.group(rule.unit_group).strip() if rule.unit_group else None
            hits: list[_Hit] = []
            for row in rows:
                unit = row.unit or anchor_unit
                if not unit:
                    warnings.append(f"{rule.variable} {row.year} (p.{row.page}): no unit found")
                    continue
                try:
                    value = parse_br_number(row.num)
                except AmbiguousNumberError:
                    warnings.append(
                        f"{rule.variable} {row.year} (p.{row.page}): ambiguous number "
                        f"{row.num!r} not emitted"
                    )
                    continue
                page_text = pages[row.page - 1]
                if rule.quote_from_anchor and row.page == pno:
                    q_start = am.start()
                else:
                    q_start = next(r for r in rows if r.page == row.page).line_start
                quote = collapse_ws(page_text[q_start : row.line_end])
                if len(quote) > QUOTE_MAX_CHARS:
                    quote = collapse_ws(page_text[row.line_start : row.line_end])
                section = _section_header_before(pages, row.page, row.line_start)
                where = f"{section} — {rule.label}" if section else rule.label
                hit = _Hit(rule.variable, value, unit, row.page, quote, row.num, row.year, where)
                if rule.note:
                    hit.notes.append(rule.note)
                hits.append(hit)
            return _SeriesResult(hits, rows, pno)
    warnings.append(f"{rule.variable}: anchor/rows not found")
    return None


def _vinasse_basis_notes(
    pages: Sequence[str], result: _SeriesResult, cane_by_year: dict[int, float]
) -> dict[int, str]:
    """Explain the per-tonne vinasse intensity printed under the table (which cane basis?)."""
    last = result.rows[-1]
    text = pages[last.page - 1]
    intensity: dict[int, str] = {}
    seen_lines = 0
    for start, _end, line in _lines(text):
        if start <= last.line_end:
            continue
        m = _INTENSITY_ROW_RE.match(line)
        if m:
            intensity[int(m.group("year"))] = m.group("num")
            continue
        if line.strip():
            seen_lines += 1
            if seen_lines > 1 or intensity:
                break
    notes: dict[int, str] = {}
    all_tokens = [(pno, tok) for pno, t in enumerate(pages, 1) for tok in find_br_numbers(t)]
    for hit in result.hits:
        if hit.year not in intensity:
            continue
        tok_text = intensity[hit.year]
        l_per_t = parse_br_number(tok_text)
        if l_per_t <= 0:
            continue
        implied_t = hit.value / l_per_t
        # tolerance = rounding of the printed intensity (half a unit of its last decimal)
        tol_t = implied_t * (0.5 * 10 ** (-_decimals(tok_text))) / l_per_t
        note = (
            f"Report intensity '{hit.year}: {tok_text} L/t cana' (p.{last.page}) implies a cane "
            f"basis of {implied_t:.0f} t (= {hit.value:.2f} L / {l_per_t:.2f} L/t)"
        )
        cane = cane_by_year.get(hit.year)
        if cane:
            note += f", not the {cane:.2f} t of cane processed"
        match = next(
            (
                (pno, tok)
                for pno, tok in all_tokens
                if abs(tok.value - implied_t) <= tol_t and pno != last.page
            ),
            None,
        )
        if match:
            pno, tok = match
            label = _label_above(pages[pno - 1], tok.start)
            row = _line_at(pages[pno - 1], tok.start)
            note += f"; it matches '{row}' on p.{pno}" + (f" (under '{label}')" if label else "")
        note += (
            ". Whether the volume covers all vinasse applied or only that cane basis is not "
            "stated; never use it as vinasse generated (CLAUDE.md rule 9)."
        )
        notes[hit.year] = note
    return notes


def _block_lines_after(
    text: str, heading_re: re.Pattern[str], stop_re: re.Pattern[str], max_lines: int = 8
) -> list[str]:
    """Lines after a heading up to and including the first ``stop_re`` line (else ``[]``)."""
    m = heading_re.search(text)
    if not m:
        return []
    out: list[str] = []
    for line in text[m.end() :].split("\n")[1 : max_lines + 1]:
        out.append(line)
        if stop_re.search(line):
            return out
    return []


_LABEL_RAZAO_RE = re.compile(r"^\s*Razão\s+Social:?\s*")
_CNPJ_LABEL_RE = re.compile(r"\bCNPJ\b")


@dataclass
class _Header:
    cnpj: str | None = None
    cnpj_page: int | None = None
    mill_name: str | None = None
    inspection_firm: str | None = None
    inspection_firm_cnpj: str | None = None
    route: str | None = None
    period_years: list[int] = field(default_factory=list)


def _name_and_cnpj(lines: list[str]) -> tuple[str | None, str | None]:
    parts: list[str] = []
    cnpj = None
    for line in lines:
        if _CNPJ_LABEL_RE.search(line):
            found = find_cnpj(line)
            cnpj = found[0].cnpj if found else None
            break
        cleaned = collapse_ws(_LABEL_RAZAO_RE.sub("", line))
        if cleaned:
            parts.append(cleaned)
    return (" ".join(parts) or None), cnpj


def _extract_header(pages: Sequence[str], max_pages: int = 5) -> _Header:
    h = _Header()
    # whole-line headings only, so the table of contents ("... ....... 3") does not match
    producer_re = re.compile(
        r"^[ \t]*(?:\d+(?:\.\d+)*[ \t]+)?PRODUTOR(?:/IMPORTADOR)?[ \t]+DE[ \t]+"
        r"BIOCOMBUST\w*[ \t]*$",
        re.M,
    )
    firm_re = re.compile(r"^[ \t]*(?:\d+(?:\.\d+)*[ \t]+)?FIRMA[ \t]+INSPETORA[ \t]*$", re.M)
    for pno, text in enumerate(pages[:max_pages], 1):
        if h.cnpj is None and producer_re.search(text):
            name, cnpj = _name_and_cnpj(_block_lines_after(text, producer_re, _CNPJ_LABEL_RE))
            if cnpj:
                h.cnpj, h.cnpj_page, h.mill_name = cnpj, pno, name
        if h.inspection_firm is None and firm_re.search(text):
            name, cnpj = _name_and_cnpj(_block_lines_after(text, firm_re, _CNPJ_LABEL_RE))
            if name:
                h.inspection_firm, h.inspection_firm_cnpj = name, cnpj
        if h.route is None:
            m = re.search(r"Rota\s+de\s+produção:\s*(?P<route>[A-Z0-9]{3,12})\b", text)
            if m:
                h.route = m.group("route")
        if not h.period_years:
            m = re.search(r"Período\s+da\s+RenovaCalc\s+(?P<y>[\d,\se]{4,60}?)\s*auditado", text)
            if m:
                h.period_years = sorted({int(y) for y in re.findall(_YEAR_PAT, m.group("y"))})
    if h.cnpj is None:  # fallback: first valid CNPJ that is not the inspection firm's
        for pno, text in enumerate(pages[:max_pages], 1):
            for cm in find_cnpj(text):
                if cm.cnpj != h.inspection_firm_cnpj:
                    h.cnpj, h.cnpj_page = cm.cnpj, pno
                    break
            if h.cnpj:
                break
    return h


def _period_hit(
    pages: Sequence[str], pattern: re.Pattern[str], variable: str, where: str
) -> _Hit | None:
    for pno, text in enumerate(pages, 1):
        m = pattern.search(text)
        if m:
            value = parse_br_number(m.group("num"))
            quote = collapse_ws(m.group(0))
            section = _section_header_before(pages, pno, m.start())
            label = f"{section} — {where}" if section else where
            return _Hit(variable, value, m.group("unit"), pno, quote, m.group("num"), None, label)
    return None


def _eligible_crosscheck(pages: Sequence[str], hit: _Hit) -> str | None:
    for pno, text in enumerate(pages, 1):
        mt, me = _MOAGEM_TOTAL_RE.search(text), _CANA_ELEGIVEL_RE.search(text)
        if mt and me:
            total_t, elig_t = parse_br_number(mt.group("num")), parse_br_number(me.group("num"))
            if total_t <= 0:
                return None
            pct = 100.0 * elig_t / total_t
            half_unit = 0.5 * 10 ** (-_decimals(hit.token))
            verdict = "consistent" if abs(pct - hit.value) <= half_unit else "INCONSISTENT"
            return (
                f"Cross-check p.{pno}: Cana elegível {me.group('num')} t / Moagem de cana "
                f"{mt.group('num')} t = {pct:.3f} % ({verdict} with {hit.value} %)."
            )
    return None


def _annotate_occurrences(pages: Sequence[str], hit: _Hit, ethanol_l: float | None) -> None:
    """Add notes about the same figure elsewhere in the document (same unit or a unit conflict)."""
    here = unit_info(hit.unit)
    same: list[int] = []
    for pno, unit in _occurrences(pages, hit.token):
        if pno == hit.page:
            continue
        other = unit_info(unit)
        if here and other and not _same_scale(here, other):
            note = (
                f"UNIT CONFLICT IN SOURCE: the same figure '{hit.token}' appears on p.{pno} "
                f"followed by '{unit}' (vs '{hit.unit}' on p.{hit.page})."
            )
            if ethanol_l and hit.variable == "cane_processed" and hit.value > 0:
                as_written = hit.value * here[2]
                alt = hit.value * other[2]
                note += (
                    f" Ethanol yield would be {ethanol_l / as_written:.2f} L/t with "
                    f"'{hit.unit}' but {ethanol_l / alt:.0f} L/t with '{unit}'; the "
                    f"'{hit.unit}' reading is kept and '{unit}' is treated as a unit typo in "
                    "the source (flag, not a data conflict)."
                )
            hit.notes.append(note)
        elif other is not None or unit is None:
            same.append(pno)
    if same:
        pages_txt = ", ".join(f"p.{p}" for p in sorted(set(same)))
        hit.notes.append(f"Same figure also on {pages_txt}.")


def extract_mill_year(
    pages: Sequence[str],
    source_id: str,
    document_url: str,
    *,
    document_sha256: str | None = None,
    extracted_at: str | None = None,
) -> list[dict[str, Any]]:
    """Extract one schema record per data year from a RenovaBio certification report.

    Args:
        pages: page texts from :func:`engine.ingest.pdftext.load_pages` (1-based numbering:
            ``pages[0]`` is page 1). Tuned on ``pdftotext -layout`` output of the Benri
            template (RQ 0607.1, route E1GC).
        source_id: registry id of the source (``registry/sources.yaml``), e.g.
            ``"renovabio_cert_reports"``.
        document_url: URL of the PDF (copied into each record; never fetched).
        document_sha256: sha256 of the PDF, copied into each record when given.
        extracted_at: ISO-8601 timestamp for ``extraction.extracted_at`` (default: now, UTC).

    Returns:
        List of records (one per year of the audited RenovaCalc period, ascending), each valid
        against ``templates/extraction_schema_mill_year.json``. Values: ``cane_processed``
        (t, as "ton"), ``anhydrous_ethanol`` / ``hydrated_ethanol`` (L, as "Litros"),
        ``vinasse_applied`` or ``vinasse_generated`` (L), ``electricity_exported`` (kWh, SOLD
        electricity), ``bagasse_surplus`` (t, SOLD bagasse = lower bound), and the
        period-level ``neea_anhydrous`` / ``neea_hydrated`` (gCO2eq/MJ) and
        ``eligible_fraction`` (%), repeated in every year record with a note.
        ``record["extraction"]["warnings"]`` lists values that could not be emitted.

    Raises:
        ExtractionError: if no page is given or the producer CNPJ cannot be found.
    """
    if not pages:
        raise ExtractionError("no pages")
    header = _extract_header(pages)
    if header.cnpj is None:
        raise ExtractionError("producer CNPJ not found (section 'PRODUTOR ... DE BIOCOMBUSTÍVEL')")
    warnings: list[str] = []
    if header.mill_name is None:
        warnings.append("mill_name not found")

    series: dict[str, _SeriesResult] = {}
    for rule in _SERIES_RULES:
        res = _extract_series(pages, rule, warnings)
        if res is None:
            continue
        if rule.variable == "vinasse":
            variable, evidence = classify_vinasse_context(pages, res.anchor_page)
            if variable is None:
                warnings.append(
                    "vinasse: context does not say applied vs generated "
                    f"(cues: {evidence or 'none'}); values not emitted (CLAUDE.md rule 9)"
                )
                continue
            kind = "APPLIED (fertirrigation)" if variable == "vinasse_applied" else "GENERATED"
            for hit in res.hits:
                hit.variable = variable
                hit.notes.append(
                    f"Classified as vinasse {kind} from context: " + "; ".join(evidence) + "."
                )
            series[variable] = res
        else:
            series[rule.variable] = res

    per_year: dict[int, dict[str, _Hit]] = {}
    for variable, res in series.items():
        for hit in res.hits:
            assert hit.year is not None
            per_year.setdefault(hit.year, {})[variable] = hit

    cane_by_year = {
        y: hits["cane_processed"].value for y, hits in per_year.items() if "cane_processed" in hits
    }
    for vin_var in ("vinasse_applied", "vinasse_generated"):
        if vin_var in series:
            for year, note in _vinasse_basis_notes(pages, series[vin_var], cane_by_year).items():
                per_year[year][vin_var].notes.append(note)

    for hits in per_year.values():
        ethanol_l = None
        if "anhydrous_ethanol" in hits or "hydrated_ethanol" in hits:
            ethanol_l = 0.0
            for var in ("anhydrous_ethanol", "hydrated_ethanol"):
                if var in hits:
                    info = unit_info(hits[var].unit)
                    ethanol_l += hits[var].value * (info[2] if info else 1.0)
        for hit in hits.values():
            _annotate_occurrences(pages, hit, ethanol_l)

    years = sorted(set(header.period_years) | set(per_year))
    if header.period_years:
        extra = sorted(set(per_year) - set(header.period_years))
        if extra:
            warnings.append(f"years {extra} found in tables but outside the declared period")
    period_txt = ", ".join(str(y) for y in years) if years else "unknown"
    period_hits: list[_Hit] = []
    for pattern, variable, where in (
        (_NEEA_ANHYDROUS_RE, "neea_anhydrous", "Nota de Eficiência Energético-Ambiental"),
        (_NEEA_HYDRATED_RE, "neea_hydrated", "Nota de Eficiência Energético-Ambiental"),
        (_ELIGIBLE_RE, "eligible_fraction", "Fração do volume de biocombustível elegível"),
    ):
        hit = _period_hit(pages, pattern, variable, where)
        if hit is None:
            warnings.append(f"{variable}: not found")
            continue
        hit.notes.append(_PERIOD_NOTE.format(period=period_txt))
        if variable == "eligible_fraction":
            hit.notes.append("Percent units.")
            check = _eligible_crosscheck(pages, hit)
            if check:
                hit.notes.append(check)
        period_hits.append(hit)

    stamp = extracted_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    records: list[dict[str, Any]] = []
    for year in years:
        record: dict[str, Any] = {"source_id": source_id, "document_url": document_url}
        if document_sha256:
            record["document_sha256"] = document_sha256
        if header.inspection_firm:
            record["inspection_firm"] = header.inspection_firm
        record["cnpj"] = header.cnpj
        record["mill_name"] = header.mill_name or ""
        if header.route:
            record["route"] = header.route
        record["year"] = year
        year_hits = per_year.get(year, {})
        record["values"] = [h.to_value() for h in year_hits.values()] + [
            h.to_value() for h in period_hits
        ]
        extraction: dict[str, Any] = {
            "model": EXTRACTOR_ID,
            "extracted_at": stamp,
            "human_audited": False,
        }
        if warnings:
            extraction["warnings"] = list(warnings)
        record["extraction"] = extraction
        records.append(record)
    return records


# --------------------------------------------------------------------------------------------
# Verification (reusable for LLM output)
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Problem:
    """One verification finding.

    Attributes:
        severity: ``"error"`` (do not trust the value/record), ``"flag"`` (needs human review;
            may be legitimate) or ``"info"`` (computed diagnostic, e.g. a ratio).
        code: stable machine-readable code (e.g. ``"quote_not_on_page"``).
        message: human-readable explanation.
        variable: schema variable concerned, if any.
        page: cited page, if any.
        data: extra numbers (ratios, bands, pages).
    """

    severity: str
    code: str
    message: str
    variable: str | None = None
    page: int | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable form."""
        return asdict(self)


@lru_cache(maxsize=4)
def _schema_validator(path: str) -> Any:
    import jsonschema

    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def validate_record_schema(
    record: dict[str, Any], schema_path: str | Path = SCHEMA_PATH
) -> list[str]:
    """Return JSON-schema validation messages for ``record`` (empty list when valid)."""
    validator = _schema_validator(str(schema_path))
    messages = []
    for err in sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in err.absolute_path) or "<record>"
        messages.append(f"{where}: {err.message}")
    return messages


def _registry_band(param_id: str) -> tuple[float, float] | None:
    try:
        from engine.registry import get_param

        p = get_param(param_id)
    except (KeyError, OSError):
        return None
    return (p.low, p.high) if p.has_range else None  # type: ignore[return-value]


def _value_hint(tokens: list[NumberToken], value: float) -> str:
    for tok in tokens:
        for factor, what in ((100.0, "x100 (fraction vs percent?)"), (1e3, "x1000 (unit scale?)")):
            if _close(tok.value * factor, value) or _close(tok.value, value * factor):
                return f" Token '{tok.text}' matches up to a factor {what}."
    return ""


def _year_adjacent(quote: str, year: int, tok: NumberToken) -> bool:
    return bool(re.search(rf"(?<!\d){year}\s*[=:]?\s*$", quote[: tok.start]))


def _verify_value(
    item: dict[str, Any],
    year: Any,
    pages: Sequence[str],
    norm_pages: list[str],
    canon: dict[str, tuple[float, str]],
    seen: set[str],
) -> list[Problem]:
    probs: list[Problem] = []
    var = item.get("variable")
    value = item.get("value")
    unit = item.get("unit")
    page = item.get("page")
    quote = item.get("quote")
    var_s = var if isinstance(var, str) else None

    def add(sev: str, code: str, msg: str, **data: Any) -> None:
        probs.append(Problem(sev, code, msg, var_s, page if isinstance(page, int) else None, data))

    if var_s in seen:
        add("error", "duplicate_variable", f"variable {var_s!r} appears more than once")
    if var_s:
        seen.add(var_s)
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        add("error", "value_not_numeric", f"value {value!r} is not a finite number")
        return probs
    if not isinstance(page, int) or isinstance(page, bool) or not 1 <= page <= len(pages):
        add("error", "page_out_of_range", f"page {page!r} not in 1..{len(pages)}")
        return probs
    if not isinstance(quote, str) or not quote.strip():
        add("error", "quote_missing", "no quote")
        return probs

    q = normalize_text(quote)
    if q not in norm_pages[page - 1]:
        elsewhere = [i + 1 for i, p in enumerate(norm_pages) if q in p]
        hint = f" It occurs on page(s) {elsewhere}." if elsewhere else " Not found on any page."
        add(
            "error",
            "quote_not_on_page",
            f"quote not found verbatim on p.{page}.{hint}",
            found_on_pages=elsewhere,
        )

    tokens = find_br_numbers(q)
    matches = [
        t
        for t in tokens
        if _close(t.value, value) or (t.alt_value is not None and _close(t.alt_value, value))
    ]
    if not matches:
        add(
            "error",
            "value_not_in_quote",
            f"value {value} cannot be parsed from the quote.{_value_hint(tokens, value)}",
        )
    elif all(t.ambiguous for t in matches):
        add(
            "flag",
            "ambiguous_number_format",
            f"value {value} matched only ambiguous token(s) {[t.text for t in matches]}",
        )

    if value < 0:
        add("error", "negative_value", f"{var_s} must be non-negative, got {value}")
    if var_s == "eligible_fraction" and not 0.0 <= value <= 100.0:
        add("error", "percent_out_of_range", f"eligible_fraction {value} not in 0..100 %")

    info = unit_info(unit) if isinstance(unit, str) else None
    expected = VARIABLE_DIMENSION.get(var_s or "")
    if info is None:
        add("flag", "unknown_unit", f"unit {unit!r} not recognised; ratios not computed")
    elif expected and info[0] != expected:
        add(
            "error",
            "unit_dimension_mismatch",
            f"unit {unit!r} is {info[0]}, but {var_s} needs {expected}",
        )
    else:
        canon[var_s or ""] = (value * info[2], info[1])
        aliases = [k for k, v in _UNIT_TABLE.items() if _same_scale(v, info)]
        if not any(
            re.search(rf"(?<![A-Za-z]){re.escape(a)}(?![A-Za-z])", q, re.I) for a in aliases
        ):
            add("flag", "unit_not_in_quote", f"unit {unit!r} (or an alias) not visible in quote")
        for tok in matches:
            after = unit_info(_unit_after(q, tok.end))
            if after and not _same_scale(after, info):
                add(
                    "error",
                    "unit_differs_from_quote",
                    f"quote shows '{tok.text} {_unit_after(q, tok.end)}' but unit is {unit!r}",
                )
                break
        if matches:
            conflicts = sorted(
                {
                    (pno, u)
                    for pno, u in _occurrences(pages, matches[0].text)
                    if (oi := unit_info(u)) is not None
                    and oi[0] == info[0]
                    and not _same_scale(oi, info)
                }
            )
            if conflicts:
                where = ", ".join(f"p.{p} '{u}'" for p, u in conflicts)
                add(
                    "flag",
                    "unit_conflict_in_source",
                    f"same figure '{matches[0].text}' appears with a different unit: {where}",
                    pages=[p for p, _ in conflicts],
                    units=[u for _, u in conflicts],
                )

    if (
        var_s not in PERIOD_LEVEL_VARIABLES
        and isinstance(year, int)
        and matches
        and not any(_year_adjacent(q, year, t) for t in matches)
    ):
        add(
            "flag",
            "year_not_adjacent",
            f"year {year} does not directly precede the value in the quote",
        )
    return probs


def verify_record(
    record: dict[str, Any],
    pages: Sequence[str],
    *,
    ethanol_yield_band_l_per_t: tuple[float, float] | None = ETHANOL_YIELD_SCREEN_L_PER_T,
    vinasse_applied_band_l_per_l: tuple[float, float] | None = VINASSE_APPLIED_SCREEN_L_PER_L,
    vinasse_generated_band_l_per_l: tuple[float, float] | None = None,
    check_schema: bool = True,
) -> list[Problem]:
    """Check one mill-year record (rule-based or LLM-produced) against the document pages.

    Checks (severity in brackets):

    - JSON schema [error]; CNPJ check digits [error]; CNPJ present in the document [flag].
    - Per value: page in range [error]; quote non-empty and found verbatim on the cited page
      after :func:`normalize_text` on both sides [error; message names the page where it does
      occur]; value parseable from a number token inside the quote [error, with a hint when it
      matches up to x100/x1000]; only ambiguous tokens match [flag]; negative quantity or
      percent outside 0..100 [error]; duplicate variable [error].
    - Units: unknown unit [flag]; dimension incompatible with the variable [error]; unit or an
      alias not visible in the quote [flag]; unit written right after the number in the quote
      differs in scale from ``unit`` [error]; the same figure printed elsewhere in the document
      with a unit of different scale, e.g. ``t`` vs ``Kg`` [flag ``unit_conflict_in_source``].
    - Year: for year-specific variables the record year must directly precede the number in
      the quote (``2021: 2.329.621,65`` / ``2021 = ...`` / ``2021 1.286...``) [flag].
    - Plausibility (canonical units t, L): ethanol yield (anhydrous + hydrated) L per t cane
      [info; flag outside ``ethanol_yield_band_l_per_t`` when both ethanol types are present];
      vinasse L per L ethanol [info; flag outside ``vinasse_applied_band_l_per_l`` for applied
      vinasse, or outside ``vinasse_generated_band_l_per_l`` (default: registry ``vin_gen``
      low/high) for generated vinasse].

    Args:
        record: a dict in the shape of ``templates/extraction_schema_mill_year.json``.
        pages: page texts of the cited document (1-based numbering, ``pages[0]`` = page 1).
        ethanol_yield_band_l_per_t: (low, high) screening band in L/t; ``None`` disables it.
        vinasse_applied_band_l_per_l: (low, high) for applied vinasse in L/L; ``None`` disables.
        vinasse_generated_band_l_per_l: (low, high) for generated vinasse in L/L; ``None`` reads
            registry ``vin_gen``.
        check_schema: run JSON-schema validation.

    Returns:
        List of :class:`Problem`; a record is acceptable when no problem has severity "error".
    """
    problems: list[Problem] = []
    if check_schema:
        problems += [Problem("error", "schema", m) for m in validate_record_schema(record)]
    norm_pages = [normalize_text(p) for p in pages]

    cnpj = record.get("cnpj")
    if isinstance(cnpj, str):
        if not is_valid_cnpj(cnpj):
            problems.append(Problem("error", "cnpj_check_digits", f"invalid CNPJ {cnpj!r}"))
        else:
            digits = re.sub(r"\D", "", cnpj)
            if not any(m.cnpj == digits for text in pages for m in find_cnpj(text)):
                problems.append(
                    Problem("flag", "cnpj_not_in_document", f"CNPJ {cnpj} not found in pages")
                )

    year = record.get("year")
    canon: dict[str, tuple[float, str]] = {}
    seen: set[str] = set()
    for item in record.get("values") or []:
        if isinstance(item, dict):
            problems += _verify_value(item, year, pages, norm_pages, canon, seen)

    problems += _plausibility(
        canon,
        ethanol_yield_band_l_per_t,
        vinasse_applied_band_l_per_l,
        vinasse_generated_band_l_per_l,
    )
    return problems


def _plausibility(
    canon: dict[str, tuple[float, str]],
    ethanol_band: tuple[float, float] | None,
    applied_band: tuple[float, float] | None,
    generated_band: tuple[float, float] | None,
) -> list[Problem]:
    probs: list[Problem] = []
    eth_parts = {v: canon[v][0] for v in ("anhydrous_ethanol", "hydrated_ethanol") if v in canon}
    ethanol_l = sum(eth_parts.values())
    both = len(eth_parts) == 2
    cane = canon.get("cane_processed")
    if cane and cane[0] > 0 and eth_parts:
        yield_l_per_t = ethanol_l / cane[0]
        data = {"ethanol_yield_l_per_t": yield_l_per_t, "ethanol_l": ethanol_l, "cane_t": cane[0]}
        scope = "anhydrous + hydrated" if both else f"only {', '.join(eth_parts)}"
        probs.append(
            Problem(
                "info",
                "ethanol_yield_l_per_t",
                f"ethanol ({scope}) / cane = {yield_l_per_t:.2f} L/t",
                "cane_processed",
                data=data,
            )
        )
        if both and ethanol_band and not ethanol_band[0] <= yield_l_per_t <= ethanol_band[1]:
            probs.append(
                Problem(
                    "flag",
                    "ethanol_yield_out_of_band",
                    f"ethanol yield {yield_l_per_t:.2f} L/t outside screening band "
                    f"{ethanol_band[0]:g}-{ethanol_band[1]:g} L/t (may be legitimate with a "
                    "high sugar mix; check units, e.g. cane in kg)",
                    "cane_processed",
                    data={**data, "band_l_per_t": list(ethanol_band)},
                )
            )
    for vin_var in ("vinasse_generated", "vinasse_applied"):
        if vin_var not in canon or ethanol_l <= 0:
            continue
        ratio = canon[vin_var][0] / ethanol_l
        data = {
            "vinasse_l_per_l_ethanol": ratio,
            "vinasse_l": canon[vin_var][0],
            "ethanol_l": ethanol_l,
        }
        probs.append(
            Problem(
                "info",
                "vinasse_l_per_l_ethanol",
                f"{vin_var} / ethanol = {ratio:.2f} L/L",
                vin_var,
                data=data,
            )
        )
        if vin_var == "vinasse_applied":
            band, src = applied_band, "docs/06 §1.1 screening band"
        else:
            band = generated_band or _registry_band(VINASSE_GENERATED_PARAM_ID)
            src = "registry vin_gen" if generated_band is None else "caller band"
        if band and not band[0] <= ratio <= band[1]:
            msg = f"{vin_var} {ratio:.2f} L/L outside {band[0]:g}-{band[1]:g} L/L ({src})"
            if vin_var == "vinasse_applied":
                msg += "; applied vinasse is not generated vinasse (CLAUDE.md rule 9)"
            probs.append(
                Problem(
                    "flag",
                    "vinasse_ratio_out_of_band",
                    msg,
                    vin_var,
                    data={**data, "band_l_per_l": list(band)},
                )
            )
    return probs


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point; returns the process exit code."""
    ap = argparse.ArgumentParser(
        prog="python -m engine.ingest.renovabio",
        description="Extract mill-year records (JSON) from a RenovaBio certification report.",
    )
    ap.add_argument("path", type=Path, help="report PDF, or its pdftotext -layout .txt")
    ap.add_argument("--source-id", required=True, help="registry source id")
    ap.add_argument("--url", required=True, help="document URL (stored, never fetched)")
    ap.add_argument(
        "--document-sha256",
        default=None,
        help="sha256 of the PDF (default: " "computed when PATH is a .pdf)",
    )
    ap.add_argument(
        "--verify",
        action="store_true",
        help="run verify_record; problems go to stderr; exit 1 on errors",
    )
    ap.add_argument("--indent", type=int, default=2)
    args = ap.parse_args(argv)

    path: Path = args.path
    pages = load_pages(path)
    sha = args.document_sha256
    if sha is None and path.suffix.lower() == ".pdf":
        sha = _sha256_file(path)
    records = extract_mill_year(pages, args.source_id, args.url, document_sha256=sha)
    json.dump(records, sys.stdout, ensure_ascii=False, indent=args.indent)
    sys.stdout.write("\n")
    if args.verify:
        n_errors = 0
        report = []
        for rec in records:
            probs = verify_record(rec, pages)
            n_errors += sum(p.severity == "error" for p in probs)
            report.append({"year": rec["year"], "problems": [p.to_dict() for p in probs]})
        json.dump(report, sys.stderr, ensure_ascii=False, indent=args.indent)
        sys.stderr.write("\n")
        return 1 if n_errors else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
