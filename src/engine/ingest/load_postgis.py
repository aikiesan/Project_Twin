"""Load the held datasets into the local PostGIS database (docs/27_POSTGIS_LOAD.md).

What is loaded:

- every map layer in ``src/engine/viz/layers.yaml`` (vector files, point CSVs and the tables
  behind choropleths);
- the key tables in ``src/engine/ingest/postgis_tables.yaml``.

Rules (CLAUDE.md §2–§3):

- **Registered only.** The ``source_id`` is the ``data/raw/<source_id>/`` folder. A file whose
  ``source_id`` is not in ``registry/sources.yaml`` is refused.
- **Naming.** ``<schema>.raw_<source_id>__<layer>``. Source column names are kept; unit suffixes
  belong in views. Columns added by the loader start with ``_``.
- **Private data stays private.** Files under ``data/private/``, and sources marked
  ``access: restricted``, go to schema ``private`` (owned by ``engine``, revoked from PUBLIC).
- **CRS.** Geometries are stored in EPSG:4674, with a GiST index; every table is ANALYZEd.
- **Load log.** One row per table in ``engine.load_log`` with the input files' sha256.
- **Idempotent.** A table is replaced only when its input hash changed (or with ``--force``).

CLI::

    uv run python -m engine.ingest.load_postgis --dry-run   # plan only, no database
    uv run python -m engine.ingest.load_postgis             # load what changed
    uv run python -m engine.ingest.load_postgis --force --only 'raw_mapbiomas_infra__*'

``DATABASE_URL`` is read from the environment or from ``.env`` at the repo root.
"""

from __future__ import annotations

import argparse
import fnmatch
import glob
import hashlib
import os
import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

from engine.ingest.inventory import sha256_file

PACKAGE_DIR = Path(__file__).parent
TABLES_YAML = PACKAGE_DIR / "postgis_tables.yaml"
LAYERS_YAML = PACKAGE_DIR.parent / "viz" / "layers.yaml"

STORAGE_CRS = "EPSG:4674"  # SIRGAS 2000 geographic (CLAUDE.md §3)
PUBLIC_SCHEMA = "engine"
PRIVATE_SCHEMA = "private"
LOG_TABLE = f"{PUBLIC_SCHEMA}.load_log"
MAX_IDENT_BYTES = 63  # PostgreSQL NAMEDATALEN - 1

#: Never loaded, whatever a config says (team decision 2026-10-04; same list as local_import).
DENY_SUBSTRINGS = ("harvex", "joel", "cp2b_maps_v3")

#: Shapefile sidecars hashed together with the ``.shp``.
SHAPEFILE_SIDECARS = (".shp", ".shx", ".dbf", ".prj", ".cpg")

LOG_DDL = f"""
CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
    table_name    text PRIMARY KEY,
    source_id     text NOT NULL,
    file_relpath  text NOT NULL,
    file_sha256   text NOT NULL,
    n_rows        bigint NOT NULL,
    crs           text,
    loaded_at_utc timestamptz NOT NULL,
    engine_commit text
)
"""

PRIVATE_DDL = (
    f"CREATE SCHEMA IF NOT EXISTS {PRIVATE_SCHEMA} AUTHORIZATION engine",
    f"REVOKE ALL ON SCHEMA {PRIVATE_SCHEMA} FROM PUBLIC",
    f"ALTER DEFAULT PRIVILEGES IN SCHEMA {PRIVATE_SCHEMA} REVOKE ALL ON TABLES FROM PUBLIC",
)


class UnregisteredSourceError(ValueError):
    """A table's ``source_id`` is not in ``registry/sources.yaml``."""


