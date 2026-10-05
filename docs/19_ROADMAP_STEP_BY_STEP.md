# 19 — Roadmap, step by step (the working checklist)

Tick boxes as you go. Each phase ends with a **gate** — don't move on until it passes.

> **Re-planned 2026-10-05 (ADR-0010).** Phase 0 now ends with a **walking skeleton**: two calibration mills, from cane to monthly CH₄ to LCOB, compared with ANP monthly output. Parameter verification follows the skeleton's sensitivity ranking instead of verifying everything up front. Phase 1 covers cane plus manure only, and the other substrates move to Phase 1b. Later phases keep their numbers and shift by about three weeks.

---

## PHASE 0 — Foundation, requests, walking skeleton (weeks 1–6)

### Week 1 — Environment & repo
- [x] Create private repo; copy this seed (`04_DEV_ENVIRONMENT_SETUP.md` §1) — done 2026-10-04 as the **public** repo `aikiesan/Project_Twin`
- [x] WSL2 + Docker Desktop configured (12–16 GB RAM); repo inside WSL, **not OneDrive** — native Windows route used instead (docs/04 §0b), repo on `A:\`
- [x] `uv` project, `pyproject.toml`, pre-commit (ruff, black, nbstripout)
- [x] DVC initialized; choose remote(s) — public-safe + private — manual Drive zips for now (ADR-0009)
- [x] `docker-compose.yml` with PostGIS (port 5433) + Jupyter
- [x] Create schema `engine` — exists since 2026-10-04; holds the raw tables since 2026-10-05. Restoring the PILAR-2b dump into `pilar2b` moved to Phase 5
- [x] Copy `feedstocks.yaml`, ANP `05c`/`05e` into `data/raw/pilar2b/` — as `pilar2b_canonical_parameters/` and `anp_biomethane_plants/`
- [x] Load the held datasets into PostGIS (`python -m engine.ingest.load_postgis`, docs/27) — 41 tables, 184,551 rows, private data in schema `private` (2026-10-05)
- [x] Register all **already-held** CP2B datasets in `registry/sources.yaml` (`status: have`, provenance) — 101 sources (2026-10-04); see docs/25
- [x] Survey and import the holdings in the `Documents` folders — 16 sources, 2026-10-05 (docs/25 §5)

### Requests that take time (do now — they are the critical path)
- [ ] File LAI R1 and R2 (ANP per-plant ethanol and biomethane) and R4 (CETESB vinasse plans) — `07_LAI_REQUESTS.md`
- [ ] File LAI R3 (SAPCANA) and R5 (CDA livestock); then R6 and R8; start the R7 agreement (LUPA)
- [ ] Email partners (São Martinho, Comgás, Equinor) with a precise data wish-list + NDA scope
- [ ] Email PPBIOEN/LABIOEN leads with E1–E3 proposals (`17_LAB_AND_PILOT_EXPERIMENTS.md`)

### Weeks 2–4 — Walking skeleton: Costa Pinto and Narandiba, cane → monthly CH₄ → LCOB
- [ ] Clip the MapBiomas col. 10 annual 30 m rasters (held under `Documents/ILUC_NIPE`) to SP, 2008–2024; register them, then run the `cane_area_h3` DVC stage
- [ ] Catchment v0 for the two mills: road distance (OSRM) and a simple nearest-mill rule, with parameters from `parameters.csv`
- [ ] Residues v0: vinasse, filter cake and straw from the coefficients in `parameters.csv`; monthly harvest profile (UNICA biweekly, or a fixed April–November profile until it is downloaded)
- [ ] Manure base-load v0 from municipal PPM herds (`ibge_ppm`), aggregated; no farm points
- [ ] Process v0: Level-1 CSTR mass balance with operating constraints (`10_MODULE_PROCESS.md`); unit test that reproduces Volpi et al. 2021
- [ ] LCOB v0: annuity, with EPE NT 2025-08 and the FIESP 2025 report as anchors
- [ ] Compare simulated and observed (ANP) monthly output for both plants; resolve or log conflicts C2 and C6
- [ ] Each run gets a `run_id` and a parameter hash; outputs go to `data/processed/skeleton/`

### Weeks 4–6 — Verification led by sensitivity
- [ ] Morris screening (SALib) on the skeleton, for annual CH₄, capacity factor and LCOB
- [ ] Add columns `page, quote, verified_by, verified_on, conditions, price_year, currency` to `parameters.csv`
- [ ] Verify the top-ranked parameters (target: top 15), in the order of `08_VERIFICATION_PROTOCOL.md` §5 within that set
- [ ] Normalize `projects_capex.csv` (capacity basis, scope, price year)
- [ ] Resolve/log all conflicts in `21_RISKS_AND_OPEN_QUESTIONS.md`

### Downloads, when a step needs them (was "Week 2 — Priority downloads")
- [ ] EPE NT 2025-08 (skeleton LCOB anchor), 2023-07, 2023-05; CNPE 4/2026; ANP 995/996/1.006/2026, 987/2025; ARSESP 744/1.342/1.765; Decreto 12.614/2025
- [ ] UNICA SP biweekly series (skeleton harvest profile)
- [ ] RenovaBio: list SP certified units (ANP); collect reports (Benri, Accenture, SGS, KPMG, Verifit, Totum) — needed for Phase 1
- [ ] SAPCANA registry — Phase 1
- [ ] ANP ethanol producers (capacity, tankage, production open data) — Phase 1
- [ ] BNDES operations CSV → filter biomethane/biogas — Phase 3

**Gate 0:** the skeleton runs end to end for both mills with a `run_id`; the Morris ranking is documented; ≥ 60 % of the top-15 parameters are `V`; LAI R1, R2 and R4 filed; environment reproducible on a second machine (done 2026-10-05).

---

## PHASE 1 — Supply panel: cane and manure (weeks 7–11)

- [ ] **Facilities registry** keyed on CNPJ (ANP + SAPCANA + RenovaBio + CP2B list); status by year
- [ ] **RenovaBio extraction**: LLM + schema + quotes (write `engine.ingest.renovabio_batch`); 10 % audit → `mill_year_renovabio.parquet`
- [ ] Cane per pixel → H3 res 8, rescaled to IBGE/SEADE municipal totals (2008–2025)
- [ ] Road-network OD matrix H3 → mills (Valhalla/OSRM)
- [ ] Huff allocation; **Bayesian calibration** on RenovaBio cane; leave-region-out validation
- [ ] Residue rules (vinasse generated/applied/available, filter cake, straw) with Monte Carlo
- [ ] Monthly profile from UNICA biweekly
- [ ] Manure: municipal PPM herds × coefficients, allocated to catchments; farm points only as a private aggregate
- [ ] Write/update `09_MODULE_SUPPLY.md` with actual choices and diagnostics

**Gate 1:** held-out mill cane MAPE < 15 % (or documented why not); Σ mills ≈ UNICA SP within tolerance; outputs with p05/p50/p95.
**Release:** `v0.1.0` bundle → PR to PILAR-2b (facilities + supply layers).

---

## PHASE 1b — Other substrates (alongside Phase 2, as time allows)

- [ ] Sewage sludge: ETE points + CETESB ICTEM 2024 + SNIS
- [ ] OFMSW: SNIS + CETESB IQR destinations (`cetesb_datageo_waste_indices`)
- [ ] Slaughterhouses (SIF) and dairies (RAIS screening points, confirmed by CNPJ before use)
- [ ] Prototype Sentinel-2 harvest detection on 3 catchments

---

## PHASE 2 — Process + LCOB v0 (weeks 12–15)

- [ ] Extend the skeleton's mass balance and constraints (`10_MODULE_PROCESS.md`) to all candidate mills
- [ ] Implement strategies S0–S5
- [ ] **Calibrate to ANP monthly** utilization: Costa Pinto (S0-like) and Narandiba (S1-like)
- [ ] Simple LCOB (annuity) with EPE anchors

**Gate 2:** simulated monthly profiles reproduce observed off-season collapse vs storage-supported operation (qualitatively and within stated error).
**Release:** `v0.2.0`.

---

## PHASE 3 — Economics full (weeks 16–19)

- [ ] Component CAPEX structure (KTBL/DEA) + Brazilian empirical curve
- [ ] **Hierarchical Bayesian CAPEX model** (Brazil + international priors)
- [ ] OPEX model; finance (WACC scenarios, BNDES terms); taxes
- [ ] Revenue stack scenarios (gas, CGOB 0–1.5, CBIO, digestate)
- [ ] LHS Monte Carlo + Morris + Sobol (SALib)
- [ ] Validate LCOB vs EPE / FIESP / IEA ranges

**Gate 3:** LCOB distributions for all candidate mill sites; Sobol ranking documented.
**Release:** `v0.3.0`.

---

## PHASE 4 — Siting & supply curve (weeks 20–25)

- [ ] Candidate sites (mills + hub cells) after exclusions
- [ ] OD matrices for feedstock and gas delivery; mode costs (grid/TUSD-Verde, CNG, LNG)
- [ ] Multi-period MILP with storage and process constraints (Pyomo/linopy + HiGHS)
- [ ] Baseline comparison with Paulino et al. 2024 criteria
- [ ] **SP biomethane supply curve** with Monte Carlo bands + mandate overlays
- [ ] Maps and figures

**Gate 4:** supply curve and optimal sites robust to allocation rule and key price scenarios (documented).
**Release:** `v1.0.0` → PILAR-2b pages.

---

## PHASE 5 — Integration, papers, shadow (weeks 26–33)

- [ ] Restore the PILAR-2b dump into schema `pilar2b` (moved from Phase 0)
- [ ] PILAR-2b: `engine_release` ingest, tables, API, pages
- [ ] Manuscripts (see `20_PUBLICATIONS_PLAN.md`)
- [ ] Monthly ANP ingestion + predicted-vs-observed dashboard (system-level shadow)
- [ ] Make repo public + Zenodo DOI at first paper submission

---

## Parallel tracks (any time)
- [ ] Lab E1–E2 (LABIOEN), pilot E3 (PPBIOEN)
- [ ] International benchmarks downloads (`15_INTERNATIONAL_BENCHMARKS.md` §5)
- [ ] Partnership contacts (DBFZ, KTBL, Swedish institutes, IEA Task 37 Brazil delegate)
