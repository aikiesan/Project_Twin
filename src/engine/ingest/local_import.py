"""Copy datasets the team already holds on local drives into ``data/raw/<source_id>/``.

Driven by a YAML manifest (default ``scripts/ingest/local_holdings.yaml``) so every import is
reviewable in git before it runs. Rules (CLAUDE.md §2):

- **Read-only on the origin.** Files are only read and copied.
- **Never overwrites.** A file already in ``data/raw/`` is skipped (raw data is immutable, rule 4).
- **Logged.** Each copy appends origin path, bytes and sha256 to
  ``data/interim/import_local_holdings_log.tsv`` (outside ``data/raw/``).
- **Deny list.** Paths matching :data:`DENY_SUBSTRINGS` (LGPD personal data, partner/NDA folders)
  are refused even if a manifest lists them; the run stops with an error.

Manifest shape::

    roots:
      downloads: C:/Users/Lucas/Downloads   # override with env LOCAL_ROOT_DOWNLOADS
    sources:
      - id: cetesb_ictem_2023
        root: downloads
        base: 06_DADOS_ENERGIA_EPE/Mapeamento EPE/Recursos Energeticos
        include: [VWM_ICTEM_CETESB_2023_POL.zip]   # globs relative to base; sub-folders kept

CLI::

    python -m engine.ingest.local_import scripts/ingest/local_holdings.yaml --dry-run
    python -m engine.ingest.local_import scripts/ingest/local_holdings.yaml
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

from engine.ingest.inventory import sha256_file

#: Case-insensitive path fragments that are never imported (personal data under LGPD,
#: partner/NDA material, files with CPF/owner names). Extend, never shrink, without review.
DENY_SUBSTRINGS = (
    "cp2b_maps_v3",  # Amasa origin-destination interviews (LGPD)
    "05_parceiros_nda",  # partner material under NDA -> data/private only, by hand
    "data/private",
    "granjas_sui",  # farm registry with address/contact fields (LGPD)
    "granjas_aves",  # same registry, poultry (LGPD)
    "farms_for_gee",  # point layers derived from those registries (exact farm coordinates)
    "sao_paulo_farms",
    "sao_paulo_pig_farms",
    "mapa_amasa_artigo_01",  # origin-destination interviews (LGPD), never opened
    "produto_4_cepal",  # interview transcriptions, part not anonymised
    "listaparticipante",  # participant lists
    "serasa",  # credit-bureau folder, out of scope
    "empreendimento-geracao-distribuida",  # full ANEEL GD file: CPF/CNPJ + owner names
    "balanço zm",  # named-mill engineering balance, possibly NDA
    "harvex",  # HARVEX deliverables: discarded by the team (2026-10-04), never imported
    "joel",  # JOEL indicators: discarded by the team (2026-10-04)
)

#: Files never worth copying.
JUNK_NAMES = {"desktop.ini", "thumbs.db", ".ds_store"}

LOG_HEADER = "imported_at_utc\tsource_id\tdest_relpath\tbytes\tsha256\torigin_path\n"


class DeniedPathError(ValueError):
    """A manifest entry points at a path on the deny list."""


@dataclass
class CopyResult:
    """Counts for one run."""

    copied: int = 0
    skipped: int = 0
    missing: int = 0


def is_denied(path: str | Path) -> bool:
    """True if ``path`` contains a :data:`DENY_SUBSTRINGS` fragment (case-insensitive)."""
    text = str(path).replace("\\", "/").lower()
    return any(s in text for s in DENY_SUBSTRINGS)


def _is_junk(path: Path) -> bool:
    return path.name.lower() in JUNK_NAMES or "__macosx" in (p.lower() for p in path.parts)


def resolve_root(name: str, roots: dict[str, str]) -> Path:
    """Root folder ``name``: env ``LOCAL_ROOT_<NAME>`` wins over the manifest value."""
    env = os.environ.get(f"LOCAL_ROOT_{name.upper()}")
    if env:
        return Path(env)
    if name not in roots:
        raise KeyError(f"root {name!r} is not defined in the manifest 'roots:'")
    return Path(roots[name])


def plan(manifest: dict) -> list[tuple[str, Path, Path, str]]:
    """Expand a manifest into ``(source_id, origin_file, base_dir, relpath)`` tuples.

    Patterns that match nothing yield one tuple with a non-existent origin, reported as missing.

    Raises:
        DeniedPathError: if any base or matched file is on the deny list.
    """
    roots = manifest.get("roots", {})
    out: list[tuple[str, Path, Path, str]] = []
    for src in manifest["sources"]:
        sid = src["id"]
        base = resolve_root(src["root"], roots) / src.get("base", "")
        if is_denied(base):
            raise DeniedPathError(f"{sid}: base {base} is on the deny list")
        for pattern in src["include"]:
            matches = sorted(p for p in base.glob(pattern) if p.is_file() and not _is_junk(p))
            if not matches:
                out.append((sid, base / pattern, base, pattern))
                continue
            for p in matches:
                if is_denied(p):
                    raise DeniedPathError(f"{sid}: {p} is on the deny list")
                out.append((sid, p, base, p.relative_to(base).as_posix()))
    return out


def run(
    manifest: dict,
    raw_dir: Path,
    log_file: Path,
    *,
    dry_run: bool = False,
    only: set[str] | None = None,
) -> CopyResult:
    """Copy every planned file that is not yet in ``raw_dir``. See module docstring."""
    items = plan(manifest)
    result = CopyResult()
    stamp = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not dry_run:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if not log_file.exists():
            log_file.write_text(LOG_HEADER, encoding="utf-8")
    for sid, origin, _base, rel in items:
        if only and sid not in only:
            continue
        if not origin.is_file():
            print(f"MISSING   {sid}: {origin}")
            result.missing += 1
            continue
        dest = raw_dir / sid / rel
        if dest.exists():
            print(f"skip      {sid}/{rel} (exists)")
            result.skipped += 1
            continue
        if dry_run:
            print(f"would     {sid}/{rel}")
            result.copied += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, dest)
        with open(log_file, "a", encoding="utf-8") as fh:
            fh.write(
                f"{stamp}\t{sid}\t{rel}\t{dest.stat().st_size}\t{sha256_file(dest)}\t"
                f"{origin.as_posix()}\n"
            )
        print(f"copied    {sid}/{rel}")
        result.copied += 1
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    ap.add_argument("--log", type=Path, default=Path("data/interim/import_local_holdings_log.tsv"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", action="append", help="source id to import (repeatable)")
    args = ap.parse_args(argv)
    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    try:
        res = run(
            manifest,
            args.raw_dir,
            args.log,
            dry_run=args.dry_run,
            only=set(args.only) if args.only else None,
        )
    except DeniedPathError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    print(f"== copied={res.copied} skipped={res.skipped} missing={res.missing}", file=sys.stderr)
    return 1 if res.missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
