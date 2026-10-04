"""Tests for raster → H3 aggregation on small synthetic GeoTIFFs (no real data)."""

import math

import numpy as np
import pandas as pd
import pytest

rasterio = pytest.importorskip("rasterio")
h3 = pytest.importorskip("h3")
from rasterio.transform import from_origin  # noqa: E402

from engine.supply.raster_h3 import (  # noqa: E402
    AUTHALIC_RADIUS_M,
    aggregate_raster_to_h3,
    row_areas_geographic_m2,
)

CODE = 7  # synthetic class code (not a MapBiomas legend value)


def _write(path, arr, transform, crs):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype=arr.dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(arr, 1)


def test_row_area_matches_hand_formula():
    # One 0.001° x 0.001° pixel with top edge at the equator:
    # A = R² · Δλ · (sin 0 − sin(−0.001°)) = R² · (0.001·π/180)² approx (small angle)
    a = row_areas_geographic_m2(0.0, 0.001, 0.001, 1)[0]
    d = math.radians(0.001)
    expected = AUTHALIC_RADIUS_M**2 * d * math.sin(d)
    assert a == pytest.approx(expected, rel=1e-12)
    assert a == pytest.approx(12_364.7, rel=1e-3)  # ≈ (111.2 m)²


def test_sphere_vs_ellipsoid_close_at_sp_latitude():
    sph = row_areas_geographic_m2(-21.0, 0.00025, 0.00025, 10)
    ell = row_areas_geographic_m2(-21.0, 0.00025, 0.00025, 10, geodesic=True)
    # authalic sphere vs GRS80 at ~21°S: differences well under 1 %
    assert np.allclose(sph, ell, rtol=1e-2)


def test_geographic_total_area_conserved(tmp_path):
    arr = np.zeros((200, 200), dtype=np.uint8)
    arr[20:180, 30:170] = CODE
    arr[0:5, 0:5] = 3  # other class ignored
    tr = from_origin(-47.85, -21.15, 0.00025, 0.00025)  # west, north, xres, yres (~27 m)
    p = tmp_path / "geo.tif"
    _write(p, arr, tr, "EPSG:4326")
    df = aggregate_raster_to_h3(p, [CODE], res=8, year=2023, block_rows=37)
    rows = row_areas_geographic_m2(-21.15, 0.00025, 0.00025, 200)
    expected_ha = (rows[20:180] * 140).sum() / 1e4
    assert df["area_ha"].sum() == pytest.approx(expected_ha, rel=1e-9)
    assert df["n_pixels"].sum() == 160 * 140
    assert set(df["class_code"]) == {CODE}
    assert (df["year"] == 2023).all()
    assert all(h3.get_resolution(c) == 8 for c in df["h3_index"])
    # block size must not change the answer (up to float summation order)
    df2 = aggregate_raster_to_h3(p, [CODE], res=8, year=2023, block_rows=512)
    pd.testing.assert_frame_equal(df2, df, rtol=1e-12)


def test_projected_equal_area_pixel_area(tmp_path):
    arr = np.full((50, 60), CODE, dtype=np.uint8)
    albers = "+proj=aea +lat_1=-2 +lat_2=-22 +lat_0=-12 +lon_0=-54 +ellps=GRS80 +units=m"
    tr = from_origin(700_000, -1_000_000, 30, 30)
    p = tmp_path / "aea.tif"
    _write(p, arr, tr, albers)
    with pytest.warns(UserWarning, match="equal-area"):
        df = aggregate_raster_to_h3(p, [CODE], res=8)
    # 50*60 pixels * 900 m² = 2,700,000 m² = 270 ha
    assert df["area_ha"].sum() == pytest.approx(270.0)


def test_requires_class_codes(tmp_path):
    arr = np.zeros((2, 2), dtype=np.uint8)
    p = tmp_path / "x.tif"
    _write(p, arr, from_origin(-47.0, -21.0, 0.001, 0.001), "EPSG:4326")
    with pytest.raises(ValueError, match="class_codes"):
        aggregate_raster_to_h3(p, [])
