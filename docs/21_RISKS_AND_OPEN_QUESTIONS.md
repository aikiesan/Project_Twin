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

## 3. Risks
| Risk | Impact | Mitigation |
|---|---|---|
| Key data refused (LAI) | Weaker calibration | RenovaBio reports; aggregated alternatives; partner data |
| Most parameters stay S/K | Credibility | Phase 0 verification sprint; gate criteria |
| Partner data confidentiality | Publication limits | Aggregate; private DVC; NDA terms early |
| Scope creep (ADM1, digital twin) | Delay | Phases & gates; ADM1 only after Gate 2 |
| Regulatory change (CGOB, ICMS) | Results outdated | Scenario-based design; monthly market notes |
| Compute/storage at home | Slow raster work | Aggregate to H3 in GEE; process in windows; Docker memory |
| Single-person bottleneck | Delay | Docs-first, ADRs, CLAUDE.md for AI-assisted continuity |
