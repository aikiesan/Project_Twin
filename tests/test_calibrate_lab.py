"""Tests for lab/pilot data processing on SYNTHETIC curves (no real lab data in git)."""

import numpy as np
import pandas as pd
import pytest

from engine.calibrate.lab import (
    bmp_validity,
    first_order,
    fit_first_order,
    fit_gompertz,
    gompertz,
    load_bmp,
    net_specific_yield,
    proposed_registry_rows,
    summarize_cstr,
)

DAYS = np.array([0, 1, 2, 4, 7, 10, 14, 21, 28, 35])


def _synthetic_bmp():
    """Synthetic experiment: blank produces 2 NmL/d·(1-e^-0.2t)*?; sample B0=230, k=0.15."""
    rows = []
    blank = 50.0 * (1 - np.exp(-0.2 * DAYS))  # NmL from inoculum alone (15 g VS)
    for rep in (1, 2, 3):
        for d, vb in zip(DAYS, blank, strict=True):
            rows.append(("E", "blank", f"BL{rep}", "blank", rep, 15.0, 0.0, d, vb))
        net = 7.5 * first_order(DAYS, 230.0 * (1 + 0.01 * (rep - 2)), 0.15)
        for d, vb, vn in zip(DAYS, blank, net, strict=True):
            rows.append(("E", "fc", f"S{rep}", "sample", rep, 15.0, 7.5, d, vb + vn))
        pc = 7.5 * first_order(DAYS, 350.0, 0.3)
        for d, vb, vp in zip(DAYS, blank, pc, strict=True):
            rows.append(
                ("E", "cellulose", f"P{rep}", "positive_control", rep, 15.0, 7.5, d, vb + vp)
            )
    cols = [
        "experiment_id",
        "substrate_id",
        "bottle_id",
        "role",
        "replicate",
        "inoculum_vs_g",
        "substrate_vs_g",
        "day",
        "cum_ch4_nml",
    ]
    return pd.DataFrame(rows, columns=cols)


def test_load_bmp_rejects_bad_tables():
    df = _synthetic_bmp()
    load_bmp(df)  # valid
    bad = df.copy()
    bad.loc[bad.index[5], "cum_ch4_nml"] = -1
    with pytest.raises(ValueError, match="negative"):
        load_bmp(bad)
    bad = df.copy()
    bad.loc[bad["role"] == "blank", "substrate_vs_g"] = 1.0
    with pytest.raises(ValueError, match="blank bottles"):
        load_bmp(bad)
    bad = df.copy()
    bad.loc[bad.index[0], "role"] = "control"
    with pytest.raises(ValueError, match="unknown role"):
        load_bmp(bad)


def test_template_example_rows_are_skipped(root):
    df = load_bmp(root / "templates/lab/bmp_results_template.csv")
    assert df.empty  # template only contains synthetic example rows


def test_net_yield_removes_blank_exactly():
    curves = net_specific_yield(load_bmp(_synthetic_bmp()))
    s2 = curves[(curves["bottle_id"] == "S2")].sort_values("day")
    # rep 2 has B0 = 230 exactly → yield(t) = 230(1 − e^{−0.15 t})
    np.testing.assert_allclose(s2["yield_nml_per_gvs"], first_order(DAYS, 230.0, 0.15), atol=1e-9)


def test_first_order_fit_recovers_parameters():
    y = first_order(DAYS, 230.0, 0.15)
    fit = fit_first_order(DAYS, y)
    assert fit.params["b0_nml_gvs"] == pytest.approx(230.0, rel=1e-6)
    assert fit.params["k_per_d"] == pytest.approx(0.15, rel=1e-6)
    assert fit.r2 == pytest.approx(1.0)


def test_gompertz_fit_recovers_parameters():
    t = np.linspace(0, 40, 41)
    y = gompertz(t, 250.0, 20.0, 2.0)
    fit = fit_gompertz(t, y)
    assert fit.params["bmax_nml_gvs"] == pytest.approx(250.0, rel=1e-4)
    assert fit.params["rmax_nml_gvs_d"] == pytest.approx(20.0, rel=1e-3)
    assert fit.params["lag_d"] == pytest.approx(2.0, abs=1e-3)


def test_bmp_validity_flags():
    curves = net_specific_yield(load_bmp(_synthetic_bmp()))
    curves = curves.rename(columns={"yield_nml_per_gvs": "yield_nml_gvs"})
    # thresholds below are SYNTHETIC test values, not Holliger 2016 criteria
    v = bmp_validity(curves, 350.0, 0.85, 1.0, 0.05, 0.01).set_index("substrate_id")
    pc = v.loc["cellulose"]
    # cellulose: 350·(1 − e^{−0.3·35}) = 349.99 → recovery ≈ 1.0
    assert pc["pc_recovery"] == pytest.approx(1.0, abs=1e-3)
    assert pc["ok_pc"] is True or pc["ok_pc"] == True  # noqa: E712
    fc = v.loc["fc"]
    assert fc["ok_rsd"]  # replicates differ by ±1 % → RSD ≈ 0.01
    # last interval 28→35 d: 230(e^−4.2 − e^−5.25)/7 = 0.320 NmL/gVS/d; ÷ 228.8 ≈ 0.0014 < 0.01
    assert fc["ok_termination"]


def test_summarize_cstr_hand_computed():
    log = pd.DataFrame(
        {
            "reactor_id": ["R1"] * 2,
            "date": ["2026-10-05", "2026-10-06"],
            "working_volume_l": [4.0, 4.0],
            "feed_vs_g": ["8;4", "12"],
            "effluent_volume_l": [0.2, 0.2],
            "biogas_nl": [5.0, 5.0],
            "ch4_pct": [60.0, 60.0],
            "fos_mg_l": [1000, 1000],
            "tac_mg_caco3_l": [4000, 4000],
        }
    )
    s = summarize_cstr(log, period="W", fos_tac_limit=0.3).iloc[0]
    # feed 12 g VS/d over 4 L → OLR 3.0 g VS/L·d; HRT 4/0.2 = 20 d
    assert s["olr_gvs_l_d"] == pytest.approx(3.0)
    assert s["hrt_d"] == pytest.approx(20.0)
    # CH4 = 5 NL × 0.60 = 3 NL/d = 3000 NmL/d ÷ 12 g VS/d = 250 NmL/g VS
    assert s["spec_yield_nml_gvs"] == pytest.approx(250.0)
    assert s["fos_tac"] == pytest.approx(0.25)
    assert bool(s["ok_fos_tac"])


def test_proposed_row_format():
    row = proposed_registry_rows(
        "fc_bmp",
        "process",
        "Filter cake BMP",
        [220, 230, 240],
        "NL CH4 per kg VS",
        "E6",
        "LABIOEN",
        "2026-12-01",
    )
    parts = row.split(",")
    assert parts[:7] == [
        "fc_bmp",
        "process",
        "Filter cake BMP",
        "230",
        "220",
        "240",
        "NL CH4 per kg VS",
    ]
    assert parts[8] == "V"
    assert len(parts) == 17  # parameters.csv width, evidence columns left for the reviewer
