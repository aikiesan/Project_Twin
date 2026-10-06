"""Access to the in-git registry: ``parameters.csv``, ``sources.yaml``, ``projects_capex.csv``,
``references.csv``.

This module is the **single entry point** other modules use to read model parameters, so every
number used in a run can be traced to a registry row (id, source, confidence flag).

Public API (stable — other modules depend on it):

- :func:`load_parameters` -> ``dict[str, Param]``
- :func:`get_param` -> :class:`Param`
- :func:`load_sources` -> ``list[dict]``
- :func:`load_projects_capex` -> ``pandas.DataFrame``

Parameters whose ``central`` field is not a single number (e.g. ``"16 / 9"`` for TS / VS)
keep the raw text in :attr:`Param.raw_central` and have ``central = None``.

Quality tooling (added 2026-10, does not change the loaders):

- :func:`validate_parameters`, :func:`validate_sources`, :func:`validate_projects_capex`,
  :func:`validate_references`, :func:`validate_all` -> ``list[Issue]``
  (``level`` = ``"error"`` | ``"warning"``)
- :func:`load_references` -> ``list[dict]`` (scientific references, what each supports and the
  result of its double-check; docs/08 §8)
- :func:`summary_markdown` -> counts by module / confidence / status / feedstock
- :func:`param_hash` -> short SHA-256 of ``parameters.csv`` or of an overrides dict
- CLI: ``python -m engine.registry validate|summary|hash`` (:func:`main`)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from engine import REGISTRY_DIR

PARAMETERS_CSV = REGISTRY_DIR / "parameters.csv"
SOURCES_YAML = REGISTRY_DIR / "sources.yaml"
PROJECTS_CAPEX_CSV = REGISTRY_DIR / "projects_capex.csv"
REFERENCES_CSV = REGISTRY_DIR / "references.csv"
VALUE_EVIDENCE_CSV = REGISTRY_DIR / "value_evidence.csv"

CONFIDENCE_FLAGS = ("V", "S", "K", "D")


def _to_float(text: str | None) -> float | None:
    """Parse a registry cell to float; return ``None`` for blanks or non-numeric text."""
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


@dataclass(frozen=True)
class Param:
    """One row of ``registry/parameters.csv``.

    Attributes:
        id: unique parameter id (e.g. ``"vin_gen"``).
        module: owning module (supply, process, costs, market, spatial).
        name: human-readable parameter name.
        central, low, high: numeric values in ``unit`` (``None`` when blank/non-numeric).
        unit: unit string exactly as in the registry.
        source: citation text.
        confidence: one of V, S, K, D (see docs/08_VERIFICATION_PROTOCOL.md).
        notes: free text.
        raw_central, raw_low, raw_high: the original cell text.
        page, quote: where the value was read in the primary document and the verbatim text
            (docs/08 §3-4); empty until the value is verified. Required for flag ``V``.
    """

    id: str
    module: str
    name: str
    central: float | None
    low: float | None
    high: float | None
    unit: str
    source: str
    confidence: str
    notes: str
    raw_central: str
    raw_low: str
    raw_high: str
    page: str = ""
    quote: str = ""

    @property
    def has_range(self) -> bool:
        """True when both ``low`` and ``high`` are numeric."""
        return self.low is not None and self.high is not None

    def require_central(self) -> float:
        """Return ``central`` or raise if the registry has no numeric central value."""
        if self.central is None:
            raise ValueError(
                f"Parameter {self.id!r} has no numeric central value "
                f"(raw={self.raw_central!r}); pass the value explicitly."
            )
        return self.central


@lru_cache(maxsize=8)
def _load_parameters_cached(path: str) -> tuple[Param, ...]:
    rows: list[Param] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                Param(
                    id=row["id"].strip(),
                    module=(row.get("module") or "").strip(),
                    name=(row.get("parameter") or "").strip(),
                    central=_to_float(row.get("central")),
                    low=_to_float(row.get("low")),
                    high=_to_float(row.get("high")),
                    unit=(row.get("unit") or "").strip(),
                    source=(row.get("source") or "").strip(),
                    confidence=(row.get("confidence") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                    raw_central=(row.get("central") or "").strip(),
                    raw_low=(row.get("low") or "").strip(),
                    raw_high=(row.get("high") or "").strip(),
                    page=(row.get("page") or "").strip(),
                    quote=(row.get("quote") or "").strip(),
                )
            )
    return tuple(rows)


def load_parameters(path: Path | str = PARAMETERS_CSV) -> dict[str, Param]:
    """Load ``parameters.csv`` into ``{id: Param}`` (cached per path)."""
    return {p.id: p for p in _load_parameters_cached(str(path))}


def get_param(param_id: str, path: Path | str = PARAMETERS_CSV) -> Param:
    """Return one parameter by id; raise ``KeyError`` with a helpful message if absent."""
    params = load_parameters(path)
    if param_id not in params:
        raise KeyError(
            f"Parameter {param_id!r} is not in {path}. Add it to the registry (with source and "
            "confidence flag) instead of hard-coding a value."
        )
    return params[param_id]


def load_sources(path: Path | str = SOURCES_YAML) -> list[dict]:
    """Return the list under ``sources:`` in ``sources.yaml``."""
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return list(doc.get("sources", []))


def load_projects_capex(path: Path | str = PROJECTS_CAPEX_CSV):
    """Return ``projects_capex.csv`` as a pandas DataFrame (numeric columns coerced)."""
    import pandas as pd

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in ("capacity_value", "investment_total_R$M", "bndes_R$M"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", "", regex=False), errors="coerce")
    return df


# ---------------------------------------------------------------------------------------------
# Validation, summary, reproducibility hash and CLI (added 2026-10; see
# docs/08_VERIFICATION_PROTOCOL.md "Implementation status"). Nothing below changes the loaders
# above; validation re-reads the raw files so it can report problems the loaders hide.
# ---------------------------------------------------------------------------------------------

#: Issue severities. ``error`` fails ``python -m engine.registry validate`` (exit 1).
ISSUE_LEVELS = ("error", "warning")

#: Allowed ``status`` values in ``sources.yaml`` (see the header comment of that file).
SOURCE_STATUSES = ("have", "get", "lai", "paid", "build")

#: Columns ``parameters.csv`` must have (the loader reads them by name).
PARAMETER_COLUMNS = (
    "id",
    "module",
    "parameter",
    "central",
    "low",
    "high",
    "unit",
    "source",
    "confidence",
    "notes",
)

#: Evidence columns of ``parameters.csv`` (docs/08 §4). Optional for the loader and the
#: validator; a ``V`` row needs ``page`` and ``quote``. ``verified_by`` names who or what read
#: the document (an LLM extraction must say so, docs/08 §6), ``conditions`` the basis of the
#: value (substrate, scale, temperature, units), ``price_year``/``currency`` monetary rows.
PARAMETER_EVIDENCE_COLUMNS = (
    "page",
    "quote",
    "verified_by",
    "verified_on",
    "conditions",
    "price_year",
    "currency",
)

#: Keys every ``sources.yaml`` entry must carry (missing or empty -> error).
SOURCE_REQUIRED_KEYS = ("id", "name", "publisher", "url", "module", "status", "confidence")

#: Keys every source should carry (missing -> one warning per source).
SOURCE_OPTIONAL_KEYS = ("access", "license")

#: Download record keys required (as warnings) once a source has ``status: have``
#: (CLAUDE.md §2 rule 3; header comment of ``sources.yaml``).
SOURCE_DOWNLOAD_KEYS = ("accessed", "sha256", "local_path")

#: Text accepted as an explicit "URL not available yet" placeholder (validated as a warning).
URL_PLACEHOLDERS = (
    "tbd",
    "todo",
    "n/a",
    "na",
    "none",
    "pending",
    "unknown",
    "placeholder",
    "confidential",
    "private",
    "local",
)

#: Columns ``projects_capex.csv`` must have (``load_projects_capex`` and CAPEX code read them).
PROJECTS_REQUIRED_COLUMNS = (
    "id",
    "project",
    "feedstock",
    "capacity_value",
    "capacity_unit",
    "investment_total_R$M",
    "bndes_R$M",
    "source",
    "confidence",
)

#: Monetary columns of ``projects_capex.csv`` (million BRL, nominal) that must be numeric.
PROJECTS_INVESTMENT_COLUMNS = ("investment_total_R$M", "bndes_R$M")

#: Columns ``references.csv`` must have (docs/08 §8).
REFERENCE_COLUMNS = (
    "ref_id",
    "kind",
    "authors",
    "year",
    "title",
    "container",
    "volume",
    "issue",
    "pages",
    "doi",
    "url",
    "used_for",
    "ref_check",
    "checked_on",
    "check_evidence",
    "value_check",
    "notes",
)

#: Kinds of reference in ``references.csv``.
REFERENCE_KINDS = ("article", "preprint", "report", "book", "standard", "software", "grey")

#: Outcome of the identity double-check of a reference (docs/08 §8):
#: ``two_sources`` = DOI/title/first author/year/container confirmed by two independent sources;
#: ``one_source`` = confirmed by one source only; ``corrected`` is not a status (fix the row and
#: re-check); ``unconfirmed`` = searched but not established; ``unidentified`` = the citation is
#: too vague to name one work; ``pending`` = not checked yet.
REF_CHECK_STATUSES = ("two_sources", "one_source", "unconfirmed", "unidentified", "pending")

#: Status of a value the project attributes to a reference (``value_check`` column).
VALUE_CHECK_STATUSES = ("page_quote", "seen_in_abstract", "not_seen", "contradicted")

#: Columns ``value_evidence.csv`` must have (docs/08 §6, ADR-0015): one row per value statement
#: read in a reference, with the PDF page, the verbatim quote and how the reading was checked.
VALUE_EVIDENCE_COLUMNS = (
    "evidence_id",
    "param_id",
    "ref_id",
    "pdf_page",
    "printed_page",
    "location",
    "quote",
    "value",
    "unit",
    "conditions",
    "origin",
    "support",
    "check",
    "cited_ref",
    "notes",
)

#: Whose number the quote states: the paper's own measurement, a value the paper cites from
#: another work (``cited_ref`` transcribes that work; it is not a project citation), or unclear.
EVIDENCE_ORIGINS = ("own_measurement", "cited", "unclear")

#: How the quoted value bears on the parameter: it supports the central value, falls inside
#: the low-high range, is only related (other basis or conditions), or is different.
EVIDENCE_SUPPORTS = ("supports_central", "supports_range", "related_only", "different")

#: How the row was checked: two independent LLM reads agreed (``llm_double_read``); the second
#: read confirmed the quote but disputed the support label (``llm_support_disputed``); the second
#: read corrected the quote, page or value (``llm_corrected``); a person checked it against the
#: PDF (``human_audited``). Only ``human_audited`` meets docs/08 §6.
EVIDENCE_CHECKS = ("llm_double_read", "llm_support_disputed", "llm_corrected", "human_audited")

_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
_DOI_IN_TEXT_RE = re.compile(r"10\.\d{4,9}/[^\s;,)]+")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HTTP_URL_RE = re.compile(r"^https?://\S+$")
# Gas volume per time: (N)m3 per hour / day / year / month. Group 1 = volume basis.
_GAS_FLOW_UNIT_RE = re.compile(r"^(n?m3)/(h|hr|d|day|yr|y|year|a|month|mo)$")
_UTF8_BOM = b"\xef\xbb\xbf"
_EXTRA_FIELDS_KEY = "__extra_fields__"


@dataclass(frozen=True)
class Issue:
    """One validation finding.

    Attributes:
        level: ``"error"`` (breaks loaders or project rules) or ``"warning"`` (needs attention).
        file: file name (e.g. ``"parameters.csv"``).
        row: 1-based line number in the file where the record is (``None`` = whole file).
        id: record id when known (parameter id, source id, project id).
        message: human-readable explanation.
    """

    level: str
    file: str
    row: int | None
    id: str | None
    message: str

    def __str__(self) -> str:
        where = self.file if self.row is None else f"{self.file}:{self.row}"
        ident = f" [{self.id}]" if self.id else ""
        return f"{self.level.upper()} {where}{ident}: {self.message}"


class _IssueSink:
    """Small helper that appends :class:`Issue` objects for one file."""

    def __init__(self, file_name: str) -> None:
        self.file = file_name
        self.issues: list[Issue] = []

    def error(self, message: str, row: int | None = None, ident: str | None = None) -> None:
        self.issues.append(Issue("error", self.file, row, ident or None, message))

    def warning(self, message: str, row: int | None = None, ident: str | None = None) -> None:
        self.issues.append(Issue("warning", self.file, row, ident or None, message))


def _read_registry_text(path: Path, sink: _IssueSink, *, bom_level: str = "error") -> str | None:
    """Read a registry file as UTF-8 text, recording unreadable files/BOM as issues."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        sink.error(f"cannot read file: {exc}")
        return None
    if data.startswith(_UTF8_BOM):
        msg = (
            "file starts with a UTF-8 byte-order mark (BOM); the registry loaders read plain "
            "UTF-8, so the first header becomes '\\ufeffid' — re-save as UTF-8 without BOM"
        )
        (sink.error if bom_level == "error" else sink.warning)(msg)
        data = data[len(_UTF8_BOM) :]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        sink.error(f"file is not valid UTF-8: {exc}")
        return None


