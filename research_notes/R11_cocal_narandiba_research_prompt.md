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

## Second-round prompt (2026-10-08)

> Same rules as the first prompt: no invented values; for every value give URL, document title, publisher, date, page/table and a **verbatim quote**; mark PRIMARY or SECONDARY; keep biogas, CH₄ and biomethane apart, and nameplate apart from actual; list conflicts with both values; write "not found" with the places searched. **Download and attach every primary PDF or CSV you use** (file name + sha256 if you can), so it can be read here directly.
>
> 1. **ANP Autorização SPC-ANP nº 422, de 30/06/2022** (Cocal Energia S.A., CNPJ 14.788.495/0001-70, Narandiba-SP): full text from the Diário Oficial da União (in.gov.br), DOU section, edition and page; the authorised capacity with all decimals; any later act changing it. Same for Autorização ANP nº 547/2022 and for the act authorising Cocal Energia PPT Participações Ltda. (CNPJ 44.191.268/0001-23, Paraguaçu Paulista).
> 2. **ANP reporting unit.** Any ANP note, methodology page, dictionary of the biomethane open-data files ("Biometano_DadosAbertos_CSV_Capacidade.csv") or panel FAQ that defines the unit of "Volume Processado de Biogás (m³/d)", the reference conditions of the m³, and how operators report it (form, resolution, e.g. Resolução ANP nº 734/2018 or its successor). Any record of corrections or revisions of past months.
> 3. **Paques case page "Cocal Energia"** (paquesglobal.com): the full parameter box (biogas flow, H₂S in/out, units, whether the flow is design or actual).
> 4. **Geo Biogás page "Cocal Geo Biogás"** (geobiogas.tech): every number for the Narandiba and Paraguaçu units with its label (capacity basis, digester volumes, CO₂, investment, feedstock).
> 5. **Upgrading technology** at Narandiba (membranes, PSA, water scrubbing, amine) and supplier; any CO₂ recovery plant supplier.
> 6. **CETESB**: licences (LP/LI/LO) of Cocal Energia in Narandiba — numbers, dates, licensed capacity, conditions — from the CETESB licensing portal or the Diário Oficial do Estado de SP.
> 7. **Cane and residues at the Narandiba mill**: cane crushed per crop year 2019/20–2025/26 (UNICA, RenovaBio certification report of the mill, company reports, credit-rating reports, debenture/CRA prospectuses); vinasse and filter cake volumes; share of vinasse sent to the digesters.
> 8. **RenovaBio**: the biomethane certification of Cocal Energia (certifier, carbon-intensity score in gCO₂e/MJ, eligible volume, validity) from the ANP RenovaBio panel or the certifier's public report; CBIOs issued if public.
> 9. **CCEE / MME, LRCAP 2026**: the official winners list (PDF or spreadsheet) with UTE COCAL BIOMETANO NRD and PPT — power offered, fuel, start of supply, contract length; MME outorga portaria for each UTE with installed power.
> 10. **Minimum viable plant scale (Germany, Sweden)**: peer-reviewed papers or official statistics (DBFZ, Fachverband Biogas, dena biogas register, Energigas Sverige, Swedish Energy Agency) giving the size distribution of biomethane upgrading plants (Nm³/h raw gas or biomethane) and the smallest plants that operate without feed-in support; give DOI, authors, journal, year for every paper.
>
> Output: one table per question (columns: value | unit | basis | period | source title | publisher | date | URL | page/table | verbatim quote | PRIMARY/SECONDARY), a conflicts list, a not-found list, and the list of attached files.

## Second-round prompt, self-contained version (2026-10-08)

Supersedes the short second-round prompt above. It carries its own rules and context, so it can be pasted into a tool that has never seen this project.

