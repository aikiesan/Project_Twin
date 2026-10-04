# ADR-0007 — PyMC as the primary Bayesian engine (Stan/brms as cross-check)

- **Status:** Proposed
- **Context:** Calibration of Huff allocation (ADR-0004) and the hierarchical CAPEX model (ADR-0005) need custom likelihoods (masked softmax over mills, censored observations, interval-censored totals). brms covers standard GLMMs but not the Huff softmax without custom Stan code; the engine is Python-first (one environment, CI, PILAR-2b integration).
- **Decision:** Implement the target Bayesian models in **PyMC** inside the engine (`engine.calibrate.bayes_huff`, `engine.economics.capex_hier`), with explicit prior dataclasses. Use **R (brms/Stan) as an independent cross-check** for the CAPEX model (a standard hierarchical regression brms handles natively) and for diagnostics/figures if preferred.
- **Consequences:** + single tested code path, synthetic-recovery tests in CI; − PyMC compile time (~20–50 s per model); large H3 × mill tensors may need batching or a sparse formulation (only reachable pairs within `d_max`).
- **Revisit when:** the statewide problem is too slow in PyMC (≫ 1 h per fit) → consider NumPyro/JAX backend (`pm.sample(nuts_sampler="numpyro")`) or a sparse pair-list formulation.
