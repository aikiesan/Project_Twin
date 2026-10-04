"""Inventory of datasets already held locally (CP2B drives, PILAR-2b exports, partner folders).

Purpose: register every file the engine will read **before** code reads it (CLAUDE.md rule 3)
without typing sha256 sums by hand. Walk a folder, group multi-file formats (shapefile
sidecars), hash each dataset, and emit

- an inventory CSV (one row per dataset), and
- YAML stubs ready to paste into ``registry/sources.yaml`` (``status: have``), with the
  fields a human must still fill (publisher, url, license, use) marked ``TODO``.

CRS/bounds of spatial files are read only when the optional ``geo`` extra is installed
(pyogrio/rasterio); otherwise those columns stay empty.

CLI::

    python -m engine.ingest.inventory D:/CP2B/dados --out registry/inventory_local.csv \
        --yaml registry/inventory_local_stubs.yaml --module supply --private-substr partner
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

#: Sidecar extensions grouped with their main file (shapefile family).
SHAPEFILE_SIDECARS = (".shx", ".dbf", ".prj", ".cpg", ".sbn", ".sbx", ".qix", ".xml", ".qmd")

FORMAT_BY_EXT = {
    ".shp": "ESRI Shapefile",
    ".gpkg": "GeoPackage",
    ".geojson": "GeoJSON",
    ".json": "JSON",
    ".parquet": "Parquet",
    ".tif": "GeoTIFF",
    ".tiff": "GeoTIFF",
    ".csv": "CSV",
    ".xlsx": "Excel",
    ".xls": "Excel",
    ".pdf": "PDF",
    ".zip": "ZIP",
    ".kml": "KML",
    ".kmz": "KMZ",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".txt": "Text",
    ".dump": "PostgreSQL dump",
    ".sql": "SQL",
}

SKIP_DIRS = {".git", ".dvc", "__pycache__", ".venv", "node_modules", ".ipynb_checkpoints"}


@dataclass
class DatasetEntry:
    """One held dataset (a file, or a shapefile with its sidecars)."""

    id: str
    path: str
    format: str
    size_bytes: int
    sha256: str
    modified_utc: str
    n_files: int
    sidecars: list[str] = field(default_factory=list)
    crs: str = ""
    bounds: str = ""
    private: bool = False


def sha256_file(path: Path, chunk_bytes: int = 1 << 20) -> str:
    """Streamed sha256 of one file (hex)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_bytes), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_group(paths: list[Path]) -> str:
    """sha256 over a sorted group of files (name + content), stable across machines."""
    h = hashlib.sha256()
    for p in sorted(paths, key=lambda q: q.name.lower()):
        h.update(p.name.lower().encode())
        h.update(bytes.fromhex(sha256_file(p)))
    return h.hexdigest()


def sha256_tree(folder: Path | str) -> tuple[str, int, int]:
    """sha256 of a whole folder, for registering one ``data/raw/<source_id>/`` as one source.

    Hashes, in sorted order, one line ``<relative posix path>\\0<file sha256 hex>\\n`` per file
    (``SKIP_DIRS`` ignored). Renaming, adding, removing or changing any file changes the digest;
    file timestamps do not. Re-compute with this function to check a folder against the registry.

    Returns:
        ``(hex digest, number of files, total bytes)``.
    """
    folder = Path(folder).resolve()
    files = sorted(
        (p for p in folder.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(folder).as_posix(),
    )
    files = [p for p in files if not any(s in SKIP_DIRS for s in p.relative_to(folder).parts)]
    h = hashlib.sha256()
    for p in files:
        h.update(f"{p.relative_to(folder).as_posix()}\0{sha256_file(p)}\n".encode())
    return h.hexdigest(), len(files), sum(p.stat().st_size for p in files)


def folder_manifest(root: Path | str) -> list[dict[str, object]]:
    """One row per immediate sub-folder of ``root``.

    Columns: ``source_id`` (folder name), ``n_files``, ``size_bytes``, ``sha256_tree``.
    """
    root = Path(root).resolve()
    rows: list[dict[str, object]] = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in SKIP_DIRS):
        digest, n_files, size = sha256_tree(d)
        rows.append(
            {"source_id": d.name, "n_files": n_files, "size_bytes": size, "sha256_tree": digest}
        )
    return rows


def slug_id(path: Path, root: Path) -> str:
    """Registry-style snake_case id from the path relative to ``root``."""
    rel = path.relative_to(root).with_suffix("")
    text = "_".join(rel.parts).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return f"held_{text}"[:80]