def _clean_scalar(value: object) -> str:
    """Return a YAML/CSV scalar as stripped text, dropping a trailing ``# comment``."""
    if value is None:
        return ""
    return str(value).split("#", 1)[0].strip()


def _check_header(header: Sequence[str] | None, required: Sequence[str], sink: _IssueSink) -> bool:
    """Record missing/duplicate header columns; return False when the file cannot be checked."""
    if not header:
        sink.error("file is empty (no header row)")
        return False
    dupes = sorted({c for c in header if list(header).count(c) > 1})
    if dupes:
        sink.error(f"duplicate header column(s): {', '.join(dupes)}")
    missing = [c for c in required if c not in header]
    if missing:
        sink.error(f"missing required column(s): {', '.join(missing)}")
        return False
    return True


def _check_field_count(row: dict, line: int, ident: str, sink: _IssueSink) -> bool:
    """Record rows with too many/too few fields (usually an unquoted comma)."""
    extra = row.get(_EXTRA_FIELDS_KEY)
    if extra:
        sink.error(
            f"row has {len(extra)} more field(s) than the header (unquoted comma?): {extra!r}",
            line,
            ident,
        )
        return False
    if any(value is None for key, value in row.items() if key != _EXTRA_FIELDS_KEY):
        sink.error("row has fewer fields than the header", line, ident)
        return False
    return True


