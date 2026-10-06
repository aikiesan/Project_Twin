"""Off-season strategy S1 (docs/10 §3): silo balance, release profile, loss, validation."""

import pandas as pd
import pytest

from engine.process.strategies import StorageS1, apply_s1_storage, storage_balance
from engine.supply.residues import ResidueCoefficients, monthly_residues

COEFFS = ResidueCoefficients(80, 10, 40, 150, 0.5, 0.5)
HARVEST = (4, 5, 6, 7, 8, 9, 10, 11)
OFF = (12, 1, 2, 3)


def _residues(cane_t=800_000):
    return monthly_residues(
        cane_t,
        2024,
        COEFFS,
        vinasse_to_ad_frac=1.0,
        filter_cake_to_ad_frac=1.0,
        straw_to_ad_frac=0.0,
    )


def test_no_loss_conserves_cake_and_drains_by_the_last_release_month():
    r = _residues()
    s1 = apply_s1_storage(r, StorageS1(0.5, HARVEST, OFF, loss_frac_per_month=0.0))
    assert s1["filter_cake_to_ad_t_fm"].sum() == pytest.approx(r["filter_cake_to_ad_t_fm"].sum())
    by = s1.set_index("month")
    # 800 kt cane x 40 kg/t = 32 kt cake, 4 kt/month; half stored -> 16 kt, 4 kt per off month
    assert by.loc["2024-06", "filter_cake_to_ad_t_fm"] == pytest.approx(2000)
    for m in ("2024-12", "2025-01", "2025-02", "2025-03"):
        assert by.loc[m, "filter_cake_released_t_fm"] == pytest.approx(4000)
    assert by.loc["2025-03", "filter_cake_stock_t_fm"] == pytest.approx(0, abs=1e-9)
    assert (s1["vinasse_to_ad_m3"] == r["vinasse_to_ad_m3"]).all()


def test_loss_follows_the_pool_balance():
    r = _residues()
    lam = 0.05
    s1 = apply_s1_storage(r, StorageS1(1.0, HARVEST, OFF, loss_frac_per_month=lam))
    bal = storage_balance(s1)
    assert bal["filter_cake_storage_loss_t_fm"] > 0
    assert bal["filter_cake_stored_t_fm"] == pytest.approx(
        bal["filter_cake_released_t_fm"]
        + bal["filter_cake_storage_loss_t_fm"]
        + bal["filter_cake_end_stock_t_fm"]
    )
    by = s1.set_index("month")
    # first month: stored 4 kt, no loss yet; second month loses lam of the opening stock
    assert by.loc["2024-04", "filter_cake_storage_loss_t_fm"] == 0
    assert by.loc["2024-05", "filter_cake_storage_loss_t_fm"] == pytest.approx(lam * 4000)
    # all cake goes through the silo, so nothing is fed in the harvest
    assert by.loc["2024-07", "filter_cake_to_ad_t_fm"] == pytest.approx(0)


def test_release_shares():
    r = _residues()
    s1 = apply_s1_storage(
        r, StorageS1(0.5, HARVEST, (12, 1), loss_frac_per_month=0.0, release_shares=(3, 1))
    )
    by = s1.set_index("month")
    assert by.loc["2024-12", "filter_cake_released_t_fm"] == pytest.approx(0.75 * 16000)
    assert by.loc["2025-01", "filter_cake_released_t_fm"] == pytest.approx(0.25 * 16000)
    assert by.loc["2025-02", "filter_cake_released_t_fm"] == 0


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"store_frac": 1.5}, "store_frac"),
        ({"loss_frac_per_month": 1.0}, "loss_frac_per_month"),
        ({"release_months": (11, 12)}, "overlap"),
        ({"release_months": (12, 12)}, "repeated"),
        ({"release_months": (13,)}, "1-12"),
        ({"release_shares": (1.0,)}, "one share"),
    ],
)
def test_invalid_settings(kwargs, message):
    base = {
        "store_frac": 0.5,
        "store_months": HARVEST,
        "release_months": OFF,
        "loss_frac_per_month": 0.0,
    }
    base.update(kwargs)
    with pytest.raises(ValueError, match=message):
        StorageS1(**base)


def test_needs_the_residue_table():
    with pytest.raises(ValueError, match="filter_cake_to_ad_t_fm"):
        apply_s1_storage(pd.DataFrame({"month": ["2024-04"]}), StorageS1(0.5, HARVEST, OFF, 0.0))
