# SP Biomethane Engine: 18-week execution plan, deliverables first

**Window:** Mon 2026-10-05 → Fri 2027-02-05 (18 weeks; W1 = week of Oct 5)
**Angle:** work backwards from what must exist on Fri 5 Feb 2027 and cut scope where needed. The dates stay fixed; the content of each release can shrink.
**Owner:** Lucas (one researcher, ~30–35 h/week on this) + Claude Code. Lab and company partners are external dependencies, not resources.
**Supersedes for this window:** `docs/19_ROADMAP_STEP_BY_STEP.md` (the ~30-week roadmap). Its gates are kept and compressed into monthly gates (§6). Proposed home in the repo: `docs/plan/PLAN_4M_2026-10_2027-02.md`, with `docs/19` pointing to it.

> Flags follow `docs/08`: **(verify)** = not confirmed from a primary source. Thresholds marked **(proposed)** are project choices, not facts. I quote no number that is not already in the repo docs or the computed calendar.

---

## 0. What must exist on Fri 5 Feb 2027 (the backward anchor)

| # | Deliverable | "Done" means (verifiable) | Ship date | Feeds |
|---|---|---|---|---|
| R1 | **PILAR-2b release v0.1.0: supply** | `exports/v0.1.0/` (facilities, mill_year, mill_month, hex_supply + `manifest.json`) passes `engine.export.bundle` gates. Git tag + GitHub Release. PR opened on `aikiesan/Pilar-2b` with CI green | **Fri 13 Nov (W6)** | P1 |
| R2 | **v0.2.0: process + simple LCOB** | Process results per mill × strategy (S0/S1/S2/S4) with constraint flags, ANP calibration report for the 4 plants, simple LCOB (annuity, EPE anchors) | **Fri 4 Dec (W9)** | P2 |
| R3 | **v0.3.0: economics** | `lcob_results` with p05/p50/p95, NPV, IRR, P(NPV>0) and break-even CGOB for every candidate mill site; Sobol ranking report | **Fri 18 Dec (W11)** | P2, P3 |
| R4 | **v1.0.0: siting + supply curve** | `sites`, `supply_curve` (MC bands, mandate overlays) and a robustness report (allocation rule, CGOB, ICMS scenario) | **Tue 26 Jan (W17)** | P4, demo |
| D1 | **Partner demo** | 60–90 min session, held Wed 27 or Thu 28 Jan (verify partners' calendars), using public data only. Streamlit app reads release bundles only. Feedback logged in `docs/plan/demo_feedback_2027-01.md` | **W17** | partners, PILAR-2b UI spec |
| M1 | **P1: data descriptor** (mill-level residue panel 2008–2025) | Complete draft to co-authors **Fri 18 Dec**. Submission-ready package **Fri 29 Jan**. Submitted by Fri 5 Feb if all co-authors sign off, otherwise the first week after Carnival | W11 / W17 / W18 | Zenodo DOI, repo public |
| M2 | **P2: capacity factor** | Complete draft including the **pre-registered prospective test** (protocol plus months scored so far). The final scoring section is completed when the off-season months are published (after the window) | **Fri 29 Jan (W17)** | — |
| M3 | **P3 (CAPEX) and P4 (siting): started** | Each has `outline.md` + figure list + methods section draft. P3 also has a normalized Brazilian CAPEX table + an exploratory `brms` fit | **Fri 5 Feb (W18)** | — |
| X1 | **Pre-registration of ANP plant output** (Costa Pinto, Narandiba, Santa Cruz, Paraguaçu) | Three timestamped filings: R-A0 (baselines, Fri 9 Oct), R-A (engine v0, Fri 16 Oct), R-B (calibrated v0.2, Fri 4 Dec). `reports/scoreboard.md` updated whenever ANP publishes | W1, W2, W9 + every ANP update | P2, demo |

**Release train rule:** the ship dates above are fixed. If a release is > 3 working days late, apply its **cut ladder** (§4.2) and ship anyway. Each release maps to a paper section, so shipping the release also produces the paper's evidence.

---

## 1. Capacity budget (realistic for one person)

| Week | Dates | Working days | Planned h | Notes |
|---|---|---|---|---|
| W1 | Oct 5–9 | 5 | 32 | external clocks start (LAI, lab, partners) |
| W2 | Oct 12–16 | 4 | 26 | Mon 12 Oct national holiday |
| W3 | Oct 19–23 | 5 | 32 | |
| W4 | Oct 26–30 | 5 | 32 | **Gate A** |
| W5 | Nov 2–6 | 4 | 26 | Mon 2 Nov holiday (Finados) |
| W6 | Nov 9–13 | 5 | 32 | **v0.1.0** |
| W7 | Nov 16–20 | 4 | 26 | Fri 20 Nov holiday (Consciência Negra) |
| W8 | Nov 23–27 | 5 | 32 | **Gate B**, harvest (safra) ending |
| W9 | Nov 30–Dec 4 | 5 | 32 | **v0.2.0**, pre-reg R-B |
| W10 | Dec 7–11 | 5 (4?) | 30 | Tue 8 Dec may be a Campinas municipal holiday (verify) |
| W11 | Dec 14–18 | 5 | 32 | **v0.3.0**, **Gate C**, P1 draft out |
| W12 | Dec 21–25 | ~2.5 | 16 | Thu 24 Dec suspended day (expediente suspenso, S, verify), Fri 25 Dec holiday |
| W13 | Dec 28–Jan 1 | ~1.5 | 10 (or 0) | Thu 31 Dec suspended day (S, verify), Fri 1 Jan holiday; treat as recess |
| W14 | Jan 4–8 | 5 | 32 | |
| W15 | Jan 11–15 | 5 | 32 | P1 co-author comments due |
| W16 | Jan 18–22 | 5 | 32 | v1.0.0-rc1, demo dry run |
| W17 | Jan 25–29 | 5 | 32 | **v1.0.0**, **demo**, **Gate D**. Mon 25 Jan is the São Paulo city anniversary holiday (affects SP-city partners, verify) |
| W18 | Feb 1–5 | 5 | 32 | P3/P4 started, wrap-up. Carnival Feb 8–9 falls just after the window |
| | | | **~520 h** | |

**Allocation of ~520 h:** supply / v0.1 ≈ 120 · process / v0.2 ≈ 70 · economics / v0.3 ≈ 70 · siting / v1.0 ≈ 80 · demo ≈ 25 · writing ≈ 100 (P1 60, P2 30, P3+P4 10) · LAI/partners/lab coordination + verification reading ≈ 35 · buffer ≈ 20.
**Division of labour:** Claude Code writes and tests code, drafts text from docs and results, and runs batches. Lucas's hours go to what only he can do: decisions, the 10 % extraction audits, reading primary documents for verification, partner and lab contact, and final writing.

**UNICAMP calendar (S, from DAC 2026 calendar search; verify on the official page):** classes end 5 Dec 2026; activities suspended 24 Dec and 31 Dec; the summer period starts 6 Jan 2027; classes resume 22 Jan 2027. Assume lab staff availability is reduced from ~21 Dec to ~8 Jan. Sources: https://www.dac.unicamp.br/portal/calendario/2026/graduacao/aluno · https://www.dgrh.unicamp.br/documentos/calendario-administrativo/

---

## 2. Time-locked constraints (these clocks do not wait)

| Clock | Date(s) | Consequence for the plan |
|---|---|---|
| LAI legal deadline: 20 days + 10 extension | Filed W1 (Oct 5–6) → responses due ~Oct 26, ~Nov 4 with extension. Counting rule: calendar vs business days (verify) | File **all** of R1–R6 and R8 on Mon/Tue W1. Appeals (recurso) within 10 days of each response → W5–W7. LAI data are **never on the critical path**: if they arrive, they go into P1 revision and v1.0 |
| Harvest season (safra) ends ≈ end of Nov (project convention Apr–Nov; the partner mill's actual crush end needs to be verified) | Fresh filter cake (torta de filtro) and vinasse (vinhaça) are available only until ~W8 | E2 vinasse sampling must run W3–W8. E1 filter-cake storage t0 must be collected by W4–W6 (late Oct / early Nov). A bulk filter-cake stock should be secured by W8 for E1 and the PPBIOEN E3 run |
| Off-season (entressafra), Dec 2026–Mar 2027, falls **inside** the window | Natural experiment for Costa Pinto vs Narandiba vs Santa Cruz vs Paraguaçu | Pre-register predictions **before** ANP publishes those months |
| ANP biomethane monthly publication lag: **unknown** | Our PILAR-2b extract ends at **2026-04** (`evidence/anp_monthly_sp_plants_from_pilar2b.csv`). A search snippet says the ANP panel tables were updated 17/9/2026 (S, verify). The I-SIMP manual for biomethane producers may state the reporting deadline (verify): https://csa.anp.gov.br/downloads/manuais-isimp/MANUAL-DO-I-SIMP-PRODUTORES-DE-BIOMETANO.pdf | W1: snapshot the ANP tables, record the latest published month and **measure the lag**. Re-check every Monday. If the lag is long, the off-season months will be scored after the window (P2 final) |
| CNPE 2027 biomethane target | Due ~1 Nov 2026 (S, verify) | W5: update the mandate overlays (registry param + `docs/16`) |
| SP ICMS 12 % on biomethane | Valid to 31 Dec 2026 (S, verify decree number) | v0.3 carries two scenarios: "12 % renewed" and "reduction lapses, full internal rate (verify rate)". W13/W14: record the outcome |
| CGOB 2026 compliance year-end | 31 Dec 2026 (S); the first certifications were starting in Sep 2026 (S) | Watch the digests for the first CGOB trade prices. Until a V price exists, keep the CGOB 0/0.5/1.0/1.5 scenarios |
| ANP Res. 1.006/2026 transition (off-spec industrial-only sellers) | until 9 Feb 2027 (S) | Just after the window. Note it in P4 / the demo only |
| Carnival | Feb 8–9, 2027 | P1 submission slips to after Carnival if sign-off is not in by Fri 5 Feb |

---

## 3. Starting state and how this plan treats it

- **Code (v0, 2026-10-04).** Per the brief, these exist with unit tests: registry loader/validator; RenovaBio rule-based extractor + verbatim-quote verifier; inventory (hash & register); raster→H3; Huff + frequentist calibration; residues (MC); seasonality; grid rescale; Level-1 CSTR + constraints + strategies S0–S5; finance/CAPEX/revenue/LCOB/LHS MC/Sobol; MILP facility location + merit-order supply curve; ANP utilization analysis + MAPE/CRPS/coverage; export bundle; Docker/pre-commit/CI.
- **Working tree check (2026-10-04).** It also shows `calibrate/bayes_huff.py`, `calibrate/lab.py`, `supply/harvest_detect.py`, `siting/routing.py` (OSRM table + fallback), `ingest/pdftext.py` (untracked), and several brief-listed files still landing. **Mon W1, first hour:** reconcile the inventory (`git ls-files src/engine`, `uv run pytest -q`) and write `docs/plan/STATUS.md` §Code.
- **Prototype modules are parked, not deleted.** Bayesian Huff and harvest detection are prototypes. They are **off the critical path** (see §8).
- **Not done:** real data ingestion, H3 cane panel, Bayesian calibration, hierarchical CAPEX, road OD matrices, Sentinel-2 harvest detection, ADM1, PILAR-2b ingest side. The plan builds only the first five, in reduced form, plus a **minimal** PILAR-2b ingest side.

---

## 4. Scope decisions (to be recorded as ADRs in W1)

### 4.1 New ADRs

| ADR | Decision | Why (deliverables-first) |
|---|---|---|
| **ADR-0006** Frequentist Huff for v0.x | Fit α, β on log RenovaBio cane by (penalized) least squares; intervals by parametric/cluster bootstrap; leave-region-out CV. `calibrate/bayes_huff.py` runs as a **shadow** fit in background compute (W5–W10) and is promoted for P1 only if it converges by Gate C (R-hat ≤ 1.01, bulk ESS ≥ 400; these thresholds are **proposed**) | Debugging a sampler is not allowed to block v0.1. Lucas's R/brms skill makes the Bayesian upgrade a fast follow |
| **ADR-0007** OD matrices via OSRM car profile at H3 res 7 parents | Origins = res-7 centroids with cane in any year (res-8 children inherit the parent's distance); destinations = mills within a truncation radius. Truck costing (Valhalla) is deferred. Fallback: `routing.fallback_road_km` with a **cited** detour factor, but only if OSRM is not running by Wed W4 | CLAUDE.md requires road distances; res 7 keeps the matrix small enough for a home machine |
| **ADR-0008** Pre-registration protocol for ANP plant output | Plants: Costa Pinto, Narandiba, Santa Cruz, Paraguaçu. Target: monthly `vol_biogas_m3d` (and `util_pct`) for every month after the last published month up to **Mar 2027**. Models: M0 seasonal naive, M1 phase climatology (harvest vs off-season), M2 engine structural model. Output: quantiles p05/p25/p50/p75/p95. Scoring: CRPS, 90 % interval coverage, median absolute error, skill vs M0. Zero months: scored as reported, with a sensitivity variant that treats them as missing (C6/Q9). Months already elapsed but unpublished at filing are scored as **nowcasts**, separately from true forecasts. Public data only: partner (São Martinho) data for Santa Cruz is **not** used before scoring | Turns the off-season inside the window into the core evidence for P2 |
| **ADR-0009** Feb-2027 release scope | File-based pipeline (GeoParquet/Parquet; PostGIS only for reading the PILAR-2b dump). Candidate sites = **active mills only**. Strategies S0/S1/S2/S4 (S3 and the S5 optimizer deferred). Delivery modes = distribution-grid injection vs CNG (LNG and transmission injection deferred). hex_supply exported at **res 7** to PILAR-2b (res 8 internal) | Keeps each release shippable in 2–3 weeks |
| **ADR-0010** Demo + manuscripts tooling | Demo = Streamlit app in `app/demo/` that reads `exports/<version>/` only (the contract test is also the demo test). Manuscripts = Quarto (`papers/P*/paper.qmd` → docx for co-authors) | One person, Python/R stack, and the demo doubles as the spec for future PILAR-2b pages |

### 4.2 Cut ladders: what to drop, in order, if a release runs > 3 working days late

| Release | Cut 1 | Cut 2 | Cut 3 | Floor (always ships) |
|---|---|---|---|---|
| v0.1 | drop `mill_month` from the bundle (keep it internal) | hex_supply annual only | years 2015–2025 only | facilities + mill_year with intervals |
| v0.2 | drop S4 (shutdown/restart) | calibrate only Costa Pinto + Narandiba | LCOB with EPE anchor only | process runs S0/S1 for all mills |
| v0.3 | Sobol on ≤ 8 parameters | drop CBIO-stacking scenarios | LCOB only (no NPV/IRR) | LCOB p05/p50/p95 per mill |
| v1.0 | MILP for 2–3 regional clusters only | merit-order supply curve from per-mill best LCOB (no MILP) + nearest-infrastructure mode rule | production-gate supply curve (no delivery mode) | supply curve with MC bands |
| Demo | drop the scoreboard tab | drop the plant simulator, keep maps + curve | static slide deck from release figures | — |
| P1 | — | submit after Carnival | — | complete draft with co-authors |

---

## 5. Week-by-week plan

Every week ends with the **Friday ritual** (§10): tests + `engine.registry validate` + push + weekly log `docs/plan/weekly/Wxx.md` + STATUS update. That ritual is not repeated in each checklist.

---

### W1, Mon 5 → Fri 9 Oct · 32 h: start the external clocks and the release machinery

**Goal:** every slow external process is started by Wednesday, the repo is on its own private remote with CI green, and the baseline pre-registration is filed by Friday.

**Mon 5 Oct**
- [ ] 08:30 Code inventory: `git ls-files src/engine`, `uv sync --all-extras && uv run pytest -q`. Record what exists, what fails and what is missing in `docs/plan/STATUS.md` §Code.
- [ ] Create the **private** repo `aikiesan/sp-biomethane-engine` with a **fresh history** (`ACCESS_AT_HOME.md` Option C). Do not carry the unrelated `aprenda_sobre_biometano` commits, so the repo can go public cleanly at P1. Push; GitHub Actions `ci.yml` green.
- [ ] **LAI, federal, Fala.BR:** file R1 (ANP ethanol per plant), R2 (ANP biomethane per plant + feedstock; **add an item asking for the panel's update schedule / SIMP reporting deadline**), R3 (MAPA SAPCANA). Paste the protocol numbers into the `docs/07_LAI_REQUESTS.md` tracking table.
- [ ] **LAI, state, SIC.SP:** file R4 (CETESB PAV), R5 (CDA/SAA livestock), R6 (Sabesp/ARSESP sludge), R8 (ARSESP TUSD-Verde). Record the protocols.
- [ ] Commit `docs/plan/PLAN_4M_2026-10_2027-02.md` (this file) and a pointer at the top of `docs/19`.

**Tue 6 Oct**
- [ ] **Lab emails (time-critical: harvest ends ~end Nov).** LABIOEN lead (E1 filter-cake storage, E2 vinasse composition) and UNIFAL CEMARA (ask which of E2/E6/E7 analyses they can run, and the lead time). Attach a one-page protocol each, based on `docs/17`. Propose a sampling calendar: E1 t0 by Oct 26–Nov 6, then monthly, avoiding Dec 24–Jan 1. E2 biweekly Oct 19 → end of harvest. Ask for a meeting this week or next.
- [ ] **São Martinho:** request access to fresh filter cake + vinasse at 2–3 units for E1/E2 (biosafety/transport handled by the lab). Add the data wish-list from `templates/PARTNER_DATA_REQUEST.md` and the NDA scope. Mention the late-January results demo.
- [ ] **Comgás** (network/connection cost references, TUSD-Verde methodology) and **Equinor** (investor criteria): same template, and flag the demo window (W17).
- [ ] **PPBIOEN:** E3 season-switching proposal. Ask whether a continuous run can start in Dec–Jan with stored filter cake; if not, plan for the 2027 transition.
- [ ] **LAI R7:** email CATI/IEA proposing a research agreement (termo de cooperação) for LUPA microdata.

**Wed 7 Oct**
- [ ] **ANP snapshot.** Download the biomethane producers panel tables (manually if Power BI) to `data/raw/anp_biometano/2026-10-07/`, compute sha256 and register the source. Record the **latest published month** and the **observed lag** in `docs/21` (new Q11 "ANP publication lag") and in `preregistration/PROTOCOL.md`.
- [ ] Register **all held datasets** with `ingest/inventory.py`: MapBiomas cane 2008–2025, SEADE/IBGE planted/harvested 2008–2025, UNICA SP 2008–2018, mill coordinates, gas transport/distribution, city gates, injection points, rail, transmission, roads, livestock points, exclusions, PILAR-2b FDE, prices, lab references. Done when `uv run python -m engine.registry validate` exits 0.
- [ ] Initialize DVC and **decide the remotes** (public-safe + private). Update ADR-0003 → Accepted (record the remote choice). Pending user decision from `docs/99`.

**Thu 8 Oct**
- [ ] **RenovaBio list.** From the ANP certificate list, write `data/interim/renovabio_sp_units.csv` (CNPJ, unit, inspection firm, validity, report URL found Y/N).
- [ ] Regression test: run `ingest/renovabio.py` on the Santa Adélia evidence PDF and assert the V-values in `evidence/README.md` (cane 2021–2023, vinasse, ethanol 2023).
- [ ] Draft ADR-0006 … ADR-0010 (§4.1) in `docs/decisions/` and update `docs/decisions/README.md`.

**Fri 9 Oct**
- [ ] **Pre-registration R-A0 (baselines only).** M0 (seasonal naive) and M1 (phase climatology) from the snapshot → `preregistration/RA0_2026-10-09/{PROTOCOL.md, predictions.csv, SHA256SUMS, anp_snapshot.sha256}`. Register on **OSF Registries with an embargo** (verify embargo terms). Email the SHA-256 to two co-authors as a backup timestamp. Git tag `prereg-RA0`.
- [ ] Friday ritual. Send a one-page plan summary to CP2B coordination / co-authors.

**Deliverables:** 7 LAI protocols + the R7 email; 6 partner/lab emails; private repo with CI green; ANP snapshot + measured lag; complete held-data registry; ADRs 0006–0010 drafted; R-A0 filed.
**Touches:** `ingest/inventory`, `ingest/renovabio`, `registry`, `calibrate/anp`, `calibrate/metrics` · docs 07, 17, 19, 21, decisions.

---

### W2, Tue 13 → Fri 16 Oct · 26 h (Mon 12 holiday): file pre-registration R-A and start the label harvest

**Goal:** the engine-v0 pre-registration is filed, and RenovaBio extraction is running on real reports.
- [ ] Download every findable SP RenovaBio report (Benri, Accenture, SGS, KPMG, Verifit, Totum) to `data/raw/renovabio_cert_reports/<cnpj>/`; register the checksums. Target: ≥ 50 reports by Fri W3.
- [ ] Extract batch 1 (≥ 15 mills) to `data/interim/mill_year_renovabio.parquet`, with rejects in `data/interim/extraction_raw/rejects_W02.csv`. The quote verifier must pass for 100 % of accepted values.
- [ ] Download UNICA SP biweekly crush for 2019–2026 (source/route to verify; held data covers 2008–2018 only) to `data/raw/unica_sp_biweekly/`. Use `supply/seasonality.py` to build monthly shares 2008–2025 in `data/processed/unica_monthly_shares.parquet`.
- [ ] Download the ANP ethanol producers open data (capacity, CNPJ, location) to `data/raw/anp_ethanol_producers/`.
- [ ] Facilities v0: CNPJ crosswalk of mill coordinates (held) × ANP ethanol × RenovaBio list → `data/interim/facilities_v0.parquet`; manual-review list in `data/interim/facilities_unmatched.csv`.
- [ ] **Pre-registration R-A (engine v0):** M2 structural model. Monthly utilization = f(UNICA monthly crush share; strategy: S0 for Costa Pinto, S1 for Narandiba, a documented ramp-up prior for Santa Cruz and Paraguaçu), with parameters from registry priors (S/K flagged). Write to `preregistration/RA_2026-10-16/`; OSF + tag `prereg-RA`. **Deadline: before the next ANP table update.** Months that ANP publishes earlier simply become training data.
- [ ] Follow up lab/partner emails. Target: written confirmation of the E2 start date and the E1 t0 date.

**Deliverables:** R-A filed; facilities_v0; UNICA monthly shares; ≥ 15 mills extracted.
**Touches:** `ingest/renovabio`, `ingest/pdftext`, `supply/seasonality`, `process/strategies`, `calibrate/anp` · docs 06, 09, 13.

---

### W3, Mon 19 → Fri 23 Oct · 32 h: H3 cane panel, OD matrix, supply parameters verified

**Goal:** the statewide cane panel and the road OD matrix exist, and the supply parameters used in v0.1 are V.
- [ ] Run `supply/raster_h3.py` for 2008–2025 (≈ 1–2 min per year) → `data/processed/h3_cane_area/year=YYYY/part.parquet` (res 8). Log runtimes in `reports/supply/raster_runtime.md`.
- [ ] Cane mass = area × harvested/planted × yield (SEADE/IBGE), rescaled to municipal totals with `supply/grid.py` → `data/processed/h3_cane_t.parquet`. Diagnostics in `reports/supply/municipal_scale_factors.csv` (flag outliers; log them in docs/21).
- [ ] OSRM: `scripts/routing/setup_osrm.sh` with the Geofabrik Southeast Brazil extract (verify extract name/size) and the car profile. Compute `siting/routing.od_matrix` from res-7 centroids with cane to mills within the truncation radius → `data/processed/od_h3r7_mills.parquet`. **Decision point Wed:** if OSRM is not up, switch to the ADR-0007 fallback and log it.
- [ ] RenovaBio: ≥ 40 SP mills with ≥ 1 extracted mill-year. **Audit** a random 10 % (`data/interim/audit/renovabio_audit_W03.csv`), Lucas ≈ 3 h.
- [ ] **Verification block** (~5 h): `vin_gen`, `fc_gen`, `straw_gen`, `straw_recov`, ethanol yield. Read the primary documents and add page + quote (docs/08). Anything not V is listed for the v0.1 release notes.
- [ ] Coordination: E2 round 1 (if confirmed). Lucas records the sample IDs in `data/private/lab/E2/sampling_log.csv`.

**Deliverables:** H3 cane panel 2008–2025; OD matrix; `mill_year_renovabio.parquet` v0 with audit.
**Touches:** `supply/raster_h3`, `supply/grid`, `siting/routing`, `ingest/renovabio` · docs 08, 09; ADR-0007.

---

### W4, Mon 26 → Fri 30 Oct · 32 h: calibrate Huff and produce the first full panel (Gate A)

**Goal:** a calibrated, cross-validated mill_year panel with intervals.
- [ ] Huff fit (frequentist, ADR-0006) with **leave-region-out CV** (spatial unit: RA or EDR; document the choice) → `reports/supply/huff_cv.md` (MAPE, bias, 90 % interval coverage). Never random K-fold (docs/13).
- [ ] Comparison allocation: nearest mill by network distance (Voronoi), saved as a sensitivity in `reports/supply/allocation_sensitivity.md`.
- [ ] `supply/residues.py` MC (n = 1 000, proposed) → `data/processed/mill_year.parquet` with p05/p50/p95 for cane, ethanol (est.), vinasse generated/available, filter cake, straw. Keep generated ≠ applied ≠ available (C1).
- [ ] Checks: Σ mills vs UNICA SP 2008–2018 per year; ethanol/cane in 70–90 L/t → `reports/supply/checks_v0.1.md`.
- [ ] `mill_month` from the UNICA shares.
- [ ] Start the Bayesian Huff **shadow** run (background, non-blocking).
- [ ] LAI: check Fala.BR and SIC.SP (deadlines ~Oct 26). Log the responses and prepare appeals (recurso) for refusals, citing the aggregated alternatives.
- [ ] Coordination: confirm E1 t0 collection (target this week or W5).
- [ ] **Gate A review** (§6) → `docs/plan/gates/GATE_A.md`.

**Deliverables:** mill_year / mill_month v0 (internal); Huff CV report; Gate A memo.
**Touches:** `supply/huff`, `supply/residues`, `supply/seasonality`, `calibrate/metrics`, `calibrate/bayes_huff` (shadow) · docs 09, 13; ADR-0004/0006.

---

### W5, Tue 3 → Fri 6 Nov · 26 h (Mon 2 holiday): harden v0.1, minimal PILAR-2b ingest, P1 skeleton

**Goal:** a release candidate bundle that passes the contract, plus the PILAR-2b side ready to receive it.
- [ ] Build `hex_supply` (residues per H3 × month; res 8 internal, res 7 export). Check the row counts against PILAR-2b ingest practicality.
- [ ] `export/bundle.py` → `exports/v0.1.0-rc1/`. Contract test `tests/test_bundle_contract_v01.py`: schema, unit suffixes, EPSG:4674, row counts, no private columns.
- [ ] **PILAR-2b (minimal ingest side):** on branch `engine-release-ingest` of `aikiesan/Pilar-2b`, add `backend/ingest/sources/engine_release` (gates: manifest schema, units, CRS, row counts) + a migration for `facilities`, `hex_supply`, `mill_month` (+ `engine_release_id`). Check their next migration number. **No frontend work.**
- [ ] P1 skeleton `papers/P1_data_descriptor/paper.qmd`: Background & Summary, Methods (from docs/09 + ADRs), Data Records, Technical Validation (linked to `reports/supply/`), Usage Notes. Choose the venue (Scientific Data / ESSD / Data in Brief): check scope, APC and funding (verify).
- [ ] **Regulatory:** has the CNPE 2027 target been published (due ~Nov 1, verify)? Read the resolution, add `mandate_2027` to `registry/parameters.csv` (V if read) and update `docs/16`.
- [ ] Process prep: livestock points × manure coefficients (confined animals only) → `data/processed/manure_points.parquet` (needed for S2).

**Deliverables:** v0.1.0-rc1; PILAR-2b ingest PR draft; P1 skeleton; CNPE note.
**Touches:** `export/bundle`, `supply/residues` · docs 16, 18; Pilar-2b `backend/ingest/`.

---

### W6, Mon 9 → Fri 13 Nov · 32 h: ship v0.1.0 (supply)

**Goal:** the first public-facing release is out and P1's Methods section is drafted.
- [ ] Final diagnostics. `docs/releases/v0.1.0.md` contains: contents, MAPE/coverage, Σ vs UNICA, **list of S/K parameters used**, known issues, LAI status.
- [ ] `git tag v0.1.0` → GitHub Release (private) → `dvc push` of the bundle → update the PR to Pilar-2b with the bundle (CI green). Merging is up to the PILAR-2b team.
- [ ] Email co-authors/partners a one-paragraph summary + 2 maps (public data only).
- [ ] P1: Methods section fully drafted (≈ 8 h writing).
- [ ] Start process: write `tests/test_volpi2021.py`, which reproduces the Volpi et al. 2021 reactor numbers, but only after the paper's values are verified (V) with page/quote. Verification block: `bmp_fullscale`, `olr_max_cstr`, `hrt_cstr`, vinasse COD/SO₄.
- [ ] Coordination: E1 t0 done? E2 round 2–3?

**Deliverables:** **v0.1.0** + PR; P1 Methods.
**Touches:** `export/bundle`, `process/substrates`, `process/cstr` · docs 10, 18, 20.

---

### W7, Mon 16 → Thu 19 Nov · 26 h (Fri 20 holiday): process calibration setup for the 4 ANP plants

**Goal:** prior-predictive process runs for the 4 plants, and a fixed calibration design.
- [ ] ANP refresh (Monday routine). Newly published months → score R-A0/R-A → `reports/scoreboard.md`. **Never edit filed predictions.**
- [ ] Plant ↔ mill link table `data/interim/anp_plant_mill_link.csv`: Costa Pinto ↔ Raízen Costa Pinto mill; Narandiba ↔ Cocal Narandiba; Santa Cruz ↔ Bioenergia Santa Cruz, Américo Brasiliense (São Martinho link, verify); Paraguaçu ↔ Cocal Paraguaçu (poultry-manure co-digestion per docs/10, S).
- [ ] Forward-simulate S0/S1/S2/S4 with priors → `reports/process/prior_predictive.md`.
- [ ] Calibration design, written before fitting: parameters (f_scale, φ_store, delivered feedstock share, downtime/ramp-up); method (ABC rejection or least squares on monthly utilization); hold-out = last 3 published months per plant.
- [ ] LAI: responses and extension logs; file appeals (recursos) where needed.
- [ ] Coordination: E2 final rounds before harvest end. Confirm the **bulk filter-cake stock** for E1/E3.

**Deliverables:** prior-predictive report; calibration design note; scoreboard v1 (if ANP has updated).
**Touches:** `process/strategies`, `process/cstr`, `calibrate/anp`, `calibrate/metrics` · docs 10, 13.

---

### W8, Mon 23 → Fri 27 Nov · 32 h: calibrate process to ANP (Gate B)

**Goal:** the engine reproduces the off-season collapse versus storage-supported operation.
- [ ] Run the calibration → `reports/process/calibration_v0.2.md`: fitted/accepted parameter sets, hold-out CRPS/coverage/MAPE, plots of observed vs simulated (4 plants).
- [ ] Simple LCOB (annuity) with EPE anchors. **Verification block:** EPE NT 2025-08 CAPEX factor and OPEX scope (C5). Values stay S until read.
- [ ] P1: Data Records + Technical Validation drafted from the v0.1 reports.
- [ ] Coordination: E1 t1 (if t0 was in late Oct); last harvest vinasse samples.
- [ ] **Gate B review** → `docs/plan/gates/GATE_B.md`.

**Deliverables:** calibration report; P1 sections 3–4.
**Touches:** `process/*`, `economics/lcob`, `economics/finance`, `calibrate/*` · docs 10, 11, 13.

---

### W9, Mon 30 Nov → Fri 4 Dec · 32 h: ship v0.2.0 and file pre-registration R-B

**Goal:** process/LCOB release plus calibrated, timestamped forecasts of the off-season.
- [ ] Run all candidate mills × S0/S1/S2/S4 with the calibrated parameters → `lcob_results` (simple) + process tables. Tag **v0.2.0**, write `docs/releases/v0.2.0.md`, and update the Pilar-2b PR (add the `lcob_results` migration).
- [ ] **Pre-registration R-B:** calibrated engine predictions for every unpublished month up to Mar 2027 → `preregistration/RB_2026-12-04/`, OSF, tag `prereg-RB`.
- [ ] **Demo invitations:** São Martinho, Comgás, Equinor, LABIOEN, UNIFAL CEMARA, PPBIOEN, PILAR-2b team. Propose Wed 27 / Thu 28 Jan, avoiding Mon 25 Jan. Offer São Martinho a private 30-min preview of Santa Cruz simulated vs observed (public ANP data only).
- [ ] P2 `papers/P2_capacity_factor/`: outline, Fig 1 (observed utilization, 4 plants), Fig 2 (simulated vs observed), the pre-registration protocol section.
- [ ] Regulatory: check whether the SP ICMS 12 % reduction has been renewed. Define the two v0.3 scenarios.

**Deliverables:** **v0.2.0**; **R-B filed**; invitations sent; P2 outline + 2 figures.
**Touches:** `process/*`, `economics/lcob`, `export/bundle`, `calibrate/*` · docs 13, 16, 20.

---

### W10, Mon 7 → Fri 11 Dec · 30 h (Tue 8 possible local holiday, verify): economics layer

**Goal:** CAPEX/OPEX/revenues built on verified anchors, with the MC + Sobol machinery running at full size.
- [ ] Verification block (~6 h): EPE NT 2025-08 & 2023-07, FIESP 2024, BNDES loan terms (BNDES operations CSV → `data/interim/bndes_biomethane_ops.parquet`). Check the CGOB/CBIO price status in the digests.
- [ ] Normalize `registry/projects_capex.csv` → `registry/projects_capex_normalized.csv`: capacity basis (C2/C3), scope, price year BRL_2025. Use IPCA/INCC series downloaded and registered, never typed in.
- [ ] `economics/capex`: exploratory log-log fit + EPE anchor (baseline). OPEX. Revenue scenarios: CGOB 0/0.5/1.0/1.5; CBIO yes/no (stacking question open, docs/21 Q1); ICMS 12 % vs lapse; WACC 8/10/12 %.
- [ ] LHS MC (n = 10⁴, docs/11) per mill × best strategy. Sobol (SALib) on ≤ 12 parameters → `reports/economics/sobol_v0.3.md`.
- [ ] P1: abstract, background, usage notes (≈ 6 h) → **complete draft**.

**Deliverables:** normalized CAPEX table; MC/Sobol results (pre-release); P1 complete draft (internal).
**Touches:** `economics/{capex,revenue,finance,lcob,montecarlo}` · docs 11, 16.

---

### W11, Mon 14 → Fri 18 Dec · 32 h: ship v0.3.0, P1 to co-authors (Gate C before recess)

**Goal:** close the year with three releases shipped and P1 in co-authors' hands.
- [ ] LCOB/NPV/IRR distributions for all candidate mill sites; break-even CGOB; validation against the EPE/FIESP/IEA ranges (all S unless verified) → `reports/economics/validation_v0.3.md`.
- [ ] Tag **v0.3.0**, write release notes, update the Pilar-2b PR.
- [ ] **P1 complete draft → co-authors** (docx via Quarto), with comments due **Fri 15 Jan**.
- [ ] P2: Sobol figure (H3.2: is capacity factor the most influential LCOB parameter?).
- [ ] Ask the labs for **interim E1/E2 tables** before the recess (`data/private/lab/E1|E2/`) and run them through `calibrate/lab.py`.
- [ ] Queue long robustness MC runs to execute over the recess (scenario grid) → `runs/`.
- [ ] Bayesian Huff shadow: converged per ADR-0006? Record promote or defer.
- [ ] **Gate C review** → `docs/plan/gates/GATE_C.md`.

**Deliverables:** **v0.3.0**; **P1 draft out**; Gate C memo.
**Touches:** `economics/*`, `export/bundle`, `calibrate/lab` · docs 11, 17, 20.

---

### W12, Mon 21 → Wed 23 Dec · ~16 h (24 suspended, 25 holiday): low-load buffer

**Goal:** absorb any v0.3 slip; otherwise low-coupling writing and siting prep.
- [ ] If v0.3 slipped: finish it here (buffer).
- [ ] P2 Introduction + related work, citing only references in `docs/23`.
- [ ] Siting prep: harmonize the gas infrastructure layers (distribution network, city gates, injection points; held) → `data/interim/gas_infra.parquet` (EPSG:4674, attributes documented).
- [ ] No releases, no partner emails.

**Touches:** `siting/*` (data prep) · docs 12, 20.

---

### W13, Mon 28 → Wed 30 Dec · 0–10 h (31 suspended, 1 Jan holiday): recess, optional work only

- [ ] (optional) Review the recess MC outputs; write P2 discussion notes.
- [ ] (optional) Note in `docs/16` whether the ICMS reduction was renewed by 31 Dec and any CGOB year-end signals.
- Nothing on the critical path.

---

### W14, Mon 4 → Fri 8 Jan · 32 h: siting inputs

**Goal:** everything the MILP needs, with road distances.
- [ ] Candidates = mills active in 2025 (facilities status), screened against the hard exclusions (held) → `data/processed/candidates_v1.parquet`.
- [ ] OSRM OD: mills → nearest city gate / injection point / network vertex; mills → manure points within a stated radius (≈ 20–30 km per H4.2, proposed) → `data/processed/od_mills_gas.parquet`, `od_mills_manure.parquet`.
- [ ] Delivery-mode costs: grid connection (TUSD-Verde values if verified; otherwise a per-km connection cost from Comgás or literature, flagged S) vs CNG (compression + trailer t·km). Verification block: ARSESP Del. 1.765/2025.
- [ ] E1 interim storage-loss points (if any) → φ_store sensitivity range (marked "preliminary, internal").
- [ ] ANP refresh + scoreboard. P1: triage early comments.

**Deliverables:** candidates, OD tables, mode-cost table `registry/parameters.csv` (siting rows flagged).
**Touches:** `siting/routing`, `siting/facility_milp` (inputs) · docs 12, 16.

---

### W15, Mon 11 → Fri 15 Jan · 32 h: MILP + supply curve

**Goal:** a statewide supply curve with uncertainty bands and robustness checks.
- [ ] `siting/facility_milp`: sites = mills; 3–4 discrete sizes; 12 months; manure flows; filter-cake storage with loss λ; mode choice (grid vs CNG). Solve statewide; if HiGHS takes too long, solve per region (cut 1).
- [ ] `siting/supply_curve`: merit order with MC bands from the v0.3 draws. Overlays: 0.5 % 2026, the 2027 target (if published), 1 %, 10 %. Volumes come only from documented sources (CNPE Res. 4/2026 ≈ 181.7 M m³ for 2026/27 is S; other volumes need a source), otherwise they are labelled placeholders.
- [ ] Robustness: Huff vs nearest-mill allocation; CGOB 0 vs 1.0; ICMS scenario → `reports/siting/robustness_v1.md`.
- [ ] **P1 co-author comments due Fri 15 Jan.** Make a revision list.

**Deliverables:** supply curve + robustness report.
**Touches:** `siting/{facility_milp,supply_curve}` · docs 12.

---

### W16, Mon 18 → Fri 22 Jan · 32 h: v1.0.0-rc1, demo build, dry run

**Goal:** the demo works end to end on a release candidate.
- [ ] `exports/v1.0.0-rc1/` with `sites` and `supply_curve` + contract tests.
- [ ] `app/demo/streamlit_app.py` reads **only** `exports/v1.0.0-rc1/`. Four tabs: (1) supply map (mills, residues, month slider); (2) plant simulator with precomputed strategy × scenario results; (3) supply curve with MC band + mandate overlays; (4) pre-registration scoreboard. Make static PNG/PDF fallbacks.
- [ ] **Internal dry run, Fri 22 Jan** (CP2B/LABIOEN colleagues). Log issues in `docs/plan/demo_dryrun.md`.
- [ ] P1 revision (≈ 8 h). P4: `papers/P4_siting/outline.md` + draft Figs (curve, site map).

**Deliverables:** rc1; working demo; dry-run issue list.
**Touches:** `export/bundle`, `app/demo` · docs 18, 20.

---

### W17, Mon 25 → Fri 29 Jan · 32 h: ship v1.0.0, partner demo, Gate D

**Goal:** the four releases are complete, partners have seen the results, P1 is ready to submit and P2 is fully drafted.
- [ ] Mon: fix the dry-run issues. **Tue 26: tag v1.0.0**, write release notes, update the Pilar-2b PR (`sites`, `supply_curve` migration).
- [ ] **Wed 27 / Thu 28: partner demo** (60–90 min). Agenda: problem → supply → capacity factor + pre-registration → LCOB → supply curve → asks (data, validation, co-design of the PILAR-2b pages). Record feedback in `docs/plan/demo_feedback_2027-01.md`. Fallback: a recorded walk-through.
- [ ] **P1 submission package:** cover letter, data availability statement, Zenodo deposit prepared (reserve the DOI). Repo-public checklist: `gitleaks` scan, GPL-3.0 licence, no `data/private` paths, partner names only in acknowledgements as agreed.
- [ ] **P2 complete draft**, with prospective-test results to date and the remaining months listed as "to be scored".
- [ ] **Gate D review** → `docs/plan/gates/GATE_D.md`.

**Deliverables:** **v1.0.0**; **demo held**; P1 submission-ready; P2 complete draft.
**Touches:** all modules (release), `app/demo` · docs 18, 20.

---

### W18, Mon 1 → Fri 5 Feb · 32 h: start P3/P4, submit P1, close the loop

**Goal:** the next papers are started and the following plan is written.
- [ ] **P1:** submit if all co-authors have signed off; otherwise fix a submission date after Carnival (Feb 8–9). Make the repo public + Zenodo DOI at submission (`docs/19` Phase 5 rule).
- [ ] **P3:** `papers/P3_capex/outline.md`; `r/capex_brms.R` exploratory hierarchical fit on the normalized Brazilian table (prior β ~ N(0.65, 0.1), ADR-0005), plus international anchors only if verified V. Results are labelled exploratory.
- [ ] **P4:** methods section from `docs/12` + the v1.0 robustness report.
- [ ] Update the scoreboard; retrospective `docs/plan/RETRO_2027-02.md` (hours vs plan, gates, cuts used); next plan `docs/plan/PLAN_2027H1.md` with the deferred list (§8) prioritized.
- [ ] Note in `docs/16` the ANP Res. 1.006 transition end (9 Feb 2027, S).

**Deliverables:** P3/P4 started; P1 submitted (or dated); retro + H1-2027 plan.
**Touches:** `r/`, papers · docs 05, 11, 20, 21.

---

## 6. Monthly gates (adapted from docs/19 Gates 0–4)

| Gate | Date | Pass criteria (all measurable) | If it fails |
|---|---|---|---|
| **A: Foundation & labels** (≈ old Gate 0) | Fri 30 Oct (W4) | (1) 7 LAI protocol numbers + R7 contact logged in `docs/07`. (2) CI green on the private repo and `uv sync && pytest` passes in a clean container. (3) `engine.registry validate` exit 0 with every held dataset registered (sha256). (4) R-A0 and R-A filed with external timestamps **before** ANP published the covered months. (5) ≥ 40 SP mills with ≥ 1 extracted mill-year, 100 % of values with page + verbatim quote, audit error ≤ 5 % (proposed). (6) H3 cane panel 2008–2025 complete; Σ cells = municipal totals by construction, scale factors reported. (7) E1/E2 dates confirmed in writing, or the fallback documented. (8) ≥ 80 % of the **supply** parameters used in v0.1 are V | (5) fails → P1 is framed as "calibrated on N mills"; push extraction in W5. (7) fails → E1 moves to the 2027 harvest and the model uses literature ranges (S) |
| **B: Supply shipped** (≈ old Gate 1) | Fri 27 Nov (W8) | (1) v0.1.0 tagged, PR open, CI green. (2) Leave-region-out mill cane MAPE < 15 % **or** a documented explanation. (3) 90 % interval coverage within 80–95 % (proposed). (4) Σ mills vs UNICA SP 2008–2018 within ±10 % per year (proposed tolerance). (5) Ethanol/cane within 70–90 L/t for ≥ 90 % of mill-years. (6) P1 Methods + Data Records drafted. (7) Process prior-predictive done for the 4 plants | (2)–(4) fail → ship anyway with diagnostics in the release notes; P1 Technical Validation reports them honestly |
| **C: Process + economics shipped** (≈ old Gates 2+3) | Fri 18 Dec (W11) | (1) v0.2.0 and v0.3.0 tagged. (2) The simulated off-season/peak utilization ratio falls within the observed range for Costa Pinto **and** Narandiba; ≥ 75 % of hold-out months fall inside the 90 % predictive interval (proposed). (3) LCOB p05/p50/p95 for all candidate mills; Sobol ranking documented. (4) ≥ 80 % of the process + economics core parameters used are V (PROJECT.md success criterion), the rest listed in the release notes. (5) R-B filed. (6) P1 complete draft sent | (2) fails → P2 reframes as a "diagnosis of the gap". (4) fails → the W14 verification blocks take priority over P4 drafting |
| **D: v1.0 + demo** (≈ old Gate 4) | Fri 29 Jan (W17) | (1) v1.0.0 tagged; supply curve with MC bands + ≥ 2 robustness checks documented. (2) Demo held with ≥ 2 company partners present, or the recorded walk-through sent. (3) P1 submission-ready (all comments resolved or answered). (4) P2 complete draft. (5) Scoreboard covers every month published to date | Use the cut ladders (§4.2); W18 becomes the v1.0 buffer and P3/P4 drop to outlines only |
| **Close** | Fri 5 Feb (W18) | Retro + H1-2027 plan committed; P3/P4 outlines + methods drafts exist; P1 submitted or dated | — |

---

## 7. Critical path (and float)

1. **W1** private repo + CI + registry of held data → everything downstream.
2. **W2–W4** RenovaBio harvest + extraction + audit → Huff calibration labels.
3. **W3** H3 cane panel (municipal rescale) → **W3–W4** OSRM OD matrix.
4. **W4** Huff calibration + residues MC → **W5** bundle + PILAR-2b ingest → **W6 v0.1.0** (Gate B relies on it).
5. **W7–W8** process calibration on ANP → **W9 v0.2.0** + R-B.
6. **W10** CAPEX normalization + MC/Sobol → **W11 v0.3.0**.
7. **W14** siting inputs (candidates, OD to gas infrastructure, mode costs) → **W15** MILP + supply curve → **W16** rc1 + demo → **W17 v1.0.0 + demo**.

**Float:** W12 (≈ 16 h) is the only buffer between v0.3 and siting. W18 is the buffer for v1.0, and using it shrinks P3/P4 to outlines. No other float exists, which is why every release has a cut ladder.

**Time-locked side tracks (off the code critical path, but with hard external deadlines):** LAI filing (W1), lab sample collection (W1–W8, harvest-bound), pre-registrations (W1, W2, W9; must precede ANP publication), demo invitations (W9), CNPE check (W5), ICMS scenario (W9–W14).

---

## 8. Cut or deferred until after Feb 2027

| Item | Status in window | Moves to |
|---|---|---|
| Bayesian Huff calibration (PyMC/brms) as the primary method | Shadow run only; frequentist + bootstrap ships | Mar–Apr 2027 (P1 revision / v1.1) |
| Hierarchical Bayesian CAPEX with full international pooling (BIP TF4, DEA, KTBL, EBA) | Brazilian normalization + exploratory brms prototype | P3 core analysis, Feb–Apr 2027 |
| Valhalla truck costing; ANTT t·km cost model per material | OSRM car profile + simple t·km | v1.1 |
| Sentinel-2/1 harvest detection and mill-specific monthly profiles (`harvest_detect.py` exists) | Parked; UNICA state curve used for all mills | after P1; possible P1 follow-up |
| Temporal validation 2008–2018 / 2019–2025 on mill labels | Not possible (RenovaBio starts ~2018); leave-region-out + UNICA check instead | — |
| ADM1 (Level 2 process) | Not started | after Gate C equivalent + PPBIOEN data |
| Hub (non-mill) candidate sites; LNG and transmission injection modes | Mills only; grid vs CNG | P4 extension |
| S3 (sludge/OFMSW/agro-industrial) and S5 optimized hybrid | Code kept, not in results | P4 extension |
| Sewage sludge, OFMSW, SIF agro-industrial supply layers | Not ingested | after LAI R6 responses |
| PILAR-2b frontend pages (Plant simulator, Supply curve) and API endpoints | Ingest + migrations only; the Streamlit demo serves as the spec | PILAR-2b team, H1 2027 |
| Automated monthly ANP ingestion + predicted-vs-observed dashboard ("digital shadow") | Manual Monday refresh + scoreboard script | H1 2027 |
| Morris screening | Sobol directly on a reduced set | — |
| E3–E9 lab/pilot experiments; P5 lab paper | E1/E2 sampling only (interim data used as sensitivity) | 2027 harvest transition; P5 later |
| P2 final scoring and submission | Draft with protocol + partial scoring | after the Dec–Mar months are published (lag-dependent) |
| P6 policy brief, P7 software paper | Not started | after P4 |
| International benchmark downloads beyond the LCOB sanity anchors | Not done | P3 |

---

## 9. Risk register (specific to these 18 weeks)

| ID | Risk | P | I | Early warning (date) | Mitigation | Fallback |
|---|---|---|---|---|---|---|
| K1 | Too few usable SP RenovaBio reports (some firms don't publish, PDFs are scanned or the format varies) | M | H | < 25 mills extracted by Fri W3 | Start W2; rule-based extractor + `pdftext`; OCR only for high-value mills; LLM extraction with quote verification | P1 calibrated on N mills, coverage reported; ANP capacity as prior |
| K2 | OSRM build/RAM fails on the home machine | M | M | Not running by Wed W3 | res-7 origins; Southeast extract only; Docker memory settings | ADR-0007 fallback (cited detour factor), flagged in P1 |
| K3 | ANP publishes before a pre-registration is filed | M | M | Monday check shows a new month | R-A0 on day 5 (baselines are cheap); file R-A before the expected mid-month update (verify cadence) | Affected months become training data; the protocol defines this |
| K4 | ANP lag is long, so no off-season month can be scored by 5 Feb | H | M | W1 lag measurement | Score harvest-month nowcasts within the window; frame P2 so its claims hold either way | P2 submitted after scoring (Apr–Jun 2027) |
| K5 | Lab cannot collect fresh filter cake/vinasse before the harvest ends | M | M | No written sampling date by Fri 23 Oct (W3) | Ask on day 2; São Martinho access; propose a minimal E1 design (t0 + 2 time points) | φ_store from literature (S) in sensitivity; E1 moves to the 2027 harvest |
| K6 | Recess + partner holidays push the demo out | M | M | < 2 partner confirmations by Fri 18 Dec | Invite in W9; avoid Mon 25 Jan; offer two slots | Recorded walk-through + 1:1 calls in Feb |
| K7 | One-person overload or illness | M | H | Weekly log shows > 4 h slip two weeks running | Fixed release dates + cut ladders; W12/W18 buffers | Apply cut 1–2 across releases; P3/P4 to outlines |
| K8 | Verification bottleneck (gov sites block automated access; many S/K) | H | M | Gate A criterion (8) fails | Verification blocks scheduled per release (just in time); manual downloads registered | Release notes list S/K values used; papers carry caveats |
| K9 | PILAR-2b PR review delayed or contract disputes | M | L | No review in 2 weeks | Minimal ingest (no frontend); contract tests on the engine side | Bundles stay in engine releases; merge after the window |
| K10 | Regulatory surprise (CNPE 2027 target, ICMS lapse, first CGOB trades) changes headline numbers | H | M | Daily digests (00:55 and 01:50 BRT routines) | Scenario parameters, not code; update `docs/16` within 1 week | Results reported as scenarios |
| K11 | v0 code breaks at statewide real-data scale (memory, runtime) | M | M | W3 first full runs | Partitioned Parquet by year; test on one region first; profile | Restrict years (cut ladder) |
| K12 | LLM/regex extraction errors propagate into P1 | M | H | Audit error > 5 % | Verbatim-quote verifier; reject rows without a quote; 10 % audit + all > 3 MAD outliers (docs/08) | Drop affected variables from P1 Data Records |
| K13 | Partner/NDA data arrive and leak into exports or the demo | L | H | Any file in `data/private/` | `bundle.py` private-column gates; demo reads bundles only; never commit `data/private` | Revoke and rebuild the bundle; inform the partner |
| K14 | Repo going public for P1 exposes history or secrets | L | H | W17 checklist | Fresh history in W1; `gitleaks` before going public; `.env` gitignored | Publish a clean export repo instead |
| K15 | Journal APC/format blocks P1 submission | M | L | W5 venue check | Check APC + funding (FAPESP; verify) in W5 | Data in Brief / ESSD alternative |
| K16 | Santa Cruz / Paraguaçu are still commissioning, so their predictions are uninformative | H | L | Data flat at ~0 | Treat them as ramp-up tests; report separately | P2 focuses on Costa Pinto vs Narandiba |

---

## 10. Weekly rhythm

| When | What (≈ time) | Output |
|---|---|---|
| **Mon 08:30–09:30** | Read the Sunday digest (weekly synthesis + 5 priorities from the routine) and skim the week's digests. Run the ANP refresh check and the LAI portal check. Then the Claude "Monday plan" session (prompt P-1) | `docs/plan/STATUS.md` updated; week tasks in `docs/plan/weekly/Wxx.md` |
| **Tue–Thu** | Two deep-work blocks per day (≈ 3 h each) on **one** release; 45 min/day verification reading **or** writing (from W5 on, writing every day) | commits on a `wXX/<topic>` branch |
| **Wed 16:00 (30 min)** | Correspondence slot: lab, partners, LAI appeals, PILAR-2b PR | email log in STATUS |
| **Fri 14:00–17:00** | Review + push: tests, ruff/black, `engine.registry validate`, merge to `main`, `dvc push`. On a release week: tag + release notes + bundle + PILAR-2b PR. Weekly log: hours, done vs planned, % V of parameters used, scoreboard delta, risks with triggered warnings | `docs/plan/weekly/Wxx.md`; `CHANGELOG.md`; `docs/releases/vX.Y.Z.md` |
| **Last Fri of the month** | Gate review (A–D) | `docs/plan/gates/GATE_X.md` |

**Definition of Done (every release):** CI green · `engine.registry validate` = 0 · bundle passes `export/bundle` gates (`strict=True` for v1.0) · release notes list the S/K parameters used and their effect · the release maps to a paper section (figure/table regenerated from `run_id`) · PILAR-2b PR opened/updated · a 1-paragraph email to co-authors/partners.

---

## 11. Claude Code session prompts for recurring tasks

**P-1 · Monday plan**
```
Read docs/plan/PLAN_4M_2026-10_2027-02.md, docs/plan/STATUS.md and the last weekly log
docs/plan/weekly/W<NN-1>.md. Show `git log --since="7 days ago" --oneline` and failing tests if
any. Produce this week's (W<NN>) Mon–Fri schedule within <H> hours, ordered by the critical path in §7.
Flag any task at risk of missing its release date and propose the cut-ladder step (§4.2) to apply.
Write it to docs/plan/weekly/W<NN>.md. Do not start coding.
```

**P-2 · Friday review & release**
```
Run: uv run pytest -q; uv run ruff check src tests; uv run black --check src tests;
uv run python -m engine.registry validate. Summarize changes since the last tag. If this is a
release week (v<X.Y.Z>): build exports/v<X.Y.Z>/ with engine.export.bundle (strict for v1.0),
list every registry parameter used by this run whose flag is S or K, and draft
docs/releases/v<X.Y.Z>.md (contents, metrics vs gate criteria, S/K list, known issues, LAI/lab
status). Append the weekly log to docs/plan/weekly/W<NN>.md. Do not tag or push until I confirm.
```

**P-3 · Parameter verification (one document at a time)**
```
Verification per docs/08. Document: <local path to PDF in data/raw/...>. Parameters: <ids>.
For each id: find the value in the document, record page/table and a verbatim quote (≤ 2
sentences), conditions (units, basis, year, currency, price year). Compare with
registry/parameters.csv and propose the exact CSV diff and a change-log line. If the value is not
in the document, write "not found in <doc>"; never supply values from memory. If it conflicts with
another V source, add a row to docs/21 §Conflicts instead of averaging.
```

**P-4 · RenovaBio extraction batch**
```
Run engine.ingest.renovabio on data/raw/renovabio_cert_reports/<batch>/. Accept only records
whose quote passes verify_record. Write accepted rows to data/interim/mill_year_renovabio.parquet
(append, dedupe on cnpj+year+variable), rejects to data/interim/extraction_raw/rejects_<date>.csv.
Then sample 10 % of new rows plus all >3 MAD outliers into
data/interim/audit/renovabio_audit_<date>.csv with page numbers for my manual check. Report
coverage: mills, mill-years, variables, by inspection firm.
```

**P-5 · ANP refresh & scoring (never edits predictions)**
```
New ANP biomethane file at data/raw/anp_biometano/<date>/ (downloaded manually). Register it
(sha256) via engine.ingest.inventory, diff against the previous snapshot, list newly published
plant-months for Costa Pinto, Narandiba, Santa Cruz, Paraguaçu, and any revisions to old months.
Score every filing in preregistration/*/predictions.csv against the new months with
engine.calibrate.metrics (CRPS, 90 % coverage, median abs error, skill vs M0), nowcasts and
forecasts separately. Update reports/scoreboard.md. Do NOT modify anything under preregistration/.
Record the observed publication lag in docs/21 Q11.
```

**P-6 · Manuscript section drafting**
```
Draft section "<section>" of papers/<P#>/paper.qmd. Use only docs/<NN>, ADRs and results in
reports/<...> produced by run_id <id>. Every number must cite a run_id or a registry source_id;
insert [VERIFY] wherever the underlying parameter is S/K. Cite only references already in
docs/23_REFERENCES.md; if one is missing, list it at the end instead of inventing it. Keep
Methods consistent with the code (quote function names). Output a diff.
```

**P-7 · PILAR-2b integration for a release**
```
In a branch of aikiesan/Pilar-2b, extend backend/ingest/sources/engine_release so it loads
exports/v<X.Y.Z>/ (manifest gates: schema, units, CRS EPSG:4674, row counts) and add the next
migration for tables <list> with engine_release_id. Follow their existing ingest contract and
migration numbering. Run their tests, then open a draft PR with a description linking the release
notes. No frontend changes.
```

**P-8 · Regulation & market digest triage (weekly, Monday)**
```
Read the last 7 "CP2B Radar Biometano" digests (Drive folder / Gmail). Extract only items that
change a registry parameter or a scenario (CNPE 2027 target, ICMS renewal, CGOB trades, CBIO,
TUSD-Verde, ANP resolutions). For each: source URL, date, quoted sentence, affected parameter or
scenario, proposed flag (S unless a primary text is attached). Propose diffs to docs/16 and
registry/parameters.csv; do not apply them.
```

**P-9 · Pre-release code review**
```
/code-review high on the diff since tag v<prev>. Focus: unit handling (column suffixes, Nm³ basis,
BRL price year), CRS, private-data leakage into exports, random-seed and run_id provenance.
```

**P-10 · Demo build / refresh**
```
Update app/demo/streamlit_app.py to read exports/<version>/ only (fail loudly if a file is
missing). Tabs: supply map, plant simulator (precomputed strategy × scenario), supply curve with
MC band + mandate overlays (labelled with their source flags), pre-registration scoreboard.
No data/private access. Add a smoke test that loads every tab against the bundle.
```

---

## 12. Paths introduced by this plan

```
docs/plan/PLAN_4M_2026-10_2027-02.md   docs/plan/STATUS.md   docs/plan/weekly/W01.md …W18.md
docs/plan/gates/GATE_A.md … GATE_D.md  docs/plan/demo_feedback_2027-01.md  docs/plan/RETRO_2027-02.md
docs/decisions/ADR-0006 … ADR-0010     docs/releases/v0.1.0.md … v1.0.0.md   CHANGELOG.md
preregistration/PROTOCOL.md  preregistration/{RA0_2026-10-09,RA_2026-10-16,RB_2026-12-04}/
reports/{supply,process,economics,siting}/   reports/scoreboard.md
papers/{P1_data_descriptor,P2_capacity_factor,P3_capex,P4_siting}/paper.qmd
app/demo/streamlit_app.py   r/capex_brms.R   registry/projects_capex_normalized.csv
data/processed/{h3_cane_area/,h3_cane_t,od_h3r7_mills,mill_year,mill_month,hex_supply,manure_points}.parquet
data/private/lab/{E1,E2}/   exports/v0.1.0 … v1.0.0/
```

## 13. To verify (collected from this plan)

UNICAMP suspended days and recess dates · Campinas municipal holiday on 8 Dec · São Paulo city holiday on 25 Jan and the partners' calendars · LAI deadline counting rule (calendar vs business days; Fala.BR and SIC.SP) · ANP panel update cadence and publication lag (snippet: tables updated 17/9/2026) · SIMP reporting deadline for biomethane producers · CNPE 2027 target date and content · SP ICMS 12 % decree and the rate after a lapse · OSF embargo terms · UNICA biweekly 2019–2026 download route · Geofabrik extract name/size · Bioenergia Santa Cruz ↔ São Martinho link · partner mill crush end date · journal APC/funding for P1 · PILAR-2b next migration number.