def _parse_number(text: str) -> float | None:
    """Parse a CSV cell (thousands commas allowed) to a finite float, else ``None``."""
    return _to_float(text.replace(",", "")) if text else None


def validate_parameters(path: Path | str = PARAMETERS_CSV) -> list[Issue]:
    """Validate ``parameters.csv``.

    Rules (error unless stated):

    - header has :data:`PARAMETER_COLUMNS`; no BOM; every row has exactly the header's fields;
    - ``id`` non-empty, snake_case and unique;
    - ``confidence`` is exactly one of ``V/S/K/D`` (compound flags such as ``S/D`` are errors);
    - ``unit`` and ``source`` non-empty; empty ``module`` / ``parameter`` name -> warning;
    - numeric ``low``/``central``/``high`` must satisfy ``low <= central <= high`` for every
      pair that is numeric (blank values are fine);
    - non-numeric ``central``/``low``/``high`` text is allowed (the loader keeps it in
      ``raw_*``) but listed as a warning; a blank ``central`` is a warning because
      :meth:`Param.require_central` will raise;
    - flag ``V`` without a non-empty ``page`` and ``quote`` column -> warning
      (docs/08_VERIFICATION_PROTOCOL.md §3-4);
    - ``verified_on`` empty or ``YYYY-MM-DD``; a ``quote`` without ``page`` or ``verified_by``
      -> warning (where it was read and by whom must go with it).

    Args:
        path: CSV file to check (default: the registry's ``parameters.csv``).

    Returns:
        List of :class:`Issue` (empty when the file is clean).
    """
    path = Path(path)
    sink = _IssueSink(path.name)
    text = _read_registry_text(path, sink)
    if text is None:
        return sink.issues
    reader = csv.DictReader(io.StringIO(text, newline=""), restkey=_EXTRA_FIELDS_KEY)
    if not _check_header(reader.fieldnames, PARAMETER_COLUMNS, sink):
        return sink.issues
    seen: dict[str, int] = {}
    for row in reader:
        line = reader.line_num
        pid = (row.get("id") or "").strip()
        if not _check_field_count(row, line, pid, sink):
            continue
        if not pid:
            sink.error("empty id", line)
        elif not _SNAKE_CASE_RE.fullmatch(pid):
            sink.error(f"id {pid!r} is not snake_case ([a-z][a-z0-9_]*)", line, pid)
        if pid and pid in seen:
            sink.error(f"duplicate id (first defined on line {seen[pid]})", line, pid)
        elif pid:
            seen[pid] = line

        flag = (row.get("confidence") or "").strip()
        if flag not in CONFIDENCE_FLAGS:
            sink.error(
                f"confidence {flag!r} is not one of {'/'.join(CONFIDENCE_FLAGS)} "
                "(use a single flag; explain mixed provenance in notes)",
                line,
                pid,
            )
        if not (row.get("unit") or "").strip():
            sink.error("unit is empty (use '-' for dimensionless values)", line, pid)
        if not (row.get("source") or "").strip():
            sink.error(
                "source is empty (never invent a value; cite where it comes from)", line, pid
            )
        if not (row.get("module") or "").strip():
            sink.warning("module is empty", line, pid)
        if not (row.get("parameter") or "").strip():
            sink.warning("parameter name is empty", line, pid)

        raw = {k: (row.get(k) or "").strip() for k in ("low", "central", "high")}
        num = {k: _to_float(v) for k, v in raw.items()}
        if not raw["central"]:
            sink.warning(
                "central is blank: Param.central is None and require_central() raises",
                line,
                pid,
            )
        for key in ("central", "low", "high"):
            if raw[key] and num[key] is None:
                sink.warning(
                    f"non-numeric {key} {raw[key]!r}: kept as Param.raw_{key}, "
                    f"Param.{key} is None",
                    line,
                    pid,
                )
        pairs = (("low", "central"), ("central", "high"), ("low", "high"))
        bad = [(a, b) for a, b in pairs if num[a] is not None and num[b] is not None]
        bad = [(a, b) for a, b in bad if num[a] > num[b]]
        if bad:
            shown = ", ".join(f"{k}={raw[k]}" for k in ("low", "central", "high") if raw[k])
            broken = "; ".join(f"{a} > {b}" for a, b in bad)
            sink.error(f"values not ordered low <= central <= high ({broken}): {shown}", line, pid)

        page = (row.get("page") or "").strip()
        quote = (row.get("quote") or "").strip()
        if flag == "V" and (not page or not quote):
            sink.warning(
                "flag V but no page and verbatim quote recorded (add 'page'/'quote' "
                "columns, docs/08_VERIFICATION_PROTOCOL.md §3-4)",
                line,
                pid,
            )
        verified_on = (row.get("verified_on") or "").strip()
        if verified_on and not _ISO_DATE_RE.fullmatch(verified_on):
            sink.error(f"verified_on {verified_on!r} is not YYYY-MM-DD", line, pid)
        if quote and not (page and (row.get("verified_by") or "").strip()):
            sink.warning("quote recorded without page or verified_by", line, pid)
    return sink.issues


