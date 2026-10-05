# 05 — Data catalog (foundation v0.1)

**Scope:** São Paulo State · CSTR co-digestion (vinasse, filter cake, straw, manure, other residues) → upgrading → grid/CNG/LNG · costs, viability, technical and economic aspects, siting.
**Status:** v0.1 draft, 2026-10-03 · seed for `registry/sources.yaml`, `registry/parameters.csv`, `registry/projects_capex.csv`.

---

## 0. Read this first — verification status

This catalog was compiled from five parallel literature/data searches. The research environment **blocked direct access** to most primary sources (gov.br, epe.gov.br, bndes, arsesp, cetesb, sciencedirect, mdpi, ibge…) and hit a **web-search quota**, so most items were confirmed only through search-result snippets.

| Flag | Meaning | What to do |
|---|---|---|
| **V** | Document opened and read | Usable; still cite page/table |
| **S** | Seen in search snippet / abstract | **Verify number against original before citing** |
| **K** | From prior knowledge, not re-checked | **Verify existence, URL/DOI and value** |
| **D** | Derived/calculated by us from cited numbers | Re-derive after verification |

> **Rule for the project:** nothing enters `parameters.csv` as `confidence: V` until someone has opened the primary document and recorded the page/table. Phase 0 (§7) is a verification sprint run locally, where these sites are reachable.

---

## 1. Key findings (what changes the project design)

1. **Mill-level data exists publicly — via RenovaBio certification reports.** Inspection firms (Benri, Accenture, SGS, KPMG, Verifit, Totum) publish the RenovaCalc data of each certified unit during public consultation: **cane crushed, anhydrous/hydrated ethanol, vinasse applied, bagasse, electricity, straw, NEEA**. One was read in full (Usina Santa Adélia–Pereira Barreto: 2.33 → 3.55 Mt cane, 2021–2023; vinasse applied 1.29 → 1.61 billion L) **[V]**. ~128 SP certificates in force (2025) **[S]** → a near-census of mill-year data 2018–2025. This solves the "UNICA only has state totals" problem.
2. **ANP gives per-plant ethanol capacity and tankage (open)**, but monthly production only by UF/feedstock **[S]**. Per-plant monthly → LAI request (likely refused).
3. **The off-season problem is visible in official data, and so is the solution.** PILAR-2b's ANP monthly file shows Raízen Costa Pinto at **0–12 % utilization in the off-season vs 56–58 % at peak**, while Cocal Narandiba holds **30–39 % in the off-season** **[V, PILAR-2b `05e_anp_biometano_plant_volume_monthly.csv`]**. Press reports say Cocal **stores filter cake/straw in silos** for the off-season **[S]**, and the UNICAMP Moraes group showed a **thermophilic CSTR co-digesting vinasse + filter cake** works at up to 4.8 g VS/L·d, ~230 NmL CH₄/g VS **[S, Volpi et al. 2021]**.
4. **Real Brazilian CAPEX can be benchmarked** from ~20 announced projects (BNDES/Fundo Clima approvals, company releases): **≈ R$ 3,600–4,200 per Nm³/d for 60–100 k Nm³/d vinasse plants, ≈ R$ 5,200–7,500 per Nm³/d at 15–30 k Nm³/d** → implied scale exponent ≈ 0.6–0.85 **[D from S]**. EPE official factor: **R$ 3,734.9/(Nm³/d)**, OPEX **R$ 0.150/Nm³** (NT 2025-08) **[S]**. **BNDES per-operation financing CSV is open** (value, rate, grace, term) **[S]**.
5. **The regulatory revenue stack is now defined but unpriced.** CNPE Res. 4/2026 set **0.5 %** for 2026 → **181.7 million m³ (≈ 505 k m³/d) for 2026/27 compliance** **[S]**; ANP Res. 995/996/2026 define the **CGOB (1 CGOB = 100 m³)**; first issuances still pending in Sept 2026 **[S]**. Producers cite **≈ R$ 1/m³** as the CGOB value needed for new projects **[S]**. Only public biomethane price: **Argus FOB R$ 3.28/m³ (Jan 2026)** **[S]**; industrial NG delivered ≈ **R$ 3.80/m³**; CBIO ≈ **R$ 25** (Jul 2026, historic low) **[S]**.
6. **SP-specific grid connection rule exists:** ARSESP Del. 1.765/2025 (**TUSD-Verde**, Bio-Citygate paid by the producer) **[S]**. New spec **ANP Res. 1.006/2026** replaced 886/2022 and 906/2022 **[S]**. SP ICMS effective 12 % on biomethane **until 31/12/2026** **[S]**.
7. **Closest methodological precedent for SP siting:** Paulino, Cherri & Soler 2024, *Energy Reports* 11:4726 (GIS-AHP + optimization for biodigesters in SP) **[S]** — the work must benchmark against and go beyond it (seasonality, CAPEX realism, CGOB revenues, calibration to ANP output).

