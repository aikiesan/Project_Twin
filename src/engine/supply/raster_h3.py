"""Aggregate a classified land-use raster (e.g. MapBiomas sugarcane) to H3 cells.

Step 2 of ``docs/09_MODULE_SUPPLY.md`` starts from *area of a class per H3 cell per year*.
This module produces exactly that table, streaming the raster block by block so a statewide
30 m mosaic fits in memory:

    h3_index | year | class_code | area_ha | n_pixels

Design choices (see ADR-0002 for the H3 resolution):

- Each pixel is assigned to the H3 cell containing its **centre** (standard "centroid in cell"
  rule; boundary error averages out at res 8 ≈ 0.74 km² ≈ 800 pixels of 30 m).
- Pixel area is computed **per pixel row** from the raster geometry, never assumed constant:
  geographic rasters (EPSG:4326/4674) use the exact spherical-zone area on the authalic sphere
  (or the ellipsoid via ``pyproj.Geod`` when ``geodesic=True``; use it for real areas: the
  sphere overstates pixel area by 0.20-0.30 % across SP's latitudes); projected rasters use
  ``|a·e − b·d|`` from the affine transform (correct for equal-area projections only —
  a warning is raised otherwise).
- The class code(s) are **required arguments**: check the legend of the collection you
  downloaded (MapBiomas legends change between collections). Nothing is hard-coded.

Requires the optional ``geo`` extra (rasterio, pyproj, h3).

Throughput (cloud test box, 1 core): ~0.9 million class pixels/s, i.e. roughly 1–2 min per
statewide year of sugarcane at 30 m. The H3 lookup is the bottleneck; run years in parallel.

CLI::

    python -m engine.supply.raster_h3 mapbiomas_2023.tif --year 2023 --class-code <code> \
        --res 8 --out data/interim/cane_area_h3_2023.parquet
"""

from __future__ import annotations

import argparse
import math
import sys
import warnings
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

#: Authalic (equal-area) radius of the GRS80/WGS84 ellipsoid, m. Geodetic constant
#: (Moritz 1980, Geodetic Reference System 1980): a sphere with the ellipsoid's surface area.
AUTHALIC_RADIUS_M = 6_371_007.181


def row_areas_geographic_m2(
    top_lat_deg: float,
    pixel_height_deg: float,
    pixel_width_deg: float,
    n_rows: int,
    geodesic: bool = False,
) -> np.ndarray:
    """Area (m²) of one pixel in each of ``n_rows`` rows of a north-up geographic raster.

    Spherical zone formula: ``A = R² · Δλ · |sin φ₁ − sin φ₂|`` with Δλ in radians.
    With ``geodesic=True`` uses ``pyproj.Geod(ellps="GRS80")`` polygon areas instead
    (SIRGAS 2000 uses GRS80; WGS84 differs negligibly at this scale).

    Args:
        top_lat_deg: latitude of the top edge of the first row (degrees).
        pixel_height_deg: positive pixel height (degrees).
        pixel_width_deg: positive pixel width (degrees).
        n_rows: number of rows.
        geodesic: use the ellipsoid instead of the authalic sphere.
    """
    edges = top_lat_deg - pixel_height_deg * np.arange(n_rows + 1)
    if geodesic:
        from pyproj import Geod

        geod = Geod(ellps="GRS80")
        out = np.empty(n_rows)
        for i in range(n_rows):
            lats = [edges[i], edges[i], edges[i + 1], edges[i + 1]]
            lons = [0.0, pixel_width_deg, pixel_width_deg, 0.0]
            area, _ = geod.polygon_area_perimeter(lons, lats)
            out[i] = abs(area)
        return out
    phi = np.radians(edges)
    return AUTHALIC_RADIUS_M**2 * math.radians(pixel_width_deg) * np.abs(np.diff(np.sin(phi)))


def _cells_for_points(lats: np.ndarray, lngs: np.ndarray, res: int) -> np.ndarray:
    """H3 cell (as uint64) for each point; loops in C via h3, Python overhead per point."""
    import h3

    to_int = h3.str_to_int
    cell = h3.latlng_to_cell
    return np.fromiter(
        (to_int(cell(float(a), float(b), res)) for a, b in zip(lats, lngs, strict=True)),
        dtype=np.uint64,
        count=len(lats),
    )