@dataclass
class TableSpec:
    """One table to load; ``paths`` are repo-relative (globs and ``/vsizip/`` allowed)."""

    source_id: str
    layer: str
    kind: str
    paths: list[str]
    options: dict = field(default_factory=dict)
    private: bool = False
    #: what the load log records: the declared path or glob (defaults to ``paths`` joined by ``;``)
    relpath: str = ""

    def __post_init__(self) -> None:
        self.relpath = self.relpath or ";".join(self.paths)

    @property
    def schema(self) -> str:
        return PRIVATE_SCHEMA if self.private else PUBLIC_SCHEMA

    @property
    def table(self) -> str:
        return table_name(self.source_id, self.layer)

    @property
    def qualified(self) -> str:
        return f"{self.schema}.{self.table}"


@dataclass
class LoadResult:
    """Outcome for one table: ``loaded``, ``skipped`` (hash unchanged) or ``failed``."""

    table: str
    status: str
    n_rows: int | None = None
    message: str = ""


# --------------------------------------------------------------------------------------
# naming and routing (pure, unit-tested)
# --------------------------------------------------------------------------------------
def slug(text: str) -> str:
    """Lower-case ASCII identifier: accents folded, other characters -> ``_``."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", ascii_text.lower())).strip("_")


def table_name(source_id: str, layer: str) -> str:
    """``raw_<source_id>__<layer>``; names over 63 bytes are cut and get a 6-hex hash suffix."""
    name = f"raw_{slug(source_id)}__{slug(layer)}"
    if len(name) <= MAX_IDENT_BYTES:
        return name
    digest = hashlib.sha256(name.encode()).hexdigest()[:6]
    return f"{name[: MAX_IDENT_BYTES - 7].rstrip('_')}_{digest}"


def strip_vsizip(path: str) -> str:
    return path.removeprefix("/vsizip/")


def source_id_from_path(path: str) -> str:
    """The ``<source_id>`` folder of ``data/{raw,private}/<source_id>/…``."""
    parts = Path(strip_vsizip(path).replace("\\", "/")).parts
    if len(parts) < 3 or parts[0] != "data" or parts[1] not in ("raw", "private"):
        raise ValueError(f"{path}: not under data/raw/<source_id>/ or data/private/<source_id>/")
    return parts[2]


def is_private_path(path: str) -> bool:
    return strip_vsizip(path).replace("\\", "/").startswith("data/private/")


def is_denied(path: str) -> bool:
    text = path.replace("\\", "/").lower()
    return any(s in text for s in DENY_SUBSTRINGS)


def route_private(spec: TableSpec, registry: dict[str, dict]) -> TableSpec:
    """Mark ``spec`` private if any input is under ``data/private/`` or its source is restricted."""
    entry = registry.get(spec.source_id) or {}
    spec.private = (
        spec.private
        or any(is_private_path(p) for p in spec.paths)
        or str(entry.get("access", "")).lower() == "restricted"
    )
    return spec


def check_registered(specs: Iterable[TableSpec], registry: dict[str, dict]) -> None:
    """Raise :class:`UnregisteredSourceError` listing every spec whose source is unregistered."""
    missing = sorted({s.source_id for s in specs if s.source_id not in registry})
    if missing:
        raise UnregisteredSourceError(
            "not in registry/sources.yaml (CLAUDE.md rule 3): " + ", ".join(missing)
        )


def needs_load(previous_sha: str | None, current_sha: str, table_exists: bool, force: bool) -> bool:
    """Idempotency rule: reload only on a hash change, a missing table, or ``force``."""
    return force or not table_exists or previous_sha != current_sha


# --------------------------------------------------------------------------------------
# config -> specs
# --------------------------------------------------------------------------------------
def expand_paths(repo: Path, patterns: Sequence[str]) -> list[str]:
    """Resolve globs to sorted repo-relative paths (``/vsizip/`` kept); skips ``__MACOSX`` junk."""
    out: list[str] = []
    for pattern in patterns:
        prefix = "/vsizip/" if pattern.startswith("/vsizip/") else ""
        rel = strip_vsizip(pattern)
        if glob.has_magic(rel):
            hits = sorted(
                Path(p).relative_to(repo).as_posix()
                for p in glob.glob(str(repo / rel))
                if "__MACOSX" not in p
            )
        else:
            hits = [rel]
        out.extend(prefix + h for h in hits)
    return out


def _spec(entry: dict, paths: list[str], layer: str | None = None, relpath: str = "") -> TableSpec:
    ids = {source_id_from_path(p) for p in paths}
    if len(ids) != 1:
        raise ValueError(f"{paths}: one table must come from one source folder, got {sorted(ids)}")
    source_id = ids.pop()
    declared = entry.get("source_id")
    if declared and declared != source_id:
        raise ValueError(f"{paths}: source_id {declared!r} does not match folder {source_id!r}")
    name = layer or entry.get("layer") or Path(strip_vsizip(paths[0])).stem
    options = {
        k: v for k, v in entry.items() if k not in ("kind", "paths", "path", "layer", "source_id")
    }
    return TableSpec(
        source_id=source_id,
        layer=name,
        kind=entry["kind"],
        paths=paths,
        options=options,
        relpath=relpath,
    )


def specs_from_tables(cfg: dict, repo: Path) -> list[TableSpec]:
    """Specs from ``postgis_tables.yaml``. A glob without ``layer`` gives one table per file."""
    specs: list[TableSpec] = []
    for entry in cfg.get("tables", []):
        paths = expand_paths(repo, entry["paths"])
        if not paths:
            raise FileNotFoundError(f"no file matches {entry['paths']}")
        if entry.get("layer") or len(paths) == 1:
            specs.append(_spec(entry, paths, relpath=";".join(entry["paths"])))
        else:
            specs.extend(_spec(entry, [p]) for p in paths)
    return specs


def specs_from_layers(cfg: dict) -> list[TableSpec]:
    """Specs for every viewer layer: its file, plus the table behind a choropleth.

    Viewer-only keys (colours, ``filter``, ``clip_sp``, ``simplify``) are ignored: raw tables keep
    every row. ``db_layer`` overrides the table's layer name.
    """
    specs: list[TableSpec] = []
    for lay in cfg.get("layers", []):
        enc = {"encoding": lay["encoding"]} if lay.get("encoding") else {}
        private = {"private": True} if lay.get("private") else {}
        if lay["kind"] == "points":
            entry = {"kind": "points", "lat": lay["lat"], "lon": lay["lon"], "sep": lay.get("sep")}
            specs.append(_spec({**entry, **enc}, [lay["path"]], lay.get("db_layer")))
        elif lay["kind"] == "choropleth":
            specs.append(_spec({"kind": "vector", **enc}, [lay["geometry"]], lay.get("db_layer")))
            if lay.get("table"):
                specs.append(_spec({"kind": "csv"}, [lay["table"]]))
        else:
            specs.append(_spec({"kind": "vector", **enc}, [lay["path"]], lay.get("db_layer")))
        if private:
            specs[-1].private = True
    return specs


def dedupe(specs: Iterable[TableSpec]) -> list[TableSpec]:
    """First spec per input-path set wins; two different inputs on one table name is an error."""
    by_paths: dict[tuple[str, ...], TableSpec] = {}
    by_name: dict[str, tuple[str, ...]] = {}
    for s in specs:
        key = tuple(s.paths)
        if key in by_paths:
            by_paths[key].private = by_paths[key].private or s.private
            continue
        if s.qualified in by_name and by_name[s.qualified] != key:
            raise ValueError(f"{s.qualified}: two different inputs map to the same table name")
        by_paths[key] = s
        by_name[s.qualified] = key
    return list(by_paths.values())


def plan(repo: Path, registry: dict[str, dict], *, include_private: bool = True) -> list[TableSpec]:
    """All specs (layers + key tables), deduplicated, routed and registry-checked."""
    tables_cfg = yaml.safe_load(TABLES_YAML.read_text(encoding="utf-8"))
    layers_cfg = yaml.safe_load(LAYERS_YAML.read_text(encoding="utf-8"))
    specs = dedupe([*specs_from_tables(tables_cfg, repo), *specs_from_layers(layers_cfg)])
    denied = [p for s in specs for p in s.paths if is_denied(p)]
    if denied:
        raise ValueError(f"denied paths in config (HARVEX/JOEL/LGPD): {denied}")
    check_registered(specs, registry)
    specs = [route_private(s, registry) for s in specs]
    return [s for s in specs if include_private or not s.private]


# --------------------------------------------------------------------------------------
# files
# --------------------------------------------------------------------------------------
def input_files(repo: Path, spec: TableSpec) -> list[Path]:
    """Every file that defines the table (shapefile sidecars included)."""
    files: list[Path] = []
    for p in spec.paths:
        path = repo / strip_vsizip(p)
        if path.suffix.lower() == ".shp":
            files.extend(
                path.with_suffix(ext)
                for ext in SHAPEFILE_SIDECARS
                if path.with_suffix(ext).exists()
            )
        else:
            files.append(path)
    return files


def inputs_sha256(repo: Path, spec: TableSpec) -> str:
    """sha256 of the single input file, or of the sorted ``relpath  sha256`` lines for several."""
    files = input_files(repo, spec)
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        raise FileNotFoundError(", ".join(missing))
    if len(files) == 1:
        return sha256_file(files[0])
    lines = sorted(f"{f.relative_to(repo).as_posix()}  {sha256_file(f)}\n" for f in files)
    return hashlib.sha256("".join(lines).encode()).hexdigest()


_DECIMAL_COMMA = re.compile(r"^-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$")


def convert_decimal_comma(df, keep_text: Sequence[str] = ()):
    """Text columns holding Brazilian numbers (``1.234,5``) -> float. Identifier-like columns
    (any value with a leading zero, e.g. CNPJ) and ``keep_text`` stay text."""
    import pandas as pd

    df = df.copy()
    for col in df.columns:
        if col in keep_text or not (
            df[col].dtype == object or pd.api.types.is_string_dtype(df[col])
        ):
            continue
        vals = df[col].dropna().astype(str).str.strip()
        vals = vals[vals != ""]
        if vals.empty or not vals.map(lambda v: bool(_DECIMAL_COMMA.match(v))).all():
            continue
        if vals.str.match(r"^-?0\d").any():
            continue
        num = df[col].astype(str).str.strip().str.replace(".", "", regex=False)
        df[col] = pd.to_numeric(num.str.replace(",", ".", regex=False), errors="coerce")
    return df


def read_spec(repo: Path, spec: TableSpec):
    """Read one spec into a (Geo)DataFrame; geometries reprojected to EPSG:4674."""
    import pandas as pd

    o = spec.options
    frames = []
    for p in spec.paths:
        full = repo / strip_vsizip(p)
        if spec.kind == "vector":
            import geopandas as gpd

            src = f"/vsizip/{full.as_posix()}" if p.startswith("/vsizip/") else str(full)
            df = gpd.read_file(src, **({"encoding": o["encoding"]} if o.get("encoding") else {}))
            if df.crs is None:
                raise ValueError(f"{p}: no CRS (.prj missing)")
            df = df.to_crs(STORAGE_CRS)
        elif spec.kind in ("csv", "points"):
            text = o.get("decimal_comma") or o.get("text_columns")
            df = pd.read_csv(
                full,
                sep=o.get("sep") or ",",
                encoding="utf-8-sig",
                dtype=str if text else None,
                low_memory=False,
            )
            if o.get("decimal_comma"):
                df = convert_decimal_comma(df, keep_text=o.get("text_columns", ()))
            elif text:
                keep = set(o.get("text_columns", ()))
                for col in df.columns.difference(list(keep)):
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        pass  # genuine text column
        elif spec.kind == "xlsx":
            df = pd.read_excel(full, sheet_name=o["sheet"])
        else:
            raise ValueError(f"unknown kind {spec.kind!r}")

        df = df.drop(columns=[c for c in o.get("drop_columns", []) if c in df.columns])
        for col, val in (o.get("filter") or {}).items():
            df = df[df[col].astype(str) == str(val)]
        for col in o.get("int_columns", []):
            df[col] = pd.to_numeric(df[col]).round().astype("Int64")
        if fc := o.get("filename_column"):
            m = re.search(fc["pattern"], Path(p).name)
            df[fc["name"]] = m.group(1) if m else None
        if len(spec.paths) > 1:
            df["_source_file"] = Path(strip_vsizip(p)).name
        frames.append(df)

    if spec.kind == "vector":
        import geopandas as gpd

        out = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=STORAGE_CRS)
    else:
        out = pd.concat(frames, ignore_index=True)
    if spec.kind == "points":
        import geopandas as gpd

        lon = pd.to_numeric(out[o["lon"]], errors="coerce")
        lat = pd.to_numeric(out[o["lat"]], errors="coerce")
        out = gpd.GeoDataFrame(out, geometry=gpd.points_from_xy(lon, lat), crs="EPSG:4326")
        out = out.to_crs(STORAGE_CRS)
    too_long = [c for c in out.columns if len(str(c).encode()) > MAX_IDENT_BYTES]
    if too_long:
        raise ValueError(f"column names over {MAX_IDENT_BYTES} bytes (would be cut): {too_long}")
    return out


# --------------------------------------------------------------------------------------
# database
# --------------------------------------------------------------------------------------
def database_url(repo: Path) -> str | None:
    """``DATABASE_URL`` from the environment, else from ``<repo>/.env``."""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    env = repo / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key.strip() == "DATABASE_URL":
                return value.strip().strip("'\"")
    return None


def engine_commit(repo: Path) -> str:
    def git(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=repo, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""

    commit = git("rev-parse", "--short", "HEAD")
    return f"{commit}+dirty" if commit and git("status", "--porcelain", "--", "src") else commit


def prepare_database(conn) -> None:
    """Create ``engine.load_log`` and the ``private`` schema (revoked from PUBLIC)."""
    from sqlalchemy import text

    conn.execute(text(LOG_DDL))
    for stmt in PRIVATE_DDL:
        conn.execute(text(stmt))


def _index_name(table: str, column: str) -> str:
    return "gix_" + hashlib.sha256(f"{table}.{column}".encode()).hexdigest()[:16]


def staging_name(qualified: str) -> str:
    """Short table name used while writing (geoalchemy2 names its index ``idx_<table>_<col>``,
    which would pass 63 bytes for long table names)."""
    return "_load_" + hashlib.sha256(qualified.encode()).hexdigest()[:12]


def write_table(conn, spec: TableSpec, df) -> str | None:
    """Write to a staging table, swap it in, add GiST indexes, ANALYZE. Returns the CRS or None."""
    from sqlalchemy import text

    tmp = staging_name(spec.qualified)
    is_geo = hasattr(df, "geometry") and getattr(df, "crs", None) is not None
    if is_geo:
        df.to_postgis(tmp, conn, schema=spec.schema, if_exists="replace", index=False)
    else:
        df.to_sql(tmp, conn, schema=spec.schema, if_exists="replace", index=False, chunksize=5000)
    conn.execute(text(f"DROP TABLE IF EXISTS {spec.qualified} CASCADE"))
    conn.execute(text(f'ALTER TABLE {spec.schema}."{tmp}" RENAME TO {spec.table}'))
    if is_geo:
        for col in df.columns[df.dtypes == "geometry"]:
            conn.execute(text(f'DROP INDEX IF EXISTS {spec.schema}."idx_{tmp}_{col}"'))
            conn.execute(
                text(
                    f"CREATE INDEX {_index_name(spec.qualified, col)} "
                    f'ON {spec.qualified} USING GIST ("{col}")'
                )
            )
    conn.execute(text(f"ANALYZE {spec.qualified}"))
    return STORAGE_CRS if is_geo else None


def load_all(
    db, repo: Path, specs: Sequence[TableSpec], *, force: bool = False
) -> list[LoadResult]:
    """Load every spec in its own transaction; one failure does not stop the others."""
    from sqlalchemy import inspect, text

    with db.begin() as conn:
        prepare_database(conn)
    commit = engine_commit(repo)
    results: list[LoadResult] = []
    for spec in specs:
        try:
            sha = inputs_sha256(repo, spec)
            with db.connect() as conn:
                prev = conn.execute(
                    text(f"SELECT file_sha256, n_rows FROM {LOG_TABLE} WHERE table_name = :t"),
                    {"t": spec.qualified},
                ).first()
                exists = inspect(conn).has_table(spec.table, schema=spec.schema)
            if not needs_load(prev[0] if prev else None, sha, exists, force):
                results.append(LoadResult(spec.qualified, "skipped", prev[1], "hash unchanged"))
                continue
            df = read_spec(repo, spec)
            with db.begin() as conn:
                crs = write_table(conn, spec, df)
                conn.execute(
                    text(f"DELETE FROM {LOG_TABLE} WHERE table_name = :t"), {"t": spec.qualified}
                )
                conn.execute(
                    text(
                        f"INSERT INTO {LOG_TABLE} (table_name, source_id, file_relpath, "
                        "file_sha256, n_rows, crs, loaded_at_utc, engine_commit) VALUES "
                        "(:t, :s, :p, :h, :n, :c, :ts, :g)"
                    ),
                    {
                        "t": spec.qualified,
                        "s": spec.source_id,
                        "p": spec.relpath,
                        "h": sha,
                        "n": len(df),
                        "c": crs,
                        "ts": datetime.now(tz=UTC),
                        "g": commit,
                    },
                )
            results.append(LoadResult(spec.qualified, "loaded", len(df)))
        except Exception as exc:  # noqa: BLE001 - report the failure, keep loading the rest
            results.append(
                LoadResult(spec.qualified, "failed", message=f"{type(exc).__name__}: {exc}")
            )
    return results


def report(results: Sequence[LoadResult]) -> str:
    """Plain-text table of results plus totals."""
    width = max((len(r.table) for r in results), default=10)
    lines = [f"{'table':<{width}}  {'status':<7}  {'rows':>9}  note"]
    for r in results:
        rows = "" if r.n_rows is None else f"{r.n_rows:,}"
        lines.append(f"{r.table:<{width}}  {r.status:<7}  {rows:>9}  {r.message}")
    ok = [r for r in results if r.status != "failed"]
    lines.append(
        f"{len(ok)} tables ok ({sum(r.n_rows or 0 for r in ok):,} rows), "
        f"{len(results) - len(ok)} failed"
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point; returns 1 if any table failed."""
    ap = argparse.ArgumentParser(
        prog="python -m engine.ingest.load_postgis", description=__doc__.split("\n\n")[0]
    )
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--database-url", help="default: $DATABASE_URL or DATABASE_URL in .env")
    ap.add_argument("--force", action="store_true", help="reload even when the hash is unchanged")
    ap.add_argument("--only", action="append", help="fnmatch on table name (repeatable)")
    ap.add_argument("--no-private", action="store_true", help="skip data/private and restricted")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, touch no database")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows consoles: cp1252

    from engine.registry import load_sources

    repo = args.repo.resolve()
    registry = {s["id"]: s for s in load_sources(repo / "registry" / "sources.yaml")}
    specs = plan(repo, registry, include_private=not args.no_private)
    if args.only:
        specs = [s for s in specs if any(fnmatch.fnmatch(s.table, pat) for pat in args.only)]

    if args.dry_run:
        for s in specs:
            print(f"{s.qualified:<70} {s.kind:<7} {s.relpath}")
        print(f"{len(specs)} tables planned ({sum(s.private for s in specs)} private)")
        return 0

    url = args.database_url or database_url(repo)
    if not url:
        print("DATABASE_URL is not set (environment or .env)", file=sys.stderr)
        return 2
    from sqlalchemy import create_engine

    db = create_engine(url)
    results = load_all(db, repo, specs, force=args.force)
    print(report(results))
    return 1 if any(r.status == "failed" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
