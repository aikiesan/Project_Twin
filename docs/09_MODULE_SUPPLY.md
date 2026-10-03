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
| Poultry (layers, Bastos cluster) | Points + PPM | Same; seasonality ~flat |
| Sewage sludge | ANA ETE points + SINISA flows | Flow × sludge factor; only plants above size threshold |
| OFMSW | CETESB RSU t/d per landfill/municipality | Organic fraction × collection scenario |
| Agro-industrial (slaughterhouse, dairy, citrus) | SIF points; others TBD | Coefficients per unit of output |
| Competing uses | PILAR-2b FDE | Apply mobilisable fraction |

### Step 8 — Outputs & checks
- Tables: `mill_year`, `mill_month`, `hex_supply` (Parquet), with `p05/p50/p95`.
- Checks: Σ mills ≈ UNICA SP totals; Σ cells ≈ IBGE; ethanol/cane within 70–90 L/t; vinasse ratio flags.

## 4. Open issues
- Generated vs applied vs available vinasse (Santa Adélia ~5.6 L/L applied) — see conflicts.
- Mill status history (closures 2008–2015).
- Border effects (cane from MG/PR/MS supplying SP mills and vice versa).
- Typical SP haul distance (20–30 km grey literature) — derive from calibrated β.
