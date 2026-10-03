# 01 — Context and motivation

## 1. The policy setting (verify all items — flags in brackets)

- **Lei 14.993/2024 (Combustível do Futuro)** created the *Programa Nacional de Descarbonização do Produtor e Importador de Gás Natural e de Incentivo ao Biometano*: natural gas producers/importers must reduce GHG emissions via biomethane, with a legal base of **1 % in 2026**, adjustable up to **10 %** [S].
- **CNPE Res. 4/2026** fixed the 2026 target at **0.5 %** (the MME had proposed 0.25 %) citing the current supply/demand situation; created the **Mesa de Monitoramento do Mercado de Biometano** [S].
  - Combined 2026/2027 compliance ≈ **181.7 million m³ biomethane** (≈ 505 thousand m³/d) [S].
  - Obligated parties: producers/importers averaging ≥ 160,000 m³/d [S].
- **ANP Res. 995/2026 & 996/2026** set individual targets and the **CGOB** (Certificado de Garantia de Origem do Biometano; **1 CGOB = 100 m³**); first certifications/issuances were still starting in Sept 2026 [S].
- Compliance: use biomethane directly or retire CGOBs by 31 Dec; fines R$ 100 k–50 M [S].

## 2. The supply situation

- Brazil: ~**21 authorized plants, ~1.37 million Nm³/d** capacity (Jul 2026); ~50 more in authorization (~2.0 million Nm³/d) [S].
- SP: ~9 authorized plants, ~0.7 million m³/d, about half the national capacity [S].
- **Capacity ≠ production.** PILAR-2b's ANP monthly dataset (`analysis/data/05e_anp_biometano_plant_volume_monthly.csv`) shows [V]:

| Month | Raízen Costa Pinto (vinasse + filter cake) | Cocal Narandiba (vinasse + filter cake + straw) |
|---|---|---|
| Feb–Mar 2025 (off-season) | 0–1 % | 0 % reported (ANP shows 0 % Jul 2022–Jul 2025 — see conflict C6) |
| Jul–Aug 2025 (peak) | 56–58 % | 46 % |
| Dec 2025–Mar 2026 (off-season) | 0–12 % | 30–39 % |

Interpretation (to test): **seasonality and ramp-up** drive low capacity factors; Narandiba's off-season output is consistent with reported **silo storage of filter cake/straw** [S].

## 3. Why São Paulo

- ~57 % of Centro-Sul cane crush (UNICA) [S]; ~170 mills listed (NovaCana) [S]; ~128 RenovaBio certificates in force in SP (2025) [S].
- Dense gas infrastructure (Comgás, Necta, Naturgy SP Sul), ARSESP rules for biomethane injection (Del. 744/2017, 1.342/2022, **1.765/2025 TUSD-Verde**) [S].
- Strong research base: CP2B, LABIOEN, PPBIOEN, PILAR-2b (645 municipalities), UNICAMP vinasse AD literature (Moraes group).

## 4. The gap this project fills

| Existing work | Limitation | This project |
|---|---|---|
| Potential inventories (EPE, Biomass 2026, PILAR-2b FDE) | Annual totals, no costs or siting | Monthly, mill-level, cost & siting |
| SP siting study (Paulino, Cherri & Soler 2024) | GIS-AHP + distance optimization, no seasonality/economics calibration | Seasonality, CAPEX realism, revenue stack, calibration to ANP output |
| TEAs of single plants (Paraná 2025, vinasse upgrading routes) | One site, deterministic | Statewide, probabilistic, comparable |
| FIESP SP study (2024) | Cost ranges (US$ 9.1–13.7/MMBtu production; 15.1–28.3 with taxes & logistics) [S] | Spatially explicit supply curve |

## 5. Naming — what this is and is not

- **Not a digital twin**: no live data from a single physical asset, no feedback control.
- **Is**: a *spatial techno-economic simulation / decision-support model* of SP's biomethane supply system.
- Once ANP monthly data is ingested automatically and predicted vs observed output is compared each month, it can be described as a **system-level digital shadow of SP's biomethane fleet** — a defensible claim.
- A plant-level shadow becomes possible later if PPBIOEN streams sensor data into the process module.

## 6. Key takeaways for the team

1. Supply is the bottleneck, but **utilization** (not only nameplate) is the hidden variable.
2. Seasonality is the core technical-economic problem for cane-based plants.
3. Mill-level data exists publicly (RenovaBio reports) — the model can be calibrated, not just assumed.
4. Revenues are defined in law but **largely unpriced** (CGOB not yet traded; CBIO at historic lows) → scenario analysis is essential.
