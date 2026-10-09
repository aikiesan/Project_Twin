# ADR-0014 — Morris screen of the skeleton: one factor per registry row, registry ranges, a synthetic reference case

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** project lead (ADR-0010 asks for a Morris ranking to decide what to verify first)

## Context
- **What ADR-0010 asks for.** Verification starts with the parameters that move the results. Gate 0 asks that at least 60 % of the top-15 parameters be `V`. That needs a ranking of the parameters the skeleton reads.
- **What the registry offers.** The skeleton reads 27 registry rows. 21 of them have a numeric range. Two are pairs (`"a / b"`, with a range per component). Six have a central value only: `ethanol_yield`, `opex_epe`, `plant_life`, `straw_ch4_pct`, `straw_gen` and `straw_recov`.
- **What is missing for a mill run.** The calibration mills have no sourced cane value yet (`registry/skeleton_mills.yaml`). Without cane there is no mill case to screen.
- **Since 2026-10-06, references are tied to values (ADR-0013).** A ranking of registry rows is therefore also a ranking of the references behind them.

## Decision
1. **One factor per registry row.** One row has one source and is one verification task. A pair row such as `fc_ts_vs` is a single factor: both components move to the same quantile of their own ranges.
2. **Ranges come from the registry only.**
   - Each row is sampled uniformly over its own `[low, high]`. This is a screening choice, not a claim about the value's distribution.
   - Rows without a numeric range are **excluded** and listed with the reason, never given an invented range.
   - Every row with a numeric central value also gets one-sided local elasticities (±10 %). A row without a range is therefore still ranked by its local effect, and a large elasticity says a sourced range is worth finding.
3. **A perturbed row is collapsed to `central = low = high = v`.** Code that reads the low end sees the same value; for example, `hrt_cstr` is used as a minimum HRT.
4. **Outputs:**
   - annual biomethane (Nm³);
   - annual capacity factor;
   - LCOB (R$/Nm³);
   - months failing a mass-balance check.

   The priority of a row is its largest μ*/|y| over the first three outputs.
5. **Method:** Morris elementary effects summarised by μ* (Campolongo et al. 2007), via SALib, with a fixed seed. Defaults are 20 trajectories and 4 levels.
6. **Reference cases.**
   - **Mill case:** a calibration mill, with the same inputs as the skeleton run (ANP nameplate). It runs once cane is sourced.
   - **Synthetic case, until then:**
     - a cane normalisation unit of 10⁶ t;
     - the mills' AD shares;
     - strategy S0;
     - the nameplate sized to the peak month of the central-value potential.

     With linear CAPEX, the synthetic LCOB, capacity factor and relative μ* do not depend on the cane value. The case is labelled synthetic in every output and is not a result.
7. **Outputs are files, not git.** They go to `data/processed/sensitivity/<run_id>/`: `morris.csv`, `priority.csv`, `elasticities.csv` and `summary.json`. The `run_id` hashes the registry, the case and the settings. The summary also records the engine version and the git commit.

## Consequences
- \+ The verification order of docs/08 §5 can follow the ranking, row by row, and through `references.csv` reference by reference.
- \+ Rows that cannot move the outputs in the current chain are visible as such. Their verification can wait. Examples: straw rows while the straw AD share is 0, and OLR or HRT limits while the digester is sized to them.
- \+ The screen exposed a rounding bug in the mass balance: a digester sized exactly at the HRT limit was flagged infeasible. It is fixed with `CHECK_RTOL` (docs/10 §7).
- − The ranking depends on the width of the registry ranges, which are themselves mostly `S`. A row with a wide unverified range ranks high; that is the intended signal, since the width is the uncertainty to remove.
- − The synthetic nameplate puts the case on the capacity cap, so higher values are partly curtailed. The one-sided elasticities show both sides.
- **Follow-up:**
  - re-run the screen per mill once cane is sourced;
  - add sourced ranges for `ethanol_yield`, `opex_epe` and `plant_life`;
  - move to Sobol on the top rows when the Monte Carlo of docs/11 is built.

## Alternatives considered
- **Invent ±x % ranges for rows without one.** Rejected by CLAUDE.md rule 1. Such rows get elasticities instead, which need no range.
- **One factor per component of a pair row.** Rejected: the components come from one source and are verified together. Independent sampling of vinasse TS and VS could also make VS exceed TS.
- **Wait for the mill cane values.** Rejected: the ranking of what to verify does not depend much on the cane, and verification is on the critical path (ADR-0010).
- **Sobol indices directly.** Kept for later. They cost about 100 times more runs: N(2k + 2) runs with N ≈ 10³, against r(k + 1) with r = 20 here. They also need distributions rather than ranges.
