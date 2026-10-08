# 09 — Supply module (where and when are the residues?)

## 1. Goal
Produce, with uncertainty:
- `mill_year`: cane crushed, ethanol (anhydrous/hydrated), sugar share, vinasse (generated / applied / available), filter cake, straw — per mill (CNPJ) per year 2008–2025.
- `mill_month`: same, per month.
- `hex_supply`: residue availability per H3 cell × month × residue (cane-based and others).

## 2. Inputs
MapBiomas cana 30 m (have) · SEADE/IBGE planted vs harvested + yield (have) · mill coordinates (have) · ANP capacity · SAPCANA status · RenovaBio mill-year (calibration) · UNICA biweekly SP · livestock points + IBGE PPM + LUPA · ANA ETE + SINISA · CETESB RSU · SIF · PILAR-2b FDE.

## 3. Step-by-step method

### Step 1 — Facilities registry (CNPJ crosswalk)
- Union of ANP ethanol plants, SAPCANA units, RenovaBio certified units, CP2B mill list, NovaCana (if available).
- Match on CNPJ (14-digit) first; then fuzzy name + municipality; LLM adjudication for ambiguous pairs; human review.
- Attributes: status by year (active/idle/closed), capacity, type (distillery/annexed/sugar-only), group.
- Activity check from satellite: no harvest within reach of a mill in a year → likely idle (see Step 6).

### Step 2 — Cane per pixel → H3
$$\text{cane}_{i,t} = \text{area}^{\text{MapBiomas}}_{i,t}\times \frac{\text{harvested}_{m,t}}{\text{planted}_{m,t}} \times \text{yield}_{m,t}$$
- *i* pixel, *m* municipality, *t* year. Harvested/planted corrects for renovation areas (not harvested that year).
- Aggregate to H3 res 8 (sum). Constraint: Σ cells in municipality = IBGE/SEADE production (rescale per municipality — record scale factors as diagnostics).
- Optional refinement: yield prior by soil production environment (Rossi 2017) + climate, then IPF/cross-entropy to municipal totals (You & Wood 2006).

### Step 3 — Allocate cane to mills (Huff spatial interaction)
$$P_{hj,t}=\frac{a_{j,t}\,C_j^{\alpha}\,e^{-\beta d_{hj}}}{\sum_{k\in M_t} a_{k,t}\,C_k^{\alpha}\,e^{-\beta d_{hk}}}, \qquad \widehat{\text{Crush}}_{j,t}=\sum_h P_{hj,t}\,\text{cane}_{h,t}$$
- *h* H3 cell, *j* mill, *d* road-network distance (OSRM/Valhalla), *C* capacity, *a* activity indicator, *M_t* active mills.
- Truncate at d_max (e.g. 60 km) and add an "outside SP / unallocated" sink for border cells.
- Constraint: crush ≤ capacity × season days.
- **Calibration:** fit α, β (and mill efficiency random effects) to **RenovaBio mill-year cane** (Bayesian; PyMC or brms). Hold out mills/regions for validation.
- Alternatives for sensitivity: network Voronoi; capacity-constrained transportation LP. Report differences.

### Step 4 — Products and residues per mill-year
| Quantity | Rule | Parameter ids |
|---|---|---|
| Ethanol | from RenovaBio where available; else cane × ethanol yield × ethanol share (mill random effect × state mix from UNICA) | `ethanol_yield` |
| Vinasse generated | ethanol × L/L (juice vs molasses mix matters) | `vin_gen` |
| Vinasse applied | RenovaBio/CETESB where available | — |
| Vinasse available for AD | generated × (1 − losses) — **must be ≥ applied?** logic to define | — |
| Filter cake | cane × kg/t | `fc_gen` |
| Straw | cane × 140 kg DM/t × recoverable fraction × (1 − competing use) | `straw_gen`, `straw_recov` |
| Bagasse | excluded (boilers) unless mill reports surplus | — |

Uncertainty: propagate parameter ranges (Monte Carlo) + Huff posterior.

### Step 5 — Monthly disaggregation
- Default: UNICA SP biweekly crush curve for that safra → monthly shares.
- Mill-specific shift: harvest timing from Sentinel-2/Landsat within each catchment (Step 6).
- Vinasse and filter cake follow crush; straw follows harvest (collection lag).