def _yaml_source_nodes(text: str) -> list[yaml.Node] | None:
    """Return the YAML nodes of the ``sources:`` sequence (for line numbers and duplicate keys)."""
    root = yaml.compose(text, Loader=yaml.SafeLoader)
    if not isinstance(root, yaml.MappingNode):
        return None
    for key_node, value_node in root.value:
        if getattr(key_node, "value", None) == "sources" and isinstance(
            value_node, yaml.SequenceNode
        ):
            return list(value_node.value)
    return None


def _is_url_placeholder(text: str) -> bool:
    low = text.strip().lower()
    return (
        low in URL_PLACEHOLDERS
        or (low.startswith("<") and low.endswith(">"))
        or low.startswith(("todo", "tbd"))
    )


def validate_sources(path: Path | str = SOURCES_YAML) -> list[Issue]:
    """Validate ``sources.yaml``.

    Rules (error unless stated):

    - the file parses as YAML and has a top-level ``sources:`` list of mappings
      (missing ``schema_version`` / ``updated`` -> warning);
    - no duplicate keys inside an entry (YAML would silently keep the last one);
    - every key in :data:`SOURCE_REQUIRED_KEYS` present and non-empty;
    - ``id`` unique (non-snake_case id -> warning);
    - ``status`` in :data:`SOURCE_STATUSES`; ``confidence`` in ``V/S/K/D`` (trailing
      ``# comments`` are stripped before checking);
    - ``url`` starts with ``http://`` or ``https://``; an explicit placeholder
      (:data:`URL_PLACEHOLDERS`, ``<...>``, ``TODO...``) is a warning; anything else is an error;
      non-http(s) items in ``also:`` -> warning;
    - missing :data:`SOURCE_OPTIONAL_KEYS` -> one warning per source;
    - ``status: have`` without :data:`SOURCE_DOWNLOAD_KEYS` -> one warning per source.

    Args:
        path: YAML file to check (default: the registry's ``sources.yaml``).

    Returns:
        List of :class:`Issue`.
    """
    path = Path(path)
    sink = _IssueSink(path.name)
    text = _read_registry_text(path, sink)
    if text is None:
        return sink.issues
    try:
        doc = yaml.safe_load(text)
        nodes = _yaml_source_nodes(text)
    except yaml.YAMLError as exc:
        sink.error(f"YAML parse error: {exc}".replace("\n", " "))
        return sink.issues
    if not isinstance(doc, dict) or not isinstance(doc.get("sources"), list):
        sink.error("top level must be a mapping with a 'sources:' list")
        return sink.issues
    for key in ("schema_version", "updated"):
        if key not in doc:
            sink.warning(f"top-level key {key!r} is missing")

    entries = doc["sources"]
    if nodes is None or len(nodes) != len(entries):
        nodes = [None] * len(entries)
    seen: dict[str, int | None] = {}
    for index, (entry, node) in enumerate(zip(entries, nodes, strict=True)):
        line = node.start_mark.line + 1 if node is not None else None
        if not isinstance(entry, dict):
            sink.error(f"sources[{index}] is not a mapping", line)
            continue
        sid = _clean_scalar(entry.get("id"))
        if isinstance(node, yaml.MappingNode):
            keys = [getattr(k, "value", None) for k, _ in node.value]
            dupes = sorted({k for k in keys if k is not None and keys.count(k) > 1})
            if dupes:
                sink.error(
                    f"duplicate key(s) {', '.join(dupes)} (YAML keeps only the last value)",
                    line,
                    sid,
                )

        missing = [k for k in SOURCE_REQUIRED_KEYS if not _clean_scalar(entry.get(k))]
        if missing:
            sink.error(f"missing required key(s): {', '.join(missing)}", line, sid)

        if sid:
            if sid in seen:
                first = seen[sid]
                where = f" (first defined on line {first})" if first else ""
                sink.error(f"duplicate id{where}", line, sid)
            else:
                seen[sid] = line
            if not _SNAKE_CASE_RE.fullmatch(sid):
                sink.warning(f"id {sid!r} is not snake_case", line, sid)

        status = _clean_scalar(entry.get("status"))
        if status and status not in SOURCE_STATUSES:
            sink.error(f"status {status!r} is not one of {'|'.join(SOURCE_STATUSES)}", line, sid)
        flag = _clean_scalar(entry.get("confidence"))
        if flag and flag not in CONFIDENCE_FLAGS:
            sink.error(f"confidence {flag!r} is not one of {'/'.join(CONFIDENCE_FLAGS)}", line, sid)

        url = _clean_scalar(entry.get("url"))
        if url and not _HTTP_URL_RE.fullmatch(url):
            if _is_url_placeholder(url):
                sink.warning(
                    f"url is a placeholder ({url!r}); replace with the real URL", line, sid
                )
            else:
                sink.error(
                    f"url {url!r} is neither http(s):// nor an explicit placeholder", line, sid
                )
        also = entry.get("also")
        if also is not None:
            items = also if isinstance(also, list) else [also]
            bad_also = [str(u) for u in items if not _HTTP_URL_RE.fullmatch(_clean_scalar(u))]
            if bad_also:
                sink.warning(f"'also' item(s) are not http(s) URLs: {bad_also!r}", line, sid)

        optional = [k for k in SOURCE_OPTIONAL_KEYS if k not in entry]
        if optional:
            sink.warning(f"missing optional key(s): {', '.join(optional)}", line, sid)
        if status == "have":
            download = [k for k in SOURCE_DOWNLOAD_KEYS if not _clean_scalar(entry.get(k))]
            if download:
                sink.warning(
                    "status 'have' but download record incomplete — missing "
                    f"{', '.join(download)} (CLAUDE.md §2 rule 3)",
                    line,
                    sid,
                )
    return sink.issues


