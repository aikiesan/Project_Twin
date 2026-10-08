# R11 — Deep-research prompt: Cocal Narandiba biomethane plant (reference plant)

- **Date:** 2026-10-08
- **Why:** the project lead named Cocal Narandiba (Narandiba, SP) as the reference plant (ADR-0017 notes, 2026-10-08). The repository holds only press snippets [S] and the ANP monthly series [V] for it, and two records disagree on its feedstock (docs/21 C36).
- **How to use:** paste the prompt below into a deep-research tool. Save the answer in `research_notes/raw/` and triage it like a digest (ADR-0012). Every value stays `S` until its page and verbatim quote have been read in the primary document (docs/08). A search-engine summary is not a source (docs/08 §8 rule 2).

## What the repository already holds (to be confirmed or contradicted)

| Item | Value in the repo | Where | Flag |
|---|---|---|---|
| Feedstock | vinasse + filter cake + straw | `registry/projects_capex.csv` row 3; docs/01; R04 | S |
| Feedstock (conflicting) | vinasse + filter cake + manure | `registry/sources.yaml` `pilar2b_biogas_plants_brazil` notes | S |
| Capacity | 25,000 m³/d (basis unclear) | `projects_capex.csv` row 3 | S |
| ANP authorised capacity | 27,112 m³/d | `projects_capex.csv` row 3 notes | S |
| CAPEX | R$ 150 M, price year 2021, plus R$ 30 M distribution pipeline | `projects_capex.csv` row 3 | S |
| Start of operation | late 2021 or Jul 2022 (press) vs first ANP output Aug 2025 | docs/21 C6 | S / V |
| Capacity factor | 30–49 % including off-season months | `parameters.csv` `capacity_factor` notes | V (ANP file via PILAR-2b) |
| Technology | Geo design; filter cake and straw stored in silos and fed off-season | R04 lines 57 and 64 | S |
| Pipeline | Necta / GasBrasiliano | R04 line 57 | S |
| LRCAP | Cocal won 9.2 MW for 15 years from Aug 2028; stored vinasse and filter cake cited for year-round output. Not stated which Cocal plant. | digest 2026-10-06; docs/21 Q11 | S |
| Cane crushed, storage shares, silo losses | empty | `registry/skeleton_mills.yaml` `narandiba` | — |

## Prompt (copy from here)

