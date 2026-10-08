# ADR-0017 — Feedstock in the suitability screen: one CH₄ criterion, percentile normalisation as an option

- **Status:** Proposed
- **Date:** 2026-10-07
- **Deciders:** project lead

## Context
- ADR-0016 normalises each criterion linearly from 0 to the 99th percentile of non-excluded cells and gives the 8 criteria equal weights. Feedstock enters as 4 separate criteria in different physical units: cane t, and head of swine, poultry and cattle within 30 km.
- Run `suitability_v0_20261007T181811Z` (45,327 scored cells, federal UCs excluded), best cell per municipality. Values below were computed on the PC by the project lead, with IBGE codes from `municipal_panel_v0.csv`:

  | Municipality | Score | Rank | gas | cane | swine | poultry | cattle |
  |---|---|---|---|---|---|---|---|
  | Tietê | 0.693 | 1 | 0.988 | 0.421 | 1.000 | 0.812 | 0.405 |
  | Pitangueiras | 0.453 | 5,509 | 0.599 | 1.000 | 0.018 | 0.023 | 0.101 |
  | Sertãozinho | 0.456 | 5,122 | 0.602 | 0.993 | 0.020 | 0.026 | 0.109 |
  | Guaíra | 0.355 | 27,095 | 0.263 | 0.824 | 0.010 | 0.013 | 0.148 |

- The 0.239 gap between Tietê and Pitangueiras breaks down as follows:
  - **+0.259 from the three herds;**
  - +0.049 from gas;
  - +0.004 from power, road and demand together;
  - −0.072 from cane.
- Cane is **saturated** across the cane belt. Its cells hold 13.6–15.3 Mt within 30 km, above the p99 bound of 13.7 Mt, so n_cane ≈ 1. Yet a cell with all the cane can gain at most 1/8. A cell with moderate amounts of three herds can gain up to 3/8.
- In the ESD cascade, which measures CH₄, cane accounts for 89 % of N3 (`docs/inbox/esd_inventory.md`). The screen's top sites therefore follow herd counts, not methane.
- Raising the cane weight in the WebGIS does not fix this: the criterion is already at 1 across the whole belt.
- Separately, herds and population are very skewed under the linear scale. Medians of n_swine 0.037, n_poultry 0.043 and n_demand 0.016, against gas 0.735 and road 0.801.

## Decision (proposed)
1. **Feedstock becomes one criterion: CH₄ potential within 30 km (Nm³ CH₄/d).**
   - Candidate input: the ESD 1 km N3 supply grid (derived; register it in `sources.yaml` before use). The alternative is to convert cane and herds with registry factors.
   - In the default weighting it replaces the 4 feedstock criteria. The single-resource layers can still be shown on the map.
   - Its BMP and availability factors are flagged S. Every run states this as a caveat until they are verified.
2. **Percentile normalisation is available as an option.**
   - `normalize(method="percentile")` gives each cell its mid-rank share among the non-excluded cells, with ties counting half. Through the CLI, `score_grid_v0.py --normalization percentile` writes outputs with the suffix `_per`.
   - `linear` stays the default.
   - This option addresses the skew. It does **not** fix the structural problem above, since three herd criteria still outweigh one cane criterion.
3. Pick the default normalisation only after the CH₄ criterion exists. Then compare linear and percentile runs on:
   - the spaced site lists;
   - the top-100 overlap;
   - where the cane belt lands.

## Consequences
- + The screen ranks on the quantity the project optimises (CH₄), consistent with the supply module and with the ESD N4.
- + Percentile scaling makes equal weights mean roughly equal influence and removes the p99 cap.
- − A single CH₄ criterion inherits the uncertainty of BMP and availability factors (S).
- − Percentiles lose magnitude and depend on the set of cells scored, so runs are comparable only with the same exclusions.

## Alternatives considered
- **Weight the 4 feedstock criteria by each resource's share of CH₄.**
  - Simpler, but it keeps the saturation of cane at p99 and the mismatch of units within each criterion.
- **log(1 + x) before the linear scale.**
  - Compresses the peaks, but the transform is an arbitrary choice with no source.
- **Raise the p99 bound for cane.**
  - Removes the saturation, but leaves the 1-vs-3 structure.

## Notes
- **2026-10-08, implementation of point 1.** Two pieces:
  - `engine.siting.catchment.disc_sums`: sums within the radius by convolving the 1 km raster with a disc. It is exact on cell centres, checked against brute force.
  - `scripts/siting/n3_ch4_30km.py`: reads `grade_oferta_1km.gpkg` (`esd_n3_supply_grid_1km`, both layers, one scenario). It writes `n3_ch4_30km_<scenario>.parquet` with one row per H3 cell.
- **LGPD in that script.**
  - The five farm-register residues enter only as 30 km sums.
  - Where fewer than 3 one-km cells with a farm value fall in the radius, the farm part is withheld and only the non-farm part counts (`farm_suppressed`).
- **Scoring.** `score_grid_v0.py --ch4 <parquet>` replaces cane, swine, poultry and cattle with the one criterion `ch4`; outputs carry `_ch4`.
- **Weights.** With equal weights the screen has 5 criteria. Feedstock then weighs 1/5, against 4/8 before, and gas, power and road together weigh 3/5. That baseline is a choice to review with the first real run; the WebGIS sliders show the alternatives.

- **2026-10-08, first real run (`docs/inbox/n3_ch4_30km_run.txt`, `score_grid_v0_ch4_run.txt`).**
  - Input check: the gpkg sums to 19,183,201.3 Nm³ CH₄/d, against 19,183,201 for N3 med in the ESD T1.
  - LGPD: the farm part is withheld in 18 of 47,273 H3 cells.
  - Quantiles of the criterion (Nm³ CH₄/d within 30 km): P5 2,779; P50 181,750; P95 517,283; P99 728,931.
  - Run `suitability_v0_ch4_20261008T113536Z`, linear scale, equal weights over 5 criteria:
    - 45,327 cells scored;
    - minimum top-100 kept under OAT ±20 %: 0.96.
  - **The cane belt now enters both spaced lists:**
    - robust list: Ribeirão Preto (3rd), Pitangueiras (4th), Guariba (8th), Araraquara (9th) and Morro Agudo (11th);
    - equal-weight list: Ribeirão Preto (8th), Araraquara (10th) and Pitangueiras (12th).
    - Before, the belt was absent from the top 15.
  - **New issue: the São Paulo metro takes the top places.**
    - The 15 best cells are in São Paulo or Guarulhos, with score up to 0.849.
    - Their rank P95 under the Dirichlet weights is about 4,000, against about 15,000–18,000 for the belt sites.
    - Likely causes, still to confirm with the residue-group breakdown:
      - urban residues (RSU, sewage sludge, prunings) inside the CH₄ criterion;
      - population counted again through the `demand` criterion;
      - the shortest gas, power and road distances.
    - Urban land is not yet an exclusion.
    - Open question 19 in `docs/21`.
  - Follow-up in code: `n3_ch4_30km.py` now also writes the non-farm part split into cane, urban and other agro groups. `score_grid_v0.py --ch4` prints the shares for the spaced sites. Status stays Proposed until the metro question is settled.
