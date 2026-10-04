"""Bayesian Huff calibration on a SYNTHETIC problem (parameter recovery). Slow-ish (~1 min)."""

import numpy as np
import pytest

from engine.calibrate.bayes_huff import HuffData, HuffPriors, build_model, fit, simulate

pm = pytest.importorskip("pymc")

# Weakly-informative priors used ONLY for this synthetic test
PRIORS = HuffPriors(alpha_mu=1.0, alpha_sd=0.5, beta_sd=0.2, sigma_sd=0.3, tau_sd=0.1)


def _problem(seed=1, n_cells=150, n_mills=5, n_years=2, alpha=1.0, beta=0.08):
    rng = np.random.default_rng(seed)
    cells = rng.uniform(0, 100, size=(n_cells, 2))
    mills = rng.uniform(10, 90, size=(n_mills, 2))
    dist = np.linalg.norm(cells[:, None, :] - mills[None, :, :], axis=2) * 1.3
    cap = rng.uniform(1.0, 4.0, size=n_mills)
    cane = rng.gamma(2.0, 5_000.0, size=(n_years, n_cells))
    active = np.ones((n_years, n_mills), dtype=bool)
    active[1, 0] = False  # mill 0 idle in year 2
    crush = simulate(dist, cap, cane, active, alpha, beta, d_max_km=60.0)
    noise = np.exp(rng.normal(0, 0.03, size=crush.shape))
    obs = np.where(active, crush * noise, np.nan)
    return dist, cap, cane, active, crush, obs


def test_simulate_conserves_reachable_cane():
    dist, cap, cane, active, crush, _ = _problem()
    reach_any = ((dist <= 60.0)[None] & active[:, None, :]).any(axis=2)
    np.testing.assert_allclose(crush.sum(axis=1), (cane * reach_any).sum(axis=1), rtol=1e-10)
    assert crush[1, 0] == 0.0  # inactive mill gets nothing


def test_model_builds_with_all_terms():
    dist, cap, cane, active, crush, obs = _problem()
    lb = np.zeros_like(active)
    lb[0, 1] = True
    totals = np.stack([crush.sum(1) * 0.98, crush.sum(1) * 1.02], axis=1)
    data = HuffData(dist, cap, cane, active, obs, lb, 60.0, totals, total_sd=1_000.0)
    model = build_model(data, PRIORS)
    names = {v.name for v in model.free_RVs}
    assert {"alpha", "beta", "sigma", "tau", "z"} <= names
    assert {p.name for p in model.potentials} == {"y_lower_bound", "state_total_interval"}
    lp = model.compile_logp()(model.initial_point())
    assert np.isfinite(lp)


def test_posterior_recovers_alpha_beta():
    dist, cap, cane, active, _, obs = _problem()
    data = HuffData(dist, cap, cane, active, obs, d_max_km=60.0)
    idata = fit(data, PRIORS, draws=300, tune=400, chains=2, seed=3, cores=1)
    post = idata.posterior
    beta_mean = float(post["beta"].mean())
    alpha_mean = float(post["alpha"].mean())
    # truth: alpha=1.0, beta=0.08; tolerance reflects 9 noisy observations
    assert beta_mean == pytest.approx(0.08, abs=0.03)
    assert alpha_mean == pytest.approx(1.0, abs=0.5)
