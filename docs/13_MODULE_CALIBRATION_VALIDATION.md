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


## 8. ANP reporting scale check (2026-10-08)

**Why.** The ANP plant series for Cocal Narandiba shows 1–30 m³/d of processed biogas from Aug 2022 to Jul 2025, against a biogas processing capacity of 51,600 m³/d, then 23,913 m³/d in Aug 2025 (C6). §6 drops those months as near zero. If they were reported in thousand m³/d, they are 2–58 % utilisation and hold two more harvests for calibration.

**What the series is.** The capacity file header says "Volume Processado de Biogás (m³/d)" and "Volume Processado/Capacidade (%)". The plant series is processed biogas against biogas processing capacity, which is the basis the skeleton runner already uses (§6). It is not biomethane output. Biomethane production is published only per state and product, in m³ per month.

**Method** (`engine.calibrate.anp_units`, data `anp_biometano_dados_abertos`):
1. Flag plant-months with 0 < processed biogas < 1 % of biogas capacity.
2. Convert each SP plant's processed biogas to biomethane with its ratio of authorised biomethane capacity to biogas capacity (Narandiba 27,112 / 51,600 = 0.525). This yield proxy is an assumption (D).
3. Multiply by the days in the month and sum over SP plants. Compare with the SP "BIOMETANO" production for that month, as published and with the flagged Narandiba months ×1000.

**Result, Sep 2023–Jul 2025 (23 months).**

| | Median ratio to state production | P10–P90 | Mean abs log ratio |
|---|---|---|---|
| As published | 0.69 | 0.61–0.92 | 0.33 |
| Narandiba ×1000 | 1.04 | 0.87–1.53 | 0.19 |

The rescaled series fits better in most months. It overshoots in Jun–Sep 2024 (1.43–1.64), which the yield proxy or other plants may explain. Reading: the thousand-unit hypothesis is supported, not proven. Santa Cruz (16–91 m³/d of 152,440) and Paulínia (18–274 of 480,000) show the same pattern in 2025–2026.

**Rule until ANP answers (Q9).** Keep the flagged months out of the calibration metrics (§6). Report a sensitivity run with them ×1000, labelled as such. Never mix the two in one metric.

Run: `PYTHONPATH=src python -m engine.calibrate.anp_units evidence/anp_biometano_dadosabertos_capacidade_2026-08.csv evidence/anp_biometano_dadosabertos_producao_2026-08.csv --rescale NARANDIBA --start 2023-09 --end 2025-07`.

**Plant-level check against company reports (2026-10-08, R11 round 2).** Cocal and Geo publish Narandiba's annual biogas and biomethane (docs/21 C40). Summed per safra, the ANP field "Volume Processado de Biogás" (flagged months ×1000) gives 0.39, 4.23, 8.39 and 7.61 M m³ for 2022/23–2025/26. The reports give biogas 23.4, 30.5, 27.7, 32.7 M Nm³ and biomethane 4.3, 7.9, 8.1, 10.6 M Nm³. Two consequences:

1. The thousand-unit reading fixes the scale only from about 2024. Aug 2022–Aug 2023 stays about ten times too low even ×1000.
2. At Narandiba the field tracks biomethane, not biogas. The ×0.525 yield proxy in step 2 then undercounts Narandiba, so the good state-level fit of the rescaled series may be partly a coincidence of two errors. The state check stays a diagnostic, not a proof.

**Rule added.** For Narandiba, calibrate against the company's annual figures (biogas, biomethane, flare, feed tonnages per safra; `registry/skeleton_mills.yaml` notes) and use ANP months only for the seasonal shape from Aug 2025, labelled. Utilisation shares computed as ANP "processed biogas" / biogas capacity (§4 target series) mix bases at Narandiba until ANP answers Q9.
