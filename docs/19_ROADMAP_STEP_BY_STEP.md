# 19 — Roadmap, step by step (the working checklist)

Tick boxes as you go. Each phase ends with a **gate** — don't move on until it passes.

---

## PHASE 0 — Foundation & verification (weeks 1–3)

### Week 1 — Environment & repo
- [x] Create private repo; copy this seed (`04_DEV_ENVIRONMENT_SETUP.md` §1) — done 2026-10-04 as the **public** repo `aikiesan/Project_Twin`
- [x] WSL2 + Docker Desktop configured (12–16 GB RAM); repo inside WSL, **not OneDrive** — native Windows route used instead (docs/04 §0b), repo on `A:\`
- [x] `uv` project, `pyproject.toml`, pre-commit (ruff, black, nbstripout)
- [x] DVC initialized; choose remote(s) — public-safe + private — manual Drive zips for now (ADR-0009)
- [x] `docker-compose.yml` with PostGIS (port 5433) + Jupyter
- [ ] Restore PILAR-2b dump into schema `pilar2b`; create schema `engine` — schemas exist (2026-10-04); `engine` holds the raw tables since 2026-10-05, `pilar2b` is still empty: dump not restored
- [x] Copy `feedstocks.yaml`, ANP `05c`/`05e` into `data/raw/pilar2b/` — as `pilar2b_canonical_parameters/` and `anp_biomethane_plants/`
- [x] Load the held datasets into PostGIS (`python -m engine.ingest.load_postgis`, docs/27) — 41 tables, 184,551 rows, private data in schema `private` (2026-10-05)
- [x] Register all **already-held** CP2B datasets in `registry/sources.yaml` (`status: have`, provenance) — 101 sources (2026-10-04); see docs/25

### Week 1 — Requests that take time (do on day 1!)
- [ ] File LAI R1–R6, R8 (`07_LAI_REQUESTS.md`); start R7 agreement (LUPA)
- [ ] Email partners (São Martinho, Comgás, Equinor) with a precise data wish-list + NDA scope
- [ ] Email PPBIOEN/LABIOEN leads with E1–E3 proposals (`17_LAB_AND_PILOT_EXPERIMENTS.md`)

### Week 2 — Priority downloads
- [ ] RenovaBio: list SP certified units (ANP); collect reports (Benri, Accenture, SGS, KPMG, Verifit, Totum)
- [ ] ANP ethanol producers (capacity, tankage, production open data)
- [ ] BNDES operations CSV → filter biomethane/biogas
- [ ] EPE NT 2025-08, 2023-07, 2023-05; CNPE 4/2026; ANP 995/996/1.006/2026, 987/2025; ARSESP 744/1.342/1.765; Decreto 12.614/2025
- [ ] SAPCANA registry; UNICA SP biweekly series

### Week 3 — Verification sprint
- [ ] Add columns `page, quote, verified_by, verified_on, conditions, price_year, currency` to `parameters.csv`
- [ ] Verify in order of `08_VERIFICATION_PROTOCOL.md` §5
- [ ] Normalize `projects_capex.csv` (capacity basis, scope, price year)
- [ ] Resolve/log all conflicts in `21_RISKS_AND_OPEN_QUESTIONS.md`

**Gate 0:** ≥ 60 % of parameters in the process + economics core are `V`; LAI filed; environment reproducible on a second machine.

---

## PHASE 1 — Supply panel (weeks 4–8)

- [ ] **Facilities registry** keyed on CNPJ (ANP + SAPCANA + RenovaBio + CP2B list); status by year
- [ ] **RenovaBio extraction**: LLM + schema + quotes; 10 % audit → `mill_year_renovabio.parquet`
- [ ] Cane per pixel → H3 res 8, rescaled to IBGE/SEADE municipal totals (2008–2025)
- [ ] Road-network OD matrix H3 → mills (Valhalla/OSRM)
- [ ] Huff allocation; **Bayesian calibration** on RenovaBio cane; leave-region-out validation
- [ ] Residue rules (vinasse generated/applied/available, filter cake, straw) with Monte Carlo
- [ ] Monthly profile from UNICA biweekly; prototype Sentinel-2 harvest detection on 3 catchments
- [ ] Non-cane substrates: livestock points × coefficients; ETE; RSU; SIF
- [ ] Write/update `09_MODULE_SUPPLY.md` with actual choices and diagnostics

**Gate 1:** held-out mill cane MAPE < 15 % (or documented why not); Σ mills ≈ UNICA SP within tolerance; outputs with p05/p50/p95.
**Release:** `v0.1.0` bundle → PR to PILAR-2b (facilities + supply layers).

---

## PHASE 2 — Process + LCOB v0 (weeks 9–12)

- [ ] Implement Level-1 mass balance + constraints (`10_MODULE_PROCESS.md`)
- [ ] Implement strategies S0–S5
- [ ] Reproduce Volpi et al. 2021 reactor numbers (unit test)
- [ ] **Calibrate to ANP monthly** utilization: Costa Pinto (S0-like) and Narandiba (S1-like)
- [ ] Simple LCOB (annuity) with EPE anchors

**Gate 2:** simulated monthly profiles reproduce observed off-season collapse vs storage-supported operation (qualitatively and within stated error).
**Release:** `v0.2.0`.

---

## PHASE 3 — Economics full (weeks 13–16)

- [ ] Component CAPEX structure (KTBL/DEA) + Brazilian empirical curve
- [ ] **Hierarchical Bayesian CAPEX model** (Brazil + international priors)
- [ ] OPEX model; finance (WACC scenarios, BNDES terms); taxes
- [ ] Revenue stack scenarios (gas, CGOB 0–1.5, CBIO, digestate)
- [ ] LHS Monte Carlo + Morris + Sobol (SALib)
- [ ] Validate LCOB vs EPE / FIESP / IEA ranges

**Gate 3:** LCOB distributions for all candidate mill sites; Sobol ranking documented.
**Release:** `v0.3.0`.

---

## PHASE 4 — Siting & supply curve (weeks 17–22)

- [ ] Candidate sites (mills + hub cells) after exclusions
- [ ] OD matrices for feedstock and gas delivery; mode costs (grid/TUSD-Verde, CNG, LNG)
- [ ] Multi-period MILP with storage and process constraints (Pyomo/linopy + HiGHS)
- [ ] Baseline comparison with Paulino et al. 2024 criteria
- [ ] **SP biomethane supply curve** with Monte Carlo bands + mandate overlays
- [ ] Maps and figures

**Gate 4:** supply curve and optimal sites robust to allocation rule and key price scenarios (documented).
**Release:** `v1.0.0` → PILAR-2b pages.

---

## PHASE 5 — Integration, papers, shadow (weeks 23–30)

- [ ] PILAR-2b: `engine_release` ingest, tables, API, pages
- [ ] Manuscripts (see `20_PUBLICATIONS_PLAN.md`)
- [ ] Monthly ANP ingestion + predicted-vs-observed dashboard (system-level shadow)
- [ ] Make repo public + Zenodo DOI at first paper submission

---

## Parallel tracks (any time)
- [ ] Lab E1–E2 (LABIOEN), pilot E3 (PPBIOEN)
- [ ] International benchmarks downloads (`15_INTERNATIONAL_BENCHMARKS.md` §5)
- [ ] Partnership contacts (DBFZ, KTBL, Swedish institutes, IEA Task 37 Brazil delegate)
