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
| S1 Stored filter cake (+straw) | Silo/ensiled filter cake fed off-season | Cocal reports; Narandiba 30–39 % off-season; Cocal's 15-year LRCAP 2026 contract, which cites stored vinasse and cake for year-round output [S, digest 2026-10-06] |
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

## 7. Implementation status (v0, 2026-10-05)

Module: `engine.process.mass_balance`. It is the process step of the walking skeleton (ADR-0010). Tests: `tests/test_process_mass_balance.py`.

**Implemented (§2.1–2.4)**
- `Substrate` on a VS basis (BMP × full-scale factor × first-order completion) or a COD basis (vinasse).
- `simulate()`, month by month: CH₄ → biogas → biomethane. Output is capped at the upgrading nameplate; the excess is reported as `biomethane_curtailed_nm3`. Capacity factor is reported per month.
- Monthly checks with three states (True, False, or None = not evaluable): OLR, HRT, feed TS, COD/SO₄ and potassium. `feasible` is true when every evaluable check passes.
- `size_digester()`: the volume that meets OLR and HRT in the worst month.
- `substrates_from_registry()` and `limits_from_registry()` build vinasse, filter cake and the limits from central values. Each substrate records the parameter ids it used.

**v0 assumptions, stated in code**
- **Density:** fresh-matter density is 1.0 t/m³ for every substrate. The registry has no density row; it is an explicit argument of `substrates_from_registry()`.
- **Minimum HRT:** the low end of `hrt_cstr` (20 d) is the minimum, and the central value (30 d) is treated as typical.
- **TS check:** it uses feed TS against 12 %, the upper end of §2.3. This is conservative, because digestion lowers TS.
- **Biogas CH₄ fraction:** `x_ch4` is a required input of `PlantDesign`. There is no registry row yet; §2.2 gives 0.55–0.65.
- **Mixed feeds:** COD/SO₄ and K are not evaluable when any fed substrate lacks those values, for example filter cake alongside vinasse.

**Not yet implemented:** the heat balance, electricity use, digestate N/P/K, H₂S load, a measured filter-cake storage loss (φ_store, which waits on E1) and the ammonia check (no TAN content per substrate). Strategies S2–S5 are Phase 2.

**Strategies S0 and S1 (2026-10-06).** Module `engine.process.strategies`; tests in `tests/test_process_strategies.py`.
- **S0** is the plain residue table: each residue is fed in the month it is generated.
- **S1** (`StorageS1`, `apply_s1_storage`):
  - a share of the filter cake sent to AD goes into one silo pool in the storing months;
  - the pool loses a constant fresh-mass fraction λ per month held;
  - it is emptied over the release months by the shares given, by the last release month.
- **v0 limits:**
  - λ applies to fresh mass, while `fc_storage_loss` is a share of methane potential and is not numeric yet. λ is therefore an explicit scenario input with its own source;
  - the off-season feed is cake only, so the TS check flags those months. Digestate recirculation for dilution is not modelled.

**Straw and manure (added 2026-10-05).** `parameters.csv` now holds TS, VS/TS, BMP and the biogas CH₄ fraction for straw (untreated), cattle slurry, swine slurry, fresh poultry droppings and poultry litter. The values come from PILAR-2b's `feedstocks.yaml` and its cited papers: S for TS, VS and BMP, and K for the CH₄ fractions, which have no reference attached. `substrates_from_registry()` builds all five, together with vinasse and filter cake. These are lab BMP values; the `b0_*` rows are IPCC B₀, a different concept, and are not used here.

**Biogas CH₄ fraction.** `PlantDesign.x_ch4` can be one value for the whole mix, or `None`. With `None`, biogas is Σ CH₄ₛ / xₛ over the fed substrates, and `x_ch4_mix` reports the result. A fed substrate with no fraction is refused, not guessed.

**Remaining registry gaps** (`REGISTRY_GAPS` in the module):
- **CH₄ fraction for vinasse and filter cake.** The vinasse value is in conflict (docs/21 C13), and filter cake has no row.
- **Fresh-matter density per substrate.** v0 assumes 1.0 t/m³.
- **TAN content per substrate,** needed for the ammonia check.

**Volpi et al. 2021:** `test_volpi_2021_consistency` only checks the two values recorded in §5 (maximum OLR 4.8 g VS/L·d, about 230 NmL CH₄/g VS). A full reproduction needs the paper's feed composition and HRT, so the paper is now on the verification list.

**Internal registry conflict found while building v0 (docs/21 C12):** filter cake TS 28 % × VS 74 % × BMP 220 NL/kg VS gives 45.6 Nm³ CH₄ per t FM. That is below the registry's own `fc_ch4_fm` range of 50–58 (central 54). Off-season strategy S1 depends on this value; resolve it during verification, never by tuning.