---

## 2. Data catalog by model module

Legend — **Have**: already held by CP2B/PILAR-2b · **Get**: open, to download · **LAI**: request via Lei de Acesso à Informação · **Paid**: subscription.

### 2.1 Supply — sugarcane mills

| Source | Gives | Spatial | Temporal | Access | Use | Conf |
|---|---|---|---|---|---|---|
| **RenovaBio certification reports** (Benri, Accenture, SGS, KPMG, Verifit, Totum) | Cane crushed, ethanol by type, vinasse applied, bagasse, electricity, straw, NEEA, eligible fraction | Per mill | Annual, 3-yr windows, 2018–2025 | Get (PDF/XLSX scraping + LLM extraction) | **Mill-level calibration labels** | V (1 report) / S |
| ANP RenovaBio certification panel + certificate list | Certified units, CNPJ, route, NEEA, eligible fraction, validity | Per unit | Weekly | Get | Active-mill registry, carbon baseline | S |
| ANP Plataforma CBIO panel | Lastro, CBIOs issued/retired | Per issuer (verify) | Biweekly | Get | Proxy for eligible ethanol sold | S |
| ANP Painel Produtores de Etanol + open data | Location, authorized capacity (anhydrous/hydrated m³/d), tankage; monthly production | Capacity: per plant · production: UF/feedstock | Monthly 2012–2026 | Get / LAI for per-plant | Point layer, capacity prior, seasonality | S |
| MAPA SAPCANA | Unit registry (type, municipality); production reports | Registry per unit; production state | Biweekly | Get / LAI | Status cross-check, SP biweekly curve | S |
| UNICA / UNICAdata | Crush, ATR, sugar/ethanol mix | Centro-Sul + SP | **Biweekly** | Have (2008–2018 SP totals) / Get | Intra-season curve | S |
| CONAB cana survey | Area, yield, crush, ATR, products | UF | 4×/season | Get | Annual validation | S |
| IEA-SP Banco de Dados | Cane area/production, herds | **Municipality / EDR** | Annual since 1983 | Get | Alternative to PAM | S |
| IBGE PAM / SEADE | Planted/harvested area, production | Municipality | Annual | **Have** 2008–2025 | Hard constraint for downscaling | — |
| MapBiomas cana 30 m | Cane pixels | 30 m | Annual | **Have** 2008–2025 | Dasymetric weight | — |
| CETESB P4.231 Vinasse Application Plans (PAV) | Measured vinasse volume, composition, field polygons | Per mill / field | Annual (filed by 2 April) | **LAI / partnership** | Gold-standard vinasse; digestate land constraint | S/K |
| Company reports (São Martinho, Raízen, Cocal…) | Crush, mix, sometimes per unit; biogas plants | Group / unit | Quarterly/annual | Get | Validation | S |
| NovaCana usinas DB | 170 SP mills, group, capacity, status | Per mill | Snapshot | Paid (partial free) | Status/capacity cross-check | S |
| Zheng et al. 2022 ESSD; Di Tommaso et al. 2024 ESSD | 30 m harvest area 2016–19; 10 m cane 2019–22 | 30 m / 10 m | Annual | Get (Zenodo) | Sharpen/validate MapBiomas | S |
| Sentinel-2/1 harvest detection (cane_cycle method; RS 2020 optical+SAR) | Harvest date per field | 10 m / field | 5–12 days | Build (GEE / STAC) | **Monthly supply per catchment** | S |

### 2.2 Supply — livestock and other off-season substrates

