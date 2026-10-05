"""Copy the PILAR-2b research tables from the local NewLook database into schema ``pilar2b``.

Source: the NewLook docker stack (``Pilar2b/cp2b-workspace/NewLook``), container ``cp2b-db-dev``,
database ``cp2b_maps``, schema ``public``. Target: this project's PostGIS (compose service
``db``), schema ``pilar2b`` (docs/04 §6, docs/19 Phase 0, docs/27 §PILAR-2b).

Rules:

- **Read-only on the source.** Only ``pg_dump`` and catalogue queries run there.
- **No personal data.** Excluded: the fixed list :data:`EXCLUDE_TABLES` (users, auth, leads,
  subscribers, analytics, audit log), every table with a column matching
  :data:`PERSONAL_COLUMN_RE`, backup tables, and every view that reads an excluded relation.
  The other schemas (``auth``, ``storage``, ``realtime``, ``staging``, ``tiger``) are never
  dumped.
- **Data, not behaviour.** Functions, triggers, RLS policies, publications and foreign keys
  to schemas that are not copied are dropped from the restore list.
- **Safe swap.** The archive is restored into ``public`` of the target in one transaction (it
  must hold no relations of its own), then every restored relation is moved to ``pilar2b``.
  ``pilar2b`` must be empty unless ``--replace`` is given.
- **Logged.** One row per table in ``engine.load_log`` (source ``pilar2b_platform_db``, the
  dump's sha256), so the viewer's Database card lists them.

CLI::

    uv run python -m engine.ingest.restore_pilar2b --dry-run     # plan: what is copied, what not
    uv run python -m engine.ingest.restore_pilar2b               # dump, restore, move, log
    uv run python -m engine.ingest.restore_pilar2b --replace     # refresh an existing copy
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from engine.ingest.inventory import sha256_file
from engine.ingest.load_postgis import LOG_DDL, LOG_TABLE, engine_commit

SOURCE_ID = "pilar2b_platform_db"
TARGET_SCHEMA = "pilar2b"

#: Tables never copied, whatever their columns (accounts, leads, logs, migrations, scratch).
EXCLUDE_TABLES = frozenset(
    {
        "audit_log",
        "analytics_pageviews",
        "analysis_results",
        "auth_access_log",
        "auth_token_denylist",
        "auth_users",
        "calculator_leads",
        "newsletter_subscribers",
        "user_preferences",
        "user_profiles",
        "user_routes",
        "schema_migrations",
        "missing_doi_lookup",
        "spatial_ref_sys",  # PostGIS catalogue, already in the target
    }
)

#: Column names that suggest personal data: a table holding one is excluded.
PERSONAL_COLUMN_RE = re.compile(
    r"(e_?mail|phone|telefone|celular|cpf|whatsapp|contato|contact|user|usuario|ip_?addr|^ip$|"
    r"session|token|password|senha|endereco|address|^cep$|full_name|first_name|last_name)",
    re.IGNORECASE,
)

#: pg_restore list entries never restored (behaviour, security, extension objects).
DROP_TOC_DESCS = frozenset(
    {
        "FUNCTION",
        "PROCEDURE",
        "AGGREGATE",
        "TRIGGER",
        "EVENT TRIGGER",
        "POLICY",
        "ROW SECURITY",
        "PUBLICATION",
        "PUBLICATION TABLE",
        "EXTENSION",
        "SCHEMA",
        "ACL",
        "DEFAULT ACL",
    }
)
_COMMENT_ON_DROPPED = ("FUNCTION ", "PROCEDURE ", "TRIGGER ", "EXTENSION ", "SCHEMA ", "POLICY ")
_TOC_LINE = re.compile(
    r"^\s*\d+;\s*\d+\s+\d+\s+(?P<desc>(?:[A-Z]+ )*[A-Z]+)\s+(?P<schema>-|[a-z_][a-z0-9_]*)\s+"
    r"(?P<rest>.*)$"
)


@dataclass
class Plan:
    """What the dump keeps and leaves out, with the reason for each exclusion."""

    tables: list[str]
    views: list[str]
    excluded: dict[str, str]
    dropped_fks: list[str]


# --------------------------------------------------------------------------------------
# pure planning (unit-tested)
# --------------------------------------------------------------------------------------
def is_backup(name: str) -> bool:
    return "backup" in name.lower()


def choose_exclusions(
    table_columns: dict[str, list[str]],
    view_reads: dict[str, set[str]],
    view_functions: dict[str, set[str]] | None = None,
    sequence_owner: dict[str, str] | None = None,
) -> dict[str, str]:
    """``{relation: reason}`` for tables to leave out and every view that depends on one.

    ``view_reads`` maps each view (or materialized view) to the public relations it reads;
    dependencies are followed transitively (a view over an excluded view is excluded).
    ``view_functions`` maps views to the non-extension functions they call: functions are not
    restored, so those views are left out too. ``sequence_owner`` maps sequences to the table
    that owns them: an excluded table's sequence is excluded (its value counts the rows).
    """
    out: dict[str, str] = {}
    for view, funcs in (view_functions or {}).items():
        if funcs:
            out[view] = "calls function(s) not restored: " + ", ".join(sorted(funcs))
    for table, cols in table_columns.items():
        personal = [c for c in cols if PERSONAL_COLUMN_RE.search(c)]
        if table in EXCLUDE_TABLES:
            out[table] = "listed (accounts, leads, logs or catalogue)"
        elif personal:
            out[table] = "personal-looking column(s): " + ", ".join(personal)
        elif is_backup(table):
            out[table] = "backup table"
    changed = True
    while changed:
        changed = False
        for view, reads in view_reads.items():
            hit = sorted(r for r in reads if r in out)
            if view not in out and hit:
                out[view] = "reads excluded " + ", ".join(hit)
                changed = True
    for seq, owner in (sequence_owner or {}).items():
        if owner in out:
            out[seq] = f"sequence of excluded {owner}"
    return out


def fks_to_drop(fks: Iterable[tuple[str, str, str]], kept_tables: Iterable[str]) -> list[str]:
    """Names of FK constraints whose target is not copied (another schema or an excluded table).

    ``fks`` holds ``(constraint, target_schema, target_table)`` for the public tables.
    """
    kept = set(kept_tables)
    return sorted({name for name, schema, table in fks if schema != "public" or table not in kept})


def filter_toc(lines: Iterable[str], drop_constraints: Iterable[str] = ()) -> list[str]:
    """Drop behaviour/security entries and the named FK constraints from a ``pg_restore -l``."""
    drop_fk = set(drop_constraints)
    kept: list[str] = []
    for line in lines:
        m = _TOC_LINE.match(line)
        if not m:
            kept.append(line)  # comments and blank lines
            continue
        desc, rest = m["desc"], m["rest"]
        if desc in DROP_TOC_DESCS:
            continue
        if desc == "COMMENT" and rest.startswith(_COMMENT_ON_DROPPED):
            continue
        if desc == "FK CONSTRAINT" and len(rest.split()) >= 2 and rest.split()[1] in drop_fk:
            continue
        kept.append(line)
    return kept


MOVE_SQL = f"""
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT c.relname, c.relkind FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm', 'S')
      AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = c.oid AND d.deptype = 'e')
      AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = c.oid AND d.deptype IN ('a', 'i')
                      AND c.relkind = 'S')
    ORDER BY CASE c.relkind WHEN 'r' THEN 0 WHEN 'p' THEN 0 WHEN 'S' THEN 1 ELSE 2 END
  LOOP
    EXECUTE format(
      'ALTER %s public.%I SET SCHEMA {TARGET_SCHEMA}',
      CASE r.relkind WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED VIEW'
                     WHEN 'S' THEN 'SEQUENCE' ELSE 'TABLE' END,
      r.relname);
  END LOOP;
