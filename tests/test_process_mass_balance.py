"""Level-1 CSTR mass balance (docs/10 §2): arithmetic, constraints, sizing, registry builders."""

import math

import pandas as pd
import pytest

from engine.process.mass_balance import (
    K_PER_K2O,
    OperatingLimits,
    PlantDesign,
    Substrate,
    limits_from_registry,
    simulate,
    size_digester,
    substrates_from_registry,
)
from engine.registry import load_parameters

LIMITS = OperatingLimits(
    olr_max_kg_vs_m3_d=3.0, hrt_min_d=20, bmp_fullscale=0.85, cod_so4_min=10, k_max_kg_m3=3.0
)
VINASSE = Substrate(
    name="vinasse",
    basis="cod",
    density_t_per_m3=1.0,
    ts_frac_fm=0.016,
    vs_frac_ts=9 / 16,
    cod_kg_per_m3=30,
    cod_removal_frac=0.70,
    ch4_yield_nm3_per_kg_cod=0.30,
    so4_kg_per_m3=2.0,
    k_kg_per_m3=2.5,
)
CAKE = Substrate(
    name="filter_cake",
    basis="vs",
    density_t_per_m3=1.0,
    ts_frac_fm=0.28,
    vs_frac_ts=0.74,
    bmp_nm3_ch4_per_t_vs=220,
)


def _feed(rows):
    return pd.DataFrame(rows, columns=["month", "substrate", "fresh_t"])


def _design(volume=10_000.0, nameplate=1e9):
    return PlantDesign(
        digester_volume_m3=volume,
        upgrading_capacity_nm3_d=nameplate,
        x_ch4=0.6,
        ch4_recovery_frac=0.99,
    )


def test_cod_basis_arithmetic():
    # 1000 m3 x 30 kg COD/m3 x 0.70 x 0.30 Nm3/kg COD
    assert VINASSE.ch4_nm3(1000, hrt_d=30, bmp_fullscale=0.85) == pytest.approx(6300)


def test_vs_basis_arithmetic_and_first_order_kinetics():
    # 100 t x 0.28 x 0.74 x 220 Nm3/t VS x 0.85
    assert CAKE.ch4_nm3(100, hrt_d=30, bmp_fullscale=0.85) == pytest.approx(3874.64)
    slow = Substrate(**{**CAKE.__dict__, "k_first_order_per_d": 0.1})
    full = CAKE.ch4_nm3(100, 30, 0.85)
    assert slow.ch4_nm3(100, 30, 0.85) == pytest.approx(full * (1 - math.exp(-3)))


def test_simulate_gas_chain_and_capacity_factor():
    out = simulate(_feed([("2024-06", "vinasse", 30_000)]), {"vinasse": VINASSE}, _design(), LIMITS)
    row = out.iloc[0]
    assert row["days"] == 30
    assert row["ch4_nm3"] == pytest.approx(30_000 * 30 * 0.7 * 0.3)
    assert row["biogas_nm3"] == pytest.approx(row["ch4_nm3"] / 0.6)
    assert row["biomethane_nm3"] == pytest.approx(row["ch4_nm3"] * 0.99)
    assert row["biomethane_curtailed_nm3"] == 0
    assert row["hrt_d"] == pytest.approx(10_000 / 1000)  # 30,000 m3 over 30 d


def test_nameplate_caps_output_and_reports_curtailment():
    out = simulate(
        _feed([("2024-06", "vinasse", 30_000)]),
        {"vinasse": VINASSE},
        _design(volume=30_000, nameplate=1000),
        LIMITS,
    )
    row = out.iloc[0]
    assert row["capacity_factor"] == pytest.approx(1.0)
    assert row["biomethane_nm3"] == pytest.approx(30_000)
    assert row["biomethane_curtailed_nm3"] > 0


def test_empty_month_produces_nothing_and_is_feasible():
    out = simulate(_feed([("2024-12", "vinasse", 0.0)]), {"vinasse": VINASSE}, _design(), LIMITS)
    row = out.iloc[0]
    assert row["ch4_nm3"] == 0 and row["capacity_factor"] == 0
    assert math.isinf(row["hrt_d"]) and row["feasible"]


def test_constraint_flags():
    feed = _feed([("2024-06", "vinasse", 30_000)])
    # HRT 10 d < 20 d -> infeasible; OLR = 30,000 x 0.009 t VS / 30 d / 10,000 m3 = 0.9 -> ok
    out = simulate(feed, {"vinasse": VINASSE}, _design(volume=10_000), LIMITS).iloc[0]
    assert out["olr_ok"] and not out["hrt_ok"] and not out["feasible"]
    assert out["feed_cod_so4"] == pytest.approx(15) and out["cod_so4_ok"]
    assert out["k_ok"] and out["tan_ok"] is None
    sulfate_rich = Substrate(**{**VINASSE.__dict__, "so4_kg_per_m3": 4.0})
    low = simulate(feed, {"vinasse": sulfate_rich}, _design(volume=30_000), LIMITS).iloc[0]
    assert low["hrt_ok"] and low["cod_so4_ok"] is False and not low["feasible"]