| Source | Gives | Spatial | Temporal | Access | Use | Conf |
|---|---|---|---|---|---|---|
| State livestock points (CDA/SAA) | Georeferenced farms | Point | Snapshot | **Have** | Manure supply | — |
| IBGE PPM tab. 3939 / 74 | Herds by species | Municipality | Annual 1974–2024 | Get (SIDRA API) | Herd totals constraint | S |
| Censo Agro 2017 | Confinement practice, herd-size classes | Municipality | 2017 | Get | Collectable fraction | S/K |
| **LUPA 2016/17** (CATI/IEA) | Farm-unit census: land use, livestock by type | Municipality/EDR public; UPA microdata restricted | 1995/96, 2007/08, 2016/17 (2026/27 planned) | Get / agreement | Finest SP livestock & land-use | S |
| GEDAVE / e-GTA (CDA-SP) | Herd balance per property, animal movements | Property | Event | **LAI** (aggregates) | Locate layers, swine, feedlots | S/K |
| MAPA SIF/SIGSIF | Slaughterhouses/dairies list; monthly slaughter | Point; UF | Monthly | Get (CSV) | Agro-industrial waste points | S |
| SISP (state inspection) | State-registered abattoirs/dairies | Point | — | **LAI** | Same | S |
| ANA Atlas Esgotos — ETE 2019 | WWTP points, process, design flow | Point | 2019 | Get (SHP) | Sludge supply | S |
| SINISA (ex-SNIS) | Sewage & solid waste volumes | Municipality/provider | Annual | Get | Sludge/OFMSW | S |
| CETESB Inventário RSU (+ IQR on DataGEO) | t/d per municipality and landfill | Municipality/landfill | Annual | Get | OFMSW, landfill gas | S |
| PILAR-2b FDE competing uses | Mobilisable fraction by residue | Municipality | — | **Have** | Availability ≠ generation | — |

### 2.3 Process (technical parameters) — see `parameters.csv` for values

Anchor literature (all **S/K — verify**): Moraes, Zaiat & Bonomi 2015 (RSER, 10.1016/j.rser.2015.01.023); Fuess, Garcia & Zaiat 2018 (STOTEN 634:29, seasonal vinasse characterization, SP); Fuess et al. 2024 (CEJ, seasonality solution); Janke et al. 2015 (IJMS 10.3390/ijms160920685 and 10.3390/ijms161023210); Janke et al. 2017/2018/2020 (straw, filter cake pre-treatment, CSTR); **Volpi … Moraes 2021** (AMB 10.1007/s00253-021-11635-x, thermophilic CSTR vinasse+filter cake); Volpi et al. 2022 (BioEnergy Res. 10.1007/s12155-021-10293-1); Kiyuna, Fuess & Zaiat 2017 (COD/SO₄); Barbosa et al. 2022 (JWPE, shutdown vs substrate switching); Chen, Cheng & Creamer 2008 (inhibition, 10.1016/j.biortech.2007.01.057); Angelidaki et al. 2018 (upgrading, 10.1016/j.biotechadv.2018.01.011); Bauer et al. 2013 (SGC 270); Holliger et al. 2016 (BMP protocol, 10.2166/wst.2016.336); Batstone et al. 2002 (ADM1) and Barrera et al. 2015 (ADM1 + sulfate for vinasse); IPCC 2019 Refinement Vol. 4 Ch. 10 (manure VS, B₀).

### 2.4 Costs

| Source | Gives | Access | Conf |
|---|---|---|---|
| EPE NT-EPE-DPG-SDB-2025-08 (2026–2035) + Resumo | CAPEX R$ 3,734.9/(Nm³/d) (25 units, 770 k Nm³/d, R$ 3.0 bi); OPEX R$ 0.150/Nm³ | Get | S |
| EPE NT 2023-07 (2025–2034) / 2023-05 (2024–2033) | R$ 2,701.5/(Nm³/d); sector potential CAPEX R$ 31.5 bi | Get | S |
| EPE LCOB sugar-energy (2 Mt/yr mill) | R$ 0.78–1.83/m³ | Get (identify which NT) | S |
| **BNDES open data — operações não automáticas (CSV, ODbL)** | Per operation: client, CNPJ, municipality, description, value, rate, cost base, grace, term | Get (CSV, `;`, Windows-1252) | S |
| BNDES TD 159 "A hora do biometano" (2024) | IEA-based US$ 15–27/MMBtu (LatAm) | Get | S |
| FIESP consortium SP study 2024 (via Brasil Energia) | Production cost US$ 9.1–13.7/MMBtu; 15.1–28.3 with taxes & logistics | Get original | S |
| Announced projects (see `projects_capex.csv`) | Capacity + investment → empirical CAPEX curve | Get | S/D |
| IEA Outlook for Biogas & Biomethane (2020; 2025 update) | Cost curves by feedstock, upgrading split | Get | K |
| AACE 18R-97; NETL QGESS; NREL TP-462-5173 | Estimate classes, capital cost levels, levelized cost method | Get | K |
| Escalation: CEPCI, INCC-M, IPCA, IGP-M | Cost indices | Get (CEPCI paid) | K |
| ESALQ-LOG SIFRECA | Freight R$/t·km per route (no raw cane/vinasse) | Paid/partial | S |
| CONTRAN 882/2021; ANTT freight floor | Payload limits; minimum freight | Get | S/K |
| IEA-SP Valor da Terra Nua; INCRA RAMT SP | Land price by municipality/EDR | Get | S |

