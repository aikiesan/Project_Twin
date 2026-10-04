"""Release bundles: the engine -> PILAR-2b contract (docs/18_PILAR2B_INTEGRATION.md §2).

A release ``vX.Y.Z`` is a folder (by convention ``exports/vX.Y.Z/``, see :func:`release_dir`)
holding one Parquet **and** one CSV file per table plus ``manifest.json``. The manifest records
the run (``run_id``, git commit, parameter hash, sources and scenarios) and, per file, its
SHA-256, byte size, row count and column schema. It is validated against
``templates/release_manifest_schema.json`` (JSON Schema draft 2020-12) before it is written.

Safety gates (:class:`BundleError`, nothing is written when a gate fails):

- table names must be in :data:`CONTRACT_TABLES` unless ``allow_extra=True``;
- tables flagged ``df.attrs["private"]`` (or ``"confidential"``) and table/column names that
  match the confidentiality blocklist (:data:`DEFAULT_PRIVATE_COLUMN_PATTERNS`) are refused
  (CLAUDE.md §2 rule 6: partner data never leaves the engine un-aggregated);
- a ``geom``/``geometry`` column requires ``crs="EPSG:4674"`` (the contract CRS);
- ``scenario`` values must be declared in ``scenarios``; ``h3_index`` values must be valid H3
  cells; ``sources_used`` must be ids of ``registry/sources.yaml``;
- version must be Semantic Versioning; ``created_at`` must be timezone-aware ISO 8601.

Columns without a recognised unit suffix (CLAUDE.md §2 rule 8) or a known identifier name only
produce a :class:`BundleWarning` (recorded in ``manifest["warnings"]``); ``strict=True`` turns
every warning into an error.

The bundle is written to a temporary sibling folder and renamed into place only after every
file and the manifest are complete, so a failed build never leaves a half-written release.
"""

from __future__ import annotations

import hashlib
import json
import numbers
import os
import re
import shutil
import subprocess
import uuid
import warnings
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from engine import ROOT, __version__

#: Tables defined by the contract (docs/18_PILAR2B_INTEGRATION.md §2).
CONTRACT_TABLES = (
    "facilities",
    "hex_supply",
    "mill_month",
    "lcob_results",
    "sites",
    "supply_curve",
)

#: Column names the contract lists per table (docs/18 §2). Missing ones -> warning only,
#: because the contract text is still a sketch (e.g. ``capacity``/``npv`` carry no unit).
CONTRACT_KEY_COLUMNS: dict[str, tuple[str, ...]] = {
    "facilities": ("cnpj", "name", "type", "geom"),
    "hex_supply": ("h3_index", "month", "residue", "unit"),
    "mill_month": ("cnpj", "month"),
    "lcob_results": ("site_id", "scenario", "strategy"),
    "sites": ("mode", "geom"),
    "supply_curve": ("scenario",),
}

#: Storage CRS of the project and of the contract (CLAUDE.md §3 "Spatial").
CONTRACT_CRS = "EPSG:4674"

#: Column names treated as geometry.
GEOMETRY_COLUMNS = ("geom", "geometry")

#: Default confidentiality blocklist: regular expressions searched (case-insensitive) in table
#: and column names. Short words are anchored on ``_`` boundaries so that e.g. ``calendar`` or
#: ``mandate`` do not match ``nda``.
DEFAULT_PRIVATE_COLUMN_PATTERNS: tuple[str, ...] = (
    r"private",
    r"confidential",
    r"proprietary",
    r"(^|_)partners?($|_)",
    r"(^|_)nda($|_)",
    r"(^|_)secret($|_)",
)

#: JSON Schema of ``manifest.json``.
MANIFEST_SCHEMA_PATH = ROOT / "templates" / "release_manifest_schema.json"
MANIFEST_FILENAME = "manifest.json"
MANIFEST_SCHEMA_VERSION = "0.1.0"
CONTRACT_REFERENCE = "docs/18_PILAR2B_INTEGRATION.md §2"

