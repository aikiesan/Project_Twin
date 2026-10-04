"""Bayesian calibration of the Huff cane-to-mill allocation (docs/13 §3.1, ADR-0004).

Model for mill *j*, year *t*, H3 cell *h* (cells × mills distance matrix in km)::

    score_hjt = α·log C_j − β·d_hj            (−∞ if mill inactive or d_hj > d_max)
    P_hjt     = softmax_j(score_hjt)          (cells with no reachable mill → "unallocated")
    Ĉ_jt      = Σ_h P_hjt · cane_ht
    log y_jt  ~ Normal(log Ĉ_jt + u_j, σ)     (RenovaBio mill-year cane, t)
    u_j       ~ Normal(0, τ)                  (mill effect: outsourcing, misallocated catchment)

Optional terms:

- ``lower_bound`` mask: observations known to be **lower bounds** (e.g. RenovaBio eligible-only
  volumes) enter as right-censored: P(log y_true ≥ log y_obs).
- ``state_totals``: interval-censored statewide totals per year (UNICA rounded values) —
  ``lo_t ≤ Σ_j Ĉ_jt ≤ hi_t`` with a soft Normal CDF of scale ``total_sd``.

Priors are **modelling choices** (weakly informative), not empirical values: pass a
:class:`HuffPriors` and report it in the methods. Frequentist v0 fitting lives in
``engine.supply.huff``; this module is the target method.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HuffPriors:
    """Prior hyper-parameters (state them in the paper's methods; justify in ADR-0004).

    Attributes:
        alpha_mu, alpha_sd: Normal prior on the capacity exponent α (truncated at 0).
        beta_sd: HalfNormal scale for the distance-decay β (1/km).
        sigma_sd: HalfNormal scale for observation log-error σ.
        tau_sd: HalfNormal scale for the mill-effect sd τ.
    """

    alpha_mu: float
    alpha_sd: float
    beta_sd: float
    sigma_sd: float
    tau_sd: float


@dataclass
class HuffData:
    """Inputs for one or more years (arrays are year-stacked along the first axis).

    Attributes:
        dist_km: [cells × mills] road distance (same network for all years).
        capacity: [mills] capacity (any consistent unit; only ratios matter via α).
        cane_t: [years × cells] cane per cell per year (t).
        active: [years × mills] boolean activity mask.
        obs_t: [years × mills] observed crush (t), NaN where unobserved.
        lower_bound: [years × mills] True where the observation is only a lower bound.
        d_max_km: truncation distance.
        state_totals: optional [years × 2] (lo, hi) statewide crush bounds (t).
        total_sd: softness of the interval constraint (t).
    """

    dist_km: np.ndarray
    capacity: np.ndarray
    cane_t: np.ndarray
    active: np.ndarray
    obs_t: np.ndarray
    lower_bound: np.ndarray | None = None
    d_max_km: float = np.inf
    state_totals: np.ndarray | None = None
    total_sd: float | None = None

    def validate(self) -> None:
        n_cells, n_mills = self.dist_km.shape
        n_years = self.cane_t.shape[0]
        assert self.capacity.shape == (n_mills,), "capacity shape"
        assert self.cane_t.shape == (n_years, n_cells), "cane_t shape"
        assert self.active.shape == (n_years, n_mills), "active shape"
        assert self.obs_t.shape == (n_years, n_mills), "obs_t shape"
        if self.lower_bound is not None:
            assert self.lower_bound.shape == (n_years, n_mills), "lower_bound shape"
        if self.state_totals is not None:
            assert self.state_totals.shape == (n_years, 2), "state_totals shape"
            if self.total_sd is None or self.total_sd <= 0:
                raise ValueError("state_totals requires a positive total_sd")
        if np.any(self.capacity <= 0):
            raise ValueError("capacity must be > 0")


def build_model(data: HuffData, priors: HuffPriors):
    """Return a PyMC model implementing the module docstring."""
    import pymc as pm
    import pytensor.tensor as pt

    data.validate()
    n_years, n_cells = data.cane_t.shape
    n_mills = data.capacity.shape[0]
    reach = data.dist_km <= data.d_max_km  # [cells × mills]
    allowed = reach[None, :, :] & data.active[:, None, :]  # [years × cells × mills]
    has_mill = allowed.any(axis=2)  # [years × cells]
    obs = np.asarray(data.obs_t, dtype=float)
    observed = np.isfinite(obs) & (obs > 0)
    lb = np.zeros_like(observed) if data.lower_bound is None else data.lower_bound.astype(bool)
    exact = observed & ~lb
    censored = observed & lb
    log_cap = np.log(data.capacity)
    dist = np.where(reach, data.dist_km, 0.0)
    cane_eff = np.where(has_mill, data.cane_t, 0.0)  # cells without a mill → unallocated

    with pm.Model() as model:
        alpha = pm.TruncatedNormal("alpha", mu=priors.alpha_mu, sigma=priors.alpha_sd, lower=0.0)
        beta = pm.HalfNormal("beta", sigma=priors.beta_sd)
        sigma = pm.HalfNormal("sigma", sigma=priors.sigma_sd)
        tau = pm.HalfNormal("tau", sigma=priors.tau_sd)
        z = pm.Normal("z", 0.0, 1.0, shape=n_mills)
        u = pm.Deterministic("u", tau * z)

        score = alpha * log_cap[None, None, :] - beta * dist[None, :, :]
        # stable masked softmax (finite sentinel instead of −inf keeps gradients NaN-free);
        # cells with no reachable mill get zero weight and zero cane (→ unallocated)
        masked = pt.where(allowed, score, -1e30)
        smax = pt.max(masked, axis=2, keepdims=True)
        w = pt.where(allowed, pt.exp(masked - smax), 0.0)
        denom = pt.maximum(pt.sum(w, axis=2, keepdims=True), 1e-300)
        prob = w / denom
        crush = pm.Deterministic("crush_t", pt.sum(prob * cane_eff[:, :, None], axis=1))
        mu = pt.log(pt.maximum(crush, 1e-9)) + u[None, :]

        if exact.any():
            yi, mj = np.nonzero(exact)
            pm.Normal("y_obs", mu=mu[yi, mj], sigma=sigma, observed=np.log(obs[yi, mj]))
        if censored.any():
            yi, mj = np.nonzero(censored)
            z_c = (np.log(obs[yi, mj]) - mu[yi, mj]) / sigma
            # log P(Y ≥ y_obs) = log(1 − Φ(z)) = log Φ(−z)
            pm.Potential("y_lower_bound", pt.sum(pm.math.log(pm.math.invprobit(-z_c) + 1e-300)))
        if data.state_totals is not None:
            total = pt.sum(crush, axis=1)
            lo = data.state_totals[:, 0]
            hi = data.state_totals[:, 1]
            p_in = pm.math.invprobit((hi - total) / data.total_sd) - pm.math.invprobit(
                (lo - total) / data.total_sd
            )
            pm.Potential("state_total_interval", pt.sum(pt.log(pt.maximum(p_in, 1e-300))))
    return model


def fit(
    data: HuffData,
    priors: HuffPriors,
    draws: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    seed: int = 0,
    **kwargs,
):
    """Sample the posterior with NUTS; returns an ArviZ ``InferenceData``."""
    import pymc as pm

    model = build_model(data, priors)
    with model:
        return pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            random_seed=seed,
            progressbar=False,
            **kwargs,
        )


def simulate(
    dist_km: np.ndarray,
    capacity: np.ndarray,
    cane_t: np.ndarray,
    active: np.ndarray,
    alpha: float,
    beta: float,
    d_max_km: float = np.inf,
) -> np.ndarray:
    """Forward Huff allocation in numpy ([years × mills] crush); used for tests and PPCs."""
    reach = dist_km <= d_max_km
    allowed = reach[None, :, :] & active[:, None, :]
    score = alpha * np.log(capacity)[None, None, :] - beta * np.where(reach, dist_km, 0.0)[None]
    masked = np.where(allowed, score, -1e30)
    smax = np.max(masked, axis=2, keepdims=True)
    w = np.where(allowed, np.exp(masked - smax), 0.0)
    denom = np.maximum(w.sum(axis=2, keepdims=True), 1e-300)
    prob = w / denom
    cane_eff = np.where(allowed.any(axis=2), cane_t, 0.0)
    return np.einsum("ycm,yc->ym", prob, cane_eff)