def _spatial_metadata(path: Path) -> tuple[str, str]:
    """Return (crs, bounds) for vector/raster files when optional libraries exist."""
    ext = path.suffix.lower()
    try:
        if ext in (".tif", ".tiff"):
            import rasterio  # type: ignore[import-not-found]

            with rasterio.open(path) as src:
                return (str(src.crs or ""), ",".join(f"{v:.6f}" for v in src.bounds))
        if ext in (".shp", ".gpkg", ".geojson"):
            import pyogrio  # type: ignore[import-not-found]

            info = pyogrio.read_info(path)
            bounds = info.get("total_bounds")
            return (
                str(info.get("crs") or ""),
                ",".join(f"{v:.6f}" for v in bounds) if bounds is not None else "",
            )
    except ImportError:
        return ("", "")
    except Exception as exc:  # noqa: BLE001 - metadata is best effort, never fatal
        return (f"unreadable: {type(exc).__name__}", "")
    return ("", "")


def scan(root: Path | str, private_substrings: tuple[str, ...] = ()) -> list[DatasetEntry]:
    """Walk ``root`` and return one :class:`DatasetEntry` per dataset.

    Shapefile sidecars (``.dbf``, ``.prj``…) are grouped with their ``.shp`` and hashed together.
    Paths containing any of ``private_substrings`` (case-insensitive) are flagged ``private``
    so they are routed to ``data/private`` and never registered as public.
    """
    root = Path(root).resolve()
    files = [
        p
        for p in root.rglob("*")
        if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(root).parts)
    ]
    shp_stems = {p.with_suffix("").as_posix().lower() for p in files if p.suffix.lower() == ".shp"}
    entries: list[DatasetEntry] = []
    for p in sorted(files):
        ext = p.suffix.lower()
        stem_key = p.with_suffix("").as_posix().lower()
        if ext in SHAPEFILE_SIDECARS and stem_key in shp_stems:
            continue  # counted with its .shp
        group = [p]
        if ext == ".shp":
            group += [
                q
                for q in files
                if q.with_suffix("").as_posix().lower() == stem_key
                and q.suffix.lower() in SHAPEFILE_SIDECARS
            ]
        digest = sha256_file(p) if len(group) == 1 else sha256_group(group)
        crs, bounds = _spatial_metadata(p)
        rel = p.relative_to(root).as_posix()
        entries.append(
            DatasetEntry(
                id=slug_id(p, root),
                path=rel,
                format=FORMAT_BY_EXT.get(ext, ext.lstrip(".") or "unknown"),
                size_bytes=sum(q.stat().st_size for q in group),
                sha256=digest,
                modified_utc=datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat(
                    timespec="seconds"
                ),
                n_files=len(group),
                sidecars=sorted(q.suffix.lower() for q in group[1:]),
                crs=crs,
                bounds=bounds,
                private=any(s.lower() in rel.lower() for s in private_substrings),
            )
        )
    return entries


def write_inventory_csv(entries: list[DatasetEntry], out: Path | str) -> None:
    """Write the inventory table (one row per dataset)."""
    cols = list(DatasetEntry.__dataclass_fields__)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for e in entries:
            row = asdict(e)
            row["sidecars"] = ";".join(e.sidecars)
            w.writerow(row)


def yaml_stubs(entries: list[DatasetEntry], module: str, accessed: str) -> str:
    """YAML stubs for ``registry/sources.yaml`` (public entries only; private are skipped)."""
    stubs = []
    for e in entries:
        if e.private:
            continue
        stubs.append(
            {
                "id": e.id,
                "name": f"TODO human-readable name ({Path(e.path).name})",
                "publisher": "TODO",
                "url": "TODO original download URL or 'internal CP2B'",
                "module": module,
                "provides": ["TODO"],
                "spatial": f"TODO (crs: {e.crs})" if e.crs else "TODO",
                "temporal": "TODO",
                "format": e.format,
                "access": "TODO open|restricted",
                "status": "have",
                "confidence": "K",
                "use": "TODO",
                "local_path": f"data/raw/{e.path}",
                "sha256": e.sha256,
                "accessed": accessed,
                "notes": f"size {e.size_bytes} B; {e.n_files} file(s)",
            }
        )
    return yaml.safe_dump(stubs, sort_keys=False, allow_unicode=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, required=True, help="inventory CSV path")
    ap.add_argument("--yaml", type=Path, help="write sources.yaml stubs here")
    ap.add_argument("--module", default="TODO")
    ap.add_argument(
        "--private-substr",
        action="append",
        default=[],
        help="path substring marking confidential data (repeatable), e.g. partner, nda",
    )
    ap.add_argument(
        "--folders-out",
        type=Path,
        help="also write one row per sub-folder (source_id, n_files, size_bytes, sha256_tree)",
    )
    args = ap.parse_args(argv)
    entries = scan(args.folder, tuple(args.private_substr))
    write_inventory_csv(entries, args.out)
    if args.folders_out:
        rows = folder_manifest(args.folder)
        with open(args.folders_out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["source_id", "n_files", "size_bytes", "sha256_tree"])
            w.writeheader()
            w.writerows(rows)
    if args.yaml:
        accessed = datetime.now(tz=UTC).date().isoformat()
        args.yaml.write_text(yaml_stubs(entries, args.module, accessed), encoding="utf-8")
    n_priv = sum(e.private for e in entries)
    print(f"{len(entries)} datasets inventoried ({n_priv} private) -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