### 2.5 Revenues & markets

| Source | Gives | Granularity | Access | Conf |
|---|---|---|---|---|
| MME Boletim Mensal Gás Natural | NG prices by distributor & consumer band | Distributor, monthly | Get (PDF) | S |
| ARSESP tariffs (Comgás, Necta, Naturgy SP Sul) | Tariffs by segment/band, TUSD | Concession, per adjustment | Get | S |
| Petrobras supply price releases | Molecule price changes (quarterly; Brent/FX/Henry Hub, collar 2026) | National | Get | S |
| Argus biomethane assessments | FOB plant price (R$ 3.28/m³ Jan 2026), parity indicators | National | Paid / press | S |
| IEPUC/PUC-Rio Boletim do Biometano (from Jul 2026) | Monthly capacity, utilization, substitute & attribute prices | National | Get | S |
| ANP Levantamento de Preços (station-level weekly) | Diesel, GNV by station | Station / municipality | Get (CSV) | K |
| B3 CBIO prices; ANP RenovaBio panels | Daily CBIO price; NEEA per certified unit | Daily | Get | S/K |
| ANEEL tariffs; CCEE PLD | Electricity cost/opportunity (CHP alternative) | Distributor; hourly submarket | Get | K |
| IEA-SP / CONAB input prices | KCl, urea, MAP… → digestate value | SP / municipality, monthly | Get | K |
| ANP Painel Produtores de Biometano + PILAR-2b `05c/05e` | Capacity, monthly volume, utilization per plant | Per plant, monthly | **Have** | V |

### 2.6 Regulation (checklist inputs)

Lei 14.993/2024 (Combustível do Futuro) · Decreto 12.614/2025 · CNPE Res. 4/2026 (0.5 %) · ANP Res. 995/2026 (targets, CGOB) & 996/2026 (certification, lastro, issuance) · ANP Res. 1.006/2026 (spec; replaces 886 & 906/2022) · ANP Res. 987/2025 (producer authorization; replaces 734/2018) · ARSESP Del. 744/2017, 1.342/2022, **1.765/2025 (TUSD-Verde)** · Comgás Chamada Pública 01/2025 & Mercado Cativo Verde · SP Certificado de Garantia de Origem do Biometano Paulista (consultation; status unknown) · SP ICMS reduction (to 31/12/2026; verify decree no.) · RenovaBio (Lei 13.576/2017) · REIDI, incentivized debentures, PATEN (verify) · MAPA IN 61/2020 (digestate as fertilizer) · CETESB licensing + **P4.231** (vinasse) · SBCE Lei 15.042/2024 (no price yet). All **S/K**.

### 2.7 Spatial, logistics, environment

| Source | Gives | Access | Conf |
|---|---|---|---|
| Infrastructure (gas transport + distribution, city gates, injection, rail, transmission, roads) | — | **Have** | — |
| Exclusion layers | — | **Have** | — |
| DataGEO / IDEA-SP (SEMIL) | UCs, soils, DER roads, ZEE | Get (SHP/WMS) | S |
| DER-SP SRE; DNIT SNV | Road class & surface | Get | S |
| OSM (Geofabrik Sudeste) + Valhalla/OSRM | Truck routing, OD matrices | Get | S/K |
| ZAA Setor Sucroenergético (SAD-69 → SIRGAS) | Agro-environmental suitability | Get | S |
| CAR/SICAR | Property polygons, APP, RL | Get | S |
| IGC-SP; GEOSEADE; IBGE BC250 2023 | Official boundaries, census tracts, pipelines cross-check | Get | S |
| Rossi 2017 soil map; MapBiomas Solo | Soils for yield prior & digestate capacity | Get | S |
| FABDEM / Copernicus GLO-30 | Slope, earthworks | Get | S |
| BR-DWGD (Xavier 2022), ERA5-Land, CHIRPS, INMET | Temperature, wind, soil temp, rain → digester heat loss, harvest interruptions | Get | S |
| EPE WebMap; ANEEL SIGEL | Gas/biofuel/power layers for reconciliation | Get | S |