def validate_projects_capex(path: Path | str = PROJECTS_CAPEX_CSV) -> list[Issue]:
    """Validate ``projects_capex.csv``.

    Rules (error unless stated):

    - header has :data:`PROJECTS_REQUIRED_COLUMNS`; every row has the header's fields
      (a BOM is only a warning here because ``pandas.read_csv`` tolerates it);
    - ``id`` non-empty and unique;
    - ``capacity_value``, when present, is numeric and > 0 and has a ``capacity_unit``;
    - ``capacity_unit`` that is not a gas flow (``Nm3/d``, ``Nm3/h``, ``m3/yr``, ...) -> warning
      (e.g. ``MW`` or ``t/yr`` cannot enter a specific-CAPEX regression without conversion);
      a flow in ``m3`` without the ``N`` reference basis -> warning (CLAUDE.md §3: Nm3 at 0 °C,
      1 atm);
    - ``confidence`` is exactly one of ``V/S/K/D``;
    - :data:`PROJECTS_INVESTMENT_COLUMNS`, when present, numeric and >= 0
      (BNDES amount larger than the total investment -> warning);
    - ``source`` non-empty.

    Args:
        path: CSV file to check (default: the registry's ``projects_capex.csv``).

    Returns:
        List of :class:`Issue`.
    """
    path = Path(path)
    sink = _IssueSink(path.name)
    text = _read_registry_text(path, sink, bom_level="warning")
    if text is None:
        return sink.issues
    reader = csv.DictReader(io.StringIO(text, newline=""), restkey=_EXTRA_FIELDS_KEY)
    if not _check_header(reader.fieldnames, PROJECTS_REQUIRED_COLUMNS, sink):
        return sink.issues
    seen: dict[str, int] = {}
    for row in reader:
        line = reader.line_num
        pid = (row.get("id") or "").strip()
        if not _check_field_count(row, line, pid, sink):
            continue
        if not pid:
            sink.error("empty id", line)
        elif pid in seen:
            sink.error(f"duplicate id (first defined on line {seen[pid]})", line, pid)
        else:
            seen[pid] = line

        cap_raw = (row.get("capacity_value") or "").strip()
        unit = (row.get("capacity_unit") or "").strip()
        if cap_raw:
            cap = _parse_number(cap_raw)
            if cap is None:
                sink.error(f"capacity_value {cap_raw!r} is not numeric", line, pid)
            elif cap <= 0:
                sink.error(f"capacity_value {cap_raw!r} must be > 0", line, pid)
            if not unit:
                sink.error("capacity_value given without capacity_unit", line, pid)
        elif unit:
            sink.warning(f"capacity_unit {unit!r} given without capacity_value", line, pid)
        if unit:
            norm = unit.lower().replace(" ", "").replace("³", "3")
            match = _GAS_FLOW_UNIT_RE.fullmatch(norm)
            if match is None:
                sink.warning(
                    f"capacity_unit {unit!r} is not a gas-flow unit (Nm3/d, Nm3/h, m3/yr, ...); "
                    "convert before using this row in specific-CAPEX (R$ per Nm3/d) analyses",
                    line,
                    pid,
                )
            elif match.group(1) == "m3":
                sink.warning(
                    f"capacity_unit {unit!r} has no reference conditions (project basis is "
                    "Nm3 at 0 °C, 1 atm); confirm the basis before normalising",
                    line,
                    pid,
                )

        flag = (row.get("confidence") or "").strip()
        if flag not in CONFIDENCE_FLAGS:
            sink.error(
                f"confidence {flag!r} is not one of {'/'.join(CONFIDENCE_FLAGS)} "
                "(use a single flag; explain mixed provenance in notes)",
                line,
                pid,
            )

        money: dict[str, float] = {}
        for col in PROJECTS_INVESTMENT_COLUMNS:
            raw_money = (row.get(col) or "").strip()
            if not raw_money:
                continue
            value = _parse_number(raw_money)
            if value is None:
                sink.error(f"{col} {raw_money!r} is not numeric", line, pid)
            elif value < 0:
                sink.error(f"{col} {raw_money!r} is negative", line, pid)
            else:
                money[col] = value
        total, bndes = money.get("investment_total_R$M"), money.get("bndes_R$M")
        if total is not None and bndes is not None and bndes > total:
            sink.warning(
                f"bndes_R$M ({bndes:g}) exceeds investment_total_R$M ({total:g})", line, pid
            )
        if not (row.get("source") or "").strip():
            sink.error("source is empty", line, pid)
    return sink.issues


def load_references(path: Path | str = REFERENCES_CSV) -> list[dict[str, str]]:
    """Rows of ``references.csv`` as dicts of stripped strings."""
    with open(path, newline="", encoding="utf-8") as fh:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh)]


def load_value_evidence(path: Path | str = VALUE_EVIDENCE_CSV) -> list[dict[str, str]]:
    """Rows of ``value_evidence.csv`` as dicts of stripped strings (ADR-0015)."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh)]


def _read_param_sources(path: Path) -> dict[str, tuple[str, str]]:
    """``{id: (source, confidence)}`` read fresh from ``parameters.csv`` (no cache: validators
    must see the file as it is now). Empty when the file cannot be read."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            return {
                (r.get("id") or "").strip(): (
                    (r.get("source") or "").strip(),
                    (r.get("confidence") or "").strip(),
                )
                for r in csv.DictReader(fh)
                if (r.get("id") or "").strip()
            }
    except (OSError, csv.Error):
        return {}


def _split_list(text: str) -> list[str]:
    return [x.strip() for x in text.split(";") if x.strip()]


def _url_domain(url: str) -> str:
    host = url.split("://", 1)[-1].split("/", 1)[0].lower()
    return host[4:] if host.startswith("www.") else host