```text
ROLE AND PURPOSE
You are a research assistant collecting evidence for a peer-reviewed techno-economic and
spatial study of biomethane production in São Paulo State (SP), Brazil (CP2B / NIPE-UNICAMP).
The study uses the Cocal biomethane plant at the Narandiba sugarcane mill (Narandiba, SP) as its
reference plant and calibrates a plant model against ANP monthly data. Every number you return
may end up in a scientific paper, so traceability matters more than coverage. A short answer
with verifiable sources is better than a long answer with guesses.

RULES (breaking any of them makes the answer unusable)
1. Never invent or estimate a number, date, name, URL, DOI or document number. If you cannot
   find something, write "not found" and list the places you searched (sites, portals, queries).
2. For every value give: value; unit; basis (see rule 4); period; source title; publisher or
   author; publication date; full URL; page, table, section or paragraph; and a VERBATIM QUOTE
   in the original language (Portuguese, English, German or Swedish as published).
3. Mark each value PRIMARY (the regulator, the operator, the supplier or the official
   statistics body speaking about its own act, plant or data, read in the original document)
   or SECONDARY (press, association, blog, aggregator or a site reproducing someone else's
   document). A search-engine snippet or AI summary is never a source: open the document.
4. Keep these apart and state which one each source means:
   - biogas (raw, about 50-60 % CH4) vs CH4 vs biomethane (upgraded to the ANP specification);
   - nameplate / authorised / design capacity vs actual production or throughput;
   - per day during the harvest vs annual average vs per year;
   - m³ vs Nm³; give the reference temperature and pressure when stated.
5. When two sources disagree, report BOTH values with both sources. Do not average, round or
   choose. Put each disagreement in the conflicts list.
6. Date every statement. Keep plans and announcements apart from operation.
7. DOWNLOAD AND ATTACH every primary document you use (PDF, CSV, XLSX, saved HTML), with file
   name and, if you can compute it, its SHA-256. If a document cannot be downloaded (paywall,
   HTTP 403, login), say so and give the exact URL and how it can be obtained.
8. For scientific papers give DOI, all authors (or first author + "et al." if more than six),
   title, journal, year, volume, pages. Check the DOI resolves to that title.
9. Do not use or return personal data of private individuals (names of employees, CPFs,
   personal phone numbers or e-mails). Company names, CNPJs and official acts are fine.

WHAT IS ALREADY KNOWN (to be confirmed or contradicted, not repeated without a source)
- Operator: COCAL ENERGIA S.A., CNPJ 14.788.495/0001-70, Narandiba-SP. Second plant: COCAL
  ENERGIA PPT PARTICIPAÇÕES LTDA, CNPJ 44.191.268/0001-23, Paraguaçu Paulista-SP (from the ANP
  open-data file, read directly).
- ANP open data ("Biometano_DadosAbertos_CSV_Capacidade.csv", ZIP members dated 2026-09-17),
  Narandiba: authorised biomethane capacity 27,112.00 m³/d; biogas processing capacity
  51,600 m³/d; column "Volume Processado de Biogás (m³/d)" = 0-30 every month from Jul 2022 to
  Jul 2025 (for example 2 in Aug 2022, 14-30 from Sep 2023), then 23,913 in Aug 2025 and
  11,596 in Aug 2026. Hypothesis under test: the early months were reported in THOUSAND m³/d.
  Similar small values appear for Biometano Santa Cruz (Américo Brasiliense) and Biometano
  Verde Paulínia in 2025-2026.
- Capacity statements that disagree: Cocal "até 25 mil m³/dia"; Geo "26 thousand Nm³/day
  BIOMETHANE"; ANP act 422/2022 relayed by atosoficiais.com.br as 27,112.8 m³/d (not read).
- Start dates that disagree: Copersucar (Jul 2021) "começou a operar, em junho", biomethane
  expected Aug 2021; Cocal "entrou em atividade no final de 2021"; Geo "Opened in 2022";
  ANP authorisation 422 dated 30/06/2022; ANP authorisation 547/2022 dated 11/08/2022 (relayed).
- Feedstock: Cocal names vinasse and filter cake; Copersucar (2021) lists 1.5 million m³
  vinasse, 135 thousand t filter cake and 10 thousand t straw as planned feed; manure and
  effluent from Granja Shida are stated for the Paraguaçu plant, not Narandiba.
- CAPEX: Copersucar (2021) R$ 139 million; Cocal later R$ 150 million (Cocal) + R$ 30 million
  (GasBrasiliano/Necta pipeline, about 65 km).
- Technology (relayed, not read): Geo, 2 x 8,000 m³ vertical + 4 x 18,000 m³ horizontal
  digesters; Paques THIOPAQ desulfurisation, H2S 12,000 ppmV in, < 80 ppmV out, biogas flow
  5,200 Nm³/h (= 124,800 Nm³/d, which is far above ANP's 51,600 m³/d biogas capacity).
  Upgrading technology unknown. CO2: Cocal sells "CO2 verde" from Narandiba since 2021;
  Geo states 50 t/day biogenic CO2.
- LRCAP 2026 (relayed): two plants of 4.6 MW each, UTE COCAL BIOMETANO NRD and UTE COCAL
  BIOMETANO PPT; NRD in Narandiba with 5 MW installed. The CCEE result PDF returned HTTP 403.
- Mandate (relayed, not read): Lei 14.993/2024 sets a biomethane participation target for
  natural gas producers and importers, "base 1 % (2026), up to 10 %"; CNPE Resolução 4/2026 set
  0.5 % for 2026 (about 181.7 million m³ for 2026/27); the 2027 target is due by 1 Nov 2026.
  The project lead understands that the target grows gradually to a 10 % maximum in 2035.

QUESTIONS (answer each separately; questions 1, 2, 7 and 11 have priority)

1. ANP authorisations. Full text of Autorização SPC-ANP nº 422, de 30/06/2022 (Cocal Energia
   S.A.) from the Diário Oficial da União (in.gov.br): DOU section, edition, page, and the
   authorised capacity with all its decimals and its unit. Do the same for Autorização ANP
   nº 547/2022, for any later act that changes the Narandiba authorisation, and for the act(s)
   authorising Cocal Energia PPT Participações Ltda. in Paraguaçu Paulista.

2. ANP reporting unit and definitions. Find any ANP document that defines the fields of the
   biomethane open data: a data dictionary or metadata file for "Biometano_DadosAbertos_CSV_
   Capacidade.csv" and "Biometano_DadosAbertos_CSV_Producao.csv", the methodology or FAQ of the
   "Painel Dinâmico de Produtores de Biometano", or the reporting rules for producers (the
   regulation that requires the monthly report, the form or system used, e.g. under Resolução
   ANP nº 734/2018 or its replacement, Resolução ANP nº 987/2025). Report: the unit of "Volume
   Processado de Biogás (m³/d)"; whether it is a monthly average per day; the reference
   temperature and pressure of the m³; whether operators ever reported in thousand m³/d; any
   correction or revision of past months; the unit and basis of "Produção (m³)" in the state
   file. If nothing is published, give the ANP channel (e-mail, Fala.BR / e-SIC) through which
   the question can be asked.

3. Paques case page "Cocal Energia" (paquesglobal.com): the complete parameter box, with each
   label and unit as printed, and whether the biogas flow is a design value or measured; the
   date of the page or project.

4. Geo Biogás page "Cocal Geo Biogás" (geobiogas.tech), and any Geo presentation or paper on
   the Narandiba and Paraguaçu units: every number with its label (capacity and its basis,
   digester number and volumes, reactor type, retention time, organic loading rate, operating
   temperature, feedstock and its storage, straw pre-treatment, CO2, investment, start date).

5. Upgrading and CO2 recovery at Narandiba: technology (membranes, PSA, water scrubbing, amine,
   cryogenic) and supplier; methane slip if published; supplier and capacity of the CO2
   recovery plant; who buys the CO2.

6. CETESB licences of Cocal Energia in Narandiba: type (LP, LI, LO), number, date, validity,
   licensed capacity and main conditions, from the CETESB licensing portal
   (licenciamento.cetesb.sp.gov.br) or the Diário Oficial do Estado de São Paulo. The old
   query URL returned "404 - File or directory not found"; try the current portal search by
   CNPJ 14.788.495/0001-70 and by municipality.

7. Cane and residues at the Narandiba mill: cane crushed (t) per crop year 2019/20 to 2025/26;
   ethanol produced (m³, anhydrous and hydrated); vinasse generated (m³) and how much goes to
   fertirrigation vs to the digesters; filter cake (t); straw recovered from the field (t) and
   how. Good places: the mill's RenovaBio certification report (public consultation documents
   of the certifier, ANP RenovaBio panel), Cocal annual or sustainability reports, credit
   rating reports (Fitch, S&P, Moody's, Austin), debenture or CRA prospectuses, UNICA, MAPA
   SAPCANA. Keep mill data (Narandiba unit) apart from group totals.

8. RenovaBio certification of the biomethane: certifier, certificate number and dates, route,
   carbon-intensity score (gCO2e/MJ), eligible volume fraction, validity, renewals, and CBIOs
   issued if public; the public consultation report if it exists (attach it).

9. CCEE / MME, LRCAP 2026: the official result (CCEE PDF or spreadsheet) listing UTE COCAL
   BIOMETANO NRD and UTE COCAL BIOMETANO PPT with power offered (MW), fuel, start of supply,
   contract length and price if public; the MME portaria granting each plant its outorga, with
   installed power and location.

10. Minimum viable plant scale in Germany and Sweden. Peer-reviewed papers or official
    statistics that give (a) the size distribution of biogas upgrading / biomethane plants
    (raw biogas Nm³/h or biomethane Nm³/h) and its change over time; (b) the smallest plants
    that operate commercially, and whether they rely on feed-in tariffs or other support;
    (c) cost against scale curves for upgrading and grid injection. Sources to check: DBFZ
    (Deutsches Biomasseforschungszentrum) reports and the "Biogas-Messprogramm", dena
    Biogaspartner / biogas register, Fachverband Biogas statistics, Bundesnetzagentur
    (biomethane injection), Energigas Sverige, Energimyndigheten (Swedish Energy Agency,
    "Produktion och användning av biogas och rötrester"), IEA Bioenergy Task 37 country reports,
    and peer-reviewed literature. Give full bibliographic data and DOI for every paper (rule 8).

11. Biomethane mandate path. From the primary texts (Planalto / DOU): Lei nº 14.993/2024
    ("Combustível do Futuro") — the article(s) on the biomethane participation target for
    natural gas producers and importers: starting percentage and year, maximum percentage, the
    year or rule for reaching it, who sets each year's target and how. Decreto nº 12.614/2025 —
    target setting, allocation and compliance. CNPE Resolução nº 4/2026 — the 2026 target and
    the volume it implies. Any CNPE resolution or MME consultation setting the 2027 or later
    targets (published on or after 2026-10-01). Quote the article numbers verbatim.

OUTPUT FORMAT
- One table per question with columns:
  value | unit | basis | period | source title | publisher/author | date | URL |
  page/table/section | verbatim quote | PRIMARY/SECONDARY
- A conflicts list: each conflict with both values and both sources.
- A not-found list: what was not found and where you searched.
- A list of attached files: file name, what it is, URL it came from, SHA-256 if available.
- Do not write a narrative summary that adds values not in the tables.
```

