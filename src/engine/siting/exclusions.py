"""Hard exclusions for the suitability grid from polygon layers (ADR-0016).

A grid cell is excluded by a layer when its **centre** lies inside one of the layer's polygons
(H3 res-7 cells are about 5 km², so a cell partly inside a protected area may stay in; the
screen is a first cut, not a permit check). Only layers with a cited legal basis are used as
exclusions (docs/12 Step 2).

Needs the ``geo`` extra (shapely, pyproj) and pyogrio; imported lazily so the rest of
``engine.siting`` works without them.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np


def points_in_layer(
    lat: Sequence[float], lon: Sequence[float], path: str | Path, *, layer: str | None = None
) -> np.ndarray:
    """Boolean array: is each (lat, lon) point (degrees, WGS84/SIRGAS) inside a layer polygon?

    The points are projected to the layer's own CRS, so the layer is used as published.
    Invalid polygons are repaired with ``make_valid`` first.
    """
    import pyogrio
    import shapely
    from pyproj import CRS, Transformer

    meta, _, geom, _ = pyogrio.raw.read(path, layer=layer, read_geometry=True)
    polys = shapely.make_valid(shapely.from_wkb(geom))
    crs = CRS.from_user_input(meta["crs"]) if meta.get("crs") else CRS.from_epsg(4326)
    x, y = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(
        np.asarray(lon, float), np.asarray(lat, float)
    )
    pts = shapely.points(x, y)
    hit = shapely.STRtree(polys).query(pts, predicate="within")
    out = np.zeros(len(pts), dtype=bool)
    out[hit[0]] = True
    return out
