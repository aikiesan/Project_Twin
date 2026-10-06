"""Clip oversized rasters to a boundary on import, with a provenance manifest (ADR-0011).

Some held rasters are too large to copy whole into ``data/raw/``. The MapBiomas national mosaics
on the project PC are 13 GB for 17 years, while the engine needs only São Paulo. This module
is the import step for such files. It reads each origin raster, keeps the pixels whose
**centre** lies inside the boundary (the same centroid rule as ``engine.supply.raster_h3``),
crops to the boundary's bounding box and writes a compressed GeoTIFF into ``data/raw/<id>/``.

Rules (CLAUDE.md §2):

- **Read-only on the origin.** Origin files are only read.
- **Never overwrites.** An existing output is skipped (raw data is immutable, rule 4).
- **Logged.** Every output gets one row in ``CLIP_MANIFEST.tsv`` next to it, with the origin
  path, size and sha256, the boundary files' sha256 and the clip settings, so anyone with the
  origin file can reproduce the clip exactly.
- **Deny list.** Origins on :data:`engine.ingest.local_import.DENY_SUBSTRINGS` are refused.
- **Nodata is an explicit argument.** Pixels outside the boundary get ``nodata``. Pick a value
  that is not a valid class in the source legend, and say how you checked it.

Memory: :func:`rasterio.mask.mask` reads the boundary's bounding-box window at once. For SP at
30 m that is about 33,000 × 20,500 pixels of uint8 (≈ 0.7 GB, plus the same again for the mask).

CLI::

    python -m engine.ingest.clip_raster <origin>/brazil_coverage_*.tif
        --boundary data/raw/ibge_malha_municipal_sp_2025/SP_Municipios_2025.shp
        --out-dir data/raw/mapbiomas_col10_coverage_sp --nodata 0
        --out-template "mapbiomas_sp_{year}.tif"

(one command; the line breaks are for reading only)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from engine.ingest.inventory import sha256_file, sha256_group
from engine.ingest.local_import import DeniedPathError, is_denied

MANIFEST_NAME = "CLIP_MANIFEST.tsv"
MANIFEST_COLUMNS = (
    "clipped_at_utc",
    "dest_file",
    "dest_bytes",
    "dest_sha256",
    "origin_path",
    "origin_bytes",
    "origin_sha256",
    "boundary_path",
    "boundary_sha256",
    "all_touched",
    "nodata",
    "dest_width",
    "dest_height",
)


@dataclass(frozen=True)
class ClipSettings:
    """How a clip is made. ``all_touched=False`` keeps pixels whose centre is inside."""

    nodata: int | float
    all_touched: bool = False
    block_size: int = 512


def boundary_files(boundary: Path) -> list[Path]:
    """The boundary file and its sidecars (same stem), for hashing."""
    return sorted(p for p in boundary.parent.glob(boundary.stem + ".*") if p.is_file())


def load_boundary(boundary: Path, dst_crs) -> object:
    """Union of all boundary features, reprojected to ``dst_crs`` (a shapely geometry)."""
    import geopandas as gpd

    gdf = gpd.read_file(boundary)
    if gdf.crs is None:
        raise ValueError(f"{boundary} has no CRS; refuse to guess it")
    return gdf.to_crs(dst_crs).union_all()


def clip_one(origin: Path, geom: object, dest: Path, settings: ClipSettings) -> tuple[int, int]:
    """Clip ``origin`` to ``geom`` (already in the origin's CRS) and write ``dest``.

    Returns:
        ``(width, height)`` of the written raster.
    """
    import rasterio
    from rasterio.mask import mask
    from shapely.geometry import mapping

    with rasterio.open(origin) as src:
        data, transform = mask(
            src,
            [mapping(geom)],
            crop=True,
            all_touched=settings.all_touched,
            nodata=settings.nodata,
            filled=True,
        )
        profile = src.profile.copy()
    profile.update(
        driver="GTiff",
        height=data.shape[1],
        width=data.shape[2],
        transform=transform,
        nodata=settings.nodata,
        compress="deflate",
        tiled=True,
        blockxsize=settings.block_size,
        blockysize=settings.block_size,
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".partial")
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.write(data)
    tmp.replace(dest)
    return data.shape[2], data.shape[1]


def _dest_name(origin: Path, year_regex: str, out_template: str) -> str:
    m = re.search(year_regex, origin.name)
    if not m:
        raise ValueError(f"{origin.name}: no match for --year-regex {year_regex!r}")
    return out_template.format(year=m.group(1))


def run(
    origins: list[Path],
    boundary: Path,
    out_dir: Path,
    settings: ClipSettings,
    *,
    year_regex: str = r"(\d{4})",
    out_template: str = "{year}.tif",
    dry_run: bool = False,
) -> dict[str, int]:
    """Clip every origin not yet in ``out_dir``. Returns counts: clipped, skipped."""
    import rasterio

    for o in [*origins, boundary]:
        if is_denied(o):
            raise DeniedPathError(f"{o} is on the deny list")
    plan = [(o, out_dir / _dest_name(o, year_regex, out_template)) for o in sorted(origins)]
    dests = [d for _, d in plan]
    if len(set(dests)) != len(dests):
        raise ValueError("two origins map to the same output name; check --year-regex")
    todo = [(o, d) for o, d in plan if not d.exists()]
    counts = {"clipped": 0, "skipped": len(plan) - len(todo)}
    for _, d in plan:
        if d.exists():
            print(f"skip      {d.name} (exists)")
    if dry_run or not todo:
        for o, d in todo:
            print(f"would     {o.name} -> {d.name}")
        counts["clipped"] = len(todo) if dry_run else 0
        return counts

    b_files = boundary_files(boundary)
    b_sha = sha256_group(b_files)
    manifest = out_dir / MANIFEST_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    if not manifest.exists():
        manifest.write_text("\t".join(MANIFEST_COLUMNS) + "\n", encoding="utf-8", newline="\n")
    geoms: dict[str, object] = {}
    for origin, dest in todo:
        with rasterio.open(origin) as src:
            crs_key = src.crs.to_string()
            if crs_key not in geoms:
                geoms[crs_key] = load_boundary(boundary, src.crs)
        width, height = clip_one(origin, geoms[crs_key], dest, settings)
        row = (
            datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            dest.name,
            dest.stat().st_size,
            sha256_file(dest),
            origin.as_posix(),
            origin.stat().st_size,
            sha256_file(origin),
            boundary.as_posix(),
            b_sha,
            settings.all_touched,
            settings.nodata,
            width,
            height,
        )
        with open(manifest, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(str(v) for v in row) + "\n")
        print(f"clipped   {origin.name} -> {dest.name} ({width} x {height})")
        counts["clipped"] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("origins", nargs="+", type=Path)
    ap.add_argument("--boundary", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--nodata", type=float, required=True)
    ap.add_argument(
        "--all-touched", action="store_true", help="keep every pixel the boundary touches"
    )
    ap.add_argument("--year-regex", default=r"(\d{4})")
    ap.add_argument("--out-template", default="{year}.tif")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    nodata = int(args.nodata) if float(args.nodata).is_integer() else args.nodata
    try:
        counts = run(
            args.origins,
            args.boundary,
            args.out_dir,
            ClipSettings(nodata=nodata, all_touched=args.all_touched),
            year_regex=args.year_regex,
            out_template=args.out_template,
            dry_run=args.dry_run,
        )
    except DeniedPathError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    print(f"== clipped={counts['clipped']} skipped={counts['skipped']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