def test_cod_so4_not_evaluable_when_a_substrate_lacks_it():
    feed = _feed([("2024-06", "vinasse", 30_000), ("2024-06", "filter_cake", 1000)])
    out = simulate(feed, {"vinasse": VINASSE, "filter_cake": CAKE}, _design(30_000), LIMITS)
    assert out.iloc[0]["cod_so4_ok"] is None


def test_size_digester_takes_worst_month_of_olr_and_hrt():
    feed = _feed(
        [
            ("2024-06", "vinasse", 30_000),  # flow 1000 m3/d -> HRT needs 20,000 m3
            ("2024-12", "filter_cake", 3_000),  # 20.72 t VS/d... /31 d -> OLR needs ~6,684 m3
        ]
    )
    v = size_digester(feed, {"vinasse": VINASSE, "filter_cake": CAKE}, LIMITS)
    assert v == pytest.approx(20_000)
    out = simulate(feed, {"vinasse": VINASSE, "filter_cake": CAKE}, _design(volume=v), LIMITS)
    assert out["olr_ok"].all() and out["hrt_ok"].all()


def test_bad_inputs_are_refused():
    with pytest.raises(KeyError):
        simulate(_feed([("2024-06", "manure", 1)]), {"vinasse": VINASSE}, _design(), LIMITS)
    with pytest.raises(ValueError):
        Substrate(name="x", basis="cod", density_t_per_m3=1, ts_frac_fm=0.1, vs_frac_ts=0.5)
    with pytest.raises(ValueError):
        simulate(_feed([("2024-06", "vinasse", -1)]), {"vinasse": VINASSE}, _design(), LIMITS)


def test_volpi_2021_consistency():
    """Consistency with the two Volpi et al. 2021 values recorded in docs/10 §5 only.

    docs/10 gives the reactor's maximum OLR (4.8 g VS/L·d) and its yield (~230 NmL CH4/g VS,
    registry ``codig_bmp``). This test checks that a lab-scale run at that OLR reproduces that
    specific yield and is OLR-feasible only with the registry's upper OLR bound. A full
    reproduction needs the paper's feed composition and HRT, which are not recorded yet.
    """
    p = load_parameters()
    codig = Substrate(
        name="codig",
        basis="vs",
        density_t_per_m3=1.0,
        ts_frac_fm=0.10,
        vs_frac_ts=0.80,
        bmp_nm3_ch4_per_t_vs=p["codig_bmp"].require_central(),
    )
    volume_m3, olr = 1000.0, 4.8
    vs_t_month = olr * volume_m3 * 30 / 1000
    feed = _feed([("2024-06", "codig", vs_t_month / codig.vs_t_per_t_fm)])
    lab = OperatingLimits(olr_max_kg_vs_m3_d=p["olr_max_cstr"].high, hrt_min_d=0, bmp_fullscale=1.0)
    row = simulate(feed, {"codig": codig}, _design(volume_m3), lab).iloc[0]
    assert row["olr_kg_vs_m3_d"] == pytest.approx(olr)
    assert row["ch4_nm3"] / vs_t_month == pytest.approx(230)
    assert row["olr_ok"]
    central = OperatingLimits(
        olr_max_kg_vs_m3_d=p["olr_max_cstr"].central, hrt_min_d=0, bmp_fullscale=1.0
    )
    assert not simulate(feed, {"codig": codig}, _design(volume_m3), central).iloc[0]["olr_ok"]


def test_registry_builders_trace_every_value():
    params = load_parameters()
    subs = substrates_from_registry(params)
    for s in subs.values():
        assert s.param_ids and all(pid in params for pid in s.param_ids)
    vin = subs["vinasse"]
    assert vin.cod_kg_per_m3 == params["vin_cod"].central
    assert vin.k_kg_per_m3 == pytest.approx(params["vin_k2o"].central * K_PER_K2O)
    assert subs["filter_cake"].vs_t_per_t_fm == pytest.approx(0.28 * 0.74)
    lim = limits_from_registry(params)
    assert lim.olr_max_kg_vs_m3_d == params["olr_max_cstr"].central
    assert lim.hrt_min_d == params["hrt_cstr"].low


def test_registry_vinasse_yield_sits_inside_registry_volume_range():
    """Independent check: vin_cod x cod_removal x vin_ch4_yield vs the vin_ch4_vol range."""
    params = load_parameters()
    per_m3 = substrates_from_registry(params)["vinasse"].ch4_nm3(1.0, 30, 1.0)
    assert params["vin_ch4_vol"].low <= per_m3 <= params["vin_ch4_vol"].high
