# 11 — Economics module (cost, viability, risk)

## 1. Goal
Per site × strategy × scenario: CAPEX, OPEX, revenues, cash flow, **LCOB**, NPV, IRR, payback — as **distributions** (Monte Carlo), with global sensitivity (Sobol).

## 2. Levelized cost of biomethane (real terms)
$$\text{LCOB}=\frac{\sum_{y}\frac{I_y + O_y + F_y + T_y - R^{co}_y}{(1+r)^y}}{\sum_{y}\frac{E_y}{(1+r)^y}}$$
- I investment, O O&M, F feedstock (gate fees ±), T transport, R^co co-product revenue (digestate, CO₂), E biomethane (Nm³ or MMBtu), r real WACC.
- Simplified annuity form: $\text{LCOB}=\frac{\text{CAPEX}\cdot CRF + \text{OPEX} + F + T - R^{co}}{E}$, $CRF=\frac{r(1+r)^n}{(1+r)^n-1}$.
- Report in **R$/Nm³** and **US$/MMBtu** (state FX and year).

## 3. CAPEX

### 3.1 Components (bottom-up structure from KTBL/DEA; values Brazilian where possible)
Reception & storage (incl. filter-cake silos) · pre-treatment · digesters (per m³) · gas holder · H₂S removal · upgrading (per Nm³/h raw biogas) · compression/CNG/LNG · grid connection (TUSD-Verde: network km + Bio-Citygate) · digestate handling · civil, electrical, automation · engineering, contingency, owner's costs · land.

### 3.2 Top-down empirical curve (Brazil)
$$\log(\text{CAPEX}_{ij}) = \alpha + \beta\log(\text{cap}_{ij}) + \gamma_{\text{feedstock}} + \delta\,\text{scope}_{ij} + u_{\text{country}(j)} + \varepsilon_{ij}$$
- Data: `registry/projects_capex.csv` (Brazil, ~20) + international plants (BIP TF4, DEA, KTBL model plants, EBA) as other "countries".
- Priors: β ~ N(0.65, 0.1); u_country ~ N(0, τ).
- Normalize first: capacity basis (harvest-day vs annual ÷ 365; biogas vs biomethane), scope (with/without pipeline, CO₂ recovery), price year (IPCA/INCC; CEPCI+FX for imported equipment).
- Reference anchors: EPE R$ 3,734.9/(Nm³/d) (NT 2025-08) and R$ 2,701.5 (NT 2023-07) [S].
- Accuracy class: AACE 18R-97 Class 5/4 → state it.

## 4. OPEX
| Item | Basis | Source |
|---|---|---|
| Electricity | kWh/Nm³ × tariff (ANEEL / own CHP) | process module; ANEEL |
| Maintenance | % CAPEX/yr (digester vs upgrading differ) | KTBL/DEA (verify) |
| Labour | FTE × SP wages | KTBL structure + Brazilian wages |
| Chemicals | alkali (vinasse), Fe for H₂S, activated carbon | literature |
| Feedstock | gate price / avoided disposal / purchase of manure | partners, literature |
| Transport | t·km cost function by material | ANTT/ESALQ-LOG |
| Digestate | spreading/fertirrigation cost (often already paid by mill) | mills |
| Insurance, admin | % CAPEX | standard |
| Reference | EPE OPEX R$ 0.150/Nm³ — **check scope** | EPE NT 2025-08 [S] |

## 5. Revenue stack
| Stream | Price basis | Notes |
|---|---|---|
| Gas sale | Parity: industrial NG delivered ≈ R$ 3.80/m³; Argus FOB R$ 3.28/m³ (Jan 2026); diesel parity for fleets | Scenario by buyer: Comgás call, Mercado Cativo Verde, free market, CNG/LNG |
| CGOB | No traded price yet; producers cite ≈ R$ 1/m³ needed | Scenario 0 / 0.5 / 1.0 / 1.5 R$/m³ |
| CBIO | ≈ R$ 25 (Jul 2026), historic 80–120 | Requires RenovaBio certification; **check legality of stacking with CGOB** |
| Digestate | NPK × fertilizer prices − logistics | MAPA registration if sold |
| Avoided costs | Own diesel fleet, own NG/LPG, electricity | Mill-integrated cases |
| Carbon credits | Voluntary (manure methane avoidance) | Additionality rules |
| SP certificate | Under design | — |

## 6. Finance & taxes
- WACC real (scenarios 8 / 10 / 12 %); BNDES/Fundo Clima debt share 70–89 % [D]; loan terms from BNDES CSV.
- Taxes: SP ICMS effective 12 % on biomethane (to 31/12/2026; renewal uncertain); PIS/COFINS; IBS/CBS transition 2026–2033; REIDI; incentivized debentures — **verify with counsel**.
- Lifetime 20 yr (upgrading replacement at ~10–12 yr).

## 7. Uncertainty & sensitivity
- Latin Hypercube Monte Carlo (n ≈ 10⁴) over CAPEX residual, capacity factor, BMP, prices, CGOB, WACC, FX.
- Morris screening → Sobol first/total indices (SALib).
- Outputs: LCOB/NPV distributions, P(NPV > 0), break-even CGOB, tornado, Sobol bars.

## 8. Validation
- Compare LCOB with EPE (R$ 0.78–1.83/m³ for a 2 Mt/yr mill), FIESP (US$ 9.1–13.7/MMBtu production; 15.1–28.3 with taxes & logistics), IEA via BNDES (US$ 15–27/MMBtu LatAm) — all [S].
- Sanity: European average ≈ €75–80/MWh (OIES 2026) [S].

## 9. Implementation status (LCOB v0, 2026-10-06)

Module: `engine.economics.lcob`. It is the economics step of the walking skeleton (ADR-0010). Tests: `tests/test_economics_lcob.py`, which also runs the chain cane → residues → CSTR → LCOB on registry values.

**Implemented**
- `crf()`, `capex_brl()` (linear in nameplate, or a power law with `scale_exp`), `lcob_annuity()` (the §2 annuity form, with each component per Nm³) and `brl_per_nm3_to_usd_per_mmbtu()` (heating value and exchange rate are explicit arguments).
- `economics_from_registry()` / `lcob_from_registry()`: specific CAPEX (`capex_epe` by default, or any other specific-CAPEX row), `opex_epe` per Nm³, `wacc_real` and `plant_life`.
- `compare_with_anchors()`: places an LCOB inside the registry ranges `lcob_epe_sucro` (R$/m³) and `lcob_fiesp` (US$/MMBtu, converted with `hhv_biomethane` and a given exchange rate).

**New registry rows (2026-10-06), all `K`:** `wacc_real` 10 % (8–12 %) and `plant_life` 20 yr, both the scenario choices of §6, with no external source yet; `hhv_biomethane` 38 MJ/Nm³ (37–39), from CLAUDE.md §3, used only for unit conversion.

**v0 limits**
- One CAPEX at year 0, constant real costs and output, no upgrading replacement, no taxes or financing structure.
- **No price-year escalation:** the EPE CAPEX is in R$ of Dec 2024 (docs/21 C15); other values keep their own years.
- The denominator is delivered biomethane, so the capacity factor from the process module drives the LCOB.
- **Not yet implemented:** NPV/IRR, the revenue stack, feedstock and transport costs from the supply and siting modules, Monte Carlo and Sobol (§7).

`compare_with_anchors(..., brl_per_usd=None)` lists the US$/MMBtu anchor without evaluating it. The skeleton runner uses this when no exchange rate is given (docs/13 §6).