# ADR-0018 — Hub coverage: greedy selection with a minimum scale, each source counted once

- **Status:** Proposed
- **Date:** 2026-10-08
- **Deciders:** project lead (to confirm)

## Context
- The suitability screen (ADR-0016, ADR-0017) ranks cells. It does not say how many plants the SP supply can feed, or where, if each plant must reach a minimum scale. Adjacent cells share their 30 km sums, so the top of the ranking can be one cluster counted many times.
- The ESD "FL espacial" (`docs/inbox/esd_inventory.md` §2 M1) answers this with a greedy covering on the 1 km N3 supply grid:
  - a source at road distance d from a hub counts with w(d) = 1 up to r1, falling linearly to 0 at r2, with radii by material class (liquid, wet solid, dry solid);
  - variant B, the main one: "alocação gulosa sem dupla contagem"; a hub enters only if the residue it adds is ≥ Q_min;
  - variant A is the upper bound (all viable hubs); straw goes only to mills.
  - Results as read in the inventory (`mclp.csv`, v5.1, med): B stops at 455 hubs (423 grid + 32 existing). With straw at the mills, 16 hubs reach 50 % of total N3 and 114 reach 80 %. Without straw, 55 and 143.
- The ESD code stays on the user's PC, so the port follows the inventory's description. The description leaves three points open:
  - how a source within reach of two open hubs counts;
  - whether Q_min applies to a hub's whole catchment or to what it adds;
  - what happens when, with r1 < r2, a later hub takes nearer sources from an earlier one.
- No sourced value exists for the radii, the residue → class mapping or Q_min (docs/21 Q20, Q23). The ESD values are in `registry/inbox/esd_parameters.csv` with flag S.

## Decision
1. **Port** the method as `engine.siting.coverage` (numpy/scipy, unit-tested) plus `scripts/siting/hub_coverage_v0.py` for the N3 grid. It is built on the maximal covering location problem (Church & ReVelle 1974, `church1974`).
2. **Each source counts once, at its best open hub.** That is the hub where its weight is highest; ties go to the hub opened first. Covered supply of a hub set S = Σ_i s_i · max_{j∈S} w_ij.
3. **Q_min applies to the marginal gain.**
   - A hub opens only if it adds at least q_min (and more than 0) to the covered supply.
   - At each step the greedy opens the hub that adds most.
   - Gains only shrink as hubs open, so they are re-evaluated lazily, and the first gain below q_min ends the run.
4. **Existing plants** can be opened first (`fixed`), whatever they add. They are never closed.
5. **Pruning.** After the greedy, a hub (fixed ones excepted) that collects less than q_min once each source sits at its best hub is closed. Hubs close smallest first (ties: the later-opened hub), and the loop repeats until none is left below q_min. Only decay weights (r1 < r2) can cause this.
6. **Routes.** A residue can be restricted to some candidate types (straw only to mills), as in the ESD.
7. **Outputs.** The coverage curve (hubs needed for 25–95 % of the supply) is read from the greedy trace, before pruning. The upper bound (ESD variant A) opens every candidate whose own catchment reaches q_min.
8. **No defaults** for the residue classes, r1 and r2, q_min and the detour factor. The script refuses to run without them, and each run records them in its parameter hash.
9. **Distances.** Use routed distances when they exist. Otherwise use great-circle distance × a cited detour factor, the rule of `engine.siting.routing.fallback_road_km` (`road_detour_factor_*` are road km per great-circle km, flag D). The v0 script uses the fallback.
10. **LGPD.** Farm-register residues (poultry, swine, dairy and feedlot cattle) are reported only per hub. A hub's farm part, total and gain are withheld when 1 to k−1 farm cells feed it (k = 3). The state covered share is published only if the withheld hubs hold no farm cells or at least k together. Nothing is written per supply cell.

## Consequences
- **Positive:**
  - "How many hubs for X % of N3, at a minimum scale" gets explicit, testable rules.
  - The greedy hubs narrow the candidates and can warm-start the MILP of docs/12 Step 5.
  - Outputs are per hub, so farm-register data stays aggregated.
- **Negative:**
  - The greedy is a heuristic. In a unit test its two hubs cover 7 units of supply, while the best pair covers 8.
  - Results depend on the candidate grid (H3 res-7 cells plus facility points), on the 2 km aggregation of sources, and on the fallback distances.
  - They are sensitive to radii and q_min, which have no sourced values.
  - Not claimed to reproduce the ESD `mclp.csv` until both run on the same inputs.
- **Follow-ups:**
  - compare with `mclp.csv` on the PC (same classes, radii, Q_min and candidates);
  - source the radii, the class mapping and q_min (docs/21 Q20, Q23);
  - add existing biogas plants as fixed hubs (they are not in the gpkg `pontos` layer);
  - route the final hubs with OSRM;
  - run the min/med/max scenarios.

## Alternatives considered
- **First come, locked.** A source stays with the first hub that reaches it, even when a nearer hub opens later. Simpler, but later hubs are under-credited and the answer depends on the opening order more than the greedy itself does.
- **Residual fractions.** Each new hub takes w × what is left of a source. Two hubs at mid distance then collect 1 − Π(1 − w) of it, more than either alone could (max w). It credits supply that no single plant would collect.
- **Q_min on the whole catchment** (overlaps ignored). That is the upper bound (variant A): a source near several hubs is counted by each.
- **Exact MCLP as a MILP.** Exact for a given candidate set, but it needs a solver and costs. That job belongs to Step 5; the greedy is the screen before it.
