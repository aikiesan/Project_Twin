from pathlib import Path

import pandas as pd
import pytest

from engine.calibrate.anp_units import (
    plant_period_check,
    plant_rows,
    read_capacity,
    read_production,
    read_reported,
    state_check,
    summarise,
    thousand_scale_months,
)

FIX = Path(__file__).parent / "fixtures" / "anp"


def test_read_capacity_parses_brazilian_decimals():
    cap = read_capacity(FIX / "capacidade_small.csv")
    assert cap["cap_biomethane_m3_d"].iloc[0] == 5000.0
    assert cap["biogas_processed_m3_d"].iloc[0] == 20.0
    assert str(cap["month"].iloc[0]) == "2024-01"


def test_thousand_scale_months_flags_only_small_positive_values():
    cap = read_capacity(FIX / "capacidade_small.csv")
    flagged = thousand_scale_months(cap)
    assert list(flagged["operator"]) == ["PLANT A"]  # 20 of 10,000; zero rows are not flagged


def test_state_check_rescales_only_named_plants():
    cap = read_capacity(FIX / "capacidade_small.csv")
    prod = read_production(FIX / "producao_small.csv")
    t = state_check(cap, prod, "São Paulo", ("TOWNA",))
    jan = t.loc[t.index.astype(str) == "2024-01"].iloc[0]
    # A: 20 m3/d x 0.5 x 31 = 310 as published, x1000 = 310,000; B: 10,000 x 0.5 x 31 = 155,000
    assert jan["implied_as_published"] == pytest.approx(155_310)
    assert jan["implied_rescaled"] == pytest.approx(465_000)
    assert jan["ratio_rescaled"] == pytest.approx(1.0)
    feb = t.loc[t.index.astype(str) == "2024-02"].iloc[0]
    assert feb["implied_rescaled"] == feb["implied_as_published"]  # 4,000 is not small
    s = summarise(t)
    assert s.loc["ratio_rescaled", "months"] == 2


def test_plant_period_check_sums_months_and_rescales_flagged_ones():
    cap = read_capacity(FIX / "capacidade_small.csv")
    rep = read_reported(FIX / "plant_reported_small.csv")
    t = plant_period_check(cap, rep, "plant_a", "TOWNA")
    assert list(t["period"]) == ["2023/24", "2024"]
    s = t.iloc[0]
    # Jan 2024: 20 m3/d x 31 d (flagged, x1000 = 620,000); Feb 2024: 4,000 x 29 = 116,000
    assert s["months_in_period"] == 12 and s["anp_months"] == 2
    assert s["anp_m3_as_published"] == pytest.approx(116_620)
    assert s["anp_m3_rescaled"] == pytest.approx(736_000)
    assert s["ratio_rescaled_to_biomethane_produced"] == pytest.approx(1.0)
    assert s["ratio_rescaled_to_biogas_produced"] == pytest.approx(0.5)
    assert pd.isna(s["reported_biogas_to_upgrading_nm3"])
    c = t.iloc[1]
    assert c["period_kind"] == "calendar" and c["anp_m3_rescaled"] == pytest.approx(736_000)
    assert pd.isna(c["ratio_rescaled_to_biogas_produced"])


def test_plant_period_check_refuses_conflicts_and_unknown_plants():
    cap = read_capacity(FIX / "capacidade_small.csv")
    rep = read_reported(FIX / "plant_reported_small.csv")
    with pytest.raises(ValueError, match="no ANP rows"):
        plant_period_check(cap, rep, "plant_a", "NOWHERE")
    clash = rep.iloc[[0]].assign(row_id="clash", value=999.0)
    with pytest.raises(ValueError, match="reported values differ"):
        plant_period_check(cap, pd.concat([rep, clash]), "plant_a", "TOWNA")


def test_plant_period_check_sums_plants_reported_as_one_total():
    cap = read_capacity(FIX / "capacidade_small.csv")
    rep = read_reported(FIX / "plant_reported_small.csv")
    t = plant_period_check(cap, rep, "plant_ab", ["TOWNA", "TOWNB"])
    s = t.iloc[0]
    # A as above (116,620 published, 736,000 rescaled) + B: 10,000 x 31 in Jan, 0 in Feb
    assert s["anp_months"] == 2
    assert s["anp_m3_as_published"] == pytest.approx(426_620)
    assert s["anp_m3_rescaled"] == pytest.approx(1_046_000)
    assert s["ratio_rescaled_to_biomethane_produced"] == pytest.approx(1.0)
    with pytest.raises(ValueError, match="'NOWHERE'"):
        plant_period_check(cap, rep, "plant_ab", ["TOWNA", "NOWHERE"])


def test_plant_rows_keys_on_cnpj_and_refuses_shared_municipalities():
    cap = read_capacity(FIX / "capacidade_small.csv")
    rep = read_reported(FIX / "plant_reported_small.csv")
    by_cnpj = plant_period_check(cap, rep, "plant_ab", ["00000000000001", "00000000000002"])
    by_town = plant_period_check(cap, rep, "plant_ab", ["TOWNA", "TOWNB"])
    pd.testing.assert_frame_equal(by_cnpj, by_town)
    shared = cap.assign(municipality="TOWNA")  # both plants in one municipality
    with pytest.raises(ValueError, match="2 CNPJs"):
        plant_rows(shared, "TOWNA")
    assert set(plant_rows(shared, "00000000000001")["operator"]) == {"PLANT A"}
    with pytest.raises(ValueError, match="no ANP rows"):
        plant_rows(cap, "99999999999999")
