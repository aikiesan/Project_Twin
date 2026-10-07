"""Polygon exclusions for the grid (engine.siting.exclusions); skipped without the geo extra."""

import pytest

shapely = pytest.importorskip("shapely")
pyogrio = pytest.importorskip("pyogrio")
pytest.importorskip("pyproj")


def test_points_in_layer_projects_points_to_layer_crs(tmp_path):
    import numpy as np
    from pyproj import Transformer

    from engine.siting.exclusions import points_in_layer

    # A square around (-22, -48) stored in SIRGAS 2000 / UTM 22S (EPSG:31982).
    tr = Transformer.from_crs("EPSG:4326", "EPSG:31982", always_xy=True)
    x0, y0 = tr.transform(-48.0, -22.0)
    sq = shapely.box(x0 - 5000, y0 - 5000, x0 + 5000, y0 + 5000)
    path = tmp_path / "uc.gpkg"
    pyogrio.raw.write(
        path,
        geometry=np.array([shapely.to_wkb(sq)], dtype=object),
        field_data=[np.array([1])],
        fields=["id"],
        crs="EPSG:31982",
        geometry_type="Polygon",
        driver="GPKG",
    )
    got = points_in_layer([-22.0, -22.2, -22.01], [-48.0, -48.0, -48.01], path)
    assert got.tolist() == [True, False, True]
