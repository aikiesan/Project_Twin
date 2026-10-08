import math
from pathlib import Path

import pandas as pd
import pytest

from engine.calibrate.anp_units import read_reported
from engine.calibrate.plant_yield import closure_values, feed_to_gas
from engine.process.mass_balance import Substrate
from engine.registry import Param

FIX = Path(__file__).parent / "fixtures" / "plant_yield" / "reported_small.csv"

# Vinasse: 20 kg COD/m3 x 0.5 removal x 0.3 Nm3/kg = 3 Nm3 CH4 per m3.
# Filter cake: 0.25 x 0.8 = 0.2 t VS/t x 200 Nm3/t VS x full-scale 0.5 = 20 Nm3 CH4 per t.
SUBS = {
    "vinasse": Substrate(
        name="vinasse",
        basis="cod",
        density_t_per_m3=1.0,
        ts_frac_fm=0.02,
        vs_frac_ts=0.6,
        cod_kg_per_m3=20.0,
        cod_removal_frac=0.5,
        ch4_yield_nm3_per_kg_cod=0.3,
    ),
    "filter_cake": Substrate(
        name="filter_cake",
        basis="vs",
        density_t_per_m3=1.0,
        ts_frac_fm=0.25,
        vs_frac_ts=0.8,
        bmp_nm3_ch4_per_t_vs=200.0,
    ),
}


def _param(pid, central, low=None, high=None):
    return Param(
        id=pid,
        module="process",
        name=pid,
        central=central,
        low=low,
        high=high,
        unit="-",
        source="synthetic",
        confidence="S",
        notes="",
        raw_central=str(central),
        raw_low="" if low is None else str(low),
        raw_high="" if high is None else str(high),
    )


PARAMS = {
    "vin_cod": _param("vin_cod", 20.0, 10.0, 60.0),
    "cod_removal": _param("cod_removal", 50.0, 40.0, 60.0),
    "vin_ch4_yield": _param("vin_ch4_yield", 0.3, 0.25, 0.34),
    "fc_bmp": _param("fc_bmp", 200.0, 150.0, 800.0),
    "bmp_fullscale": _param("bmp_fullscale", 0.5),
}


def test_feed_to_gas_models_vinasse_and_cake_only():
    t = feed_to_gas(read_reported(FIX), "plant_p", SUBS, bmp_fullscale=0.5, x_ch4=(0.5,))
    assert list(t["period"]) == ["2023/24", "2024"]
    s = t.iloc[0]
    assert s["ch4_vinasse_nm3"] == pytest.approx(300_000)
    assert s["ch4_filter_cake_nm3"] == pytest.approx(200_000)
    assert s["biogas_modelled_nm3"] == pytest.approx(1_000_000)  # 500,000 CH4 / 0.5
    assert s["explained_share"] == pytest.approx(0.5)
    # the 1,000,000 Nm3 gap over 1,000 t of other waste
    assert s["unmodelled_feed_t"] == 1000 and s["cofeed_nm3_biogas_per_t"] == pytest.approx(1000)
    assert s["biomethane_per_upgrading_biogas"] == pytest.approx(0.6)
    c = t.iloc[1]
    assert math.isnan(c["biogas_modelled_nm3"]) and c["note"].endswith("filter_cake_processed")


def test_feed_to_gas_runs_each_ch4_fraction_and_refuses_bad_input():
    rep = read_reported(FIX)
    t = feed_to_gas(rep, "plant_p", SUBS, bmp_fullscale=0.5, x_ch4=(0.5, 0.625))
    first = t[t["period"] == "2023/24"]
    assert list(first["biogas_modelled_nm3"]) == pytest.approx([1_000_000, 800_000])
    assert feed_to_gas(rep, "plant_q", SUBS, 0.5).empty  # feed but no biogas
    with pytest.raises(ValueError, match="no reported rows"):
        feed_to_gas(rep, "nobody", SUBS, 0.5)
    clash = rep.iloc[[0]].assign(row_id="clash", value=1.0)
    with pytest.raises(ValueError, match="reported values differ"):
        feed_to_gas(pd.concat([rep, clash]), "plant_p", SUBS, 0.5)


def test_closure_values_scale_each_parameter_alone():
    t = feed_to_gas(read_reported(FIX), "plant_p", SUBS, bmp_fullscale=0.5, x_ch4=(0.5,))
    c = closure_values(t, PARAMS).set_index("param")
    # need 1,000,000 CH4: vinasse must give 800,000 (x 8/3), filter cake 700,000 (x 3.5)
    assert c.loc["vin_cod", "closure"] == pytest.approx(20 * 8 / 3)
    assert c.loc["vin_cod", "in_range"] is True
    assert c.loc["cod_removal", "in_range"] is False
    assert c.loc["fc_bmp", "closure"] == pytest.approx(700.0)
    assert c.loc["bmp_fullscale", "closure"] == pytest.approx(1.75)
    assert c.loc["bmp_fullscale", "in_range"] is None  # no range in the registry row
    assert set(c["period"]) == {"2023/24"}  # the period without modelled CH4 is skipped
    # composite rows: CH4 per unit of feed, now and at closure
    assert c.loc["vinasse_ch4_per_m3", "central"] == pytest.approx(3.0)
    assert c.loc["vinasse_ch4_per_m3", "closure"] == pytest.approx(8.0)
    assert c.loc["filter_cake_ch4_per_t_fm", "closure"] == pytest.approx(70.0)
    assert c.loc["filter_cake_ch4_per_t_fm", "flag"] == "D"
