# ADR-0016 — Suitability screen: hard exclusions, normalised criteria, weighted score, weight sensitivity

- **Status:** Proposed
- **Date:** 2026-10-07
- **Deciders:** project lead (request of 2026-10-07: prohibited areas, optimal areas, and a sensitivity analysis with equal and adjustable weights, shown in a web map)

## Context
- docs/12 Step 2 plans hard exclusions and soft criteria. It says the main siting model ranks sites by explicit cost (LCOB), with AHP weights only for comparison with Paulino et al. 2024.
- The project lead wants a map now: where plants cannot go, where they fit best, and how the answer moves with the weights.
- Screening v0 (2026-10-07, run on the PILAR-2b SP export) gave the first per-mill distances. It also showed two limits of the data:
  - the gas pipeline layer is partial (docs/21 Q17);
  - the `settlement` layer holds INCRA agrarian-reform settlements (`SOURCE` "INCRA, 2025"), not urban areas.

## Decision
1. **A suitability screen, separate from the cost model.**
   - The weighted score narrows candidate sites (H3 cells for hub plants, mills for annexed plants).
   - It is never reported as the optimal location.
   - The cost model (docs/12 Step 5) decides.
2. **Hard exclusions only with a legal or physical basis.**
   - Each exclusion layer cites its norm or source in `registry/`.
   - A buffer distance enters only with a citation. Where none exists yet (for example CBPMESP IT-29, docs/21 Q12), the buffer is a scenario input, not a default.
   - Agrarian-reform settlements are a constraint layer (distance criterion or scenario), not a hard exclusion, until a norm says otherwise.
3. **Criteria are normalised linearly to [0, 1], 1 = best.**
   - Bounds come from a cited break (for example a cost step) or, when none exists, from the data range of the non-excluded candidates.
   - The bounds are written with every run.
4. **The score is a weighted linear combination (WLC).**
   - Weights are non-negative and rescaled to sum 1.
   - A candidate missing a weighted criterion gets no score, never a 0.
5. **Sensitivity is part of every result.**
   - Equal weights are the baseline.
   - Random weights come from a Dirichlet distribution centred on the base weights. Per candidate the run reports the base rank, the median and 5–95 % rank, and the share of draws in the top k.
   - A one-at-a-time ±20 % check on each weight reports how much of the top k survives.
   - User-set weights (web map sliders) are one more base weighting and get the same report.
6. **Code:** `engine.siting.suitability` (pure pandas/numpy). Geometry (H3 cells, distances) is computed before it.

## Consequences
- + The map answers the request with ranks that carry their own robustness measure, not a single weighted picture.
- + Exclusions and bounds are traceable to sources; nothing is a hidden default.
- − Linear normalisation and WLC assume compensation between criteria (a good gas distance offsets poor feedstock). Non-compensatory rules (thresholds, ordered weighted averaging) are left for later.
- − With partial gas data (Q17), gas-distance criteria favour places where the network happens to be drawn. Results carry that caveat until Q17 is resolved.

## Alternatives considered
- **AHP pairwise weights as the main method.** Kept for the Paulino et al. 2024 comparison only (docs/12). Pairwise judgements add a consistency check but not a source for the weights.
- **Fixed thresholds (pass/fail per criterion).** Simpler, but they hide trade-offs and need cited thresholds the project does not have yet.

## Notes
- **2026-10-07, distinct sites.** Neighbouring cells share most of their 30 km sums, so on the real grid v0 the top 15 cells fall in one municipality (Tietê). Ranked lists of *sites* are therefore drawn with a minimum spacing (greedy, best-first, great-circle distance; `engine.siting.suitability.spaced_selection`, default 30 km), once by the equal-weight rank and once by the share of Dirichlet draws in the top k. Cell scores and ranks are unchanged.
- **2026-10-07, extra exclusions.** `score_grid_v0.py --exclude label=path` adds a hard exclusion from any polygon layer (cell centre inside; `engine.siting.exclusions`). Only layers registered in `sources.yaml` with a legal basis; first use is federal integral-protection UCs (`mapbiomas_federal_uc_integral`). The run records each layer's sha256.
