"""Clip-on-import (ADR-0011): centroid rule, crop, nodata, manifest, idempotency, deny list."""

import csv

import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
gpd = pytest.importorskip("geopandas")
from rasterio.transform import from_origin  # noqa: E402
from shapely.geometry import box  # noqa: E402

from engine.ingest.clip_raster import (  # noqa: E402
    MANIFEST_COLUMNS,
    MANIFEST_NAME,
    ClipSettings,
    run,
)
from engine.ingest.inventory import sha256_file  # noqa: E402
from engine.ingest.local_import import DeniedPathError  # noqa: E402


def _raster(path, values, crs="EPSG:4326"):
    """10 x 10 raster over lon 0..10, lat 0..10, 1-degree pixels."""
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype="uint8",
        crs=crs,
        transform=from_origin(0, 10, 1, 1),
    ) as dst:
        dst.write(values, 1)


def _boundary(path, geom, crs="EPSG:4674"):
    gpd.GeoDataFrame({"name": ["a"]}, geometry=[geom], crs=crs).to_file(path)


@pytest.fixture()
def setup(tmp_path):
    values = np.arange(1, 101, dtype="uint8").reshape(10, 10)
    origin = tmp_path / "src" / "brazil_coverage_2024.tif"
    origin.parent.mkdir()
    _raster(origin, values)
    boundary = tmp_path / "b" / "area.shp"
    boundary.parent.mkdir()
    # lon 2.0..5.6, lat 3.0..7.0: pixel centres at lon 2.5..5.5, lat 3.5..6.5 are inside
    _boundary(boundary, box(2.0, 3.0, 5.6, 7.0))
    return tmp_path, values, origin, boundary


def test_clip_keeps_centres_inside_and_crops(setup):
    tmp, values, origin, boundary = setup
    out = tmp / "raw" / "demo"
    counts = run([origin], boundary, out, ClipSettings(nodata=0), out_template="sp_{year}.tif")
    assert counts == {"clipped": 1, "skipped": 0}
    with rasterio.open(out / "sp_2024.tif") as r:
        a = r.read(1)
        assert r.nodata == 0
        assert r.crs.to_string() == "EPSG:4326"
        assert r.profile["compress"] == "deflate"
    # crop = bounding box of the boundary: columns 2..5 (lon 2..6), rows 3..6 (lat 7..3)
    assert a.shape == (4, 4)
    # column 5 has its centre at lon 5.5 < 5.6 -> kept; every pixel in the crop is inside
    np.testing.assert_array_equal(a, values[3:7, 2:6])


def test_pixels_with_centre_outside_get_nodata(tmp_path):
    values = np.full((10, 10), 7, dtype="uint8")
    origin = tmp_path / "x_2020.tif"
    _raster(origin, values)
    boundary = tmp_path / "tri.shp"
    from shapely.geometry import Polygon

    # lower-left triangle x + y < 10.2: no pixel centre lies exactly on the edge (a centre on
    # the edge is a tie, which GDAL counts as inside)
    _boundary(boundary, Polygon([(0, 0), (10.2, 0), (0, 10.2)]))
    run([origin], boundary, tmp_path / "out", ClipSettings(nodata=0), out_template="{year}.tif")
    with rasterio.open(tmp_path / "out" / "2020.tif") as r:
        a = r.read(1)
    # centre (col + 0.5, 9.5 - row) is inside iff (col + 0.5) + (9.5 - row) < 10.2
    rows, cols = np.indices(a.shape)
    inside = (cols + 0.5) + (9.5 - rows) < 10.2
    assert (a[inside] == 7).all() and (a[~inside] == 0).all()


def test_manifest_records_origin_and_rerun_is_idempotent(setup):
    tmp, _, origin, boundary = setup
    out = tmp / "raw" / "demo"
    run([origin], boundary, out, ClipSettings(nodata=0), out_template="sp_{year}.tif")
    again = run([origin], boundary, out, ClipSettings(nodata=0), out_template="sp_{year}.tif")
    assert again == {"clipped": 0, "skipped": 1}
    rows = list(csv.DictReader(open(out / MANIFEST_NAME, encoding="utf-8"), delimiter="\t"))
    assert len(rows) == 1 and tuple(rows[0]) == MANIFEST_COLUMNS
    row = rows[0]
    assert row["origin_sha256"] == sha256_file(origin)
    assert row["dest_sha256"] == sha256_file(out / "sp_2024.tif")
    assert row["nodata"] == "0" and row["all_touched"] == "False"
    assert not list(out.glob("*.partial"))


def test_dry_run_writes_nothing(setup):
    tmp, _, origin, boundary = setup
    out = tmp / "raw" / "demo"
    counts = run([origin], boundary, out, ClipSettings(nodata=0), dry_run=True)
    assert counts["clipped"] == 1 and not out.exists()


def test_denied_and_ambiguous_inputs_are_refused(setup, tmp_path):
    _, values, origin, boundary = setup
    bad = tmp_path / "CP2B_Maps_V3" / "r_2020.tif"
    bad.parent.mkdir()
    _raster(bad, values)
    with pytest.raises(DeniedPathError):
        run([bad], boundary, tmp_path / "o", ClipSettings(nodata=0))
    twin = tmp_path / "other" / "brazil_coverage_2024.tif"
    twin.parent.mkdir()
    _raster(twin, values)
    with pytest.raises(ValueError, match="same output name"):
        run([origin, twin], boundary, tmp_path / "o", ClipSettings(nodata=0))
