"""LCOB v0 (docs/11 §2): CRF, CAPEX scaling, annuity LCOB, unit conversion, registry anchors."""

import math

import pandas as pd
import pytest

from engine.economics.lcob import (
    ANCHORS,
    MJ_PER_MMBTU,
    brl_per_nm3_to_usd_per_mmbtu,
    capex_brl,
    compare_with_anchors,
    crf,
    economics_from_registry,
    lcob_annuity,
    lcob_from_registry,
)
from engine.process.mass_balance import (
    PlantDesign,
    limits_from_registry,
    simulate,
    size_digester,
    substrates_from_registry,
)
from engine.registry import load_parameters
from engine.supply.residues import coefficients_from_registry, monthly_residues, to_feed


def test_crf_closed_form():
    assert crf(0.10, 20) == pytest.approx(0.10 * 1.1**20 / (1.1**20 - 1))
    assert crf(0.10, 20) == pytest.approx(0.117460, abs=1e-6)
    assert crf(0.0, 20) == pytest.approx(1 / 20)
    with pytest.raises(ValueError):
        crf(0.1, 0)
    with pytest.raises(ValueError):
        crf(-0.01, 20)


def test_capex_linear_and_power_law():
    assert capex_brl(30_000, 4000) == pytest.approx(120e6)
    # at the reference capacity the power law equals the linear value
    assert capex_brl(30_000, 4000, ref_capacity_nm3_d=30_000, scale_exp=0.65) == pytest.approx(
        120e6
    )
    doubled = capex_brl(60_000, 4000, ref_capacity_nm3_d=30_000, scale_exp=0.65)
    assert doubled == pytest.approx(120e6 * 2**0.65)
    with pytest.raises(ValueError, match="both"):
        capex_brl(30_000, 4000, scale_exp=0.65)


def test_lcob_components_add_up():
    r = lcob_annuity(
        capex=100e6,
        annual_biomethane_nm3=10e6,
        rate=0.10,
        years=20,
        opex_fixed_brl_per_yr=1e6,
        opex_var_brl_per_nm3=0.15,
        feedstock_brl_per_yr=2e6,
        transport_brl_per_yr=0.5e6,
        coproduct_brl_per_yr=1e6,
    )
    assert r.capex_brl_per_nm3 == pytest.approx(100e6 * crf(0.10, 20) / 10e6)
    assert r.opex_brl_per_nm3 == pytest.approx(0.1 + 0.15)
    expected = r.capex_brl_per_nm3 + 0.25 + 0.2 + 0.05 - 0.1
    assert r.lcob_brl_per_nm3 == pytest.approx(expected)


def test_lower_output_raises_lcob():
    full = lcob_annuity(capex=100e6, annual_biomethane_nm3=10e6, rate=0.1, years=20)
    half = lcob_annuity(capex=100e6, annual_biomethane_nm3=5e6, rate=0.1, years=20)
    assert half.lcob_brl_per_nm3 == pytest.approx(2 * full.lcob_brl_per_nm3)


def test_zero_output_is_an_error():
    with pytest.raises(ValueError, match="undefined"):
        lcob_annuity(capex=1e6, annual_biomethane_nm3=0, rate=0.1, years=20)


def test_unit_conversion():
    # 1 R$/Nm3 at 5 R$/US$ and 38 MJ/Nm3 = 0.2 US$ per 38 MJ
    v = brl_per_nm3_to_usd_per_mmbtu(1.0, hhv_mj_per_nm3=38, brl_per_usd=5)
    assert v == pytest.approx(0.2 / 38 * MJ_PER_MMBTU)
    assert MJ_PER_MMBTU == pytest.approx(1055.056, abs=1e-3)
    with pytest.raises(ValueError):
        brl_per_nm3_to_usd_per_mmbtu(1.0, hhv_mj_per_nm3=0, brl_per_usd=5)


def test_registry_inputs_are_traced():
    params = load_parameters()
    e = economics_from_registry(params)
    assert all(pid in params for pid in e.param_ids)
    assert e.rate == pytest.approx(params["wacc_real"].central / 100)
    assert e.years == params["plant_life"].central
    assert e.specific_capex_brl_per_nm3_d == params["capex_epe"].central
    with pytest.raises(KeyError):
        economics_from_registry(params, capex_id="no_such_row")


def test_lcob_from_registry_matches_hand_calculation():
    params = load_parameters()
    nameplate, energy = 30_000.0, 0.5 * 30_000 * 365
    r = lcob_from_registry(nameplate, energy, params)
    capex = params["capex_epe"].central * nameplate
    rate = params["wacc_real"].central / 100
    years = int(params["plant_life"].central)
    expected = capex * crf(rate, years) / energy + params["opex_epe"].central
    assert r.lcob_brl_per_nm3 == pytest.approx(expected)


def test_anchor_table():
    df = compare_with_anchors(1.30, brl_per_usd=5.0)
    assert list(df["anchor_id"]) == list(ANCHORS)
    epe = df.set_index("anchor_id").loc["lcob_epe_sucro"]
    assert epe["engine_value"] == pytest.approx(1.30)
    assert epe["within_range"]
    fiesp = df.set_index("anchor_id").loc["lcob_fiesp"]
    hhv = load_parameters()["hhv_biomethane"].central
    assert fiesp["engine_value"] == pytest.approx(1.30 / 5.0 / hhv * MJ_PER_MMBTU)
    assert isinstance(df, pd.DataFrame) and df["confidence"].notna().all()


def test_skeleton_chain_runs_on_registry_values():
    """Cane -> residues -> CSTR mass balance -> LCOB, with registry central values.

    Inputs that the registry does not hold are test inputs here: cane crushed, the AD shares,
    the biogas CH4 fraction (docs/21 C13) and the nameplate. Only checks that the chain is
    consistent; the numbers are not results (ADR-0010).
    """
    params = load_parameters()
    residues = monthly_residues(
        2_000_000,
        2024,
        coefficients_from_registry(params),
        vinasse_to_ad_frac=1.0,
        filter_cake_to_ad_frac=1.0,
        straw_to_ad_frac=0.0,
    )
    subs = substrates_from_registry(params)
    feed = to_feed(residues, vinasse_density_t_per_m3=subs["vinasse"].density_t_per_m3)
    feed = feed[feed["substrate"] != "straw"]
    limits = limits_from_registry(params)
    volume = size_digester(feed, subs, limits)
    design = PlantDesign(
        digester_volume_m3=volume,
        upgrading_capacity_nm3_d=40_000,
        x_ch4=0.6,
        ch4_recovery_frac=params["upg_ch4_recovery"].central / 100,
    )
    out = simulate(feed, subs, design, limits)
    assert len(out) == 12
    off_season = out[out["month"].isin(["2024-12", "2025-01", "2025-02", "2025-03"])]
    assert (off_season["biomethane_nm3"] == 0).all()  # no storage in v0: S0-like
    annual = out["biomethane_nm3"].sum()
    assert annual > 0
    r = lcob_from_registry(design.upgrading_capacity_nm3_d, annual, params)
    assert math.isfinite(r.lcob_brl_per_nm3) and r.lcob_brl_per_nm3 > 0
    assert out["capacity_factor"].max() <= 1 + 1e-12