END $$;
"""

#: Non-extension relations in ``public`` of the target (must be 0 before a restore).
PUBLIC_RELATIONS_SQL = """
SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm', 'S')
  AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = c.oid AND d.deptype = 'e')
"""


# --------------------------------------------------------------------------------------
# docker / psql helpers
# --------------------------------------------------------------------------------------
@dataclass
class Db:
    """A PostgreSQL database reached through ``docker exec`` (local socket, no password)."""

    container: str
    dbname: str
    user: str

    def psql(self, sql: str, *, check: bool = True) -> list[list[str]]:
        """Run ``sql``; return rows of tab-separated fields."""
        res = subprocess.run(
            ["docker", "exec", "-i", self.container, "psql", "-U", self.user, "-d", self.dbname,
             "-v", "ON_ERROR_STOP=1", "-qAtX", "-F", "\t", "-f", "-"],
            input=sql, capture_output=True, text=True, encoding="utf-8",
        )  # fmt: skip
        if check and res.returncode != 0:
            raise RuntimeError(f"psql on {self.container} failed: {res.stderr.strip()}")
        return [line.split("\t") for line in res.stdout.splitlines() if line]


def source_catalogue(
    src: Db,
) -> tuple[
    dict[str, list[str]],
    dict[str, set[str]],
    dict[str, set[str]],
    list[tuple[str, str, str]],
    dict[str, str],
]:
    """Public tables with their columns, views with the relations and functions they use, and
    the FKs of public tables as ``(constraint, target schema, target table)``, and the owning
    table of each sequence."""
    cols: dict[str, list[str]] = {}
    for table, col in src.psql(
        "SELECT c.relname, a.attname FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = 'public' "
        "JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped "
        "WHERE c.relkind IN ('r', 'p') ORDER BY 1, a.attnum"
    ):
        cols.setdefault(table, []).append(col)
    views: dict[str, set[str]] = {}
    for view, read in src.psql(
        "SELECT DISTINCT v.relname, t.relname FROM pg_class v "
        "JOIN pg_namespace vn ON vn.oid = v.relnamespace AND vn.nspname = 'public' "
        "JOIN pg_rewrite r ON r.ev_class = v.oid "
        "JOIN pg_depend d ON d.objid = r.oid AND d.classid = 'pg_rewrite'::regclass "
        "JOIN pg_class t ON t.oid = d.refobjid AND t.oid <> v.oid "
        "JOIN pg_namespace tn ON tn.oid = t.relnamespace AND tn.nspname = 'public' "
        "WHERE v.relkind IN ('v', 'm')"
    ):
        views.setdefault(view, set()).add(read)
    for (view,) in src.psql(
        "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relkind IN ('v', 'm') AND NOT EXISTS "
        "(SELECT 1 FROM pg_depend d WHERE d.objid = c.oid AND d.deptype = 'e')"
    ):
        views.setdefault(view, set())
    funcs: dict[str, set[str]] = {}
    for view, func in src.psql(
        "SELECT DISTINCT v.relname, p.proname FROM pg_class v "
        "JOIN pg_namespace vn ON vn.oid = v.relnamespace AND vn.nspname = 'public' "
        "JOIN pg_rewrite r ON r.ev_class = v.oid "
        "JOIN pg_depend d ON d.objid = r.oid AND d.classid = 'pg_rewrite'::regclass "
        "AND d.refclassid = 'pg_proc'::regclass "
        "JOIN pg_proc p ON p.oid = d.refobjid "
        "WHERE NOT EXISTS (SELECT 1 FROM pg_depend e WHERE e.objid = p.oid AND e.deptype = 'e') "
        "AND p.pronamespace <> 'pg_catalog'::regnamespace"
    ):
        funcs.setdefault(view, set()).add(func)
    fks = [
        (r[0], r[1], r[2])
        for r in src.psql(
            "SELECT con.conname, tn.nspname, t.relname FROM pg_constraint con "
            "JOIN pg_class t ON t.oid = con.confrelid "
            "JOIN pg_namespace tn ON tn.oid = t.relnamespace "
            "WHERE con.contype = 'f' AND con.connamespace = 'public'::regnamespace"
        )
    ]
    owners = {
        r[0]: r[1]
        for r in src.psql(
            "SELECT s.relname, t.relname FROM pg_class s "
            "JOIN pg_depend d ON d.objid = s.oid AND d.deptype IN ('a', 'i') "
            "AND d.refclassid = 'pg_class'::regclass "
            "JOIN pg_class t ON t.oid = d.refobjid "
            "WHERE s.relkind = 'S' AND s.relnamespace = 'public'::regnamespace"
        )
    }
    return cols, views, funcs, fks, owners


def make_plan(src: Db) -> Plan:
    cols, views, funcs, fks, owners = source_catalogue(src)
    excluded = choose_exclusions(cols, views, funcs, owners)
    tables = sorted(t for t in cols if t not in excluded)
    return Plan(
        tables=tables,
        views=sorted(v for v in views if v not in excluded),
        excluded=dict(sorted(excluded.items())),
        dropped_fks=fks_to_drop(fks, tables),
    )


def run(cmd: Sequence[str], **kwargs) -> subprocess.CompletedProcess:
    res = subprocess.run(list(cmd), capture_output=True, **kwargs)
    if res.returncode != 0:
        err = res.stderr.decode("utf-8", "replace") if isinstance(res.stderr, bytes) else res.stderr
        err = err.strip()
        short = err if len(err) <= 1500 else err[:1000] + "\n…\n" + err[-400:]
        raise RuntimeError(f"{' '.join(cmd[:4])} ... failed: {short}")
    return res


# --------------------------------------------------------------------------------------
# the restore
# --------------------------------------------------------------------------------------
def dump(src: Db, plan: Plan, out: Path) -> Path:
    """``pg_dump -Fc -n public`` minus every excluded relation, streamed to ``out``."""
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["docker", "exec", src.container, "pg_dump", "-U", src.user, "-d", src.dbname,
           "-Fc", "-n", "public", "--no-owner", "--no-privileges"]  # fmt: skip
    for rel in plan.excluded:
        cmd += ["-T", f'public."{rel}"']
    with open(out, "wb") as fh:
        res = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE)
    if res.returncode != 0:
        out.unlink(missing_ok=True)
        raise RuntimeError("pg_dump failed: " + res.stderr.decode("utf-8", "replace")[-2000:])
    return out


def restore(dst: Db, plan: Plan, archive: Path, *, replace: bool, scratch: Path) -> None:
    """Restore ``archive`` into ``public`` of ``dst`` and move it to ``pilar2b``."""
    n_public = int(dst.psql(PUBLIC_RELATIONS_SQL)[0][0])
    if n_public:
        raise RuntimeError(f"target schema public already holds {n_public} relations; stop")
    n_target = int(
        dst.psql(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            f"WHERE n.nspname = '{TARGET_SCHEMA}'"
        )[0][0]
    )
    if n_target and not replace:
        raise RuntimeError(f"schema {TARGET_SCHEMA} is not empty ({n_target}); use --replace")

    remote = "/tmp/pilar2b_public.dump"
    remote_toc = "/tmp/pilar2b_public.toc"
    run(["docker", "cp", str(archive), f"{dst.container}:{remote}"])
    try:
        toc = run(
            ["docker", "exec", dst.container, "pg_restore", "-l", remote],
            text=True,
            encoding="utf-8",
        ).stdout
        scratch.mkdir(parents=True, exist_ok=True)
        toc_file = scratch / "pilar2b_public.toc"
        toc_file.write_text(
            "\n".join(filter_toc(toc.splitlines(), plan.dropped_fks)) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        run(["docker", "cp", str(toc_file), f"{dst.container}:{remote_toc}"])
        if replace:
            dst.psql(
                f"DROP SCHEMA IF EXISTS {TARGET_SCHEMA} CASCADE; "
                f"CREATE SCHEMA {TARGET_SCHEMA} AUTHORIZATION {dst.user};"
            )
        run(
            ["docker", "exec", dst.container, "pg_restore", "-U", dst.user, "-d", dst.dbname,
             "--no-owner", "--no-privileges", "--single-transaction", "--exit-on-error",
             "-L", remote_toc, remote]
        )  # fmt: skip
        try:
            dst.psql(MOVE_SQL)
        except RuntimeError:
            cleanup = (
                "public relations left by a failed move; drop them by hand after checking:\n"
                + PUBLIC_RELATIONS_SQL
            )
            raise RuntimeError(cleanup) from None
    finally:
        subprocess.run(
            ["docker", "exec", dst.container, "rm", "-f", remote, remote_toc], capture_output=True
        )


def log_tables(dst: Db, archive: Path, relpath: str, commit: str) -> list[tuple[str, int, str]]:
    """ANALYZE every restored table and write its row to ``engine.load_log``."""
    sha = sha256_file(archive)
    dst.psql(LOG_DDL + ";")
    dst.psql(f"DELETE FROM {LOG_TABLE} WHERE table_name LIKE '{TARGET_SCHEMA}.%';")
    tables = [
        r[0]
        for r in dst.psql(
            "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            f"WHERE n.nspname = '{TARGET_SCHEMA}' AND c.relkind IN ('r', 'p') ORDER BY 1"
        )
    ]
    srids = {
        r[0]: r[1]
        for r in dst.psql(
            "SELECT f_table_name, max(srid) FROM geometry_columns "
            f"WHERE f_table_schema = '{TARGET_SCHEMA}' GROUP BY 1"
        )
    }
    now = datetime.now(tz=UTC).isoformat()
    out = []
    for t in tables:
        n = int(
            dst.psql(f'ANALYZE {TARGET_SCHEMA}."{t}"; SELECT count(*) FROM {TARGET_SCHEMA}."{t}";')[
                0
            ][0]
        )
        crs = f"'EPSG:{srids[t]}'" if srids.get(t) not in (None, "", "0") else "NULL"
        dst.psql(
            f"INSERT INTO {LOG_TABLE} (table_name, source_id, file_relpath, file_sha256, n_rows, "
            f"crs, loaded_at_utc, engine_commit) VALUES ('{TARGET_SCHEMA}.{t}', '{SOURCE_ID}', "
            f"'{relpath}', '{sha}', {n}, {crs}, '{now}', '{commit}');"
        )
        out.append((t, n, crs.strip("'") if crs != "NULL" else ""))
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m engine.ingest.restore_pilar2b", description=__doc__.split("\n\n")[0]
    )
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--src-container", default="cp2b-db-dev")
    ap.add_argument("--src-db", default="cp2b_maps")
    ap.add_argument("--src-user", default="postgres")
    ap.add_argument("--dst-container", default="sp-biomethane-engine-db-1")
    ap.add_argument("--dst-db", default="engine")
    ap.add_argument("--dst-user", default="engine")
    ap.add_argument("--out-dir", type=Path, help="dump folder (default: ../backups/pilar2b)")
    ap.add_argument("--replace", action="store_true", help="drop and refill schema pilar2b")
    ap.add_argument("--dry-run", action="store_true", help="print the plan only")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    from engine.registry import load_sources

    repo = args.repo.resolve()
    if SOURCE_ID not in {s["id"] for s in load_sources(repo / "registry" / "sources.yaml")}:
        print(f"{SOURCE_ID} is not in registry/sources.yaml (CLAUDE.md rule 3)", file=sys.stderr)
        return 2

    src = Db(args.src_container, args.src_db, args.src_user)
    plan = make_plan(src)
    print(f"copy {len(plan.tables)} tables and {len(plan.views)} views from {src.container}")
    for rel, why in plan.excluded.items():
        print(f"  leave out {rel:<45} {why}")
    if plan.dropped_fks:
        print("  drop FKs to relations not copied: " + ", ".join(plan.dropped_fks))
    if args.dry_run:
        print("tables: " + ", ".join(plan.tables))
        print("views:  " + ", ".join(plan.views))
        return 0

    out_dir = args.out_dir or repo.parent / "backups" / "pilar2b"
    stamp = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    archive = dump(src, plan, out_dir / f"pilar2b_public_{stamp}.dump")
    print(f"dump: {archive} ({archive.stat().st_size / 1e6:.1f} MB)")
    dst = Db(args.dst_container, args.dst_db, args.dst_user)
    restore(dst, plan, archive, replace=args.replace, scratch=out_dir)
    try:
        relpath = archive.relative_to(repo.parent).as_posix()
    except ValueError:
        relpath = archive.as_posix()
    logged = log_tables(dst, archive, relpath, engine_commit(repo))
    for t, n, crs in logged:
        print(f"  {TARGET_SCHEMA}.{t:<45} {n:>10,}  {crs}")
    print(f"{len(logged)} tables, {sum(n for _, n, _ in logged):,} rows in schema {TARGET_SCHEMA}")
    print(f"dump sha256: {sha256_file(archive)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