## Triage of the second-round answers (2026-10-08)

**What came in.** A shortened round: Q2–Q5 answered, Q1 and Q6–Q11 returned "not found" (the run stopped before extraction, so "not found" says nothing about the portals). Raw answers, the short report (`00-short-report.md`) and the researcher's `SHA256SUMS.txt` are in `research_notes/raw/2026-10-08_round2/`. The user also uploaded `pdftotext -layout` extractions of the primary PDFs. Pages below are form-feed pages of those texts; they match the printed page numbers. The texts are not committed (whole corporate reports; the IFAMR text carries a download stamp with an IP address). Their SHA-256 are in `research_notes/raw/2026-10-08_round2/SOURCE_TEXTS.sha256`.

**Checks on the package.**
- The two ANP CSVs in the package have the same SHA-256 as `evidence/` (6cd432e1…852bf75, 1f40f437…3e04a4), and the quoted rows (Narandiba 08/2026 "11596,000"; SP 08/2026 BIOMETANO 5505729.718) are in our files.
- `cocal_sustainability_2023_2024.pdf` and `cocal_ras_2023-24.pdf` are one file (same SHA-256; the texts are identical). The three Paques PDFs are one file. `geo_sustainability_2022_2023.pdf` = `GEO_RS2022-23_EN_VFinal_11jun24_web.pdf`.
- The Greenlane PDF hash differs between `SHA256SUMS.txt` (0f8ce451…cbe53426a50a3c…) and the short report's table (0f8ce451…e54c26a50a3c…). One is a transcription error; `SHA256SUMS.txt` is machine output, so it is the one to trust.

