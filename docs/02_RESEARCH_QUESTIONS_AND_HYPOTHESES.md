# 02 — Research questions, hypotheses and expected outputs

## RQ1 — Supply (where and when are the residues?)
**Question:** What is the monthly availability of vinasse, filter cake, straw, manure, sewage sludge and OFMSW per mill catchment / H3 cell in SP, 2008–2025?

| Hypothesis | Test |
|---|---|
| H1.1 A Huff-type spatial interaction model calibrated on RenovaBio mill data reproduces mill cane intake with MAPE < 15 % on held-out mills | Leave-mill-out and leave-region-out CV |
| H1.2 Municipal IBGE/SEADE totals + MapBiomas pixels are sufficient to downscale cane with bounded error | Compare to RenovaBio, CONAB, IEA-SP |
| H1.3 Vinasse *available for AD* is materially lower than *generated* in some mills (reporting basis, concentration, recirculation) | Santa Adélia-type reports; CETESB PAV via LAI |

**Outputs:** mill-year and mill-month residue panel with credible intervals; H3 supply rasters.

## RQ2 — Process (what does a CSTR actually deliver year-round?)
**Question:** Which off-season strategies keep a CSTR stable and maximize annual capacity factor?

| Hypothesis | Test |
|---|---|
| H2.1 Stored filter cake + manure base-load raises annual capacity factor by > 20 p.p. vs vinasse-only | Process module + ANP Narandiba vs Costa Pinto contrast |
| H2.2 Shutdown/restart (~30 d) is cheaper than substrate switching for some mills | Economics + Barbosa 2022 evidence; PPBIOEN tests |
| H2.3 Sulfate (COD/SO₄ < ~10) and potassium are the binding constraints for vinasse-led feeds | Constraint activity in simulations; LABIOEN data |

**Outputs:** monthly CH₄ per strategy; capacity factor distributions; constraint maps.

## RQ3 — Economics (what does it cost, is it viable?)
**Question:** What is the LCOB per site/strategy, and which revenue stack achieves NPV ≥ 0?

| Hypothesis | Test |
|---|---|
| H3.1 Brazilian specific CAPEX follows a scale exponent of 0.6–0.85 with a Brazil offset vs Europe | Hierarchical Bayesian CAPEX model |
| H3.2 Capacity factor is the single most influential parameter on LCOB (Sobol total index) | Global sensitivity |
| H3.3 Without CGOB ≥ ~R$ 1/m³, most new mill plants < 60 k Nm³/d are not viable at gas parity | NPV scenarios |

**Outputs:** LCOB maps, NPV/IRR distributions, tornado & Sobol charts, break-even CGOB price.

## RQ4 — Siting & logistics
**Question:** Where should plants be, at what scale, and connected how (grid vs CNG/LNG)?

| Hypothesis | Test |
|---|---|
| H4.1 Network-based catchments change optimal sites vs Euclidean | Compare allocations |
| H4.2 Multi-feedstock hubs near mills with manure within ~20–30 km dominate the low-cost end of the supply curve | MILP results |
| H4.3 Grid distance and TUSD-Verde connection cost decide grid vs virtual pipeline for many western-SP mills | Scenario comparison |

**Outputs:** optimal sites, scales, connection modes; maps; comparison with Paulino et al. 2024.

## RQ5 — Policy (the SP supply curve)
**Question:** How much biomethane can SP supply at each cost level, and what does it mean for the 0.5 %/1 %/10 % mandate path?

**Outputs:** SP biomethane supply curve (cumulative Nm³/d vs R$/m³) with Monte Carlo bands; mandate volume overlays; policy brief.