### Step 6 — Harvest timing from satellites (build)
- Sentinel-2 L2A (2017+) & Landsat (2008+): harvest when NDVI drops ≤ ~0.30 with B11 > B8A (cane_cycle logic — reimplement), Sentinel-1 VH change points under cloud.
- Aggregate harvested area per catchment per month → mill-specific monthly profile and activity flag.
- Validate against UNICA biweekly totals.

### Step 7 — Non-cane substrates
| Substrate | Base data | Method |
|---|---|---|
| Manure | Livestock points (have) + PPM totals + LUPA/Censo confinement shares | Points × head × manure/head/day × collectable fraction (confined only); rescale to PPM |
| Poultry (layers, Bastos cluster) | Points + PPM | Same; seasonality ~flat. Keep layers and broilers apart: their N and K loads differ, and both limit the manure share in the CSTR |
| Sewage sludge | ANA ETE points + SINISA flows | Flow × sludge factor; only plants above size threshold |
| OFMSW | CETESB RSU t/d per landfill/municipality | Organic fraction × collection scenario. Local yield lead: IEE/USP plant, 120–180 Nm³ biogas per t (S, `digest_queue.csv` 20261006-01/02) |
| Agro-industrial (slaughterhouse, dairy, citrus) | SIF points; others TBD | Coefficients per unit of output |
| Competing uses | PILAR-2b FDE | Apply mobilisable fraction |

PPM base year: the held series ends in 2024 (`ibge_ppm`). IBGE published PPM 2025 in September 2026: Brazil's cattle herd fell 1.7 % and milked cows reached the lowest level since 1979, while poultry set a record, and SP produces 22.5 % of the national eggs (digest 2026-10-06, S). In western SP the manure base-load (strategy S2) should therefore lean on poultry, not cattle. Re-export the 2025 municipal tables before Phase 1.

### Step 8 — Outputs & checks
- Tables: `mill_year`, `mill_month`, `hex_supply` (Parquet), with `p05/p50/p95`.
- Checks: Σ mills ≈ UNICA SP totals; Σ cells ≈ IBGE; ethanol/cane within 70–90 L/t; vinasse ratio flags.

## 4. Open issues
- Generated vs applied vs available vinasse (Santa Adélia ~5.6 L/L applied) — see conflicts.
- Mill status history (closures 2008–2015).
- Border effects (cane from MG/PR/MS supplying SP mills and vice versa).
- Typical SP haul distance (20–30 km grey literature) — derive from calibrated β.

## 5. Implementation status (residues v0, 2026-10-06)

Module: `engine.supply.residues`. It is the supply step of the walking skeleton (ADR-0010); Steps 1–3 (facilities, cane per H3 cell, Huff allocation) are not wired in yet, so the skeleton starts from the cane crushed per mill. Tests: `tests/test_supply_residues.py`.

**Implemented (Steps 4–5, for one mill and one crop year)**
- `coefficients_from_registry()`: ethanol yield, vinasse ratio, filter cake, straw and its recoverable share and TS (`ethanol_yield`, `vin_gen`, `fc_gen`, `straw_gen`, `straw_recov`, `straw_ts`), each recorded in `param_ids`.
- `monthly_residues()`: one row per month from April to March, with unit-suffixed columns. **Generated and sent-to-AD are separate columns** (CLAUDE.md §2 rule 9). The AD shares (`vinasse_to_ad_frac`, `filter_cake_to_ad_frac`, `straw_to_ad_frac`) have no default, because they are calibration targets (docs/13 §3.2). The mill's own ethanol volume (for example from its RenovaBio report) can replace the yield.
- `to_feed()`: the long table that `engine.process.mass_balance.simulate` reads.
- A check against the Santa Adélia 2023 report: its cane gives ethanol within 1 % of the reported volume. That is expected, because `ethanol_yield` was derived from the same report (flag D).

**v0 assumptions, stated in code**
- **Harvest profile:** `UNIFORM_APR_NOV`, equal shares from April to November. It is a placeholder until the UNICA biweekly series is downloaded; any profile can be passed instead.
- **Vinasse is generated with the ethanol of the same month.** There is no vinasse storage or lag.
- **No filter-cake storage.** Off-season months get zero residues; storage belongs to strategy S1 (docs/10 §3), which waits on φ_store (lab E1).

**Manure base-load v0 (2026-10-07):** `engine.supply.manure.manure_potential` turns PPM herds (long table, unit `head`; PILAR-2b `municipality_timeseries`, source `ibge_ppm`) into manure (t FM/yr), VS (t/yr) and CH₄ (Nm³/yr):
- head × rate per head per day × 365, where a rate in litres is converted with the slurry density;
- VS = manure × TS × VS/TS; CH₄ theoretical = VS × BMP; CH₄ collectable = theoretical × `collect_frac`.