def validate_references(
    path: Path | str = REFERENCES_CSV, parameters_path: Path | str | None = None
) -> list[Issue]:
    """Validate ``references.csv`` and its links to ``parameters.csv`` (docs/08 §8).

    Rules (error unless stated):

    - header has :data:`REFERENCE_COLUMNS`; every row has the header's fields;
    - ``ref_id`` non-empty, snake_case and unique; ``kind`` in :data:`REFERENCE_KINDS`;
    - ``year`` empty or four digits; ``doi`` empty or ``10.<registrant>/<suffix>`` (no
      ``https://doi.org/`` prefix); ``url`` empty or http(s);
    - ``used_for`` non-empty (a reference must say what in the project it supports); every
      ``parameters.csv:<id>`` item names an existing parameter;
    - ``ref_check`` in :data:`REF_CHECK_STATUSES`; ``two_sources`` needs at least two http(s)
      URLs from two different domains in ``check_evidence``, ``one_source`` at least one;
      every status but ``pending`` needs ``checked_on`` (YYYY-MM-DD);
    - ``value_check`` items are ``<parameter id>=<status>`` with a status from
      :data:`VALUE_CHECK_STATUSES` and an existing parameter id;
    - warning: a reference that is not ``two_sources``;
    - warning: a parameter whose ``source`` names a DOI or "et al." but that no reference row
      lists in ``used_for``;
    - warning: a parameter flagged ``V`` whose linked references are not ``two_sources``.

    Args:
        path: CSV file to check.
        parameters_path: ``parameters.csv`` for the cross-checks (default: next to ``path``).
    """
    path = Path(path)
    sink = _IssueSink(path.name)
    text = _read_registry_text(path, sink)
    if text is None:
        return sink.issues
    params_path = Path(parameters_path) if parameters_path else path.with_name(PARAMETERS_CSV.name)
    params = _read_param_sources(params_path)
    reader = csv.DictReader(io.StringIO(text, newline=""), restkey=_EXTRA_FIELDS_KEY)
    if not _check_header(reader.fieldnames, REFERENCE_COLUMNS, sink):
        return sink.issues
    seen: dict[str, int] = {}
    linked: dict[str, list[str]] = {}
    for row in reader:
        line = reader.line_num
        rid = (row.get("ref_id") or "").strip()
        if not _check_field_count(row, line, rid, sink):
            continue
        if not rid:
            sink.error("empty ref_id", line)
        elif rid in seen:
            sink.error(f"duplicate ref_id (first defined on line {seen[rid]})", line, rid)
        elif not _SNAKE_CASE_RE.fullmatch(rid):
            sink.error(f"ref_id {rid!r} is not snake_case", line, rid)
        else:
            seen[rid] = line
        get = {k: (row.get(k) or "").strip() for k in REFERENCE_COLUMNS}
        if get["kind"] not in REFERENCE_KINDS:
            sink.error(
                f"kind {get['kind']!r} is not one of {', '.join(REFERENCE_KINDS)}", line, rid
            )
        if get["year"] and not re.fullmatch(r"\d{4}", get["year"]):
            sink.error(f"year {get['year']!r} is not four digits", line, rid)
        if get["doi"] and not _DOI_RE.fullmatch(get["doi"]):
            sink.error(f"doi {get['doi']!r} is not of the form 10.xxxx/suffix", line, rid)
        if get["url"] and not _HTTP_URL_RE.fullmatch(get["url"]):
            sink.error(f"url {get['url']!r} is not http(s)", line, rid)

        used = _split_list(get["used_for"])
        if not used:
            sink.error(
                "used_for is empty: say which values, data or methods it supports", line, rid
            )
        for item in used:
            if item.startswith("parameters.csv:"):
                pid = item.split(":", 1)[1]
                if params and pid not in params:
                    sink.error(f"used_for names unknown parameter {pid!r}", line, rid)
                linked.setdefault(pid, []).append(get["ref_check"])

        status = get["ref_check"]
        urls = [u for u in _split_list(get["check_evidence"]) if _HTTP_URL_RE.fullmatch(u)]
        if status not in REF_CHECK_STATUSES:
            sink.error(
                f"ref_check {status!r} is not one of {', '.join(REF_CHECK_STATUSES)}", line, rid
            )
        elif status == "two_sources" and len({_url_domain(u) for u in urls}) < 2:
            sink.error("two_sources needs evidence URLs from two different domains", line, rid)
        elif status == "one_source" and not urls:
            sink.error("one_source needs an evidence URL", line, rid)
        if status in REF_CHECK_STATUSES and status != "two_sources":
            sink.warning(f"reference not double-checked (ref_check={status})", line, rid)
        if status != "pending" and not _ISO_DATE_RE.fullmatch(get["checked_on"]):
            sink.error("checked_on must be YYYY-MM-DD once a check was made", line, rid)

        for item in _split_list(get["value_check"]):
            pid, _, vstatus = item.partition("=")
            pid, vstatus = pid.strip(), vstatus.strip()
            if vstatus not in VALUE_CHECK_STATUSES:
                sink.error(
                    f"value_check {item!r}: status must be one of "
                    + ", ".join(VALUE_CHECK_STATUSES),
                    line,
                    rid,
                )
            if params and pid not in params:
                sink.error(f"value_check names unknown parameter {pid!r}", line, rid)

    for pid, (source, confidence) in params.items():
        cites_paper = bool(_DOI_IN_TEXT_RE.search(source)) or "et al" in source
        if cites_paper and pid not in linked:
            sink.warning(
                f"parameter {pid!r} cites a paper that no references.csv row links to "
                "(add the reference with used_for parameters.csv:" + pid + ")",
                ident=pid,
            )
        if confidence == "V" and pid in linked and "two_sources" not in linked[pid]:
            sink.warning(
                f"parameter {pid!r} is flagged V but none of its references is double-checked",
                ident=pid,
            )
    return sink.issues


