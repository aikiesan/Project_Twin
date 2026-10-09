"""engine.siting.catchment: disc sums on a 1 km raster vs a brute-force reference."""

import numpy as np
import pytest

from engine.siting.catchment import disc_kernel, disc_sums


def test_kernel_is_a_disc():
    k = disc_kernel(2000, 1000)
    assert k.shape == (5, 5)
    assert k[2, 2] == 1 and k[0, 2] == 1 and k[0, 0] == 0  # (2,2) cells away = 2.83 km


def test_disc_sums_match_brute_force_on_cell_centres():
    rng = np.random.default_rng(1)
    # sources on 1 km cell centres, queries on cell centres too: the result must be exact
    x = (rng.integers(0, 80, 400) + 0.5) * 1000
    y = (rng.integers(0, 60, 400) + 0.5) * 1000
    v = np.c_[rng.random(400) * 10, (rng.random(400) > 0.7).astype(float)]
    qx = (rng.integers(0, 80, 50) + 0.5) * 1000
    qy = (rng.integers(0, 60, 50) + 0.5) * 1000
    got = disc_sums(x, y, v, qx, qy, radius_m=15000)
    d2 = (qx[:, None] - x[None]) ** 2 + (qy[:, None] - y[None]) ** 2
    ref = (d2 <= 15000**2).astype(float) @ v
    assert got == pytest.approx(ref, abs=1e-9)


def test_one_dimensional_values_and_nan():
    got = disc_sums(
        [500, 1500, 90500], [500, 500, 500], [1.0, np.nan, 5.0], [500], [500], radius_m=2000
    )
    assert got.shape == (1,)
    assert got[0] == pytest.approx(1.0)
