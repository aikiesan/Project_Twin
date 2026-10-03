# 10 — Process module (what does a CSTR deliver, month by month?)

## 1. Goal
For a candidate plant with a monthly substrate mix, compute: digester volume needed, CH₄ produced, biogas & biomethane, parasitic energy, digestate (N, P, K), H₂S load, and **constraint flags** (OLR, HRT, TS, COD/SO₄, NH₃, K, FOS/TAC proxy). Start simple (mass balance), extend to ADM1 later.

## 2. Level 1 — Mass balance with operating constraints (v0)

### 2.1 Methane production
For each substrate *s* in month *t*:
$$\text{CH}_{4,t} = \sum_s m_{s,t}\cdot VS_s \cdot BMP_s \cdot f_{\text{scale}} \cdot \eta_{\text{kin}}(HRT) \cdot \phi_{\text{store},s,t}$$
- *m* fresh mass (t), *VS* volatile solids fraction, *BMP* (Nm³ CH₄/t VS), *f_scale* BMP→full-scale factor (`bmp_fullscale`, 0.85 [0.70–1.0]).
- η_kin: first-order completion at HRT: $1-e^{-k\cdot HRT}$ (k per substrate; lab fits pending).
- φ_store: storage retention for stored substrates (filter cake: `fc_storage_loss` — gap).
- Vinasse alternatively on COD basis: $Q\cdot COD\cdot\eta_{COD}\cdot Y_{CH4/COD}$ (`vin_cod`, `cod_removal`, `vin_ch4_yield`).

### 2.2 Biogas, upgrading, biomethane
- Biogas = CH₄ / x_CH4 (x_CH4 ≈ 0.55–0.65 typical; vinasse-led reported higher in two-stage).
- Biomethane = CH₄ × methane recovery (`upg_ch4_recovery`), at ANP spec.
- Electricity: upgrading (`upg_elec_membrane`) + mixing + pumping + compression (`compression_250bar` if CNG).
- Heat: digester heat balance (T_target, ambient from BR-DWGD/ERA5, U·A losses); vinasse leaves distillation hot → thermophilic is cheap at mills.

### 2.3 Operating constraints (checked monthly)
| Constraint | Rule | Param |
|---|---|---|
| OLR | Σ VS load / V ≤ OLR_max | `olr_max_cstr` (3.0 [2.5–4.8] kg VS/m³·d) |
| HRT | V / Q ≥ HRT_min | `hrt_cstr` (20–40 d; straw > 35 d) |
| TS in digester | ≤ 10–12 % (wet CSTR) | — |
| Sulfate | COD/SO₄ ≥ ~10 or H₂S management | `cod_so4_crit` |
| Ammonia | TAN ≤ threshold (poultry manure) | `tan_inhib` |
| Potassium | K ≤ ~3 g/L (gap) | `k_inhib` |
| pH/alkalinity | vinasse pH ~4.5 → recirculation/alkali | `vin_ph` |
| Stability proxy | FOS/TAC ≤ 0.35 (monitored in pilot) | `fos_tac_lim` |

Infeasible months → the strategy optimizer must change mix/volume or schedule shutdown.

### 2.4 Sizing
Digester volume V = max over months of (OLR-limited, HRT-limited) requirement — or optimize V jointly with storage and mix (see siting/economics). Report capacity factor = actual biomethane / nameplate upgrading capacity.

## 3. Off-season strategies to simulate
| Strategy | Description | Evidence |
|---|---|---|
| S0 Vinasse-only | Operate in harvest, idle off-season | Costa Pinto ANP pattern (0–12 % off-season) |
| S1 Stored filter cake (+straw) | Silo/ensiled filter cake fed off-season | Cocal reports; Narandiba 30–39 % off-season |
| S2 Manure base-load | Year-round manure + seasonal vinasse/cake | Danish/German co-digestion; Cocal Paraguaçu (poultry manure) |
| S3 Other residues | Sludge, OFMSW, agro-industrial off-season | BioNorrois (beet pulp + agri-food waste) |
| S4 Shutdown/restart | Stop and restart (~30 d) | Barbosa 2022 (restart beat switching) |
| S5 Hybrid | Optimized combination | — |

## 4. Level 2 — ADM1 (later)
- ADM1 (Batstone 2002) + sulfate reduction extension for vinasse (Barrera et al. 2015) for transient analysis of season switching.
- Calibrate with PPBIOEN continuous data (FOS/TAC, VFA, biogas, H₂S).
- Python options: QSDsan (ADM1), PyADM1; stiff solver (BDF/LSODA).

## 5. Validation
- Reproduce Volpi et al. 2021 thermophilic CSTR (vinasse + filter cake, max OLR 4.8 g VS/L·d, ~230 NmL CH₄/g VS).
- Reproduce ANP monthly utilization of Costa Pinto (S0-like) and Narandiba (S1-like) — see `13_MODULE_CALIBRATION_VALIDATION.md`.

## 6. Parameters
All in `registry/parameters.csv` (module = process). Most are **S/K** — verify before results.