**Values read here in the primary text (page + quote recorded).** The reference rows are in `registry/references.csv` but none is double-checked yet (`one_source` or `pending`), so these values carry a caveat in any paper until a second identity source is recorded.

| Value | Basis, period | Source, page | Quote |
|---|---|---|---|
| 23.4 M Nm³ biogas, 4.3 M Nm³ biomethane | Narandiba, first year of operation, safra 2022/23 | Cocal RAS 2022/23, p. 52 (also p. 10) | "Em seu primeiro ano de operação, nossa planta gerou 23,4 milhões de normal-metros cúbicos de biogás e 4,3 milhões de normal-metros cúbicos de biometano" |
| 30.5 M Nm³ biogas, 7.9 M Nm³ biomethane | Cocal, safra 2023/24 (Narandiba is the only biogas plant then) | Cocal RAS 2023/24, p. 15 and p. 26 | "BIOGÁS 30,5 milhões de Nm³" / "BIOMETANO 7,9 milhões de Nm³" |
| Inputs 130 kt filter cake, 1.2 M m³ vinasse, 1.9 kt chicken manure, 5.1 kt cattle manure, 4.1 kt other waste; outputs 565 k Nm³ pipeline, 4.1 M Nm³ road, 2.4 M Nm³ industrial use, 29.3 k MWh DG, 667 k Nm³ fleet, 40 kt biofertiliser | Narandiba, safra 2023/24 | Cocal RAS 2023/24, p. 24 | "Torta de filtro 130 mil t" … "Vinhaça 1,2 milhão m3" … "Esterco bovino 5,1 mil t" … "PRODUÇÃO DE BIOMETANO 7,9 milhões/Nm3" |
| 27.66 M Nm³ biogas, 8.1 M Nm³ biomethane ("recorde histórico") | Cocal, safra 2024/25 | Cocal RAS 2024/25, p. 22; p. 32 names Narandiba ("8,10 milhões de Nm3") | "Biogás: 27,66 milhões de Nm³ produzidos" / "Biometano: 8,1 milhões de Nm³ purificados" |
| Inputs 118 kt filter cake, 1.1 M m³ vinasse, 5.1 kt cattle manure, 1.88 kt chicken manure, 23.7 kt other waste | Narandiba, safra 2024/25 | Cocal RAS 2024/25, p. 29 | "118 mil t Torta de filtro" / "1,1 milhão m³ Vinhaça" |
| Biogas 27.7 / 32.7 M Nm³; biomethane 8.1 / 10.6 M Nm³; filter cake 118.0 / 155.2 kt; vinasse 1.1 / 1.3 M m³; other waste 23.7 / 41.7 kt; chicken manure 1.9 / 4.0 kt; cattle manure 5.1 kt / 0 t; biogas flared 2.2 / 5.9 M Nm³ | safra 2024/25 / 2025/26; the page does not name the plant | Cocal RAS 2025/26, p. 19 ("Fluxo produtivo do biometano") | "25/26: 10,6 milhões" / "25/26: 32,7 milhões de Nm3" / "25/26: 155,2 mil t" |
| Paraguaçu Paulista: 127,200 Nm³/d biogas potential, 60,000 Nm³/d biomethane, R$ 216 M (BNDES) | new plant, inaugurated 2025 | Cocal RAS 2025/26, p. 20 | "potencial para gerar 127.200 Nm³/dia de biogás, resultando em uma produção de 60.000 Nm³/dia de biometano" |
| Cane milled 8,868,098.20 t (2023), 7,689,738.28 t (2024), 8,692,843.82 t (2025) | Cocal group, both mills, calendar years | Cocal RAS 2025/26, p. 79 | "8.868.098,20 t de cana moída; em 2024: … 7.689.738,28 t de cana moída; e, em 2025: … 8.692.843,82 t de cana moída" |
| 120 k Nm³/d biogas capacity, 26 k Nm³/d biomethane, 5 MW; feed "cake filter and vinasse" | Narandiba, 2022/23 report | Geo RS 2022/23, p. 29 | "Processes waste as cake filter and vinasse in its two vertical and four horizontal biodigestors. The installed capacity is 5 MW of electricity and 26 thousand Nm3/day of biomethane. It has the capacity to generate 120 thousand Nm³/day of biogas." |
| 3,276 CBIOs in 2023; certification Aug 2023 | Narandiba | Geo RS 2022/23, p. 29 | "In August 2023, after RenovaBio program certification, the plant started issuing CBIOS … In 2023, 3,276 CBIOS were generated." |
| Biogas 22 / 29 M Nm³; biomethane 3.7 / 7.5 M Nm³; electricity 21 / 27 k MWh; filter cake 91 / 124 kt; vinasse 889 / 1,294 k m³; other waste 2 / 9 kt | Narandiba, calendar 2022 / 2023 | Geo RS 2022/23, p. 30 | "Cocal Performance – Narandiba Unit (SP) in 2022 and 2023" (infographic) |
| 25,000 m³/day biomethane, 5 MW; feed "vinasse, filter cake and straw"; "5 million tons of cane milled annually" | Narandiba, case study | Franco Martinez et al. 2023, IFAMR 26(2), p. 346 | "installed capacity for 5 MW of electricity and 25,000 m3/day of biomethane. They are used as raw materials: vinasse, filter cake and straw" |
| PSA upgrading, US$ 1.8 M contract | Grupo Cocal, 7 Jul 2020; Narandiba not named as the site | Greenlane news release, p. 1 | "Greenlane will supply its Pressure Swing Adsorption (“PSA”) biogas upgrading system" |
| Biogas factory start "início de 2022" | Narandiba | Cocal results 2021/22, p. 3 | "ressaltamos o início de operação da fábrica de Biogás no início de 2022 na unidade de Narandiba" |

