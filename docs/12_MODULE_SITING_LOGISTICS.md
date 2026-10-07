# 12 — Siting & logistics module

## 1. Goal
Choose plant **locations, scales, feedstock contracts, storage and gas-delivery mode** (grid injection vs CNG/LNG trucking) that minimize system LCOB or maximize NPV — and build the **SP biomethane supply curve**.

## 2. Step-by-step

### Step 1 — Candidate sites
- Default candidates: **every active mill** (annexed plants are the realistic case), plus H3 cells passing suitability for hub plants (manure/sludge/OFMSW clusters).
- Hub candidates: H3 res 8 centroids filtered by exclusions.

### Step 2 — Exclusions & suitability (GIS)
- Hard exclusions (have): protected areas (UC), APP buffers, water bodies, urban areas, steep slopes, flood zones, ZAA "unsuitable".
- Soft criteria (score): distance to gas network/city gate, road class, distance to feedstock clusters, land price (IEA-SP VTN), digestate land (cane area within radius, P4.231 capacity).
- AHP weights optional (for comparison with Paulino et al. 2024) — main model uses explicit costs instead of weights.

#### Screening v0 and the suitability screen (2026-10-07, ADR-0016)
- **Screening v0** was run on the user's PC from the PILAR-2b SP export (`pilar2b_export_2026-10-07`). Per ethanol mill it computes the straight-line geodesic distance (GRS80, nearest search in EPSG:31983) to gas delivery points, gas pipelines, substations, transmission lines, highways, biogas and biomass thermal plants, protected areas, indigenous territories and INCRA settlements, plus the number of other mills within 30 km. It writes `data/processed/screening_v0/` (mills table, municipal panel, attribute keys, `run_meta.json` with input and output sha256).
  - These are **not** road distances and are not used for haul costs (Step 3).
  - First results (160 SP mill records, one of them a duplicate): within 25 km of a gas delivery point 22, of a transport pipeline 34, of a substation 54. The median mill is 0.7 km from a biomass thermal plant (its own cogeneration).
  - Data issues: gas pipeline layer partial (docs/21 Q17), a Paraná mill labelled SP (C32), a duplicate mill (C33).
- **Suitability screen** (`engine.siting.suitability`): normalise each criterion to [0, 1] with recorded bounds, weighted linear score, equal weights as baseline, Dirichlet random-weight ranks (median, 5–95 %, share in top k) and a one-at-a-time ±20 % weight check. Hard exclusions need a cited basis; INCRA settlements are a constraint, not an exclusion. The score narrows candidates; Step 5 decides.
- **Grid v0 scoring** (`scripts/siting/score_grid_v0.py`): H3 res-7 grid of SP (47,273 cells, 1,884 excluded by state protected areas or indigenous territories). Eight criteria: distance to gas network (min of delivery point, transport and distribution layers), substation and highway (lower is better), and cane, swine, poultry, cattle and population within 30 km (higher is better). Bounds 0 to the 99th percentile of non-excluded cells. Equal weights, 1,000 Dirichlet draws (concentration 1, seed 20261007), top-100 stability and ±20 % one-at-a-time. Under equal weights feedstock is 4 of 8 criteria; that choice is open and the map lets users change it.
  - **Distinct sites:** `suitability_sites_spaced_v0.csv` lists the best cells at least `--spacing-km` apart (default 30 km), by equal-weight rank and by robustness, because adjacent cells share their 30 km sums (ADR-0016 Notes).
  - **Normalisation:** `--normalization percentile` ranks each criterion among non-excluded cells instead of the linear 0–p99 scale, because herds and population are concentrated in few cells; outputs carry `_per`. It does not fix the main bias: feedstock as 4 separate criteria (cane saturated at p99 across the cane belt, three herd criteria) puts herd hot spots first. ADR-0017 (proposed) replaces them with one CH₄-within-30 km criterion.
  - **Extra exclusions:** `--exclude label=<polygon layer>` (repeatable) excludes cells whose centre falls inside, e.g. federal integral-protection UCs (`mapbiomas_federal_uc_integral`), missing from the v0 grid.
  - **WebGIS** `webgis/aptidao_biometano_sp.html` reads the script's `suitability_map_v0.csv` locally (no data embedded) and recomputes the score and the Dirichlet robustness in the browser for any weights. See `webgis/README.md`.
