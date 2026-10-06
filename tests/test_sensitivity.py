"""Morris screen of the skeleton (engine.sensitivity): factor space, cases, elasticities, outputs.

Uses the registry parameters held in git, the ANP evidence CSV and the skeleton test fixture
(whose cane values are test inputs, not data). Morris runs use few trajectories to stay fast.
"""

import json
import math
from pathlib import Path

import pandas as pd
import pytest

from engine.process.mass_balance import substrates_from_registry
from engine.registry import Param, load_parameters
from engine.sensitivity import (
    OUTPUTS,
    Factor,
    evaluate,
    factor_space,
    gate0_share,
    local_elasticities,
    main,
    mill_case,
    morris_screen,
    set_row,
    synthetic_case,
    write_outputs,
)
from engine.skeleton import MissingInputError, run_skeleton

FIXTURE = Path(__file__).parent / "fixtures" / "skeleton_mills_test.yaml"


def _param(pid, central, low="", high="", confidence="S"):
    def num(x):
        try:
            return float(x)
        except ValueError:
            return None

    return Param(
        id=pid,
        module="test",
        name=pid,
        central=num(central),
        low=num(low),
        high=num(high),
        unit="u",
        source="test",
        confidence=confidence,
        notes="",
        raw_central=central,
        raw_low=low,
        raw_high=high,
    )


@pytest.fixture(scope="module")
def params():
    return load_parameters()


@pytest.fixture(scope="module")
def case(params):
    return synthetic_case(params)


@pytest.fixture(scope="module")
def screen(case, params):
    return morris_screen(case, params, trajectories=3, seed=7)


def test_factor_space_takes_ranges_and_lists_every_other_row():
    p = {
        "a": _param("a", "2", "1", "3"),
        "pair": _param("pair", "28 / 74", "25-30 / 70-78"),
        "norange": _param("norange", "5"),
        "flat": _param("flat", "5", "5", "5"),
        "text": _param("text", "12 (4 mo) / 22 (6 mo)"),
    }
    factors, excluded = factor_space(p, list(p))
    assert [f.pid for f in factors] == ["a", "pair"]
    pair = factors[1]
    assert pair.is_pair and pair.lows == (25, 70) and pair.highs == (30, 78)
    assert pair.value_at(0.5) == (27.5, 74)
    reasons = {e.pid: e.reason for e in excluded}
    assert set(reasons) == {"norange", "flat", "text"}
    assert "no numeric range" in reasons["norange"]
    assert "not below" in reasons["flat"]
    assert "non-numeric" in reasons["text"]


def test_set_row_collapses_the_row_so_every_reader_sees_the_value(params):
    p = set_row(params, "hrt_cstr", [33.0])
    row = p["hrt_cstr"]
    assert row.central == row.low == row.high == 33.0  # limits read the low end as HRT_min
    assert params["hrt_cstr"].central == 30  # the input mapping is not changed
    q = set_row(params, "fc_ts_vs", [25.0, 70.0])
    cake = substrates_from_registry(q)["filter_cake"]
    assert cake.ts_frac_fm == pytest.approx(0.25) and cake.vs_frac_ts == pytest.approx(0.70)
    with pytest.raises(ValueError):
        set_row(params, "vin_cod", [1.0, 2.0, 3.0])


def test_synthetic_case_sits_at_the_peak_and_is_scale_free(params, case):
    assert case.label == "synthetic" and "SYNTHETIC" in case.basis
    base = evaluate(case, params)
    big = synthetic_case(params, cane_t=2 * case.cane_t)
    y2 = evaluate(big, params)
    assert y2["annual_biomethane_nm3"] == pytest.approx(2 * base["annual_biomethane_nm3"])
    assert y2["lcob_brl_per_nm3"] == pytest.approx(base["lcob_brl_per_nm3"])
    assert y2["capacity_factor_annual"] == pytest.approx(base["capacity_factor_annual"])
    assert base["months_infeasible"] == 0


def test_elasticities_are_one_sided_and_respect_the_valid_domain(params, case):
    e = local_elasticities(case, params, ["upg_ch4_recovery", "capex_epe", "straw_gen"])
    get = e.set_index(["param_id", "output"])
    # biomethane = CH4 × recovery below the cap: elasticity 1 downwards; 108.9 % is invalid
    rec = get.loc[("upg_ch4_recovery", "annual_biomethane_nm3")]
    assert rec["elasticity_down"] == pytest.approx(1.0)
    assert math.isnan(rec["elasticity_up"])
    # CAPEX does not change the gas, and LCOB moves less than 1:1 (OPEX share)
    assert get.loc[("capex_epe", "annual_biomethane_nm3"), "elasticity_up"] == 0
    assert 0 < get.loc[("capex_epe", "lcob_brl_per_nm3"), "elasticity_up"] < 1
    # straw is not fed in the case (AD share 0)
    assert get.loc[("straw_gen", "annual_biomethane_nm3"), "elasticity_down"] == 0


