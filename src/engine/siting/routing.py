"""Road-network distance/duration matrices (OSRM ``table`` service) with explicit fallbacks.

CLAUDE.md: logistics distances are **road-network**, never Euclidean. This module talks to a
local OSRM server (see ``docker-compose.routing.yml`` and ``scripts/routing/setup_osrm.sh``)
and builds origin × destination matrices in batches.

- :func:`osrm_table` — one request (≤ ``max_table_size`` coordinates in total).
- :func:`od_matrix` — batched matrix for any number of origins/destinations.
- :func:`haversine_km` — great-circle distance, **only** for QA (detour ratio diagnostics) or as an
  explicitly-requested fallback via :func:`fallback_road_km` with a detour factor you must supply
  and cite (no default: the SP-specific factor is an open question, docs/21).

Coordinates are (lat, lon) in EPSG:4674/4326 degrees (the ~1 m datum difference is irrelevant at
routing scale). OSRM itself expects ``lon,lat`` order — handled here.

Note: OSRM's stock ``car.lua`` profile ignores truck restrictions. For haul costs of tankers
(vinasse/digestate) and solid-bulk trucks this is a v0 approximation; switching to Valhalla
``truck`` costing needs an ADR (docs/12 §Step 3).
"""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence

import numpy as np

#: Mean Earth radius (IUGG), km — used only for great-circle QA distances.
EARTH_RADIUS_KM = 6371.0088

LatLon = tuple[float, float]
Fetcher = Callable[[str, float], dict]


def haversine_km(a: Sequence[LatLon], b: Sequence[LatLon]) -> np.ndarray:
    """Great-circle distance matrix (km) between points ``a`` (rows) and ``b`` (columns)."""
    la = np.radians(np.asarray(a, dtype=float))
    lb = np.radians(np.asarray(b, dtype=float))
    dlat = lb[None, :, 0] - la[:, None, 0]
    dlon = lb[None, :, 1] - la[:, None, 1]
    h = (
        np.sin(dlat / 2) ** 2
        + np.cos(la[:, None, 0]) * np.cos(lb[None, :, 0]) * np.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(h, 0.0, 1.0)))


def fallback_road_km(a: Sequence[LatLon], b: Sequence[LatLon], detour_factor: float) -> np.ndarray:
    """Great-circle distance × ``detour_factor`` (REQUIRED; cite its source in the run log)."""
    if not detour_factor >= 1.0:
        raise ValueError("detour_factor must be >= 1 (road distance cannot beat great-circle)")
    return haversine_km(a, b) * detour_factor


def _http_get_json(url: str, timeout_s: float) -> dict:
    with urllib.request.urlopen(url, timeout=timeout_s) as resp:  # noqa: S310 - local server
        return json.loads(resp.read().decode("utf-8"))


def osrm_table(
    origins: Sequence[LatLon],
    destinations: Sequence[LatLon],
    base_url: str = "http://localhost:5000",
    profile: str = "driving",
    timeout_s: float = 120.0,
    fetch: Fetcher | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """One OSRM ``/table`` request → (distance_km, duration_h) arrays [origins × destinations].

    Unreachable pairs are returned as ``nan``. Raises ``RuntimeError`` on an OSRM error code.
    ``fetch`` is injectable for tests (signature ``fetch(url, timeout_s) -> dict``).
    """
    fetch = fetch or _http_get_json
    pts = list(origins) + list(destinations)
    coords = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in pts)
    n_o = len(origins)
    src = ";".join(str(i) for i in range(n_o))
    dst = ";".join(str(i) for i in range(n_o, len(pts)))
    url = (
        f"{base_url.rstrip('/')}/table/v1/{profile}/{coords}"
        f"?sources={src}&destinations={dst}&annotations=distance,duration"
    )
    try:
        payload = fetch(url, timeout_s)
    except urllib.error.URLError as exc:  # pragma: no cover - network path
        raise RuntimeError(
            f"OSRM not reachable at {base_url} ({exc}). Start it with "
            "`docker compose -f docker-compose.routing.yml up -d` (see scripts/routing/)."
        ) from exc
    if payload.get("code") != "Ok":
        raise RuntimeError(f"OSRM error: {payload.get('code')} {payload.get('message', '')}")
    dist = np.array(
        [[np.nan if v is None else v for v in row] for row in payload["distances"]], dtype=float
    )
    dur = np.array(
        [[np.nan if v is None else v for v in row] for row in payload["durations"]], dtype=float
    )
    return dist / 1000.0, dur / 3600.0


def od_matrix(
    origins: Sequence[LatLon],
    destinations: Sequence[LatLon],
    base_url: str = "http://localhost:5000",
    max_table_size: int = 10_000,
    batch_origins: int | None = None,
    fetch: Fetcher | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Batched origin × destination matrices (distance_km, duration_h).

    Requests are split so that ``n_origins_in_batch + n_destinations_in_batch`` never exceeds
    ``max_table_size`` (must match ``osrm-routed --max-table-size``). Destinations are split too
    when they alone exceed the limit.
    """
    n_o, n_d = len(origins), len(destinations)
    if n_o == 0 or n_d == 0:
        return np.empty((n_o, n_d)), np.empty((n_o, n_d))
    d_step = min(n_d, max(1, max_table_size // 2))
    o_step = batch_origins or max(1, max_table_size - d_step)
    if o_step + d_step > max_table_size:
        raise ValueError("batch_origins + destination batch exceeds max_table_size")
    dist = np.full((n_o, n_d), np.nan)
    dur = np.full((n_o, n_d), np.nan)
    for i0 in range(0, n_o, o_step):
        for j0 in range(0, n_d, d_step):
            o = origins[i0 : i0 + o_step]
            d = destinations[j0 : j0 + d_step]
            di, du = osrm_table(o, d, base_url=base_url, fetch=fetch)
            dist[i0 : i0 + len(o), j0 : j0 + len(d)] = di
            dur[i0 : i0 + len(o), j0 : j0 + len(d)] = du
    return dist, dur


def detour_ratio(road_km: np.ndarray, a: Sequence[LatLon], b: Sequence[LatLon]) -> np.ndarray:
    """Road / great-circle ratio per pair (QA: values < 1 or ≫ 2 indicate snapping problems)."""
    gc = haversine_km(a, b)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(gc > 0, road_km / gc, math.nan)