---

## 3. Baseline parameter table (summary — full table in `registry/parameters.csv`)

| Parameter | Central | Range | Unit | Basis | Conf |
|---|---|---|---|---|---|
| Vinasse generation | 12 | 10–15 | L/L ethanol | Moraes 2015; NEPAM; SP avg 11.8 | S |
| Vinasse COD (juice/mixed) | 30 | 15–50 | g/L | Fuess 2018; overview tables | S |
| Vinasse SO₄ | 2.0 | 0.6–6.4 | g/L | Fuess 2024; overview tables | S |
| Vinasse CH₄ yield | 0.30 | 0.25–0.34 | Nm³ CH₄/kg COD removed | Melo 2024; Moraes 2015 | S |
| Filter cake generation | 37 | 30–40 | kg/t cane | Janke 2015 | S |
| Filter cake BMP | 220 | 185–260 | NL CH₄/kg VS | Janke 2020; Volpi 2022 | S |
| Straw available | 140 × 0.5 | — | kg DM/t cane × recoverable fraction | CNPEM/LNBR | S |
| Straw BMP | 230 | 160–291 | NL CH₄/kg VS | Janke 2017 | S |
| Max OLR (CSTR, solids) | 3.0 | 2.5–4.8 | kg VS/m³·d | Janke 2015; Volpi 2021 | S |
| HRT (CSTR with solids) | 30 | 20–40 | d | Janke 2015 | S |
| Filter cake storage loss | 12 (4 mo) / 22 (6 mo) | 6–27 | % | Energy-cane proxy (Hoffstadt 2020) — **gap** | S |
| Restart after off-season | 30 | 30–60 | d | Barbosa 2022 | S |
| BMP → full-scale factor | 0.85 | 0.70–1.0 | – | Janke 2020 | S |
| Upgrading electricity (membrane) | 0.25 | 0.18–0.35 | kWh/Nm³ raw biogas | Bauer 2013; Angelidaki 2018 | K |
| Specific CAPEX, 60–100 k Nm³/d vinasse | 3,900 | 3,600–4,200 | R$/(Nm³/d) | Announced projects | D |
| Specific CAPEX, EPE average | 3,735 | 2,700–3,735 | R$/(Nm³/d) | EPE NT 2025-08 / 2023-07 | S |
| Scale exponent | 0.65 | 0.6–0.85 | – | Six-tenths rule + projects | D |
| OPEX (EPE reference) | 0.15 | to verify scope | R$/Nm³ | EPE NT 2025-08 | S |
| Biomethane FOB price | 3.28 | — | R$/m³ (Jan 2026) | Argus | S |
| NG industrial delivered | 3.80 | 3.78–3.87 | R$/m³ | MME 2025; IEPUC 2026 | S |
| CGOB viability threshold | 1.0 | — | R$/m³ (≈ R$ 100/CGOB) | Producers via Argus | S |
| CBIO price | 25 | historic 80–120 | R$/CBIO | B3 via IEPUC (Jul 2026) | S |
| Plant capacity factor | from ANP data | 0.0–0.6 observed SP mills | – | PILAR-2b `05e` | V |

---

## 4. Method reference library (anchor papers by module)