def validate_value_evidence(
    path: Path | str = VALUE_EVIDENCE_CSV,
    parameters_path: Path | str | None = None,
    references_path: Path | str | None = None,
) -> list[Issue]:
    """Validate ``value_evidence.csv`` (docs/08 §6, ADR-0015).

    Rules (error unless stated):

    - header has :data:`VALUE_EVIDENCE_COLUMNS`; every row has the header's fields;
    - ``evidence_id`` non-empty and unique;
    - ``param_id`` names a parameter of ``parameters.csv``; ``ref_id`` names a row of
      ``references.csv`` (both checked only when the file can be read);
    - ``pdf_page`` is a positive integer (the page of the PDF file, not the printed number);
    - ``quote`` is non-empty (verbatim text from the page);
    - ``origin``, ``support`` and ``check`` are in :data:`EVIDENCE_ORIGINS`,
      :data:`EVIDENCE_SUPPORTS` and :data:`EVIDENCE_CHECKS`;
    - warning (one for the file): rows whose ``check`` is not ``human_audited``.

    Args:
        path: CSV file to check.
        parameters_path: ``parameters.csv`` (default: next to ``path``).
        references_path: ``references.csv`` (default: next to ``path``).
    """
    path = Path(path)
    sink = _IssueSink(path.name)
    text = _read_registry_text(path, sink)
    if text is None:
        return sink.issues
    params = _read_param_sources(
        Path(parameters_path) if parameters_path else path.with_name(PARAMETERS_CSV.name)
    )
    refs_path = Path(references_path) if references_path else path.with_name(REFERENCES_CSV.name)
    try:
        ref_ids = {r.get("ref_id", "") for r in load_references(refs_path)}
    except (OSError, csv.Error):
        ref_ids = set()
    reader = csv.DictReader(io.StringIO(text, newline=""), restkey=_EXTRA_FIELDS_KEY)
    if not _check_header(reader.fieldnames, VALUE_EVIDENCE_COLUMNS, sink):
        return sink.issues
    seen: dict[str, int] = {}
    not_audited = 0
    for row in reader:
        line = reader.line_num
        eid = (row.get("evidence_id") or "").strip()
        if not _check_field_count(row, line, eid, sink):
            continue
        if not eid:
            sink.error("empty evidence_id", line)
        elif eid in seen:
            sink.error(f"duplicate evidence_id (first defined on line {seen[eid]})", line, eid)
        else:
            seen[eid] = line
        get = {k: (row.get(k) or "").strip() for k in VALUE_EVIDENCE_COLUMNS}
        if params and get["param_id"] not in params:
            sink.error(f"param_id {get['param_id']!r} is not in parameters.csv", line, eid)
        if ref_ids and get["ref_id"] not in ref_ids:
            sink.error(f"ref_id {get['ref_id']!r} is not in references.csv", line, eid)
        if not re.fullmatch(r"[1-9]\d*", get["pdf_page"]):
            sink.error(f"pdf_page {get['pdf_page']!r} is not a positive integer", line, eid)
        if not get["quote"]:
            sink.error("quote is empty: record the verbatim text from the page", line, eid)
        for col, allowed in (
            ("origin", EVIDENCE_ORIGINS),
            ("support", EVIDENCE_SUPPORTS),
            ("check", EVIDENCE_CHECKS),
        ):
            if get[col] not in allowed:
                sink.error(f"{col} {get[col]!r} is not one of {', '.join(allowed)}", line, eid)
        if get["check"] in EVIDENCE_CHECKS and get["check"] != "human_audited":
            not_audited += 1
    if not_audited:
        sink.warning(
            f"{not_audited} row(s) not human_audited: LLM readings only, a person must check "
            "page and quote against the PDF before a value is used as V (docs/08 §6)"
        )
    return sink.issues


def validate_all(registry_dir: Path | str = REGISTRY_DIR) -> list[Issue]:
    """Run the validators on ``registry_dir``: parameters, sources, projects_capex and, when the
    files exist, references and value_evidence."""
    registry_dir = Path(registry_dir)
    issues = (
        validate_parameters(registry_dir / PARAMETERS_CSV.name)
        + validate_sources(registry_dir / SOURCES_YAML.name)
        + validate_projects_capex(registry_dir / PROJECTS_CAPEX_CSV.name)
    )
    if (registry_dir / REFERENCES_CSV.name).exists():
        issues += validate_references(registry_dir / REFERENCES_CSV.name)
    if (registry_dir / VALUE_EVIDENCE_CSV.name).exists():
        issues += validate_value_evidence(registry_dir / VALUE_EVIDENCE_CSV.name)
    return issues


# ---------------------------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------------------------

_MISSING = "(missing)"


def _crosstab_markdown(
    pairs: Sequence[tuple[str, str]], row_label: str, cols: Sequence[str]
) -> str:
    """Markdown table counting ``(row_key, col_key)`` pairs; extra column keys are appended."""
    col_keys = list(cols) + sorted({c for _, c in pairs if c not in cols})
    counts = Counter(pairs)
    row_keys = sorted({r for r, _ in pairs})
    lines = [
        "| " + " | ".join([row_label, *col_keys, "total"]) + " |",
        "|" + "---|" * (len(col_keys) + 2),
    ]
    for rk in row_keys:
        cells = [counts.get((rk, ck), 0) for ck in col_keys]
        lines.append("| " + " | ".join([rk, *map(str, cells), str(sum(cells))]) + " |")
    totals = [sum(counts.get((rk, ck), 0) for rk in row_keys) for ck in col_keys]
    lines.append("| " + " | ".join(["**total**", *map(str, totals), str(sum(totals))]) + " |")
    return "\n".join(lines)


def _count_markdown(values: Sequence[str], label: str) -> str:
    counts = Counter(values)
    lines = [f"| {label} | count |", "|---|---|"]
    lines += [f"| {key} | {counts[key]} |" for key in sorted(counts)]
    return "\n".join(lines)