- **Energy demand per municipality** (2026-10-07): `engine.ingest.semil_anuario` + `scripts/ingest/semil_anuario_2024.py` extract the SEMIL Anuário de Energéticos por Município 2025 (ano base 2024; registry `semil_anuario_energeticos_2025`) into one row per IBGE municipality: electricity by class (consumers, kWh), natural gas by class (consumers, m³, only municipalities with piped gas) and petroleum derivatives + hydrated ethanol (L or kg). Names are matched to IBGE codes by normalisation plus an explicit alias list; unmatched names, row-like lines that were not parsed, and the gas table's sum vs its printed state total are written to `checks.json`. Candidate criteria: industrial + cogeneration gas demand (an off-taker for biomethane) and diesel use (a substitution market for bio-CNG). They enter the screen only after the PDF run is checked (docs/21 Q18, C34).

### Step 3 — Routing & OD matrices
- Graph: OSM Sudeste + DER-SP/DNIT attributes (surface, class) → Valhalla truck costing (weight/axle) or OSRM truck profile.
- Matrices: feedstock cells/points → candidate sites; sites → injection points/city gates/CNG stations.
- Cost per t·km by material (vinasse/digestate liquid tanker; filter cake/manure solid; CNG/LNG trailers) from ANTT cost methodology + ESALQ-LOG freight; payloads from CONTRAN 882/2021.

- **Road/straight-line detour factor (SP).** Median 1.295 (P10 1.152, P90 1.641) over 5,000 OD pairs on the OSM Sudeste road graph, falling from 1.442 at 1–5 km to 1.267 at 40–60 km (`road_detour_factor_*`, flag D, source `esd_fl_espacial_outputs`). Use it only where `engine.siting.routing.fallback_road_km` is explicitly allowed; routed distances stay the rule.

### Step 4 — Delivery mode
| Mode | Cost elements |
|---|---|
| Grid injection (distribution) | TUSD-Verde (network km + Bio-Citygate) per ARSESP 1.765/2025; compression to grid pressure |
| Transmission injection | Higher pressure, fewer points |
| CNG virtual pipeline | Compression 200–250 bar, trailers, decompression at client |
| LNG/LBG | Liquefaction CAPEX/energy; Lidköping analog |
| Own use / fleet | Mill trucks, tractors (diesel parity) |
| Third-party fleet corridor | Delivery to open-access truck stations, such as the TransJordano corridor (Ribeirão Preto–Sumaré–Cubatão, docs/16 §2b); CNG transport cost to the nearest station |

### Step 5 — Optimization model (multi-period MILP)
Sets: sites *j*, feedstock sources *s*, months *t*, sizes *k*, modes *m*.
Decisions: open site with size *k* (binary), flows x_{s,j,t}, storage inventory I_{j,t}, gas delivered by mode.
Objective: minimize Σ (annualized CAPEX + OPEX + transport − co-product revenue) − or maximize NPV with revenue scenarios.
Constraints: supply availability per month; process constraints linearized (OLR, HRT, TS) per site-month; storage balance with losses (I_{t+1} = (1−λ)I_t + in − out); capacity linking; mode capacity; one plant per mill (option).
Solver: HiGHS via Pyomo or linopy; Gurobi academic if size requires.
Formulation reference: OptBio (Monteiro et al., arXiv:2603.06823, Mar 2026) [S], an open two-stage stochastic MILP with CVaR for Brazilian sugarcane biorefineries, including biomethane, with piecewise-linear economies of scale. Read it before writing this step.

### Step 6 — Supply curve
- For each optimal site: annual biomethane and LCOB (Monte Carlo bands).
- Sort by LCOB → cumulative Nm³/d vs R$/m³ (merit order).
- Overlay: mandate volumes (0.5 %, 1 %, 10 %), NG parity, parity + CGOB scenarios.

### Step 7 — Sensitivity of siting
- Allocation rule (Huff vs Voronoi vs LP), haul cost, CGOB price, connection rules, storage loss.

## 3. Benchmarks
- Paulino, Cherri & Soler 2024 (SP, GIS-AHP + optimization) — reproduce their criteria as a baseline, then show what changes with costs/seasonality.
- Blanco, Hinojosa & Zavala 2024 (waste-to-biomethane logistics: pipeline vs LNG).
- Jonker et al. 2016 (sugarcane spatial LP), Costa et al. 2020 (location-allocation for sugarcane supply; Triângulo Mineiro, MG, not SP).

## 4. Outputs
Maps of optimal sites/scales/modes, supply curve figure, table of top sites, scenario comparison.