def aggregate_raster_to_h3(
    raster_path: Path | str,
    class_codes: Iterable[int],
    res: int = 8,
    year: int | None = None,
    block_rows: int = 512,
    geodesic: bool = False,
) -> pd.DataFrame:
    """Sum the area of the given class code(s) per H3 cell.

    Args:
        raster_path: single-band classified GeoTIFF (geographic or equal-area projected CRS).
        class_codes: pixel values to count (REQUIRED — read the collection's legend).
        res: H3 resolution (project default 8; ADR-0002).
        year: stored in the output for panel stacking (optional).
        block_rows: rows read per block (memory/speed trade-off).
        geodesic: ellipsoidal pixel areas (slower) instead of authalic sphere.

    Returns:
        DataFrame with columns ``h3_index`` (str), ``class_code``, ``n_pixels``, ``area_ha``
        and ``year`` (if given), one row per (cell, class) with area > 0.
    """
    import h3
    import rasterio
    from rasterio.windows import Window

    codes = sorted({int(c) for c in class_codes})
    if not codes:
        raise ValueError("class_codes is empty — pass the legend code(s) explicitly")
    acc: dict[tuple[int, int], list[float]] = {}
    with rasterio.open(raster_path) as src:
        if src.count != 1:
            raise ValueError(f"expected a single-band raster, got {src.count} bands")
        t = src.transform
        if t.b != 0 or t.d != 0:
            raise ValueError("rotated rasters are not supported; warp to north-up first")
        crs = src.crs
        if crs is None:
            raise ValueError("raster has no CRS")
        geographic = crs.is_geographic
        if not geographic:
            warnings.warn(
                f"Projected CRS {crs}: pixel area taken from the affine transform, which is "
                "correct only for equal-area projections (e.g. SP Albers). Do not use UTM "
                "far from the central meridian for area accounting.",
                stacklevel=2,
            )
        width, height = src.width, src.height
        for row0 in range(0, height, block_rows):
            n = min(block_rows, height - row0)
            block = src.read(1, window=Window(0, row0, width, n))
            mask = np.isin(block, codes)
            if not mask.any():
                continue
            rr, cc = np.nonzero(mask)
            values = block[rr, cc]
            # pixel centres in raster CRS
            xs = t.c + (cc + 0.5) * t.a
            ys = t.f + (row0 + rr + 0.5) * t.e
            if geographic:
                lats, lngs = ys, xs
                areas_row = row_areas_geographic_m2(
                    t.f + row0 * t.e, abs(t.e), abs(t.a), n, geodesic=geodesic
                )
                areas = areas_row[rr]
            else:
                from rasterio.warp import transform as warp_transform

                lngs_list, lats_list = warp_transform(crs, "EPSG:4326", xs.tolist(), ys.tolist())
                lngs, lats = np.asarray(lngs_list), np.asarray(lats_list)
                areas = np.full(rr.shape, abs(t.a * t.e - t.b * t.d))
            cells = _cells_for_points(lats, lngs, res)
            frame = pd.DataFrame({"cell": cells, "code": values, "area_m2": areas})
            grouped = frame.groupby(["cell", "code"], sort=False)["area_m2"].agg(["sum", "size"])
            for (cell, code), (area_m2, npx) in grouped.iterrows():
                key = (int(cell), int(code))
                if key in acc:
                    acc[key][0] += float(area_m2)
                    acc[key][1] += int(npx)
                else:
                    acc[key] = [float(area_m2), int(npx)]
    rows = [
        {
            "h3_index": h3.int_to_str(cell),
            "class_code": code,
            "n_pixels": int(npx),
            "area_ha": area_m2 / 10_000.0,
        }
        for (cell, code), (area_m2, npx) in acc.items()
    ]
    out = pd.DataFrame(rows, columns=["h3_index", "class_code", "n_pixels", "area_ha"])
    if year is not None:
        out.insert(1, "year", int(year))
    return out.sort_values(["h3_index", "class_code"]).reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Aggregate classified raster area to H3 cells")
    ap.add_argument("raster", type=Path)
    ap.add_argument("--class-code", type=int, action="append", required=True)
    ap.add_argument("--year", type=int)
    ap.add_argument("--res", type=int, default=8)
    ap.add_argument("--block-rows", type=int, default=512)
    ap.add_argument("--geodesic", action="store_true")
    ap.add_argument("--out", type=Path, required=True, help=".parquet or .csv")
    args = ap.parse_args(argv)
    df = aggregate_raster_to_h3(
        args.raster, args.class_code, args.res, args.year, args.block_rows, args.geodesic
    )
    if args.out.suffix == ".parquet":
        df.to_parquet(args.out, index=False)
    else:
        df.to_csv(args.out, index=False)
    print(
        f"{len(df)} cell-class rows, total {df['area_ha'].sum():,.1f} ha -> {args.out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