def summary_markdown(registry_dir: Path | str = REGISTRY_DIR) -> str:
    """Return a Markdown summary of the registry.

    Sections: parameters (module x confidence flag), sources (module x status, and counts by
    confidence), projects (feedstock x confidence), references (by ref_check) and value evidence
    (support x check) when those files exist, and the validation error/warning counts.
    Blank cells are counted under ``(missing)``.
    """
    registry_dir = Path(registry_dir)
    out: list[str] = ["# Registry summary", ""]

    params_path = registry_dir / PARAMETERS_CSV.name
    try:
        params = list(load_parameters(params_path).values())
        pairs = [(p.module or _MISSING, p.confidence or _MISSING) for p in params]
        out += [
            f"## Parameters ({len(params)})",
            "",
            _crosstab_markdown(pairs, "module", CONFIDENCE_FLAGS),
            "",
        ]
    except (OSError, KeyError, csv.Error) as exc:
        out += ["## Parameters", "", f"Could not be read: {exc}", ""]

    try:
        sources = [s for s in load_sources(registry_dir / SOURCES_YAML.name) if isinstance(s, dict)]
        pairs = [
            (_clean_scalar(s.get("module")) or _MISSING, _clean_scalar(s.get("status")) or _MISSING)
            for s in sources
        ]
        flags = [_clean_scalar(s.get("confidence")) or _MISSING for s in sources]
        out += [
            f"## Sources ({len(sources)})",
            "",
            "By module and status:",
            "",
            _crosstab_markdown(pairs, "module", SOURCE_STATUSES),
            "",
            "By confidence:",
            "",
            _count_markdown(flags, "confidence"),
            "",
        ]
    except (OSError, AttributeError, yaml.YAMLError) as exc:
        out += ["## Sources", "", f"Could not be read: {exc}", ""]

    try:
        with open(registry_dir / PROJECTS_CAPEX_CSV.name, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
        pairs = [
            (
                (r.get("feedstock") or "").strip() or _MISSING,
                (r.get("confidence") or "").strip() or _MISSING,
            )
            for r in rows
        ]
        out += [
            f"## Projects CAPEX ({len(rows)})",
            "",
            _crosstab_markdown(pairs, "feedstock", CONFIDENCE_FLAGS),
            "",
        ]
    except (OSError, csv.Error) as exc:
        out += ["## Projects CAPEX", "", f"Could not be read: {exc}", ""]

    refs_path = registry_dir / REFERENCES_CSV.name
    if refs_path.exists():
        try:
            refs = load_references(refs_path)
            out += [
                f"## References ({len(refs)})",
                "",
                "By double-check status (docs/08 §8):",
                "",
                _count_markdown([r.get("ref_check") or _MISSING for r in refs], "ref_check"),
                "",
            ]
        except (OSError, csv.Error) as exc:
            out += ["## References", "", f"Could not be read: {exc}", ""]

    evidence_path = registry_dir / VALUE_EVIDENCE_CSV.name
    if evidence_path.exists():
        try:
            with open(evidence_path, newline="", encoding="utf-8-sig") as fh:
                ev_rows = list(csv.DictReader(fh))
            pairs = [
                (
                    (r.get("support") or "").strip() or _MISSING,
                    (r.get("check") or "").strip() or _MISSING,
                )
                for r in ev_rows
            ]
            out += [
                f"## Value evidence ({len(ev_rows)})",
                "",
                "By support and check (docs/08 §6, ADR-0015):",
                "",
                _crosstab_markdown(pairs, "support", EVIDENCE_CHECKS),
                "",
            ]
        except (OSError, csv.Error) as exc:
            out += ["## Value evidence", "", f"Could not be read: {exc}", ""]

    issues = validate_all(registry_dir)
    n_err = sum(i.level == "error" for i in issues)
    n_warn = sum(i.level == "warning" for i in issues)
    out += [
        "## Validation",
        "",
        f"{n_err} error(s), {n_warn} warning(s) — run `python -m engine.registry validate`.",
        "",
    ]
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------
# Reproducibility hash
# ---------------------------------------------------------------------------------------------


def _jsonable(obj: Any) -> Any:
    """Convert ``obj`` to JSON-serialisable built-ins with a stable representation."""
    if obj is None or isinstance(obj, bool | int | float | str):
        return obj
    if is_dataclass(obj) and not isinstance(obj, type):
        return _jsonable(asdict(obj))
    if isinstance(obj, Mapping):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError(f"param_hash: mapping keys must be str, got {key!r}")
            out[key] = _jsonable(value)
        return out
    if isinstance(obj, list | tuple):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, set | frozenset):
        return sorted((_jsonable(v) for v in obj), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(obj, Path):
        return str(obj)
    item = getattr(obj, "item", None)  # numpy scalars
    if callable(item) and getattr(obj, "shape", None) == ():
        return _jsonable(item())
    raise TypeError(f"param_hash: cannot serialise {type(obj).__name__} value {obj!r}")


def param_hash(
    params: Mapping[str, Any] | None = None,
    *,
    path: Path | str = PARAMETERS_CSV,
    length: int = 12,
) -> str:
    """Short SHA-256 identifying the parameter set of a run (CLAUDE.md §3 "Identifiers").

    Args:
        params: ``None`` -> hash the content of ``path`` (``parameters.csv``) with line endings
            normalised to ``\\n`` (so a CRLF checkout hashes the same). A mapping (e.g. scenario
            overrides ``{"vin_gen": 11.0}`` or the dict returned by :func:`load_parameters`) ->
            hash of its canonical JSON (keys sorted at every level, compact separators,
            :class:`Param`/dataclasses and numpy scalars converted). ``1`` and ``1.0`` hash
            differently on purpose.
        path: parameters file used when ``params`` is ``None``.
        length: number of hex characters returned (8-64).

    Returns:
        Lower-case hex prefix of the SHA-256 digest. To identify "registry file + overrides",
        hash both: ``param_hash({"registry": param_hash(), "overrides": overrides})``.
    """
    if not 8 <= length <= 64:
        raise ValueError(f"length must be between 8 and 64, got {length}")
    if params is None:
        data = Path(path).read_bytes().replace(b"\r\n", b"\n")
    else:
        canonical = json.dumps(
            _jsonable(params), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        data = canonical.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:length]


# ---------------------------------------------------------------------------------------------
# CLI: python -m engine.registry {validate,summary,hash}
# ---------------------------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point.

    Subcommands:
        ``validate [--strict] [--registry-dir DIR]``: print errors then warnings; exit 1 when
        there is any error (or any warning with ``--strict``).
        ``summary [--registry-dir DIR]``: print :func:`summary_markdown`.
        ``hash [--registry-dir DIR]``: print :func:`param_hash` of ``parameters.csv``.

    Returns:
        Process exit code.
    """
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--registry-dir",
        type=Path,
        default=REGISTRY_DIR,
        help="folder with parameters.csv, sources.yaml, projects_capex.csv (default: registry/)",
    )
    parser = argparse.ArgumentParser(
        prog="python -m engine.registry", description="Validate and summarise the registry."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_validate = sub.add_parser("validate", parents=[common], help="check registry files")
    p_validate.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    sub.add_parser("summary", parents=[common], help="print a Markdown summary")
    sub.add_parser("hash", parents=[common], help="print the parameters.csv hash")
    args = parser.parse_args(argv)

    if args.command == "summary":
        print(summary_markdown(args.registry_dir))
        return 0
    if args.command == "hash":
        print(param_hash(path=args.registry_dir / PARAMETERS_CSV.name))
        return 0

    issues = validate_all(args.registry_dir)
    errors = [i for i in issues if i.level == "error"]
    warns = [i for i in issues if i.level == "warning"]
    for issue in errors + warns:
        print(issue)
    print(f"{len(errors)} error(s), {len(warns)} warning(s) in {args.registry_dir}")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