- **Siting (GIS-MCDA + optimization):** Paulino, Cherri & Soler 2024 (10.1016/j.egyr.2024.04.038) · Costa et al. 2020 (10.1016/j.renene.2020.01.050) · Akca et al. 2023 (10.1016/j.apenergy.2023.121932) · Blanco, Hinojosa & Zavala 2024 (10.1021/acssuschemeng.4c01429) · Malczewski 2006 · Saaty 1990 · ReVelle & Swain 1970. **[S/K]**
- **Supply chain with seasonality/storage:** Yue, You & Snyder 2014 (10.1016/j.compchemeng.2013.11.016) · De Meyer et al. 2014 (10.1016/j.rser.2013.12.036) · Ghaderi et al. 2016 (10.1016/j.indcrop.2016.09.027) · Jonker et al. 2016 (10.1016/j.apenergy.2016.04.069). **[S]**
- **Mill catchments:** Lamsal, Jones & Thomas 2017 (10.1287/trsc.2015.0650) · Branco et al. 2019 (Biomass & Bioenergy 127:105249, verify DOI) · Granco et al. 2018 (10.1016/j.biombioe.2018.02.001) · Huff 1964 · network Voronoi (Okabe 2008). Typical SP haul 20–30 km is **grey literature — gap**. **[S/K]**
- **Downscaling:** You & Wood 2006 (10.1016/j.agsy.2006.01.008) · Yu et al. 2020 SPAM (10.5194/essd-12-3545-2020) · Joglekar et al. 2019 (10.1371/journal.pone.0212281) · Mennis 2003 (10.1111/0033-0124.10042) · Gilbert et al. 2018 GLW3 (10.1038/sdata.2018.227). **[S]**
- **TEA & uncertainty:** Zimmermann et al. 2020 (10.3389/fenrg.2020.00005) · AACE 18R-97 · NETL QGESS · NREL TP-462-5173 · IEA 2020 Biogas Outlook · Saltelli et al. 2010 · SALib (Herman & Usher 2017) · Saltelli et al. 2019. **[S/K]**
- **Brazil/SP context:** Biomass 2026 inventory (MDPI 2673-8783/6/1/4) · Biomass 2025 Paraná TEA (10.3390/biomass5010010) · Melo et al. 2024 SP vinasse (10.3390/methane3020017) · Energies 2024 SP sewage (10.3390/en17071657) · WBA Market Report Brazil 2025 · IEE-USP/RCGI SP biogas map. **[S]**
- **Reproducibility:** Wilkinson 2016 (FAIR) · Pfenninger et al. 2017/2018 · PyPSA-Eur (Snakemake + Zenodo bundles) · Mölder et al. 2021 (Snakemake). **[K/S]**

---

## 5. Data conflicts already spotted (must be resolved, not averaged)

1. **Vinasse per liter ethanol:** literature 10–15 L/L, but Santa Adélia 2023 reports ~5.6 L *applied* per L ethanol **[V, D]** → applied ≠ generated (concentration, recirculation, reporting basis). Model must distinguish *generated*, *applied*, and *available for AD*.
2. **Costa Pinto capacity:** ANP 130,368 m³/d (biomethane capacity field) vs announced 26 Mm³/yr (~71 k m³/d) → check basis (biogas vs biomethane, harvest vs annual).
3. **Capacity basis in announcements** ("per day in harvest" vs annual ÷ 365) varies → normalize before fitting the CAPEX curve.
4. **IPCC manure VS/B₀** snippets inconsistent → read Vol. 4 Ch. 10 tables directly.
5. **EPE OPEX R$ 0.15/Nm³** looks low vs project-level OPEX → check scope (feedstock, digestate, energy excluded?).

---

## 6. Gaps & how to close them

| Gap | Route | Owner |
|---|---|---|
| Per-plant monthly ethanol/crush | LAI to ANP (SIMP) & MAPA (SAPCANA); fallback: RenovaBio annual × UNICA biweekly curve | Data |
| Per-mill vinasse volume & application area | LAI / partnership with CETESB (PAV files) | Data |
| Farm-level livestock attributes | CDA/SAA aggregates (LAI) or research agreement; LUPA microdata via CATI/IEA | Data |
| Per-ETE sludge | LAI Sabesp/ARSESP; estimate from ANA design flows | Data |
| Filter cake storage loss (0–7 months) | **LABIOEN** experiment | Lab |
| Monthly vinasse composition (COD, SO₄, K, mix) | Partner mills / LABIOEN | Lab |
| Season switching protocol (vinasse → filter cake + manure) | **PPBIOEN** pilot | Pilot |
| BMP → CSTR correction; first-order k at 37/55 °C | LABIOEN + PPBIOEN | Lab/Pilot |
| Digestate N/P/K & P4.231 dose effect | LABIOEN | Lab |
| Upgrading, H₂S removal, compression CAPEX vs size | IEA, SGC 2013, DTI 2014, vendor quotes | Costs |
| TUSD-Verde values, ARSESP tariffs, CGOB traded prices | ARSESP, Comgás (partner), B3/registry once live | Market |
| WACC, TLP/Fundo Clima rates, taxes (IBS/CBS transition) | BNDES CSV, ANEEL/EPE WACC refs, tax counsel | Finance |
| Raw cane/vinasse/digestate freight per t·km | ANTT cost methodology + ESALQ-LOG | Logistics |
| SP haul distance (peer-reviewed) | Derive from catchment model; ask CTC/PECEGE | Spatial |

