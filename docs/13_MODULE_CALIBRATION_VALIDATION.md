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

## 6. Implementation status (skeleton runner, 2026-10-06)

Module: `engine.skeleton` (`python -m engine.skeleton list | run`). Tests: `tests/test_skeleton.py`. It runs the walking skeleton (ADR-0010) for one mill and one crop year, and compares the monthly output with the ANP series in `evidence/anp_monthly_sp_plants_from_pilar2b.csv` (§3.2).

**Inputs.** `registry/skeleton_mills.yaml`, one entry per calibration mill:
- cane crushed, and optionally ethanol, per crop year, each with a value, a source and a flag. The run stops when the crop year has no cane value: there is no default;
- the AD shares, which are calibration start values;
- the strategy;
- the ANP plant id, from which the nameplate is taken;
- `x_ch4`, set to 0.575 with `--x-ch4` to run 0.65 as well (docs/21 C13).

Both mills' cane values are still empty.

**Comparison rules (v0)**
- Basis: biogas, because ANP reports biogas volume (m³/d) and utilization against biogas capacity. Simulated biogas is capped at the ANP biogas capacity, since a plant cannot report more.
- **Near-zero ANP months** (below 1 % of capacity) are flagged `obs_near_zero` and left out of the metrics. §3.2 says zeros count as missing unless confirmed. Example: Narandiba's months before Aug 2025 (C6) and Costa Pinto's Sep 2025.
- Metrics:
  - months observed and compared;
  - MAE and bias of utilization (percentage points);
  - simulated / observed volume;
  - **off-season share** (Dec–Mar volume over the compared months), simulated vs observed.

**Outputs.** Written to `data/processed/skeleton/<run_id>/`:
- `monthly.csv`: residues plus the mass balance;
- `comparison.csv`;
- `summary.json`: inputs with sources, nameplate, digester volume, every registry id used with its flag, LCOB and anchors, metrics and caveats.

The `run_id` is deterministic. It is `skel-<mill>-<crop year>-<hash>`, where the hash covers the registry hash, the mill inputs, `x_ch4` and the ANP file sha256.

**First diagnostic, with a test cane value (not data).** Under S0, Narandiba's simulated off-season share is 0. ANP shows about 0.43 (30–39 % utilization from Dec 2025 to Mar 2026). This is the gap that strategy S1 (stored filter cake) has to explain.

**Strategy S1 (added the same day).** Run it with `--strategy S1` once the mill's `storage` block is filled: `store_frac`, the storing and release months, and `loss_frac_per_month` with `loss_source`. The summary then also reports the silo balance. With test values, Narandiba's simulated off-season share rises from 0 (S0) to about 0.25, against about 0.43 observed.

**Not yet implemented:**
- strategies S2–S5;
- calibration of the AD shares and of `store_frac`;
- the manure base-load;
- the Morris screening.