#: Unit tokens accepted as a column-name unit suffix (CLAUDE.md §2 rule 8). A column passes
#: when any token after the first one is in this set (``cane_t``, ``ch4_nm3_d``,
#: ``capex_brl_2025``, ``lcob_brl_nm3_p50``).
UNIT_TOKENS = frozenset(
    {
        # mass
        "g",
        "kg",
        "t",
        "kt",
        # volume
        "l",
        "ml",
        "m3",
        "nm3",
        # time (also as denominators: ch4_nm3_d)
        "s",
        "h",
        "d",
        "month",
        "yr",
        # energy and power
        "mj",
        "gj",
        "tj",
        "pj",
        "kwh",
        "mwh",
        "gwh",
        "twh",
        "mmbtu",
        "kw",
        "mw",
        "gw",
        # length, area, angle
        "m",
        "km",
        "m2",
        "km2",
        "ha",
        "deg",
        # money (pair with a price year: capex_brl_2025)
        "brl",
        "usd",
        "eur",
        # dimensionless
        "pct",
        "frac",
        "fraction",
        # composite units used in this project
        "kgvs",
        "kgcod",
        "kgdm",
        "tdm",
        "tfm",
        "m3d",
        "nm3d",
        # emissions, certificates, temperature, pressure, counts
        "gco2e",
        "kgco2e",
        "tco2e",
        "cbio",
        "degc",
        "bar",
        "count",
    }
)

#: Identifier / dimension columns that need no unit suffix.
KNOWN_DIMENSION_COLUMNS = frozenset(
    {
        "cnpj",
        "cnpj_root",
        "name",
        "type",
        "status",
        "status_by_year",
        "geom",
        "geometry",
        "h3_index",
        "month",
        "year",
        "date",
        "residue",
        "feedstock",
        "unit",
        "site_id",
        "scenario",
        "strategy",
        "mode",
        "run_id",
        "ibge_code",
        "municipality",
        "uf",
        "source_id",
        "confidence",
        "notes",
    }
)

_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HEX_HASH_RE = re.compile(r"^[0-9a-f]{8,64}$")
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")
_TABLE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SNAKE_COLUMN_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_STAT_SUFFIX_RE = re.compile(r"_(p\d{1,2}|mean|median|sd|std|min|max|low|high|lo|hi|central)$")
_STAT_COLUMN_RE = re.compile(r"^(p\d{1,2}|mean|median|sd|std|min|max|low|high|lo|hi|central)$")
_YEAR_SUFFIX_RE = re.compile(r"_(19|20)\d{2}$")
_CNPJ_RE = re.compile(r"[0-9]{14}")
# Same pattern as the manifest schema: extended ISO 8601 with seconds optional and an offset.
_CREATED_AT_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]+)?)?(Z|[+-][0-9]{2}:[0-9]{2})"
)


class BundleError(ValueError):
    """A release gate failed; the message lists every failed check."""


class BundleWarning(UserWarning):
    """Non-blocking gate finding (also recorded in ``manifest["warnings"]``)."""


# ---------------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------------


def release_dir(version: str, exports_root: Path | str = ROOT / "exports") -> Path:
    """Return the contract folder ``<exports_root>/v<version>`` (e.g. ``exports/v0.1.0``)."""
    _check_semver(version)
    return Path(exports_root) / f"v{version}"


def _check_semver(version: str) -> None:
    """Raise :class:`BundleError` unless ``version`` is Semantic Versioning 2.0.0."""
    if isinstance(version, str) and _SEMVER_RE.fullmatch(version):
        return
    hint = ""
    if str(version).startswith("v"):
        hint = " (drop the leading 'v'; it belongs to the tag/folder name)"
    raise BundleError(f"version {version!r} is not Semantic Versioning X.Y.Z{hint}")


