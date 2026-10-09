"""How much longer is a straight line in EPSG:5880 than the great-circle distance, in SP?

Context: docs/21 Q24. The ESD detour factor (``road_detour_factor_*``) is "estrada/euclidiana"
on EPSG:5880 (Brazil Polyconic, SIRGAS 2000, central meridian 54 W). The registry and
``engine.siting.routing.fallback_road_km`` apply it to great-circle distances. This script
estimates the gap between the two denominators.

Method: the forward equations of the American Polyconic on a sphere of radius
``EARTH_RADIUS_KM`` (not the GRS80 ellipsoid), from prior knowledge (K, no cited source):
E = (lam - lam0) sin(phi), x = R cot(phi) sin(E), y = R [phi + cot(phi) (1 - cos E)].
Random pairs of 1-60 km in a lat/lon box around SP (seeded). The output is an estimate (D);
check it with pyproj on EPSG:5880 before quoting it as a value.

Run: PYTHONPATH=src python scripts/routing/polyconic_vs_great_circle.py
"""

from __future__ import annotations

import numpy as np

from engine.siting.routing import EARTH_RADIUS_KM

LAM0_DEG = -54.0  # central meridian of EPSG:5880
BOX = {"lat": (-25.3, -19.8), "lon": (-53.1, -44.2)}  # degrees, around SP


def polyconic_km(lat_deg: np.ndarray, lon_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Spherical polyconic x, y in km (origin latitude 0; latitudes must be non-zero)."""
    phi = np.radians(lat_deg)
    e = (np.radians(lon_deg) - np.radians(LAM0_DEG)) * np.sin(phi)
    cot = 1.0 / np.tan(phi)
    return EARTH_RADIUS_KM * cot * np.sin(e), EARTH_RADIUS_KM * (phi + cot * (1.0 - np.cos(e)))


def great_circle_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Haversine distance in km on the same sphere."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))


def main(n: int = 200_000, seed: int = 0) -> None:
    rng = np.random.default_rng(seed)
    lat1 = rng.uniform(*BOX["lat"], n)
    lon1 = rng.uniform(*BOX["lon"], n)
    d_km = rng.uniform(1.0, 60.0, n)
    az = rng.uniform(0.0, 2 * np.pi, n)
    lat2 = lat1 + np.degrees(d_km * np.cos(az) / EARTH_RADIUS_KM)
    lon2 = lon1 + np.degrees(d_km * np.sin(az) / (EARTH_RADIUS_KM * np.cos(np.radians(lat1))))
    x1, y1 = polyconic_km(lat1, lon1)
    x2, y2 = polyconic_km(lat2, lon2)
    ratio = np.hypot(x2 - x1, y2 - y1) / great_circle_km(lat1, lon1, lat2, lon2)
    q = np.quantile(ratio, [0.0, 0.1, 0.5, 0.9, 1.0])
    print(f"planar EPSG:5880 (spherical) / great-circle, {n} pairs of 1-60 km:")
    print("  min {:.5f}  P10 {:.5f}  P50 {:.5f}  P90 {:.5f}  max {:.5f}".format(*q))
    for lo, hi in [(-53.1, -50.0), (-50.0, -47.0), (-47.0, -44.2)]:
        r = ratio[(lon1 >= lo) & (lon1 < hi)]
        print(f"  lon [{lo}, {hi}): P50 {np.median(r):.5f}  P90 {np.quantile(r, 0.9):.5f}")


if __name__ == "__main__":
    main()
