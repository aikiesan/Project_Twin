"""Tests for routing helpers with an injected fake OSRM (no network)."""

import numpy as np
import pytest

from engine.siting.routing import (
    detour_ratio,
    fallback_road_km,
    haversine_km,
    od_matrix,
    osrm_table,
)


def test_haversine_one_degree_latitude():
    # 1° of latitude on a 6371.0088 km sphere = 2πR/360 = 111.195 km
    d = haversine_km([(0.0, 0.0)], [(1.0, 0.0)])
    assert d.shape == (1, 1)
    assert d[0, 0] == pytest.approx(111.195, abs=1e-3)


def test_fallback_requires_valid_detour():
    with pytest.raises(ValueError):
        fallback_road_km([(0, 0)], [(1, 0)], detour_factor=0.9)
    assert fallback_road_km([(0, 0)], [(1, 0)], 1.3)[0, 0] == pytest.approx(111.195 * 1.3, 1e-4)


def _fake_osrm(calls):
    """Fake OSRM: distance = 1000 m × (index sum + 1); None for a designated unreachable pair."""

    def fetch(url, timeout_s):
        calls.append(url)
        q = url.split("?")[1]
        params = dict(kv.split("=") for kv in q.split("&"))
        src = [int(i) for i in params["sources"].split(";")]
        dst = [int(i) for i in params["destinations"].split(";")]
        coords = url.split("/table/v1/driving/")[1].split("?")[0].split(";")
        lons = [float(c.split(",")[0]) for c in coords]
        dist = [[1000.0 * (lons[s] + lons[d] + 1) for d in dst] for s in src]
        dur = [[60.0 * (lons[s] + lons[d] + 1) for d in dst] for s in src]
        if lons[src[0]] == 99.0:  # mark unreachable
            dist[0][0] = None
            dur[0][0] = None
        return {"code": "Ok", "distances": dist, "durations": dur}

    return fetch


def test_osrm_table_parses_and_orders_lonlat():
    calls = []
    # lon encodes identity: origins lon 1,2 ; destination lon 10
    dist, dur = osrm_table([(0, 1), (0, 2)], [(0, 10)], fetch=_fake_osrm(calls))
    assert "1.000000,0.000000;2.000000,0.000000;10.000000,0.000000" in calls[0]
    np.testing.assert_allclose(dist[:, 0], [12.0, 13.0])  # km
    np.testing.assert_allclose(dur[:, 0], [12.0 / 60, 13.0 / 60])  # h


def test_unreachable_is_nan_and_error_code_raises():
    dist, _ = osrm_table([(0, 99.0)], [(0, 1.0)], fetch=_fake_osrm([]))
    assert np.isnan(dist[0, 0])
    with pytest.raises(RuntimeError, match="NoTable"):
        osrm_table([(0, 0)], [(0, 1)], fetch=lambda u, t: {"code": "NoTable", "message": "x"})


def test_od_matrix_batches_equal_single_request():
    origins = [(0.0, float(i)) for i in range(7)]
    dests = [(0.0, float(10 + j)) for j in range(5)]
    calls = []
    d_batched, _ = od_matrix(origins, dests, max_table_size=6, fetch=_fake_osrm(calls))
    d_single, _ = osrm_table(origins, dests, fetch=_fake_osrm([]))
    np.testing.assert_allclose(d_batched, d_single)
    assert len(calls) > 1
    for url in calls:  # every request respects the table-size limit
        n = len(url.split("/table/v1/driving/")[1].split("?")[0].split(";"))
        assert n <= 6


def test_detour_ratio():
    a, b = [(0.0, 0.0)], [(1.0, 0.0)]
    r = detour_ratio(np.array([[133.434]]), a, b)
    assert r[0, 0] == pytest.approx(1.2, rel=1e-4)