def _git_head_commit(cwd: Path = ROOT) -> str | None:
    """Return ``git rev-parse HEAD`` (read-only) or ``None`` when git/the repo is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and _GIT_COMMIT_RE.fullmatch(commit) else None


def sha256_file(path: Path | str, chunk_bytes: int = 1 << 20) -> str:
    """Hex SHA-256 of a file, read in chunks of ``chunk_bytes`` bytes."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest_schema(path: Path | str = MANIFEST_SCHEMA_PATH) -> dict[str, Any]:
    """Load the manifest JSON Schema."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def manifest_schema_errors(
    manifest: Mapping[str, Any], schema_path: Path | str = MANIFEST_SCHEMA_PATH
) -> list[str]:
    """Return JSON-Schema (draft 2020-12) violations of ``manifest`` as readable strings."""
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(
        load_manifest_schema(schema_path), format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    errors = sorted(validator.iter_errors(manifest), key=lambda e: [str(p) for p in e.path])
    return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


def column_unit_ok(column: str, table_has_unit_column: bool = False) -> bool:
    """True when ``column`` carries a recognised unit suffix or is a known identifier.

    Rules: names in :data:`KNOWN_DIMENSION_COLUMNS`; identifier patterns (``*_id``,
    ``*_code``, ``*_name``, ``*_index``, ``*_date``, ``*_year``, ``is_*``, ``has_*``,
    ``n_*``); otherwise strip a statistic suffix (``_p05``, ``_p50``, ``_mean``, ``_low``...)
    and a price-year suffix (``_2025``) and require a token from :data:`UNIT_TOKENS` after the
    first token. Bare statistic columns (``p05``, ``p50``...) pass only when the table has a
    ``unit`` column (long format, e.g. ``hex_supply``).
    """
    name = column.lower()
    if name in KNOWN_DIMENSION_COLUMNS:
        return True
    if name.endswith(("_id", "_code", "_name", "_index", "_date", "_year")):
        return True
    if name.startswith(("is_", "has_", "n_")):
        return True
    if _STAT_COLUMN_RE.fullmatch(name):
        return table_has_unit_column
    name = _STAT_SUFFIX_RE.sub("", name)
    name = _YEAR_SUFFIX_RE.sub("", name)
    tokens = name.split("_")
    return any(tok in UNIT_TOKENS for tok in tokens[1:])


def _is_valid_h3(value: Any) -> bool:
    import h3

    try:
        if isinstance(value, numbers.Integral) and not isinstance(value, bool):
            cell = h3.int_to_str(int(value))
        else:
            cell = str(value)
        return bool(h3.is_valid_cell(cell))
    except (TypeError, ValueError):
        return False


def _load_registry_sources(sources_path: Path | str) -> dict[str, dict]:
    from engine.registry import load_sources

    return {
        str(s.get("id")): s
        for s in load_sources(sources_path)
        if isinstance(s, dict) and s.get("id")
    }


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


# ---------------------------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------------------------


def _check_table(
    name: str,
    df: Any,
    *,
    allow_extra: bool,
    patterns: Sequence[re.Pattern[str]],
    crs: str | None,
    scenarios: Sequence[str],
    errors: list[str],
    warns: list[str],
) -> None:
    """Run every per-table gate, appending messages to ``errors`` / ``warns``."""
    if not isinstance(name, str) or not _TABLE_NAME_RE.fullmatch(name):
        errors.append(f"table name {name!r} must be snake_case ([a-z][a-z0-9_]*)")
        return
    if name not in CONTRACT_TABLES and not allow_extra:
        errors.append(
            f"table {name!r} is not in the contract ({', '.join(CONTRACT_TABLES)}); "
            "pass allow_extra=True to export it anyway"
        )
    for pat in patterns:
        if pat.search(name):
            errors.append(f"table name {name!r} matches confidentiality pattern {pat.pattern!r}")
    if not isinstance(df, pd.DataFrame):
        errors.append(f"table {name!r} is a {type(df).__name__}, not a pandas DataFrame")
        return
    for flag in ("private", "confidential"):
        if df.attrs.get(flag):
            errors.append(f"table {name!r} is flagged attrs[{flag!r}]=True and cannot be exported")
    if any(level_name is not None for level_name in df.index.names):
        errors.append(
            f"table {name!r} has a named index {list(df.index.names)!r}; call reset_index() so "
            "the index becomes a column (the positional index is not exported)"
        )

    columns = list(df.columns)
    if not columns:
        errors.append(f"table {name!r} has no columns")
    non_str = [c for c in columns if not isinstance(c, str) or not c]
    if non_str:
        errors.append(f"table {name!r}: column names must be non-empty strings, got {non_str!r}")
        return
    dupes = sorted({c for c in columns if columns.count(c) > 1})
    if dupes:
        errors.append(f"table {name!r}: duplicate column name(s) {dupes!r}")
    for col in columns:
        for pat in patterns:
            if pat.search(col):
                errors.append(
                    f"table {name!r}: column {col!r} matches confidentiality pattern "
                    f"{pat.pattern!r}"
                )
    if df.empty:
        warns.append(f"table {name!r} has 0 rows")

    has_unit_col = "unit" in columns
    for col in columns:
        if not _SNAKE_COLUMN_RE.fullmatch(col):
            warns.append(f"table {name!r}: column {col!r} is not lower snake_case")
        if not column_unit_ok(col, has_unit_col):
            warns.append(
                f"table {name!r}: column {col!r} has no recognised unit suffix "
                "(e.g. _t, _nm3_d, _brl_2025, _frac) and is not a known id column"
            )
    missing_keys = [c for c in CONTRACT_KEY_COLUMNS.get(name, ()) if c not in columns]
    if missing_keys:
        warns.append(f"table {name!r}: contract column(s) missing: {', '.join(missing_keys)}")

    geom_cols = [c for c in columns if c in GEOMETRY_COLUMNS]
    if geom_cols:
        if crs is None:
            errors.append(
                f"table {name!r} has geometry column(s) {geom_cols!r}: pass crs={CONTRACT_CRS!r}"
            )
        table_crs = df.attrs.get("crs")
        if table_crs is not None and str(table_crs).upper() != CONTRACT_CRS:
            errors.append(
                f"table {name!r} declares attrs['crs']={table_crs!r}; reproject to {CONTRACT_CRS}"
            )

    if "scenario" in columns:
        found = {str(v) for v in df["scenario"].dropna().unique()}
        undeclared = sorted(found - set(scenarios))
        if undeclared:
            errors.append(
                f"table {name!r}: scenario value(s) {undeclared!r} are not declared in scenarios"
            )
    if "h3_index" in columns:
        cells = df["h3_index"]
        bad = [v for v in cells if pd.isna(v) or not _is_valid_h3(v)]
        if bad:
            errors.append(
                f"table {name!r}: {len(bad)} invalid/missing H3 cell(s) in h3_index, "
                f"e.g. {bad[0]!r}"
            )
    if "cnpj" in columns:
        values = df["cnpj"].dropna()
        bad_cnpj = [v for v in values if not (isinstance(v, str) and _CNPJ_RE.fullmatch(v))]
        if bad_cnpj:
            warns.append(
                f"table {name!r}: {len(bad_cnpj)} cnpj value(s) are not 14-digit strings "
                f"(store zero-padded text), e.g. {bad_cnpj[0]!r}"
            )


def _check_run_metadata(
    *,
    run_id: str,
    created_at: str,
    git_commit: str | None,
    params_hash: str,
    sources_used: Sequence[str],
    scenarios: Sequence[str],
    crs: str | None,
    errors: list[str],
) -> None:
    if not isinstance(run_id, str) or not _RUN_ID_RE.fullmatch(run_id):
        errors.append(f"run_id {run_id!r} must match {_RUN_ID_RE.pattern}")
    try:
        parsed = datetime.fromisoformat(created_at)
    except (TypeError, ValueError):
        errors.append(f"created_at {created_at!r} is not an ISO 8601 timestamp")
    else:
        if parsed.tzinfo is None or not _CREATED_AT_RE.fullmatch(created_at):
            errors.append(
                f"created_at {created_at!r} must be a full timestamp with a UTC offset "
                "(e.g. 2026-10-04T12:00:00+00:00)"
            )
    if git_commit is not None and not _GIT_COMMIT_RE.fullmatch(str(git_commit)):
        errors.append(f"git_commit {git_commit!r} is not a 7-40 character lower-case hex sha")
    if not isinstance(params_hash, str) or not _HEX_HASH_RE.fullmatch(params_hash):
        errors.append(
            f"params_hash {params_hash!r} must be 8-64 lower-case hex characters "
            "(use engine.registry.param_hash())"
        )
    for label, items in (("sources_used", sources_used), ("scenarios", scenarios)):
        if isinstance(items, str) or not isinstance(items, Sequence):
            errors.append(f"{label} must be a list of strings, got {type(items).__name__}")
            continue
        bad = [x for x in items if not isinstance(x, str) or not x.strip()]
        if bad:
            errors.append(f"{label} contains empty/non-string item(s): {bad!r}")
        dupes = sorted({x for x in items if isinstance(x, str) and list(items).count(x) > 1})
        if dupes:
            errors.append(f"{label} contains duplicates: {dupes!r}")
    if crs is not None and crs != CONTRACT_CRS:
        errors.append(f"crs {crs!r} is not the contract CRS {CONTRACT_CRS!r}")


def _check_sources(
    sources_used: Sequence[str],
    sources_path: Path | str | None,
    errors: list[str],
    warns: list[str],
) -> dict[str, dict[str, str | None]]:
    """Check ``sources_used`` against ``sources.yaml``; return ``{id: {accessed, sha256}}``."""
    if isinstance(sources_used, str) or not isinstance(sources_used, Sequence):
        return {}  # already reported by _check_run_metadata
    if not sources_used:
        return {}
    if sources_path is None:
        from engine.registry import SOURCES_YAML

        sources_path = SOURCES_YAML
    try:
        registry = _load_registry_sources(sources_path)
    except (OSError, ValueError, AttributeError, yaml.YAMLError) as exc:
        errors.append(f"cannot read sources registry {sources_path}: {exc}")
        return {}
    versions: dict[str, dict[str, str | None]] = {}
    for sid in sources_used:
        entry = registry.get(sid)
        if entry is None:
            errors.append(f"source {sid!r} is not registered in {sources_path}")
            continue
        versions[sid] = {
            "accessed": _text_or_none(entry.get("accessed")),
            "sha256": _text_or_none(entry.get("sha256")),
        }
        if "confidential" in str(entry.get("access", "")).lower():
            warns.append(
                f"source {sid!r} has access 'confidential': confirm the exported tables are "
                "aggregated (CLAUDE.md §2 rule 6)"
            )
    return versions


# ---------------------------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------------------------


def _csv_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Copy of ``df`` with bytes values (e.g. WKB geometry) written as lower-case hex text."""
    out = df.copy()
    for col in out.columns:
        if (
            out[col].dtype == object
            and out[col].map(lambda v: isinstance(v, bytes | bytearray)).any()
        ):
            out[col] = out[col].map(lambda v: v.hex() if isinstance(v, bytes | bytearray) else v)
    return out


