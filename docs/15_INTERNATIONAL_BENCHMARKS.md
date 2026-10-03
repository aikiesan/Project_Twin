# 15 — International benchmarks (Germany, Denmark, Sweden, France, EU, US)

## 1. Principle
Use international data as **benchmarks and statistical priors**, not as direct inputs. Europe differs in feedstock (maize silage + manure), climate (heating), and support schemes (EEG feed-in, French injection tariffs) vs SP (vinasse + filter cake, tropical climate, mandate + CGOB).

| Transfers well | Transfers with adjustment | Does not transfer |
|---|---|---|
| Upgrading energy & CH₄ slip; availability/operating hours; full-scale vs lab ratios; cost-structure shares; scale exponents; failure/shutdown rates | Absolute CAPEX (location factor, FX & price year, import duties, local civil costs via INCC); OPEX (labour, electricity) | Energy-crop economics; EU subsidies; heating needs; prices |

## 2. Sources and how to use each

### Germany
- **Marktstammdatenregister (MaStR)** — official register of all generation units, incl. ~biogas plants; daily XML dumps; `open-mastr` Python package; Zenodo bundles. **Use:** size distributions; commissioning/decommissioning → **survival analysis of plant shutdowns** (risk prior).
- **DBFZ** — Ressourcendatenbank (CC BY 4.0; potentials and current use of residues), annual operator survey (Betreiberbefragung), plant-inventory reports (Anlagenbestand). **Use:** method template vs PILAR-2b FDE; distributions of operating hours, availability.
- **FNR/DBFZ Biogas-Messprogramm III** — ~60 plants measured over ~4 years (technical, biological, economic efficiency). **Use:** full-scale/lab yield ratio, parasitic load, availability.
- **KTBL** — Wirtschaftlichkeitsrechner Biogas (free online, incl. biomethane route) + *Faustzahlen Biogas*. **Use:** component-level CAPEX/OPEX structure, labour, model plants.

### Denmark
- **Danish Energy Agency Technology Data — renewable fuels** (xlsx data sheets): standardized CAPEX/OPEX/efficiency with 2030/2050 projections. **Use:** learning-curve priors.
- **Biogas Danmark — Biogas Outlook 2024.** **Use:** manure-based co-digestion at scale (manure base-load analog).

### Sweden
- **Energimyndigheten / Energigas Sverige** statistics: 330 plants (end 2024); 2,688 GWh (2025, +12 %); 67 % upgraded; co-digestion plants + WWTPs ≈ 80 % of output [S].
- **Lidköping (Gasum):** ~100 kt/yr food-industry residues; 65 GWh/yr; water scrubbing; **liquefied biogas (LBG)**; 80 kt/yr biofertilizer; first gas Jan 2011 [S]. **Use:** analog for **off-grid/virtual-pipeline** delivery from mills far from the network. IEA Task 37 case study on non-grid biomethane transport in Sweden.

### France
- **ODRÉ / GRDF open data:** 851 injection sites, 16.3 TWh/yr capacity (Aug 2026), per site, monthly; reserved-capacity register (queue). **Use:** injection growth & queue dynamics (compare ARSESP TUSD-Verde).
- **BioNorrois (TotalEnergies + Cristal Union, Normandy):** sugar-beet pulp > 50 % of feed + agri-food waste; ~100 → 153 GWh/yr, transmission-grid injection; Cristal Union 10 % stake; 15-year supply deal [S]. **Closest seasonal sugar-industry analog.**

### Sugar-beet campaign analogs (seasonality ≈ 100 days)
- Hungarian sugar factory: half the press pulp (800 t/d, 22 % TS) digested; ~40 % of campaign NG demand substituted [S].
- Stored-beet methane yield studies (airtight storage) [S]. **Use:** storage-loss methodology for filter cake.

### EU-wide
- **EBA/GIE European Biomethane Map 2025:** 1,678 plants; 7 bcm/yr capacity; 86 % grid-connected [S].
- **BIP TF4 (Oct 2023):** current biomethane cost from **real industry data** — CAPEX/OPEX by size/feedstock. **Use:** cost priors.
- **OIES NG203 (Jan 2026):** avg production cost ≈ €75–80/MWh (range 50–175); **no sustained EU-wide cost decline since late 2010s**; strong scale economies [S].
- **ACER 2026; IFRI June 2026:** policy and market design lessons.

### United States
- **EPA AgSTAR** livestock digester database (Excel incl. shut-down projects). **Use:** failure rates of manure digesters.
- **EPA LMOP** landfill gas database.

### IEA Bioenergy Task 37
- Country reports & case stories; **Brazil is a member** → benchmark and dissemination channel for CP2B.

## 3. Statistical use (hierarchical pooling)
$$\log(\text{CAPEX}_{ij}) = \alpha + \beta\log(\text{cap}_{ij}) + \gamma_{\text{feedstock}} + u_{\text{country}(j)} + \varepsilon_{ij}$$
- Europe pins down β and γ; ~20 Brazilian projects estimate u_BR.
- Same pattern for capacity factor and shutdown hazard (MaStR/AgSTAR survival → prior for Brazil).

## 4. Partnership idea
CP2B ↔ DBFZ / KTBL / Swedish institutes (Energiforsk, RISE) — data exchange, co-supervision, joint papers.

## 5. Verification priority
1. BIP TF4 and DEA catalogue (cost) 2. Biogas-Messprogramm III (performance) 3. MaStR & ODRÉ (large-n) 4. BioNorrois + beet-pulp literature (seasonal analog).
