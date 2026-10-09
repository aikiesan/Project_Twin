"""Manure base-load v0 (docs/09 §Manure): arithmetic, missing coefficients, collectable share."""

import math

import pandas as pd
import pytest

from engine.registry import Param
from engine.supply.manure import SPECIES, manure_potential, missing_coefficients


def _p(pid, central, unit=""):
    return Param(
        pid, "supply", pid, central, None, None, unit, "test", "K", "", str(central), "", ""
    )


PARAMS = {
    p.id: p
    for p in (
        _p("swine_manure", 10, "L per animal per day"),
        _p("swine_slurry_density", 1.0, "t per m3"),
        _p("swine_slurry_ts", 4, "% FM"),
        _p("swine_slurry_vs_ts", 75, "% TS"),
        _p("swine_slurry_bmp", 300, "NL CH4 per kg VS"),
    )
}
HERDS = pd.DataFrame(
    {
        "ibge_code": ["3500105", "3500105", "3500204"],
        "year": [2024, 2024, 2024],
        "variable": ["suino_total", "bovino", "suino_total"],
        "value": [1000.0, 500.0, 0.0],
        "unit": ["head", "head", "head"],
    }
)


def test_swine_arithmetic():
    r = manure_potential(HERDS, params=PARAMS, collect_frac={"swine": 0.5})
    row = r[(r.ibge_code == "3500105") & (r.species == "swine")].iloc[0]
    fm = 1000 * 10 * 1.0 * 365 / 1000  # 3650 t FM/yr
    assert row.manure_t_fm_yr == pytest.approx(fm)
    assert row.vs_t_yr == pytest.approx(fm * 0.04 * 0.75)
    assert row.ch4_nm3_yr_theoretical == pytest.approx(fm * 0.04 * 0.75 * 300)
    assert row.ch4_nm3_yr_collectable == pytest.approx(row.ch4_nm3_yr_theoretical * 0.5)


def test_species_without_coefficients_are_skipped_and_listed():
    miss = missing_coefficients(PARAMS)
    assert "swine" not in miss and {"poultry", "cattle"} <= set(miss)
    r = manure_potential(HERDS, params=PARAMS)
    assert set(r.species) == {"swine"}


def test_collectable_is_missing_without_a_fraction():
    r = manure_potential(HERDS, params=PARAMS)
    assert r.ch4_nm3_yr_collectable.map(math.isnan).all()


def test_bad_fraction_and_unit_are_rejected():
    with pytest.raises(ValueError):
        manure_potential(HERDS, params=PARAMS, collect_frac={"swine": 1.5})
    bad = HERDS.assign(unit="kg")
    with pytest.raises(ValueError):
        manure_potential(bad, params=PARAMS)


def test_registry_species_ids_are_declared():
    assert {s.species for s in SPECIES} == {"swine", "poultry", "cattle"}