> You are researching one industrial plant for a peer-reviewed techno-economic study: the **Cocal biomethane plant at the Narandiba sugarcane mill, Narandiba, São Paulo State, Brazil** (Grupo Cocal; find the legal names and CNPJs of the mill and of the biogas/biomethane entity).
>
> **Rules. Breaking any rule makes the answer unusable.**
> 1. Never invent a number, URL, DOI, date or name. If you cannot find something, write "not found" and list where you looked.
> 2. For **every** value give: the value with its unit; the source URL; the document title, publisher and date; the page, table or paragraph; and a **verbatim quote** in the original language (Portuguese is fine). Prefer primary documents: ANP authorisations and the ANP biomethane production panel, Diário Oficial da União, CETESB licences, ARSESP/Necta filings, ANEEL/CCEE auction results, BNDES and MME REIDI portarias, RenovaBio/ANP certification records, Cocal sustainability or annual reports, company presentations, peer-reviewed papers. Press articles count only as secondary; say so.
> 3. Mark each value **PRIMARY** (you read it in a primary document) or **SECONDARY** (press, blog, summary).
> 4. Keep the quantities apart and say which one each source means:
>    - **biogas** (raw, ~50–60 % CH₄) vs **CH₄** vs **biomethane** (upgraded, ANP spec);
>    - **nameplate/authorised capacity** vs **actual production**;
>    - **per day during the harvest** vs **annual average** vs **per year**;
>    - **m³** vs **Nm³** (state the reference temperature and pressure if given).
> 5. When two sources disagree, report **both** values with their sources. Do not average or pick one.
> 6. Give the date of every statement. Plans, announcements and actual operation are different things; label each.
>
> **Questions.**
> 1. **Identity and location.** Legal operator(s) and CNPJ(s) of the mill and of the biogas/biomethane plant; address; geographic coordinates of the digesters and the upgrading unit (from a licence, ANP record or map); IBGE municipality.
> 2. **Feedstocks.** Which residues the plant digests: vinasse, filter cake, sugarcane straw, bagasse, animal manure (which species, from where), others. Their shares by mass, volatile solids or energy, and how they change between harvest and off-season. Two records disagree: "vinasse + filter cake + straw" vs "vinasse + filter cake + manure". Find which is correct, for which period.
> 3. **Mill data.** Cane crushed per crop year (t) since 2019/20; ethanol produced (m³, hydrated and anhydrous); vinasse generated (m³), how much goes to fertirrigation and how much to digestion; filter cake (t); straw recovered from the field (t, and how: baling or integral harvest); harvest start and end months.
> 4. **Technology.** Technology supplier (Geo Biogás & Tech or other) and EPC; reactor type (CSTR, plug-flow, UASB, other), number and volume of digesters; hydraulic retention time and organic loading rate; operating temperature; **pre-treatment of straw** (mechanical, thermal, chemical, other); co-digestion scheme; how filter cake and straw are **stored** (silage, silos, bunkers), how long, and any reported storage losses; biogas yield (Nm³/t of each feedstock) and CH₄ content; upgrading technology (membrane, PSA, water scrubbing, amine) and supplier; methane slip; on-site power or heat use.
> 5. **Capacity and production.** Nameplate biogas and biomethane capacity (with basis per rule 4); the **ANP authorisation** (number, date, authorised capacity); monthly biomethane production reported to ANP since the start; the date of first injection or first sale; expansions (planned or done) and their capacities.
> 6. **Start-up timeline.** Construction start, commissioning, first biogas, first biomethane, commercial operation. Sources say "late 2021" or "July 2022", while ANP monthly data show zero until July 2025 and first output in August 2025. Explain the gap if any source does (reporting, ramp-up, downtime, field mapping).
> 7. **Investment and financing.** Total CAPEX (R$, year), what it includes (digestion, upgrading, storage, pipeline, grid connection); the separate pipeline cost (about R$ 30 M is reported); BNDES, FINEP, REIDI or other financing and incentives; OPEX if published.
> 8. **Offtake and logistics.** Pipeline route and length, owner (Necta Gás Natural / GasBrasiliano or other), connection point and city gate; who buys the biomethane and under what kind of contract (industrial users, CNG/vehicle fuel, the mill's own trucks and machines); any compressed biomethane in cylinders or trucks (off-grid use); price formation if public.
> 9. **Power and capacity-reserve auction.** Did Cocal win a capacity-reserve contract (LRCAP 2026, about 9.2 MW, 15 years, supply from August 2028)? From which plant (Narandiba, Paraguaçu Paulista or other)? Which fuel (biogas, biomethane), and does the auction document mention stored vinasse and filter cake for year-round output?
> 10. **By-products.** Digestate: volume, nutrient content, use as fertiliser (replacing vinasse fertirrigation?). **CO₂** from upgrading: is it captured, sold or used locally or regionally (food grade, greenhouses, other)?
> 11. **Certification and carbon.** RenovaBio certification (CBIOs, carbon intensity in gCO₂e/MJ, certifier, validity); origin certificates for biomethane (GO, I-REC, SP state certificate); any other carbon credits.
> 12. **Off-season operation.** How the plant runs outside the harvest: stored filter cake, straw, manure, reduced load, shutdown months. Any reported capacity factor or load by month.
> 13. **Licences.** CETESB installation and operation licences (numbers, dates, licensed capacities, conditions); environmental impact studies if any.
> 14. **Other Cocal plants.** Briefly, for comparison: Cocal Paraguaçu Paulista (start, capacity and basis, feedstocks including poultry manure share, pipeline to Marília). Keep each value tied to the right plant.
>
> **Output format.**
> - A table with columns: `topic | value | unit | basis (biogas/CH4/biomethane; nameplate/actual; harvest/annual) | period | source title | publisher | date | URL | page/table | verbatim quote | PRIMARY/SECONDARY`.
> - A separate **conflicts** list: each conflict with both values and both sources.
> - A **not found** list with the places searched.
> - A list of primary documents that exist but could not be opened (e.g. paywalled or requiring a request), with how to obtain them.

## Triage of the first answer (2026-10-08)

- **Raw answer:** `research_notes/raw/2026-10-08_cocal_narandiba_deep_research.md`, saved unchanged. It did not have this file, so it did not reconcile the repository table line by line.
- **Data that came with it:** the ANP open-data CSVs, now in `evidence/` and registered as `anp_biometano_dados_abertos` (V for what the file says). They were read here directly; the CSV quotes in the answer match the file.
- **Everything else stays S.** The answer quotes web pages (Cocal, Copersucar, Geo, Paques, Necta, eixos, MegaWhat, ABEMA, atosoficiais). None was opened in this repo, and none is a scientific reference, so nothing goes to `references.csv`. A value moves up only after someone opens the page and records the quote.

| Topic | What the answer adds | Where it went |
|---|---|---|
| Identity | Cocal Energia S.A., CNPJ 14.788.495/0001-70 (ANP file, V). Paraguaçu: Cocal Energia PPT Participações Ltda., 44.191.268/0001-23 (V). Address Fazenda Gênesis, Estrada Municipal NRD 267 (Cocal contact page, uploaded). No coordinates. | here |
| Feedstock | Vinasse + filter cake (Cocal). Straw planned in 2021 (10 kt), not confirmed. Manure stated for Paraguaçu, not Narandiba. | docs/21 C36; `projects_capex.csv` row 3 |
| Capacity | 25,000 m³/d (Cocal), 26,000 Nm³/d (Geo), 27,112 m³/d (ANP file, V), 27,112.8 (act, relayed) | docs/21 C37 |
| ANP series | Plant series is processed biogas, not biomethane (V). "Zero" months are 1–30 m³/d, probably thousand m³/d. | docs/21 C6, Q9; docs/13 §8 |
| Digesters | 2 × 8,000 m³ vertical + 4 × 18,000 m³ horizontal (Geo, S). No HRT, OLR or reactor type. | here; candidate for `skeleton_mills.yaml` once read |
| Gas treatment | Paques THIOPAQ desulfurisation, 12,000 → < 80 ppmV H₂S, 5,200 Nm³/h biogas (S). Upgrading technology not found. | docs/21 C39 |
| CAPEX | R$ 139 M (2021) vs R$ 150 M + R$ 30 M pipeline | docs/21 C38 |
| Offtake | Necta/GasBrasiliano isolated pipeline (~65 km), industrial users in Presidente Prudente, Narandiba, Pirapozinho; first client Liane; trucks also mentioned. Paraguaçu ships CNG in cylinders by truck. | here; ADR-0017 market routes |
| LRCAP | Two UTEs of 4.6 MW, NRD and PPT; NRD in Narandiba, 5 MW installed | docs/21 Q11 |
| CO₂ | "CO2 verde" from biogas purification at Narandiba since 2021, sold to beverage industry (Cocal); 50 t/d (Geo, basis unclear) | here |
| Certification | RenovaBio certificate announced 2023, one-year validity; current status not found | here |
| Not found | Cane crushed, vinasse split, HRT/OLR, straw pre-treatment, storage losses, upgrading technology, annual biomethane output, CBIOs, CETESB licences | stays open |

**Two points for the screen (ADR-0017).**
- Off-grid is real in this region: Paraguaçu Paulista sells CNG in cylinders by truck. Paraguaçu is also in both robust lists of the no-gas run.
- Narandiba sells through a dedicated 65 km pipeline built by the distributor. A plant far from the trunk line can still reach a grid if a distributor builds a spur, so distance to the trunk line overstates the barrier.

**Next questions for a second round:** the act 422/2022 text in the DOU; the Paques and Geo pages read directly; CETESB licence numbers (the old endpoint returned 404); the ANP unit used before Aug 2025.