**Values relayed but not read here (stay S):** Paques case page (5,200 Nm³/h biogas, 12,000 → < 80 ppmV H₂S, 25,000 Nm³/day biomethane; the Paques PDF text was not uploaded); Geo plant page (26 k Nm³/d, 2 × 8,000 m³ vertical + 4 × 18,000 m³ horizontal digesters, 50 t/d biogenic CO₂); Cocal CO₂ page (16 kt "CO2 verde", no scope or period); ANP SIMP manual (monthly declaration by the 15th; kg at 20 °C and 1 atm, field 9).

**What it changes.**
1. **The plant produced from 2022.** Company reports give 4.3 M Nm³ biomethane in safra 2022/23 and 7.9 M in 2023/24. ANP's Narandiba series, even ×1000, sums to 0.39 M m³ and 4.2 M m³ of "processed biogas" over the same safras. The thousand-unit hypothesis cannot explain Aug 2022–Aug 2023 (1–3 m³/d) and explains only about half of 2023/24. See docs/21 C40.
2. **The ANP "processed biogas" field behaves like biomethane at Narandiba.** Safra 2024/25: ANP ×1000 sums to 8.39 M m³ against 8.1 M Nm³ biomethane and 27.7 M Nm³ biogas reported by Cocal. From Aug 2025 (no rescaling needed) the field runs at 11.6–25.4 k m³/d, below the 27,112 m³/d biomethane authorisation and far below the 90 k Nm³/d that 32.7 M Nm³/yr of biogas implies. The yield proxy of docs/13 §8 (×0.525) would then undercount Narandiba. Logged as C40; the ANP unit question (Q9) now has two parts.
3. **Feed.** Narandiba takes small amounts of manure (cattle 5.1 kt, chicken 1.9 kt in 2023/24) and growing "other waste" (4.1 → 23.7 → 41.7 kt). Vinasse and filter cake dominate. No company report lists straw; the IFAMR case study does. C36 updated.
4. **Capacity.** ANP's Paraguaçu row (60,000 / 127,200) equals Cocal's Nm³/d figures, which suggests the ANP capacity m³ are on the company's Nm³ basis, at least for authorised capacity. For Narandiba the Geo biogas capacity (120 k Nm³/d) is 2.3× the ANP biogas processing capacity (51,600 m³/d). C37/C39 updated.
5. **Calibration targets for Narandiba exist now:** annual biogas, biomethane, flare and feed tonnages per safra 2022/23–2025/26. They are better targets than the ANP months before Aug 2025.

