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

### Step 3 — Routing & OD matrices
- Graph: OSM Sudeste + DER-SP/DNIT attributes (surface, class) → Valhalla truck costing (weight/axle) or OSRM truck profile.
- Matrices: feedstock cells/points → candidate sites; sites → injection points/city gates/CNG stations.
- Cost per t·km by material (vinasse/digestate liquid tanker; filter cake/manure solid; CNG/LNG trailers) from ANTT cost methodology + ESALQ-LOG freight; payloads from CONTRAN 882/2021.

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