def _write_table(name: str, df: pd.DataFrame, folder: Path) -> list[dict[str, Any]]:
    """Write ``df`` as Parquet and CSV in ``folder``; return the two manifest file entries."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    try:
        arrow_table = pa.Table.from_pandas(df, preserve_index=False)
    except (pa.ArrowInvalid, pa.ArrowTypeError, pa.ArrowNotImplementedError) as exc:
        raise BundleError(f"table {name!r} cannot be converted to Parquet: {exc}") from exc
    parquet_path = folder / f"{name}.parquet"
    csv_path = folder / f"{name}.csv"
    pq.write_table(arrow_table, parquet_path)
    _csv_frame(df).to_csv(csv_path, index=False, lineterminator="\n", encoding="utf-8")

    columns = [
        {"name": str(col), "dtype": str(df[col].dtype), "arrow_type": str(field.type)}
        for col, field in zip(df.columns, arrow_table.schema, strict=True)
    ]
    geometry = [c for c in df.columns if c in GEOMETRY_COLUMNS]
    entries = []
    for fmt, path in (("parquet", parquet_path), ("csv", csv_path)):
        entries.append(
            {
                "table": name,
                "format": fmt,
                "path": path.name,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "rows": int(len(df)),
                "columns": columns,
                "geometry_columns": geometry,
            }
        )
    return entries


def build_bundle(
    tables: Mapping[str, pd.DataFrame],
    out_dir: Path | str,
    *,
    version: str,
    run_id: str,
    params_hash: str,
    sources_used: Sequence[str],
    scenarios: Sequence[str],
    created_at: str | None = None,
    git_commit: str | None = None,
    crs: str | None = None,
    private_columns_blocklist: Sequence[str] = DEFAULT_PRIVATE_COLUMN_PATTERNS,
    allow_extra: bool = False,
    strict: bool = False,
    overwrite: bool = False,
    sources_path: Path | str | None = None,
    schema_path: Path | str = MANIFEST_SCHEMA_PATH,
) -> dict[str, Any]:
    """Write a release bundle and return its manifest.

    Args:
        tables: ``{table_name: DataFrame}``; names from :data:`CONTRACT_TABLES` unless
            ``allow_extra``. Column names should carry units (``cane_t``, ``lcob_brl_nm3``).
        out_dir: bundle folder to create (convention: :func:`release_dir`, ``exports/vX.Y.Z``).
            It must not exist (releases are immutable) unless ``overwrite=True`` and the folder
            is empty or an earlier bundle (contains ``manifest.json``).
        version: Semantic Version ``X.Y.Z[-pre][+build]`` without a leading ``v``.
        run_id: run identifier (``[A-Za-z0-9][A-Za-z0-9._:-]*``, at most 128 characters).
        params_hash: :func:`engine.registry.param_hash` of the run's parameter set.
        sources_used: ids of ``registry/sources.yaml`` entries the tables derive from.
        scenarios: scenario names; every ``scenario`` column value must be declared here.
        created_at: ISO 8601 timestamp with UTC offset. Pass it explicitly for reproducible
            manifests; ``None`` -> ``datetime.now(UTC)`` (second precision).
        git_commit: engine commit sha; ``None`` -> read-only ``git rev-parse HEAD`` in the
            repository (``null`` in the manifest when that fails).
        crs: required (``"EPSG:4674"``) when any table has a ``geom``/``geometry`` column.
            Geometry values are not parsed: export WKB bytes (written as hex in the CSV) or WKT.
        private_columns_blocklist: regular expressions (case-insensitive ``re.search``) that
            table and column names must not match.
        allow_extra: allow tables outside the contract (listed in ``manifest["extra_tables"]``).
        strict: treat warnings (unit suffix, missing contract columns, ...) as errors.
        overwrite: replace an existing bundle folder (see ``out_dir``).
        sources_path: ``sources.yaml`` used to check ``sources_used`` and to record source
            versions (default: the registry file).
        schema_path: manifest JSON Schema (default: ``templates/release_manifest_schema.json``).

    Returns:
        The manifest dict, identical to the ``manifest.json`` written in ``out_dir``.

    Raises:
        BundleError: when any gate fails (the message lists all failures); nothing is written.
    """
    out_dir = Path(out_dir)
    errors: list[str] = []
    warns: list[str] = []

    _check_semver(version)
    if created_at is None:
        created_at = datetime.now(UTC).isoformat(timespec="seconds")
    if git_commit is None:
        git_commit = _git_head_commit()
    _check_run_metadata(
        run_id=run_id,
        created_at=created_at,
        git_commit=git_commit,
        params_hash=params_hash,
        sources_used=sources_used,
        scenarios=scenarios,
        crs=crs,
        errors=errors,
    )

    try:
        patterns = [re.compile(p, re.IGNORECASE) for p in private_columns_blocklist]
    except re.error as exc:
        raise BundleError(f"invalid private_columns_blocklist pattern: {exc}") from exc
    if not isinstance(tables, Mapping) or not tables:
        errors.append("tables must be a non-empty mapping {name: DataFrame}")
        tables = {}
    for name in sorted(tables, key=str):
        _check_table(
            name,
            tables[name],
            allow_extra=allow_extra,
            patterns=patterns,
            crs=crs,
            scenarios=list(scenarios) if not isinstance(scenarios, str) else [],
            errors=errors,
            warns=warns,
        )
    source_versions = _check_sources(sources_used, sources_path, errors, warns)

    if strict and warns:
        errors.extend(f"[strict] {w}" for w in warns)
    if out_dir.exists():
        if not overwrite:
            errors.append(
                f"{out_dir} already exists; releases are immutable — bump the version or pass "
                "overwrite=True"
            )
        elif not out_dir.is_dir() or (
            any(out_dir.iterdir()) and not (out_dir / MANIFEST_FILENAME).is_file()
        ):
            errors.append(
                f"{out_dir} exists and is not an empty folder or an earlier bundle; refusing to "
                "overwrite it"
            )
    if errors:
        raise BundleError("release gates failed:\n- " + "\n- ".join(errors))

    for message in warns:
        warnings.warn(message, BundleWarning, stacklevel=2)

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    # Sibling temp folder (same filesystem -> atomic rename); mkdir honours the umask, unlike
    # tempfile.mkdtemp which would leave the release folder readable by its owner only.
    tmp_dir = out_dir.parent / f".{out_dir.name}.tmp-{uuid.uuid4().hex}"
    tmp_dir.mkdir()
    try:
        files: list[dict[str, Any]] = []
        for name in sorted(tables):
            files.extend(_write_table(name, tables[name], tmp_dir))
        manifest: dict[str, Any] = {
            "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
            "contract": CONTRACT_REFERENCE,
            "engine": {"name": "sp-biomethane-engine", "version": __version__},
            "version": version,
            "run_id": run_id,
            "created_at": created_at,
            "git_commit": git_commit,
            "params_hash": params_hash,
            "sources_used": list(sources_used),
            "source_versions": source_versions,
            "scenarios": list(scenarios),
            "crs": crs,
            "extra_tables": sorted(n for n in tables if n not in CONTRACT_TABLES),
            "files": files,
            "warnings": warns,
        }
        schema_errors = manifest_schema_errors(manifest, schema_path)
        if schema_errors:
            raise BundleError(
                "manifest does not match the schema:\n- " + "\n- ".join(schema_errors)
            )
        (tmp_dir / MANIFEST_FILENAME).write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if out_dir.exists():
            shutil.rmtree(out_dir)
        os.replace(tmp_dir, out_dir)
    except BaseException:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise
    return manifest


# ---------------------------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------------------------


def _file_rows_and_columns(path: Path, fmt: str) -> tuple[int, list[str]]:
    if fmt == "parquet":
        import pyarrow.parquet as pq

        meta = pq.ParquetFile(path)
        return int(meta.metadata.num_rows), list(meta.schema_arrow.names)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return int(len(df)), [str(c) for c in df.columns]


def verify_bundle(
    bundle_dir: Path | str, schema_path: Path | str = MANIFEST_SCHEMA_PATH
) -> list[str]:
    """Re-check a bundle on disk against its ``manifest.json``.

    Checks: manifest present, valid JSON and schema-valid; every listed file exists inside the
    folder with the recorded SHA-256, byte size, row count and column names; no unlisted files.

    Args:
        bundle_dir: bundle folder (e.g. ``exports/v0.1.0``).
        schema_path: manifest JSON Schema.

    Returns:
        List of problems; empty when the bundle is intact.
    """
    bundle_dir = Path(bundle_dir)
    manifest_path = bundle_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return [f"{manifest_path} not found"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{manifest_path} is not valid JSON: {exc}"]
    problems = [f"manifest schema: {e}" for e in manifest_schema_errors(manifest, schema_path)]
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, list):
        return problems or ["manifest has no 'files' list"]

    listed = {MANIFEST_FILENAME}
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            problems.append(f"malformed file entry: {entry!r}")
            continue
        rel = entry["path"]
        path = bundle_dir / rel
        if Path(rel).name != rel:
            problems.append(f"{rel}: path must be a plain file name inside the bundle")
            continue
        listed.add(rel)
        if not path.is_file():
            problems.append(f"{rel}: missing")
            continue
        if sha256_file(path) != entry.get("sha256"):
            problems.append(f"{rel}: sha256 mismatch")
        if path.stat().st_size != entry.get("bytes"):
            problems.append(
                f"{rel}: size {path.stat().st_size} bytes != manifest {entry.get('bytes')}"
            )
        try:
            rows, names = _file_rows_and_columns(path, str(entry.get("format")))
        except Exception as exc:  # any read failure is a verification problem
            problems.append(f"{rel}: cannot be read: {exc}")
            continue
        if rows != entry.get("rows"):
            problems.append(f"{rel}: {rows} rows != manifest {entry.get('rows')}")
        expected = [c.get("name") for c in entry.get("columns", []) if isinstance(c, dict)]
        if names != expected:
            problems.append(f"{rel}: columns {names!r} != manifest {expected!r}")
    extra = sorted(p.name for p in bundle_dir.iterdir() if p.name not in listed)
    if extra:
        problems.append(f"unlisted file(s) in bundle: {', '.join(extra)}")
    return problems
