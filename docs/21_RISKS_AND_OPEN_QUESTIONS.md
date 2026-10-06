# 21 — Risks, conflicts and open questions

## 1. Data conflicts (log — resolve, never average)
| # | Topic | Value A | Value B | Status / rule |
|---|---|---|---|---|
| C1 | Vinasse per L ethanol | Literature 10–15 L/L (SP avg ~11.8) [S] | Santa Adélia 2023: ~5.6 L **applied** per L ethanol [V,D] | Model generated ≠ applied ≠ available; seek CETESB PAV |
| C2 | Costa Pinto capacity | ANP field 130,368 m³/d [V] | Announced 26 Mm³/yr (~71 k m³/d) [S] | Check biogas vs biomethane field; harvest vs annual basis |
| C3 | Capacity basis in announcements | "m³/d in harvest" | annual ÷ 365 | Normalize before CAPEX fit |
| C4 | IPCC manure VS/B₀ | Snippet values inconsistent | — | Read IPCC 2019 Vol. 4 Ch. 10 |
| C5 | EPE OPEX R$ 0.15/Nm³ | Looks low vs project-level OPEX | — | Check scope in NT |
| C6 | Cocal Narandiba start | Press: late 2021 or Jul 2022 [S] | ANP file: 0 % every month Jul 2022–Jul 2025, first output Aug 2025 [V] | Reporting gap vs real downtime vs field mapping — ask ANP/Cocal |
| C7 | Filter cake TS/VS and BMP | 185–260 NL/kg VS across studies | — | Use range; LABIOEN E6 |
| C8 | ZEG/Pindorama capacity & investment | R$ 60 vs 65 M; 36 k m³/d vs 6 M m³/yr | — | Find primary source |
| C9 | PILAR-2b raster `mapbiomas_agropecuaria_sp_2024.tif` | `mapbiomas_metadata.json`: year 2024, "MapBiomas Collection 8", EPSG:4326 | Grid 11,070 × 6,901 px over the stated bounds = 0.000808° per pixel (~90 m, 3× the 30 m MapBiomas grid) [D] | Use for screening maps only. Cane area per H3 comes from the official 30 m collection; confirm which collection the 2024 layer came from |
| C10 | CP2B potential by municipality and stream | `cp2b_redu_v2` (published, CC BY 4.0) | `cp2b_method_v5_1` (run of 2026-09-24, unpublished; ships its own v4→v5 reconciliation tables) | Not compared yet. Compare state and stream totals, check the CH₄ volume basis, then record both values here. Cite REDU v2 until v5.1 is published |
| C11 | ANP biomethane capacity and production | `anp_biomethane_plants` (PILAR-2b vendored copy) | `anp_biomethane_open_data_2026_04` (direct ANP files, to 04/2026) | Not compared yet. Diff plant lists and monthly volumes; volumes are m³ with no stated reference conditions |
| C12 | Filter cake CH₄ per tonne of fresh matter (three values) | `fc_ts_vs` × `fc_bmp`: 0.28 × 0.74 × 220 = **45.6** Nm³/t FM [S, D]; `fc_ch4_fm`: **54** (50–58) Nm³/t FM [S] | PILAR-2b `feedstocks.yaml` TORTA_FILTRO: TS 38 % × VS/TS 80 % × BMP 280 = **85.1** Nm³/t FM (refs: Talha et al. 2016; Velásquez Piñas et al. 2020) [S, D] | Found while building process v0 (docs/10 §7); third value found in the 2026-10-05 survey. Read each primary source and record its basis (lab BMP vs full scale; fresh vs stored cake; TS of which sample). Drives strategy S1. Never tune to close the gap |
| C13 | Vinasse composition and biogas CH₄ content | `parameters.csv`: TS / VS = 16 / 9 g/L (`vin_ts_vs`) [S]; CH₄ in biogas 57.5 % (CP2B convention note, `cp2b_method_v5_1_spatial`, citing feedstocks.yaml and Atlas SP 50–65 %) | PILAR-2b `feedstocks.yaml` VINHACA: TS 3 % (≈ 30 g/L), VS/TS 60 %, BMP 160 NL/kg VS; `ch4_pct` 65 % (no reference attached) [S/K] | TS differs about twofold. The two CH₄ values come from the same team: check which one the v5.1 run used (convention note says 57.5 %). Process v0 needs `x_ch4` as an input: run both until resolved |
| C14 | DOI of the 2015 vinasse AD review | `parameters.csv` `vin_gen`: "Moraes Zaiat Bonomi 2015 RSER 10.1016/j.rser.2015.01.023" | PILAR-2b `references.yaml` `bonomi2015_vinhaca`: "Bonomi, A. et al. … RSER 2015, 10.1016/j.rser.2015.01.022" | Authors and DOI suffix differ (.023 vs .022). Resolve the DOI on doi.org before citing either; fix the wrong record |
| C15 | Scope of the EPE NT 2025-08 specific CAPEX (`capex_epe`, the skeleton's LCOB anchor) | `parameters.csv` note: "Mix of landfill and agro" [S] | Radar digest 2026-10-06: R$ 3,734.9 per Nm³/d **in R$ of Dec 2024**, labelled "sugar-energy biomethane" (routine flag V, no page recorded) | Read the NT (verification target 1, docs/08 §5): record the page, the table title, the price year and which plant types it covers. If it is sugar-energy only, it anchors vinasse plants directly; if it is a mix, keep it as a sector average |

## 2. Open questions
1. Can CBIO and CGOB be claimed on the **same** biomethane volume? (legal)
2. Will SP ICMS reduction (12 %) be renewed after 31/12/2026? Effects of IBS/CBS?
3. What are actual **TUSD-Verde** values?
4. 2027 CNPE target (due 1 Nov 2026)?
5. Status of the SP biomethane origin certificate.
6. Per-plant monthly ethanol — will LAI succeed?
7. Typical SP cane haul distance (peer-reviewed)?
8. Which reactor types do SP mill plants actually use (CSTR vs plug-flow vs UASB)? Public sources describe stirred vertical tanks + horizontal digester (Geo design) — inference only.
9. Do zero months in ANP data mean shutdown or missing reports?
10. Was Programa Paulista de Biogás (Decreto 58.659/2012) revoked?
11. How much mill biomethane goes to power under capacity-reserve contracts (LRCAP) instead of the gas market? Cocal won 9.2 MW for 15 years from Aug 2028 (digest 2026-10-06, S). It is a competing outlet in the supply curve and a separate revenue route (docs/16 §4).
12. Will the revised CBPMESP IT-29 set separation distances for biomethane production? If yes, they become an exclusion buffer in siting (docs/12 Step 2).

## 3. Risks
| Risk | Impact | Mitigation |
|---|---|---|
| Key data refused (LAI) | Weaker calibration | RenovaBio reports; aggregated alternatives; partner data |
| Most parameters stay S/K | Credibility | Sensitivity-led verification on the walking skeleton (ADR-0010); gate criteria |
| Partner data confidentiality | Publication limits | Aggregate; private DVC; NDA terms early |
| Scope creep (ADM1, digital twin) | Delay | Phases & gates; ADM1 only after Gate 2 |
| Regulatory change (CGOB, ICMS) | Results outdated | Scenario-based design; monthly market notes |
| Compute/storage at home | Slow raster work | Aggregate to H3 in GEE; process in windows; Docker memory |
| Single-person bottleneck | Delay | Docs-first, ADRs, CLAUDE.md for AI-assisted continuity |