**Still open:** Q1 (ANP acts), Q6 (CETESB), Q8 detail (certificate, CI, eligible fraction), Q9 (LRCAP result), Q10 (minimum scale), Q11 (mandate path), and whether the RAS 2025/26 flow chart (p. 19) is Narandiba only (Paraguaçu reports zero to ANP until Apr 2026, so probably yes).

**Correction, later on 2026-10-08: the 2025/26 figures cover two plants.** Cocal RAS 2025/26 p. 23: "A entrada em operação da planta de Paraguaçu Paulista impulsionou a entrega desse combustível renovável. Juntas, as duas unidades da Cocal atingiram o volume recorde de produção de 10,6 milhões de Nm3 de biometano. A produção de biogás alcançou 32,7 milhões de Nm³". The p. 19 flow chart carries the same 10.6 and 32.7, so its 2025/26 column is Narandiba + Paraguaçu Paulista. Its 2024/25 column is Narandiba alone: RAS 2024/25 p. 32 says Paraguaçu "deve iniciar suas operações na safra 2025/2026". This answers the open question above with "no" and changes three points of "What it changes":
- item 2: the 90 k Nm³/d implied by 32.7 M Nm³/yr is a two-plant figure; the 2023/24 figure (30.5 M Nm³, Narandiba alone, 83.6 k Nm³/d) carries the argument;
- item 3: the 41.7 kt of "other waste" and 4.0 kt of chicken manure in 2025/26 include Paraguaçu, which takes manure and effluent from Granja Shida (p. 20);
- item 5: Narandiba targets are safras 2022/23–2024/25 and Geo's calendar 2022–2023.

