"""Residues v0 (docs/09 Step 4-5): arithmetic, harvest profile, AD shares, feed table."""

import pandas as pd
import pytest

from engine.process.mass_balance import FEED_COLUMNS, substrates_from_registry
from engine.registry import load_parameters
from engine.supply.residues import (
    CROP_YEAR_MONTHS,
    FEED_SUBSTRATES,
    UNIFORM_APR_NOV,
    ResidueCoefficients,
    check_profile,
    coefficients_from_registry,
    monthly_residues,
    to_feed,
)

COEFFS = ResidueCoefficients(
    ethanol_l_per_t_cane=80,
    vinasse_l_per_l_ethanol=10,
    filter_cake_kg_per_t_cane=40,
    straw_kg_dm_per_t_cane=150,
    straw_recoverable_frac=0.5,
    straw_ts_frac_fm=0.5,
)
ALL_TO_AD = {"vinasse_to_ad_frac": 1.0, "filter_cake_to_ad_frac": 1.0, "straw_to_ad_frac": 1.0}


def test_season_totals_follow_the_coefficients():
    r = monthly_residues(1_000_000, 2024, COEFFS, **ALL_TO_AD)
    assert r["cane_t"].sum() == pytest.approx(1_000_000)
    assert r["ethanol_m3"].sum() == pytest.approx(80_000)  # 1 Mt x 80 L/t
    assert r["vinasse_generated_m3"].sum() == pytest.approx(800_000)  # x 10 L/L
    assert r["filter_cake_generated_t_fm"].sum() == pytest.approx(40_000)  # x 40 kg/t
    assert r["straw_recoverable_t_dm"].sum() == pytest.approx(75_000)  # x 150 kg x 0.5
    assert r["straw_to_ad_t_fm"].sum() == pytest.approx(150_000)  # DM / TS 0.5


def test_months_run_april_to_march_with_zeros_off_season():
    r = monthly_residues(800, 2024, COEFFS, **ALL_TO_AD)
    assert list(r["month"]) == [f"2024-{m:02d}" for m in range(4, 13)] + [
        f"2025-{m:02d}" for m in range(1, 4)
    ]
    assert len(r) == len(CROP_YEAR_MONTHS)
    by_month = r.set_index("month")["cane_t"]
    assert by_month["2024-04"] == pytest.approx(100)  # 800 / 8 months
    assert (by_month[["2024-12", "2025-01", "2025-02", "2025-03"]] == 0).all()


def test_generated_is_kept_apart_from_what_goes_to_ad():
    r = monthly_residues(
        1000,
        2024,
        COEFFS,
        vinasse_to_ad_frac=0.5,
        filter_cake_to_ad_frac=0.25,
        straw_to_ad_frac=0.0,
    )
    assert r["vinasse_to_ad_m3"].sum() == pytest.approx(0.5 * r["vinasse_generated_m3"].sum())
    assert r["filter_cake_to_ad_t_fm"].sum() == pytest.approx(
        0.25 * r["filter_cake_generated_t_fm"].sum()
    )
    assert r["straw_to_ad_t_fm"].sum() == 0
    assert r["straw_recoverable_t_dm"].sum() > 0


def test_own_ethanol_volume_replaces_the_yield():
    r = monthly_residues(1000, 2024, COEFFS, ethanol_l=50_000, **ALL_TO_AD)
    assert r["ethanol_m3"].sum() == pytest.approx(50)
    assert r["vinasse_generated_m3"].sum() == pytest.approx(500)
    assert r["filter_cake_generated_t_fm"].sum() == pytest.approx(40)  # still cane-based


def test_custom_profile():
    r = monthly_residues(1000, 2024, COEFFS, profile={6: 0.75, 7: 0.25}, **ALL_TO_AD)
    by_month = r.set_index("month")["cane_t"]
    assert by_month["2024-06"] == pytest.approx(750)
    assert by_month["2024-07"] == pytest.approx(250)
    assert by_month.sum() == pytest.approx(1000)


@pytest.mark.parametrize(
    "profile, message",
    [({4: 0.5, 5: 0.4}, "sum to 1"), ({4: 1.2, 5: -0.2}, ">= 0"), ({13: 1.0}, "1-12")],
)
def test_bad_profiles_are_rejected(profile, message):
    with pytest.raises(ValueError, match=message):
        check_profile(profile)


def test_uniform_profile_is_valid():
    shares = check_profile(UNIFORM_APR_NOV)
    assert sum(shares.values()) == pytest.approx(1)
    assert shares[12] == shares[1] == 0


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_ad_fractions_must_be_fractions(bad):
    with pytest.raises(ValueError, match="vinasse_to_ad_frac"):
        monthly_residues(
            1000, 2024, COEFFS, vinasse_to_ad_frac=bad, filter_cake_to_ad_frac=1, straw_to_ad_frac=1
        )


def test_negative_inputs_are_rejected():
    with pytest.raises(ValueError, match="cane_t"):
        monthly_residues(-1, 2024, COEFFS, **ALL_TO_AD)
    with pytest.raises(ValueError, match="straw_ts_frac_fm"):
        ResidueCoefficients(80, 10, 40, 150, 0.5, 0.0)


def test_feed_table_matches_the_process_module():
    r = monthly_residues(1000, 2024, COEFFS, **ALL_TO_AD)
    feed = to_feed(r, vinasse_density_t_per_m3=1.0)
    assert tuple(feed.columns) == FEED_COLUMNS
    assert set(feed["substrate"]) == set(FEED_SUBSTRATES)
    assert set(FEED_SUBSTRATES) <= set(substrates_from_registry())
    vin = feed[feed["substrate"] == "vinasse"]["fresh_t"].sum()
    assert vin == pytest.approx(r["vinasse_to_ad_m3"].sum())
    dense = to_feed(r, vinasse_density_t_per_m3=1.02)
    assert dense[dense["substrate"] == "vinasse"]["fresh_t"].sum() == pytest.approx(1.02 * vin)
    with pytest.raises(ValueError):
        to_feed(r, vinasse_density_t_per_m3=0)


def test_registry_builder_traces_every_value():
    params = load_parameters()
    c = coefficients_from_registry(params)
    assert c.param_ids and all(pid in params for pid in c.param_ids)
    assert c.vinasse_l_per_l_ethanol == params["vin_gen"].central
    assert c.straw_ts_frac_fm == pytest.approx(params["straw_ts"].central / 100)


def test_santa_adelia_2023_cane_gives_ethanol_close_to_the_report():
    """The D-flagged ethanol_yield (81 L/t) was derived from the Santa Adélia 2023 report.

    evidence/README.md: cane 3,551,156.27 t; anhydrous 225,336,933 L + hydrated 61,836,900 L.
    """
    cane_t, ethanol_l = 3_551_156.27, 225_336_933 + 61_836_900
    r = monthly_residues(cane_t, 2023, coefficients_from_registry(), **ALL_TO_AD)
    assert r["ethanol_m3"].sum() * 1000 == pytest.approx(ethanol_l, rel=0.01)


def test_output_is_a_dataframe_with_unit_suffixed_columns():
    r = monthly_residues(1000, 2024, COEFFS, **ALL_TO_AD)
    assert isinstance(r, pd.DataFrame)
    for col in r.columns.drop("month"):
        assert col.endswith(("_t", "_m3", "_t_fm", "_t_dm"))