---

## 7. Step-by-step start (Phase 0 → 1)

> **Superseded in part by ADR-0010 (2026-10-05):** Phase 0 now ends with a walking skeleton on Costa Pinto and Narandiba, and verification follows its sensitivity ranking. The working checklist is docs/19.

**Phase 0 — Verification sprint (2–3 weeks, local machine, no modeling yet)**
1. Create the engine repo; commit `registry/` (this catalog, `sources.yaml`, `parameters.csv`, `projects_capex.csv`).
2. Download & checksum the "Get" items with highest value: BNDES CSV, ANP ethanol + biomethane open data, RenovaBio panel list, EPE NT 2025-08 / 2023-07, ARSESP Del. 1.765, ANP Res. 995/996/1.006, CNPE Res. 4/2026, IEPUC bulletins.
3. Open each primary document; upgrade parameters from S/K → V with page/table; resolve §5 conflicts.
4. File LAI requests (ANP, MAPA, CETESB, CDA, Sabesp) — they take 20–30 days.
5. Scrape all SP RenovaBio certification reports → structured mill-year table (LLM extraction with source quote per value + 10 % manual audit).

**Phase 1 — First calibrated slice**
6. Facilities registry keyed on CNPJ (mills + biomethane plants + livestock points).
7. Supply: MapBiomas → H3 → catchment allocation → mill-year cane, checked against RenovaBio mill data and IBGE municipal totals.
8. Process + LCOB v0, calibrated to reproduce the **Costa Pinto and Narandiba monthly utilization curves**.
9. First bundle to PILAR-2b (facilities layer + supply).

---

## 8. International benchmark sources (added after v0.1)

Used as **priors and benchmarks**, never as direct inputs. Details and usage in `15_INTERNATIONAL_BENCHMARKS.md`; registry ids prefixed `intl_` in `registry/sources.yaml`.

| Source | Gives | Use | Conf |
|---|---|---|---|
| DE Marktstammdatenregister (open XML dumps, `open-mastr`) | All generation units incl. biogas: size, commissioning/decommissioning dates | Size distributions; plant survival/shutdown hazard | S |
| DBFZ Ressourcendatenbank (CC BY 4.0), operator survey, plant inventory reports | Residue potentials, operating hours, substrate mix | Method template; performance priors | S |
| FNR/DBFZ Biogas-Messprogramm III (~60 plants) | Technical/biological/economic efficiency | Full-scale vs lab, parasitic load, availability | S |
| KTBL Wirtschaftlichkeitsrechner + Faustzahlen Biogas | Component-level CAPEX/OPEX, labour, model plants | Bottom-up cost structure | S |
| Danish Energy Agency Technology Data (renewable fuels) | Standardized CAPEX/OPEX + 2030/2050 projections | Learning/cost-trajectory priors | S |
| Biogas Danmark Outlook 2024 | Manure-based co-digestion at scale | Manure base-load analog | S |
| Energimyndigheten / Energigas Sverige | 330 plants; 2,688 GWh (2025); 67 % upgraded | Plant-type mix | S |
| Lidköping (Gasum) + IEA T37 LBG case study | Food residues, water scrubbing, LBG, 65 GWh/yr | Off-grid virtual pipeline analog | S |
| France ODRÉ / GRDF | 851 injection sites, 16.3 TWh/yr capacity, monthly | Grid injection & queue dynamics | S |
| BioNorrois (TotalEnergies + Cristal Union) | Sugar-beet pulp + agri-food waste, 100→153 GWh/yr | **Closest seasonal sugar-industry analog** | S |
| EBA/GIE Biomethane Map 2025 | 1,678 plants | Context | S |
| BIP TF4 cost study (Oct 2023) | Real industry CAPEX/OPEX by size/feedstock | Cost priors | S |
| OIES NG203 (2026); ACER 2026; IFRI 2026 | Cost trends (≈ €75–80/MWh avg), policy lessons | Context, priors | S |
| US EPA AgSTAR | Farm digesters incl. shutdowns | Failure rates for manure digesters | S |
| IEA Bioenergy Task 37 | Country reports (Brazil is a member), case stories | Benchmarks; dissemination channel | S |
