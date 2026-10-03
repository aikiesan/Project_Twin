# 13 — Calibration & validation ("simulate and correct until it matches reality")

## 1. Principle
The chain *supply → process → output* is calibrated against **observed data at three levels** before any scenario is reported. Calibration = estimating uncertain parameters so predictions match observations; validation = testing on data not used for calibration.

## 2. Observation sets
| Level | Observation | Source | Use |
|---|---|---|---|
| Municipality | Cane production 2008–2025 | IBGE/SEADE (have) | Hard constraint (downscaling) |
| State | Biweekly crush SP | UNICA | Seasonality & totals check |
| Mill | Annual cane, ethanol, vinasse applied | RenovaBio reports | **Calibrate Huff α, β, mill effects** |
| Mill | Measured vinasse (if LAI succeeds) | CETESB PAV | Validate vinasse rules |
| Plant | Monthly biogas volume, utilization | ANP (PILAR-2b `05e`) | **Calibrate process & capacity factor** |
| Reactor | OLR, yield, stability | Volpi 2021; PPBIOEN | Process parameter priors |

## 3. Calibration designs

### 3.1 Supply (Bayesian)
- Likelihood: log(RenovaBio cane_jt) ~ Normal(log(Ĉrush_jt), σ); UNICA rounded totals as **interval-censored**; RenovaBio eligible-only values as **lower bounds** where applicable.
- Parameters: α, β, mill efficiency u_j ~ N(0, τ), year effects.
- Tools: PyMC (Python) or brms/Stan (R).

### 3.2 Process & capacity factor (plant-level)
- Target series: Costa Pinto (vinasse + filter cake; off-season ~0–12 %), Narandiba (30–49 % incl. off-season), other SP plants as they accumulate months.
- Uncertain parameters: f_scale, storage retention, effective feedstock share delivered, downtime/ramp-up.
- Method: Bayesian calibration or ABC (approximate Bayesian computation) if the simulator is not differentiable; compare monthly profiles, not just annual means.
- Caveat: ANP months with 0 may be reporting gaps or shutdowns → treat as missing unless confirmed.

## 4. Validation designs
| Test | Design | Metric | Target |
|---|---|---|---|
| Temporal | Train 2008–2018, test 2019–2025 | MAPE, bias | MAPE < 15 % (mill cane) |
| Spatial | Leave-region-out (EDR/RA) | MAPE, coverage of 90 % CI | coverage ≈ 90 % |
| Independent | Company reports (São Martinho etc.) | Abs. error | — |
| Plant | Predict next months of ANP output | CRPS / interval coverage | — |
| Cost | Predict held-out project CAPEX | log error | within Class 4 band |

**Never use random K-fold** for spatial data (autocorrelation inflates skill).

## 5. The "system-level digital shadow"
Monthly job: ingest new ANP plant data → compare predicted vs observed per plant → log residuals → flag drift → recalibrate quarterly. This is the defensible "shadow" claim (see `01_CONTEXT_AND_MOTIVATION.md` §5).
