from pathlib import Path

import pytest

from engine.calibrate.anp_units import (
    read_capacity,
    read_production,
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
