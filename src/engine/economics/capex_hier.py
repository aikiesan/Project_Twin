"""Hierarchical Bayesian CAPEX model pooling Brazilian and international plants (ADR-0005).

docs/11 §3.2::

    log CAPEX_i = a + b·log cap_i + γ_feedstock[i] + δ·scope_i + u_country[i] + ε_i
    u_country ~ Normal(0, τ),   ε_i ~ Normal(0, σ)

Inputs must be **normalised before** fitting (docs/11 §3.2): one capacity basis (biomethane
Nm³/d, annual average), one currency and price year, and a scope flag (e.g. 1 = includes
grid connection/pipeline). This module does not convert anything — it refuses rows that are
not declared normalised.

Priors are modelling choices passed in :class:`CapexPriors` (docs/11 suggests b ~ N(0.65, 0.1)
— note that the centre equals registry ``scale_exp`` (D-flagged), so state the dependence).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("capex", "capacity_nm3_d", "feedstock", "country", "scope")


@dataclass(frozen=True)
class CapexPriors:
    """Prior hyper-parameters (report them; justify in ADR-0005)."""

    a_mu: float
    a_sd: float
    b_mu: float
    b_sd: float
    gamma_sd: float
    delta_sd: float
    tau_sd: float
    sigma_sd: float


def prepare(df: pd.DataFrame, currency_price_year: str) -> pd.DataFrame:
    """Validate a normalised table and add integer codes.

    Args:
        df: columns ``capex`` (> 0, in ``currency_price_year`` units), ``capacity_nm3_d``
            (> 0, biomethane, annual-average basis), ``feedstock``, ``country``,
            ``scope`` (0/1), optional ``normalised`` (bool, must be True when present).
        currency_price_year: label stored in ``df.attrs`` (e.g. ``"BRL_2025"``).
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns {missing}")
    out = df.copy()
    if "normalised" in out and not out["normalised"].astype(bool).all():
        raise ValueError("rows with normalised=False — normalise capacity basis/price year first")
    if (out["capex"] <= 0).any() or (out["capacity_nm3_d"] <= 0).any():
        raise ValueError("capex and capacity must be positive")
    if not set(out["scope"].unique()) <= {0, 1}:
        raise ValueError("scope must be 0/1")
    out["feedstock_code"], feed_levels = pd.factorize(out["feedstock"], sort=True)
    out["country_code"], country_levels = pd.factorize(out["country"], sort=True)
    out.attrs.update(
        currency_price_year=currency_price_year,
        feedstock_levels=list(feed_levels),
        country_levels=list(country_levels),
    )
    return out


def build_model(df: pd.DataFrame, priors: CapexPriors):
    """PyMC model for a table returned by :func:`prepare` (non-centred country effects)."""
    import pymc as pm

    n_feed = len(df.attrs["feedstock_levels"])
    n_country = len(df.attrs["country_levels"])
    x = np.log(df["capacity_nm3_d"].to_numpy(float))
    x_c = float(np.mean(x))  # centring improves sampling; 'a' is the log-CAPEX at mean log-capacity
    y = np.log(df["capex"].to_numpy(float))
    with pm.Model(coords={"feedstock": df.attrs["feedstock_levels"]}) as model:
        a = pm.Normal("a", priors.a_mu, priors.a_sd)
        b = pm.Normal("b", priors.b_mu, priors.b_sd)
        gamma_raw = pm.Normal("gamma_raw", 0.0, priors.gamma_sd, shape=n_feed)
        # sum-to-zero feedstock effects keep 'a' identifiable
        gamma = pm.Deterministic("gamma", gamma_raw - gamma_raw.mean(), dims="feedstock")
        delta = pm.Normal("delta", 0.0, priors.delta_sd)
        tau = pm.HalfNormal("tau", priors.tau_sd)
        z = pm.Normal("z_country", 0.0, 1.0, shape=n_country)
        u = pm.Deterministic("u_country", tau * z)
        sigma = pm.HalfNormal("sigma", priors.sigma_sd)
        mu = (
            a
            + b * (x - x_c)
            + gamma[df["feedstock_code"].to_numpy()]
            + delta * df["scope"].to_numpy(float)
            + u[df["country_code"].to_numpy()]
        )
        pm.Normal("log_capex", mu, sigma, observed=y)
    model.x_center = x_c  # type: ignore[attr-defined]
    return model


def fit(df: pd.DataFrame, priors: CapexPriors, draws=1000, tune=1000, chains=4, seed=0, **kw):
    """Sample with NUTS; returns ``(model, idata)``."""
    import pymc as pm

    model = build_model(df, priors)
    with model:
        idata = pm.sample(
            draws=draws, tune=tune, chains=chains, random_seed=seed, progressbar=False, **kw
        )
    return model, idata


def predict_capex(
    idata,
    df: pd.DataFrame,
    x_center: float,
    capacity_nm3_d: float,
    feedstock: str,
    country: str | None,
    scope: int,
    seed: int = 0,
) -> np.ndarray:
    """Posterior-predictive CAPEX draws (same currency/price year as the fitted data).

    ``country=None`` predicts for a **new** country (draws u ~ Normal(0, τ)); otherwise uses that
    country's posterior effect. Includes residual noise σ (Class 5/4 style uncertainty).
    """
    rng = np.random.default_rng(seed)
    post = idata.posterior.stack(sample=("chain", "draw"))
    n = post.sizes["sample"]
    feeds = df.attrs["feedstock_levels"]
    if feedstock not in feeds:
        raise ValueError(f"unknown feedstock {feedstock!r}; fitted levels: {feeds}")
    g = post["gamma"].sel(feedstock=feedstock).to_numpy()
    if country is None:
        u = rng.normal(0.0, 1.0, n) * post["tau"].to_numpy()
    else:
        levels = df.attrs["country_levels"]
        if country not in levels:
            raise ValueError(f"unknown country {country!r}; use None for a new country")
        u = post["u_country"].to_numpy()[levels.index(country)]
    mu = (
        post["a"].to_numpy()
        + post["b"].to_numpy() * (np.log(capacity_nm3_d) - x_center)
        + g
        + post["delta"].to_numpy() * scope
        + u
    )
    return np.exp(mu + rng.normal(0.0, 1.0, n) * post["sigma"].to_numpy())
