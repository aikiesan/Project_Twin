"""Sums of a gridded quantity within a straight-line radius of query points (catchment screen).

Used for the suitability criterion "N3 CH₄ within 30 km" (ADR-0017): supply sits on a regular
1 km grid (plus facility points snapped to it); the sum within ``radius_m`` of each query point
is a convolution of that raster with a disc, sampled at the query pixels.

Coordinates are metres in one projected CRS (the caller projects; e.g. EPSG:5880 for the CP2b
grid). Accuracy is one cell: a source counts when its *cell centre* is within ``radius_m`` of the
query point's *cell centre*. Straight-line distance, so a screening criterion, not a haul cost
(docs/12 Step 3).
"""

from __future__ import annotations

import numpy as np
from scipy.signal import fftconvolve


def disc_kernel(radius_m: float, cell_m: float) -> np.ndarray:
    """0/1 disc of cells whose centre lies within ``radius_m`` of the central cell's centre."""
    r = int(np.floor(radius_m / cell_m))
    i = np.arange(-r, r + 1)
    return ((i[:, None] ** 2 + i[None, :] ** 2) * cell_m**2 <= radius_m**2).astype(float)


def disc_sums(
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    qx: np.ndarray,
    qy: np.ndarray,
    *,
    radius_m: float,
    cell_m: float = 1000.0,
) -> np.ndarray:
    """Sum of ``values`` (one column per quantity) within ``radius_m`` of each query point.

    Args:
        x, y: source coordinates (m), length n.
        values: shape (n,) or (n, k); NaN counts as 0.
        qx, qy: query coordinates (m), length m.
        radius_m: catchment radius (m).
        cell_m: raster cell size (m); sources and queries are snapped to it.

    Returns:
        Array of shape (m,) or (m, k), same units as ``values``.
    """
    x, y, qx, qy = (np.asarray(a, float) for a in (x, y, qx, qy))
    v = np.nan_to_num(np.asarray(values, float))
    one = v.ndim == 1
    v = v[:, None] if one else v
    if len(x) != len(v):
        raise ValueError("x, y and values must have the same length")
    pad = radius_m + cell_m
    x0 = min(x.min(), qx.min()) - pad
    y0 = min(y.min(), qy.min()) - pad
    nx = int(np.ceil((max(x.max(), qx.max()) + pad - x0) / cell_m)) + 1
    ny = int(np.ceil((max(y.max(), qy.max()) + pad - y0) / cell_m)) + 1
    ix = np.floor((x - x0) / cell_m).astype(int)
    iy = np.floor((y - y0) / cell_m).astype(int)
    qix = np.floor((qx - x0) / cell_m).astype(int)
    qiy = np.floor((qy - y0) / cell_m).astype(int)
    ker = disc_kernel(radius_m, cell_m)
    out = np.empty((len(qx), v.shape[1]))
    for j in range(v.shape[1]):
        r = np.zeros((ny, nx))
        np.add.at(r, (iy, ix), v[:, j])
        s = fftconvolve(r, ker, mode="same")
        out[:, j] = s[qiy, qix]
    out[np.abs(out) < 1e-9 * max(1.0, np.abs(v).sum())] = 0.0  # FFT round-off
    return out[:, 0] if one else out
