# PROJECT.md — SP Biomethane Techno-Economic & Siting Engine

**Working title:** *Where and at what cost can São Paulo produce biomethane year-round? A calibrated spatial techno-economic model of CSTR co-digestion.*
**Host:** CP2B — Centro Paulista de Estudos em Biogás e Bioprodutos · NIPE-UNICAMP
**Related platform:** PILAR-2b (cp2b.unicamp.br/pilar2b)
**Status:** Phase 0 (foundation, requests, walking skeleton) · v0.1 · 2026-10-03 · re-planned 2026-10-05 (ADR-0010)

---

## 1. Problem

- Brazil's biomethane mandate (Lei 14.993/2024, Combustível do Futuro) set a 1 % base for 2026; **CNPE cut it to 0.5 %** (Res. 4/2026) citing insufficient supply.
- Installed capacity is growing (~21 plants, ~1.37 million Nm³/d nationally in Jul 2026), but **actual output lags nameplate**: SP mill-based plants show capacity factors of **0–58 %**, with strong **off-season collapse** (ANP monthly data).
- São Paulo has the country's largest sugarcane residue base (vinasse, filter cake, straw) plus livestock and urban residues, but sugarcane residues are **seasonal (≈ April–November)**.
- There is no open, calibrated, spatially explicit tool that answers **cost, viability and location** jointly with **seasonality** for SP.

## 2. Research questions

1. **Supply:** How much vinasse, filter cake, straw and manure is available per mill catchment, per month, 2008–2025, with uncertainty?
2. **Process:** Which year-round co-digestion strategies (stored filter cake, manure base-load, other residues, shutdown/restart) keep a CSTR within safe operating limits, and what capacity factor do they reach?
3. **Economics:** What is the levelized cost of biomethane (LCOB) per site and strategy, and which revenue stack (gas, CGOB, CBIO, digestate) makes it viable?
4. **Siting:** Where should plants be located, at what scale, connected how (grid injection vs CNG/LNG trucking)?
5. **Policy:** What SP biomethane supply curve results, and what does it imply for the 0.5 %→1 %→10 % mandate path?

Hypotheses are in `docs/02_RESEARCH_QUESTIONS_AND_HYPOTHESES.md`.

## 3. Scope

| In scope | Out of scope (for now) |
|---|---|
| SP State, 645 municipalities | Other states (later via PILAR-2b national spine) |
| CSTR wet co-digestion (mesophilic/thermophilic) | Detailed reactor CFD; dry digestion |
| Vinasse, filter cake, straw, manure (cattle/swine/poultry), sewage sludge, OFMSW, agro-industrial | Energy crops |
| Upgrading → grid injection / CNG / LNG | Power-to-gas, e-methane |
| Monthly time step, 2008–2025 history + scenarios to 2035 | Real-time control / digital twin |
| ADM1 as later extension | — |

## 4. Objectives & deliverables

| # | Deliverable | Form |
|---|---|---|
| D1 | Verified data registry + mill-level residue panel SP 2008–2025 with uncertainty | Dataset (Zenodo DOI) + data paper |
| D2 | Process module (mass balance + operating constraints), calibrated on ANP monthly output | Code + methods doc |
| D3 | Economics module (CAPEX/OPEX, LCOB, NPV/IRR, Monte Carlo + Sobol) with Brazilian empirical CAPEX curve | Code + paper |
| D4 | Siting & logistics optimization (multi-period MILP) | Code + paper |
| D5 | **SP biomethane supply curve** (Nm³/d vs R$/m³) and maps | Paper + PILAR-2b layer |
| D6 | Integration of results into PILAR-2b (new layers/pages) | Release bundles |
| D7 | Lab/pilot experimental evidence on off-season strategies | LABIOEN/PPBIOEN papers |

## 5. Approach (one paragraph)

Public data (MapBiomas, IBGE/SEADE, ANP, RenovaBio certification reports, UNICA, infrastructure layers) is harmonized on an H3 grid. A **spatial interaction (Huff) model** allocates cane to mills and is **calibrated on mill-level RenovaBio data**; residues follow engineering coefficients and a monthly harvest profile. A **CSTR mass balance with operating constraints** converts substrate mixes into methane month by month. An **economics module** with a **hierarchical Bayesian CAPEX model** (Brazilian projects + international priors) computes LCOB and viability under Monte Carlo uncertainty. A **multi-period MILP** chooses sites, scales and logistics. The whole chain is **calibrated against ANP monthly plant output** (e.g. Raízen Costa Pinto, Cocal Narandiba) before scenarios are run.

## 6. Partners & roles

| Who | Role |
|---|---|
| CP2B / NIPE-UNICAMP (modeling team) | Engine, data, papers |
| LABIOEN (CP2B lab) | Substrate characterization, BMP, storage-loss tests |
| UNIFAL CEMARA | Lab support (scope to define) |
| PPBIOEN (pilot plant) | Continuous CSTR, substrate-switching protocols |
| São Martinho · Comgás · Equinor (experiments) | Validation data under NDA, grid/market input, investor criteria |
| PILAR-2b team | Platform integration |

## 7. Timeline (summary — details in `docs/19_ROADMAP_STEP_BY_STEP.md`)

| Phase | Weeks | Output |
|---|---|---|
| 0 Foundation, requests, walking skeleton | 1–6 | Repo, environment, LAI requests filed; end-to-end v0 on Costa Pinto and Narandiba; Morris ranking; top parameters verified |
| 1 Supply panel (cane + manure) | 7–11 | Mill-year & monthly residue panel; facilities registry |
| 1b Other substrates | alongside 2 | Sewage sludge, OFMSW, slaughterhouses, dairies |
| 2 Process + LCOB v0 | 12–15 | Calibrated to ANP curves |
| 3 Economics full | 16–19 | Bayesian CAPEX, Monte Carlo, Sobol |
| 4 Siting & supply curve | 20–25 | MILP, maps, supply curve |
| 5 Integration & papers | 26–33 | PILAR-2b release, manuscripts |

## 8. Success criteria

- ≥ 80 % of parameters used in results flagged **V**.
- Supply model reproduces RenovaBio mill-level cane within a stated error (target MAPE < 15 % on held-out mills).
- Process+economics chain reproduces observed monthly utilization pattern of ≥ 2 SP mill plants.
- Every number in a paper is traceable to `registry/` via `source_id`.

## 9. Where to start

`docs/00_INDEX.md` → `docs/04_DEV_ENVIRONMENT_SETUP.md` → `docs/19_ROADMAP_STEP_BY_STEP.md` (Phase 0 checklist).