The collectable share has no default. A species runs only when all its coefficients are in the registry; `missing_coefficients()` lists the gaps (docs/21 Q16). Today swine lacks a slurry density, poultry a per-bird rate, and cattle a herd-average rate. BMP is a laboratory maximum; plant conversion is applied later (docs/10).

**Not yet implemented:** Steps 1–3 and 6, Monte Carlo over the coefficients, and the UNICA profile.
## 6. Urban-residue ceiling (2026-10-08)
- **Why.** The project lead framed urban residues (RSU, sewage sludge) as follows:
  - they are the fast start: landfill gas capture is already being built in SP;
  - they have a ceiling and weak long-term stability;
  - plants rely mainly on agro-industrial residues (ADR-0017 notes).
  - The question is how large that ceiling is and how few places hold it.
- **Script.** `scripts/supply/urban_ceiling.py <grade_oferta_1km.gpkg> <grid folder> [--names …]`.
  - Statewide N3 per residue and scenario for all 16 residues, with the share held by the urban group (RSU_ORGANICO, PODA_URBANA, LODO_ETE).
  - Urban N3 per municipality, with rank and cumulative share.
  - The number of municipalities that hold 50, 80 and 90 % of urban N3 med (`engine.supply.concentration`).
  - Point facilities use their `ibge` field. 1 km cells get the IBGE code of the H3 grid cell of their centroid. Any unassigned urban N3 is reported.
  - Farm-register residues appear only in the statewide totals (LGPD).
- **Reading it.** N3 is the CP2b mobilisable CH₄ potential (flag D), in Nm³ CH₄/d.
  - It is not landfill-gas recovery from existing landfills, which depends on waste age, decay and collection efficiency.
  - It is not biomethane plant capacity either.
  - Landfill projects in SP listed in `research_notes/R07_projects_costs_update_2026.md` are news-level (S) and quote biomethane capacity: Orizon Tremembé, Guatapará, Itapevi, the Estre "Piratininga" landfill, and Onebio Paulínia. Compare them with the ceiling as an order of magnitude only, after converting biomethane to CH₄ with a sourced CH₄ content.
- **First run (2026-10-08, `docs/inbox/urban_ceiling_run.txt`; gpkg sha256 c4bfbc72…).** All values are N3 in Nm³ CH₄/d (flag D).

  | | min | med | max |
  |---|---:|---:|---:|
  | Urban (RSU + sludge + prunings) | 123,235 | **652,196** | 2,412,750 |
  | All residues | 7,731,272 | 19,183,201 | 43,872,898 |
  | Urban share | 1.6 % | **3.4 %** | 5.5 % |

  - Urban med by residue: RSU_ORGANICO 442,516, LODO_ETE 140,906, PODA_URBANA 68,774.
  - Concentration (med):
    - São Paulo alone holds 141,147, which is 21.7 % of the urban total;
    - 21 municipalities hold 50 %, 104 hold 80 % and 193 hold 90 %, out of 645 with urban N3.
    - 1,846 of the med total could not be assigned to a municipality.
  - For comparison, cane residues give 15.5 M med: straw 8.25 M, filter cake 2.58 M, vinasse 2.42 M, bagasse 2.24 M. That is about 24 times the urban ceiling.
- **Order-of-magnitude check against announced landfill projects in SP.**
  - Biomethane capacities, all S (news), from `R07`:
    - Onebio Paulínia: 180,000 initially, up to 300,000 (docs/21 lists the 180k/225k/300k conflict);
    - Tremembé: 32,400;
    - Itapevi: ≥ 25,000 (offtake minimum);
    - "Piratininga": about 25,000;
    - Guatapará: not split from a 170,000 total shared with a PR plant.
  - Without Guatapará, these add to about 262,000–382,000 Nm³/d of biomethane. That is roughly 40–60 % of the urban N3 med, before converting biomethane to CH₄ (needs a sourced CH₄ content).
  - The two numbers measure different things:
    - a landfill draws on the waste stock of past decades and on a catchment of many municipalities;
    - N3 is today's mobilisable flow.
  - So the comparison supports the project lead's reading only as an order of magnitude: the urban ceiling is small (3.4 % of N3) and the announced landfill projects already cover a large part of it.
