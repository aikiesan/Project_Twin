"""Hierarchical CAPEX model on SYNTHETIC data (recovery of the scaling exponent)."""

import numpy as np
import pandas as pd
import pytest

from engine.economics.capex_hier import CapexPriors, fit, predict_capex, prepare

pytest.importorskip("pymc")

# Priors used ONLY for this synthetic test
PRIORS = CapexPriors(
    a_mu=0.0, a_sd=5.0, b_mu=0.65, b_sd=0.3, gamma_sd=0.5, delta_sd=0.5, tau_sd=0.5, sigma_sd=0.5
)


def _synthetic(seed=0, b=0.7):
    rng = np.random.default_rng(seed)
    rows = []
    u = {"BR": 0.2, "DE": -0.1, "DK": 0.0, "FR": -0.1}
    g = {"agro": 0.15, "landfill": -0.15}
    for country, n in (("BR", 12), ("DE", 25), ("DK", 15), ("FR", 20)):
        for _ in range(n):
            cap = float(np.exp(rng.uniform(np.log(5e3), np.log(2e5))))
            feed = "agro" if rng.random() < 0.6 else "landfill"
            scope = int(rng.random() < 0.3)
            logc = 2.0 + b * np.log(cap) + g[feed] + 0.25 * scope + u[country]
            rows.append((np.exp(logc + rng.normal(0, 0.15)), cap, feed, country, scope))
    return pd.DataFrame(rows, columns=["capex", "capacity_nm3_d", "feedstock", "country", "scope"])


def test_prepare_validates():
    df = _synthetic()
    p = prepare(df, "SYN_2025")
    assert p.attrs["country_levels"] == ["BR", "DE", "DK", "FR"]
    bad = df.assign(normalised=False)
    with pytest.raises(ValueError, match="normalise"):
        prepare(bad, "SYN_2025")
    with pytest.raises(ValueError, match="positive"):
        prepare(df.assign(capex=-1.0), "SYN_2025")


def test_fit_recovers_exponent_and_predicts():
    df = prepare(_synthetic(), "SYN_2025")
    model, idata = fit(df, PRIORS, draws=400, tune=500, chains=2, seed=1, cores=1)
    b = float(idata.posterior["b"].mean())
    assert b == pytest.approx(0.7, abs=0.06)
    draws_br = predict_capex(idata, df, model.x_center, 5e4, "agro", "BR", 0)
    draws_new = predict_capex(idata, df, model.x_center, 5e4, "agro", None, 0)
    truth_br = np.exp(2.0 + 0.7 * np.log(5e4) + 0.15 + 0.2)
    lo, hi = np.percentile(draws_br, [5, 95])
    assert lo < truth_br < hi
    # a new country is more uncertain than a fitted one
    assert np.std(np.log(draws_new)) > np.std(np.log(draws_br))