def test_morris_screen_ranks_registry_rows_and_lists_exclusions(screen):
    assert screen.run_id.startswith("morris-synthetic-")
    assert set(screen.morris["output"]) == set(OUTPUTS)
    pri = screen.priority.set_index("param_id")
    # rows that cannot move the outputs in this case (straw share 0, digester sized to the
    # OLR/HRT limits, COD/SO4 and K not evaluable for a cake mix) rank with zero effect
    for pid in ("straw_bmp_untreated", "olr_max_cstr", "hrt_cstr", "vin_so4", "k_inhib"):
        assert pri.loc[pid, "max_mu_star_rel"] == 0
    for pid in ("vin_cod", "capex_epe", "wacc_real", "fc_bmp"):
        assert pri.loc[pid, "max_mu_star_rel"] > 0
    capex = screen.morris.query("param_id == 'capex_epe'").set_index("output")
    assert capex.loc["annual_biomethane_nm3", "mu_star"] == 0
    assert capex.loc["lcob_brl_per_nm3", "mu_star"] > 0
    excluded = {e.pid: e.reason for e in screen.excluded}
    assert "no numeric range" in excluded["ethanol_yield"]
    assert set(pri.index).isdisjoint(excluded)
    # the HRT-sized digester is never flagged by rounding (mass_balance.CHECK_RTOL)
    infeasible = screen.morris.query("output == 'months_infeasible'").set_index("param_id")
    assert infeasible.loc["hrt_cstr", "mu_star"] == 0


def test_morris_screen_is_reproducible(case, params, screen):
    again = morris_screen(case, params, trajectories=3, seed=7)
    assert again.run_id == screen.run_id
    assert again.morris.equals(screen.morris)


def test_gate0_share_counts_v_among_moving_rows():
    pri = pd.DataFrame(
        {
            "param_id": ["a", "b", "c", "d"],
            "confidence": ["V", "S", "V", "V"],
            "max_mu_star_rel": [0.5, 0.2, 0.1, 0.0],
        }
    )
    g = gate0_share(pri, top_n=2)
    assert (g["n_ranked"], g["n_v"], g["share_v"]) == (2, 1, 0.5)
    assert gate0_share(pri)["n_ranked"] == 3  # the zero-effect row is not counted


def test_mill_case_matches_the_skeleton_run(params):
    ref = mill_case("narandiba_test", 2025, config_path=FIXTURE)
    assert ref.label == "narandiba_test-2025" and "test fixture" in ref.basis
    run = run_skeleton("narandiba_test", 2025, config_path=FIXTURE, params=params, out_dir=None)
    y = evaluate(ref, params)
    res = run.summary["results"]
    assert y["annual_biomethane_nm3"] == pytest.approx(res["annual_biomethane_nm3"])
    assert y["lcob_brl_per_nm3"] == pytest.approx(res["lcob"]["lcob_brl_per_nm3"])
    s1 = mill_case("storage_test", 2025, config_path=FIXTURE)
    assert s1.storage is not None and s1.storage.store_frac == 0.5


def test_mill_case_refuses_missing_cane():
    with pytest.raises(MissingInputError):
        mill_case("narandiba_test", 2026, config_path=FIXTURE)
    with pytest.raises(KeyError):
        mill_case("nope", 2025, config_path=FIXTURE)


def test_write_outputs(screen, tmp_path):
    path = write_outputs(screen, tmp_path)
    assert path.name == screen.run_id
    for name in ("morris.csv", "priority.csv", "elasticities.csv", "summary.json"):
        assert (path / name).is_file()
    summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    assert summary["run_id"] == screen.run_id
    assert summary["case"]["label"] == "synthetic"
    assert "ethanol_yield" in summary["excluded_max_abs_elasticity"]
    assert "x_ch4" in summary["not_screened_inputs"]


def test_cli_synthetic(capsys):
    assert main(["morris", "--synthetic", "--trajectories", "2", "--no-write"]) == 0
    out = capsys.readouterr().out
    assert "SYNTHETIC" in out and "excluded from the screen" in out and "Gate 0" in out


def test_cli_mill_without_cane_reports_and_exits_2(capsys):
    assert main(["morris", "--mill", "costa_pinto", "--crop-year", "2025", "--no-write"]) == 2
    assert "cannot run" in capsys.readouterr().out


def test_factor_is_frozen():
    f = Factor("a", (1.0,), (2.0,), (1.5,), "u", "S", "s")
    with pytest.raises(AttributeError):
        f.pid = "b"  # type: ignore[misc]
