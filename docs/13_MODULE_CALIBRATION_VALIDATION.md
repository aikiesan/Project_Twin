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
- the manure base-load.

The Morris screening is in §7.

## 7. Sensitivity screen (Morris, 2026-10-06, ADR-0014)

**Purpose.** Rank the registry rows the skeleton reads by how much they move its outputs, so that page-level verification (docs/08 §5) starts where it changes results (ADR-0010).

**How to run it.**
```bash
python -m engine.sensitivity morris --synthetic
python -m engine.sensitivity morris --mill costa_pinto --crop-year 2025   # once cane is sourced
python -m engine.sensitivity worklist --synthetic   # the ranking joined with references.csv
```

`worklist` writes `worklist.csv` next to the Morris outputs. For each row it lists:
- the references whose `used_for` names the row, and their identity check;
- the value checks;
- which of those references were already read page by page (`refs_read`: they have rows in `registry/value_evidence.csv`, ADR-0015);
- whether `page` and `quote` are filled;
- the next step (docs/08 §5). A row whose readable references were all read without finding the central value gets "trace its origin" instead of "read the document".

Screened rows come first, in priority order. Rows without a range follow, ordered by their largest elasticity.

**Code.** `engine.sensitivity` re-runs `engine.skeleton.run_chain`, the cane → residues → CSTR → LCOB part of the skeleton run, so the screen and the run cannot drift apart.

**Method.**
- Elementary effects (Morris 1991), summarised by μ* (Campolongo et al. 2007), via SALib.
- 20 trajectories, 4 levels, seed 20261006, so 22 × 20 = 440 chain runs.
- One factor per registry row, uniform over the row's own `[low, high]`. A pair row moves both components to the same quantile.
- Rows without a numeric range are excluded and listed.
- Every row also gets one-sided ±10 % elasticities, so the excluded rows are not ignored.
- The priority of a row is its largest μ*/|y| over annual biomethane, capacity factor and LCOB.

**Reference case: synthetic, not a mill.**
- 10⁶ t cane normalisation unit, crop year 2025;
- AD shares vinasse 1, filter cake 1, straw 0;
- strategy S0;
- nameplate sized to the peak month of the central-value potential.

Its central outputs are 7.48 × 10⁶ Nm³/yr per 10⁶ t cane, a capacity factor of 0.658 (8 of 12 months) and an LCOB of 1.98 R$/Nm³. These are not results. They rest on `S`/`K` parameters and a synthetic case.

**First ranking (run `morris-synthetic-9bb66f60fd`, registry of 2026-10-06):**

| Rank | Row | Flag | μ*/\|y\| (output) | What it means for verification |
|---|---|---|---|---|
| 1 | `vin_cod` | S | 0.45 (LCOB) | Wide range (15–50 g/L around 30), on the stream that gives about 81 % of the CH₄. First to verify (registry source: Fuess, Garcia and Zaiat 2018) |
| 2 | `capex_epe` | S | 0.28 (LCOB) | Range 2,700–3,735 R$ per Nm³/d; scope open (C15) |
| 3 | `wacc_real` | K | 0.27 (LCOB) | Project choice with no external source |
| 4 | `vin_gen` | S | 0.11 (LCOB) | DOI in conflict (C14) |
| 5 | `cod_removal` | S | 0.08 (biomethane) | |
| 6 | `vin_ch4_yield` | S | 0.07 (LCOB) | |
| 7–10 | `bmp_fullscale`, `fc_bmp`, `fc_ts_vs`, `fc_gen` | S | 0.02–0.04 | Filter cake gives about 19 % of the CH₄ |
| 11 | `upg_ch4_recovery` | K | 0.005 | Narrow range (98–99.5 %) |
| — | 10 rows | S/K | 0 | No effect in this case |

**Rows with no effect in this case, and why:**
- `straw_*`: the straw AD share is 0;
- `olr_max_cstr` and `hrt_cstr`: the digester is sized to meet them;
- `cod_so4_crit`, `k_inhib`, `vin_so4` and `vin_k2o`: the checks cannot be evaluated for a vinasse + cake mix, since filter cake has no SO₄ or K rows;
- `vin_ts_vs`: vinasse methane is on a COD basis, and the feed TS stays below the limit.

**Excluded from Morris: no range in the registry.** The largest one-sided elasticity of each:
- `ethanol_yield` [D]: **0.81**, as large as any vinasse row. A sourced range is a priority (docs/21 Q13).
- `plant_life` [K]: 0.35.
- `opex_epe` [S]: 0.08.
- `straw_ch4_pct`, `straw_gen` and `straw_recov`: 0.

**Gate 0 status.** 0 of the 11 rows that move the outputs are `V`, against a target of ≥ 60 % of the top 15.

**Asymmetry.** The synthetic nameplate sits at the central peak, so output above central is partly curtailed. The vinasse rows have a downside elasticity of 0.81 on biomethane and an upside of 0.17. In this case, the output lost when the true value is below the registry central is about five times the output gained when it is above. Evidence of lower values matters most.

**Not covered** (listed in `summary.json` → `not_screened_inputs`):
- cane;
- AD shares;
- `x_ch4`, which changes biogas only, not biomethane or LCOB, so C13 matters for the ANP comparison and not for this ranking;
- the nameplate rule;
- the harvest profile;
- the fresh density;
- `ts_max_frac`;
- the S1 storage inputs.