ANP lists Paraguaçu from Jan 2026 with zero processed biogas until Apr 2026, although the company counts the plant in 2025/26 (docs/21 C41). In `registry/plant_reported_annual.csv` the 2025/26 rows are keyed to `sp_cocal_narandiba_paraguacu`. New questions for Cocal: Narandiba's own 2025/26 biogas and biomethane, and Paraguaçu's first month of biomethane output.

**Second read and feed check, later on 2026-10-08.** A second, independent LLM reader re-read all 67 values of `registry/plant_reported_annual.csv` from the uploaded texts. It confirmed every value, the p. 10 capacity layout of RAS 2022/23 (capacity above realised), the flare boxes and biogas splits on RAS 2025/26 p. 19, and the year order on Geo p. 30. Independently of the first reader, it also found the two-plant scope of the 2025/26 column on p. 23 (rows now `llm_corrected`). Human audit against the PDFs is still owed (docs/08 §6). Two new findings:
- RAS 2022/23 p. 10 gives annual capacities of 33 M Nm³ of biogas and 9 M Nm³ of biomethane. The biogas figure conflicts with Geo's 120 k Nm³/d (docs/21 C39).
- Run through the registry central yields, Narandiba's reported vinasse and filter cake explain only 64–78 % of its reported biogas, in every year with feed data (docs/13 §9).

Questions added for Cocal (docs/21 Q22): vinasse COD and the basis of the reported volume; filter cake TS, VS/TS and BMP; what the "outros resíduos industriais e urbanos" are; the reference conditions of the reported Nm³; and what each biogas capacity measures.
