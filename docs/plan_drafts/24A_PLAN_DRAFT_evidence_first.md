# SP Biomethane Engine: 18-week execution plan (Evidence & Data First)

**Window:** Mon 5 Oct 2026 → Fri 5 Feb 2027 (18 weeks) · **Owner:** Lucas (CP2B / NIPE-UNICAMP) with Claude Code
**Angle:** build a *defensible evidence base* first: data acquisition, the S/K→V verification sprint, LAI requests (pedidos de acesso à informação), the RenovaBio census (~128 SP certificates [S]) and registry hygiene. Models come second and consume only verified evidence. The plan is risk-first: long-lead items start in Week 1 and the critical path is explicit.
**Status:** draft for decision, 2026-10-04. When accepted, copy to `docs/24_EXECUTION_PLAN_2026-10_2027-02.md` and link it from `docs/00_INDEX.md` and `docs/19_ROADMAP_STEP_BY_STEP.md`.
**Rules carried over (CLAUDE.md):** never invent a number or URL; mark every uncertain date "(verify)"; a value is V only with page + verbatim quote; conflicts are logged, never averaged; partner data stays in `data/private/`.

---

## 0. Contents

1. Strategy on one page
2. Decisions to take in Week 1 (with defaults)
3. Critical path and long-lead items
4. Monthly gates (measurable pass criteria + fail actions)
5. Week-by-week plan (W1 day by day)
6. Pre-registered prospective prediction P-REG-1 (spec)
7. RenovaBio census pipeline (spec)
8. Verification sprint mechanics (spec)
9. Cut / deferred past Feb 2027
10. Risk register (4-month specific)
11. Weekly rhythm
12. Claude Code session prompts for recurring tasks
13. Evidence metrics reported every Friday
14. Appendix: new files and paths; calendar facts to verify

---

## 1. Strategy on one page

### 1.1 Principle
> **Evidence before models, and the model ranks while the evidence decides.** The existing v0 code (Monte Carlo/Sobol, CSTR, Huff) runs early, but only to **rank what to verify** and to **pre-register a prediction**. No result leaves the repo until its inputs pass the gate criteria.

### 1.2 Three clocks set the order of work
| Clock | What runs on it | Hard dates inside the window | Consequence for the plan |
|---|---|---|---|
| **Bureaucratic** | LAI (20 + 10 days, then appeals (recursos)), NDAs, LUPA cooperation agreement | File LAI on 5–6 Oct → first due ≈ 26 Oct, extended ≈ 4–5 Nov (verify counting rule) → appeals by mid-Nov | All requests go out in W1. Nothing in the model plan *depends* on a LAI or NDA result; they only improve it. |
| **Biological (safra)** | Fresh filter cake (torta de filtro) and vinasse (vinhaça) exist only until the crush ends (project convention ≈ end of Nov 2026; verify the partner mill's actual end date) | E1 filter-cake t0 **latest Fri 13 Nov**; E2 last sample ≈ 24–27 Nov | Lab sampling is fixed W2–W8 and cannot move. If it slips, it waits for the 2027/28 harvest (Apr 2027 onward). |
| **Publication (ANP)** | Monthly plant data appear with an **unknown lag** (to verify; W1 starts logging it) | Off-season Dec 2026–Mar 2027 happens inside the window | The prediction is **frozen Fri 27 Nov**, before December starts, and scored as each month is published. |

### 1.3 What "done" means on Fri 5 Feb 2027
| # | Outcome | Measured by |
|---|---|---|
| O1 | Clean registry: every dataset the code reads is registered (sha256, accessed date, license, provenance) | `python -m engine.registry validate --strict` exits 0, plus the hygiene sweep (prompt P11) finds 0 unregistered reads |
| O2 | ≥ 80 % of parameters used in any reported number are **V** (PROJECT.md success criterion) | Traceability report `docs/status/traceability_v0.2.md` |
| O3 | RenovaBio mill-year panel built from a census of SP certified units, with a quote per value and an audit | `data/processed/mill_year_renovabio.parquet` + coverage matrix + audit error rate |
| O4 | Facilities registry keyed on CNPJ (mills + biomethane plants), status by year | `data/processed/facilities.parquet` + match log |
| O5 | H3 res-8 cane panel 2008–2025 rescaled to SEADE/IBGE municipal totals | `data/processed/cane_t_h3r8_2008_2025.parquet` + scale-factor diagnostics |
| O6 | All LAI requests filed, answered or appealed, and their results registered | `registry/lai_requests.csv` with no row in "unknown" status |
| O7 | Harvest-window lab evidence secured: E1 storage silos started (t0, t1, possibly t2), E2 late-season vinasse series, material stocked for E3 | `data/private/lab/E1/`, `E2/` metadata + LABIOEN sign-off |
| O8 | **P-REG-1**: a frozen, timestamped prediction of monthly ANP output for 4 SP plants, scored on every month published so far | `prereg/P-REG-1/` + interim scoring report |
| O9 | Calibrated supply panel released as `v0.1.0`; LCOB v0 + Sobol + **preliminary** supply curve (mill sites only) released as `v0.2.0` | `exports/v0.1.0/`, `exports/v0.2.0/` manifests |
| O10 | P1 data paper (*mill-level residue panel*) full draft circulated to co-authors | `manuscripts/P1_mill_panel/` |

### 1.4 Capacity budget (one researcher, ~30–35 h/week)
E = evidence (acquisition, verification, LAI, lab coordination, audit) · M = models/code · W = writing, releases, admin. Holidays and recess are already subtracted.

| W | Dates (Mon–Fri) | Calendar notes | h | E / M / W |
|---|---|---|---|---|
| 1 | 5–9 Oct | Launch week | 34 | 26 / 4 / 4 |
| 2 | 12–16 Oct | Mon 12 national holiday | 26 | 20 / 3 / 3 |
| 3 | 19–23 Oct | | 34 | 24 / 6 / 4 |
| 4 | 26–30 Oct | **Gate 1** Fri 30 Oct | 34 | 22 / 8 / 4 |
| 5 | 2–6 Nov | Mon 2 Finados | 27 | 18 / 6 / 3 |
| 6 | 9–13 Nov | E1 t0 hard deadline Fri 13 | 34 | 18 / 13 / 3 |
| 7 | 16–20 Nov | Fri 20 Consciência Negra | 27 | 10 / 13 / 4 |
| 8 | 23–27 Nov | **P-REG-1 freeze + Gate 2** Fri 27 Nov | 34 | 16 / 10 / 8 |
| 9 | 30 Nov–4 Dec | | 33 | 8 / 21 / 4 |
| 10 | 7–11 Dec | Tue 8 Dec: municipal holiday in Campinas? (verify) | 33 | 8 / 21 / 4 |
| 11 | 14–18 Dec | **Gate 3** Fri 18 Dec, `v0.1.0` | 33 | 8 / 15 / 10 |
| 12 | 21–25 Dec | Fri 25 Christmas; UNICAMP recess (verify dates) | 16 | 6 / 2 / 8 |
| 13 | 28 Dec–1 Jan | Fri 1 Jan; recess (verify) | 13 | 6 / 3 / 4 |
| 14 | 4–8 Jan | | 32 | 12 / 16 / 4 |
| 15 | 11–15 Jan | | 33 | 8 / 20 / 5 |
| 16 | 18–22 Jan | | 33 | 6 / 21 / 6 |
| 17 | 25–29 Jan | **Gate 4** Fri 29 Jan | 33 | 8 / 10 / 15 |
| 18 | 1–5 Feb | Close-out, `v0.2.0`; Carnival 8–9 Feb falls after the window | 30 | 6 / 6 / 18 |
| | | **Total (estimate)** | **≈ 539** | **≈ 230 / 198 / 111** |

Overall about 43 % of the hours go to evidence, 37 % to models and 21 % to writing. The evidence share is **front-loaded**: W1–W8 are ≈ 62 % evidence (154 of 250 h), while W9–W17 are about half models (129 of 259 h). On top of these hours, each week keeps ~15 % slack, and W12–W13 are explicit buffers.

### 1.5 How this compresses `docs/19` (≈30 weeks → 18)
| docs/19 phase | Original weeks | In this plan | What changed |
|---|---|---|---|
| 0 Foundation & verification | 1–3 | W1–W8, interleaved | Stretched rather than compressed: it *is* the priority |
| 1 Supply panel | 4–8 | W3–W11 | Sentinel-2 cut; Bayesian Huff becomes a stretch goal; frequentist fit + region-block bootstrap |
| 2 Process + LCOB v0 | 9–12 | W6–W8 (process fit on ANP history → P-REG-1) | The process model is used for a *prospective* test, not only a back-fit |
| 3 Economics full | 13–16 | W14–W15 | Hierarchical Bayesian CAPEX deferred; EPE anchor + Brazil-only exploratory fit |
| 4 Siting & supply curve | 17–22 | W16 | Merit-order curve for mill sites only; MILP deferred |
| 5 Integration & papers | 23–30 | W17–W18 (partial) | P1 draft + `v0.2.0` bundle; PILAR-2b ingest side deferred |

---

## 2. Decisions to take in Week 1 (with defaults)

These are the pending decisions from `docs/99_SESSION_NOTES.md`. Take each one by Fri 9 Oct; if no decision is taken, the default applies.

| # | Decision | Default if undecided by Fri 9 Oct | Record in |
|---|---|---|---|
| D1 | Engine repo name and visibility | `aikiesan/sp-biomethane-engine`, **private** until the first paper (ACCESS_AT_HOME Option C), so the CI workflow becomes active | `docs/99`, README |
| D2 | DVC remote(s) | Public-safe remote plus a separate **private** remote for `data/private/` (provider per `docs/04`; pick the one that works this week) | ADR-0003 → Accepted |
| D3 | Lab leads for E1/E2 (LABIOEN) and E3 (PPBIOEN); UNIFAL CEMARA scope | Ask LABIOEN to lead E1 + E2; PPBIOEN to stock material for E3; UNIFAL CEMARA offered E2 replicate analyses or E6 BMPs | `docs/17` |
| D4 | Which partner data to request, under which NDA | São Martinho: samples + monthly mill data + Santa Cruz plant data; Comgás: network/TUSD-Verde; Equinor: investment criteria. All NDA data used **for validation only** | `templates/PARTNER_DATA_REQUEST.md` copies in `data/private/partners/` |
| D5 | Pre-registration venue | OSF embargoed registration (verify the embargo option) **plus** a git tag and an emailed SHA-256 to two witnesses. Zenodo is the fallback | `prereg/P-REG-1/protocol.md` |
| D6 | LLM used for residual extraction | Current Claude model through the API (record model + prompt hash per `docs/14`) | run manifest |

---

## 3. Critical path and long-lead items

Each chain below is a dependency chain. "Float" is how many weeks the chain can slip before it moves a gate or loses something that cannot be recovered.

| # | Chain (→ = feeds) | Latest safe start | Float | If late |
|---|---|---|---|---|
| **CP1** | LAI filing (R1–R6, R8, R9) → responses (≈26 Oct–5 Nov, verify) → appeals (≤10 days after each answer) → data registered → facilities v1 (R3), vinasse rules (R4), P-REG information set (R2) | **Tue 6 Oct** | 0 | Every day of delay pushes the appeal round out of the window |
| **CP2** | Lab access agreement (LABIOEN + São Martinho) → E1/E2 protocol → E2 biweekly samples → **E1 t0 by 13 Nov** → E1 t1 (≈ +1 month) → t2 (≈ +2 months, lab open during recess? verify) | **Fri 16 Oct** (agreement) | 0–2 weeks, **unrecoverable** after the crush ends | Not recoverable until the 2027/28 harvest; E1 becomes a 2027 experiment |
| **CP3** | SP certified-unit list → per-firm downloaders → reports (≥ 80 % by 27 Nov) → extraction + quote verifier → audit → `mill_year` v1 (13 Nov) → Huff calibration (W9–W10) → `v0.1.0` (18 Dec) → P1 draft (29 Jan) | **Thu 8 Oct** | ≈ 1 week (W12–W13 buffer cannot absorb it, because those weeks fall after the release) | `v0.1.0` slips to W14, then LCOB v0 slips into W15 and the supply curve becomes a stretch goal |
| **CP4** | ANP vintage logger (6 Oct) → ANP history profiles → process v0 historical fit (13 Nov) → P-REG-1 build (20 Nov) → **freeze Fri 27 Nov** → scoring as months are published | **Tue 6 Oct** (logger) | **0 on the freeze date** | Freeze anyway with baselines + the simplest defensible model; never move the freeze past 30 Nov |
| **CP5** | Sobol ranking on current priors (8 Oct) → verification tiers 1–3 (W2–W6) → tier 4 prices (W13–W14) → LCOB v0 (8 Jan) → MC/Sobol (15 Jan) → supply curve v0 (22 Jan) → Gate 4 (29 Jan) | **Thu 8 Oct** | ≈ 1 week | Report LCOB with explicit S caveats and drop the supply curve to "internal" |
| **CP6** | MapBiomas + SEADE/IBGE registered (W1) → H3 cane panel (W5) → Huff (W9) | Wed 7 Oct (registration) | 2 weeks | Compute is small (≈1–2 min/year); low risk |
| **CP7** | OSRM spike (W6, timeboxed at 4 h) → road OD matrix (W9) → Huff (W9–W10) | Mon 9 Nov | 1 week | Use the OSRM car profile; Euclidean distance only as a *labelled* sensitivity run, never as the main input (CLAUDE.md rule) |
| CP8 (off path) | NDA requests (6 Oct) → university legal office (verify which office; possibly Inova UNICAMP) → signed NDAs → partner data | Tue 6 Oct | n/a by design | Partner data only validates results; no gate depends on it |
| CP9 (off path) | LUPA cooperation agreement (R7) with CATI/IEA | Tue 6 Oct | n/a | Expected to finish after the window; IBGE PPM + livestock points cover v0 |

**The critical path proper is CP2 + CP3 + CP4.** These are the three things that cannot be bought back with extra hours later: the harvest window, the census that feeds calibration, and the pre-registration date.

---

## 4. Monthly gates

Gates are adapted from `docs/19` (Gate 0 → Gate 1 here; docs Gate 1 → Gate 3; docs Gate 2 → Gate 2 + P-REG; docs Gate 3 → Gate 4). Each gate is checked on Friday with prompt **P10** and written to `docs/status/GateN_<date>.md`. Fail actions are fixed in advance: **a failed evidence criterion postpones modelling work, never evidence work.**

### Gate 1: "Evidence launched" (Fri 30 Oct 2026, end of W4)
| ID | Pass criterion | Fail action |
|---|---|---|
| G1.1 | 8/8 LAI requests filed (R1–R6, R8, new R9) with protocol numbers in `registry/lai_requests.csv` and in the `docs/07` tracking table; R7 cooperation request sent | Same day: file what is missing |
| G1.2 | Written confirmation from the LABIOEN lead **and** ≥ 1 mill (São Martinho default) for E1 + E2; ≥ 1 E2 sample in the lab; E1 t0 date fixed ≤ 13 Nov | Escalate to the CP2B coordinator within 24 h; W5 model hours are reassigned to securing samples |
| G1.3 | 100 % of held datasets registered (`status: have`, sha256, provenance, license or "unknown (verify)"); `python -m engine.registry validate --strict` exits 0; CI green in the new repo | Hygiene before anything else on Mon of W5 |
| G1.4 | SP certified-unit list complete (count *n* recorded as **V** from the ANP source); ≥ 60 % of units have ≥ 1 report downloaded and hashed; the extractor has run on all downloaded reports | < 40 %: activate the R9 follow-up, write to the inspection firms, check archived copies (verify availability); Huff moves to W10 |
| G1.5 | ≥ 12 of the top-20 leverage parameters (W1 ranking) are V (≈ docs/19 Gate 0's "≥ 60 % of core"); every conflict found is logged in `docs/21` §1 | W5 verification hours are doubled; the process fit runs with ranges only |
| G1.6 | A fresh clone on a second machine or a fresh WSL distro passes `uv sync && pytest` and `docker compose up -d` per `docs/04` | Fix `docs/04` in W5 (≤ 3 h) |

### Gate 2: "Evidence base v1 + frozen prediction" (Fri 27 Nov 2026, end of W8)
| ID | Pass criterion | Fail action |
|---|---|---|
| G2.1 | RenovaBio: ≥ 80 % of SP units have ≥ 1 report; `cane_processed` has page + verified quote for ≥ 70 % of units; audit done (10 % random + 100 % of values > 3 MAD); audited error rate ≤ 2 % of values | Error > 2 %: fix the rules, re-extract and re-audit before Huff (W9 slips). Coverage < 80 %: calibrate on what exists and state the coverage in docs/09 |
| G2.2 | Facilities: 100 % of RenovaBio units and ANP ethanol plants in SP map to a CNPJ-keyed facility; ≤ 5 % unresolved, each with a documented reason | Unresolved units are excluded from calibration and listed |
| G2.3 | H3 cane panel: 18/18 years (2008–2025); rescaled totals equal the municipal totals; mismatch list produced (municipalities with IBGE cane but no MapBiomas pixels, and the reverse); scale-factor outliers flagged | Log the gaps in `docs/21`; affected municipalities get an explicit fallback rule |
| G2.4 | **P-REG-1 frozen before 1 Dec 2026 00:00 BRT**: SHA-256 of the frozen folder recorded on an external timestamped service + emailed to two witnesses | No fail option: freeze whatever exists (baselines + simplest model) |
| G2.5 | Lab: E1 t0 done; E2 ≥ 4 biweekly samples (or every sample possible before the crush ended); decision recorded on stocking material for E3/E4 | Record what was lost; move E1/E2 to the 2027/28 harvest in the Feb plan |
| G2.6 | LAI: every answer logged; every refusal or partial answer appealed within 10 days | File the appeal the same day |
| G2.7 | ≥ 40/60 parameters are V **or** carry a documented "not found in <doc>"; 100 % of the top-20 are V or have been replaced | Parameters still S/K enter only as sensitivity ranges |
| G2.8 | Process v0 reproduces the **direction and timing** of the off-season drop at Costa Pinto and the partial off-season output at Narandiba on historical months (docs/19 Gate 2, qualitative); MAE on `util_pct` reported | The freeze still happens; the protocol notes the weak fit |

### Gate 3: "Calibrated supply panel `v0.1.0`" (Fri 18 Dec 2026, end of W11)
| ID | Pass criterion | Fail action |
|---|---|---|
| G3.1 | Held-out mill cane MAPE < 15 % under leave-region-out validation (H1.1), or a documented reason why not | Release `v0.1.0` as facilities + cane H3 panel only; Huff work continues in W14 |
| G3.2 | Σ mill crush vs UNICA SP totals within the tolerance **pre-declared in docs/09 in W9 before fitting**, for every year with UNICA data | Report the deviation by year; investigate border flows (MG/PR/MS) |
| G3.3 | `mill_year` and `mill_month` carry p05/p50/p95 for cane, vinasse (generated / applied / available, kept separate), filter cake and straw | Release without intervals, labelled `v0.1.0-pre` |
| G3.4 | `exports/v0.1.0/` built by `engine.export.bundle`; the manifest holds the git commit, parameter hash and source sha256s; **zero** partner data (automated grep for `data/private` paths and partner CNPJs) | Block the release |
| G3.5 | 100 % of sources read by the v0.1.0 pipeline are registered with sha256 (prompt P11) | Block the release |
| G3.6 | Huff uses road-network OD (OSRM); no Euclidean distance in the main run | Block the release |

### Gate 4: "Evidence-backed economics" (Fri 29 Jan 2027, end of W17)
| ID | Pass criterion | Fail action |
|---|---|---|
| G4.1 | ≥ 80 % of parameters used in any reported number are V; the rest carry an explicit caveat (traceability report) | Replace or caveat them; the supply curve stays internal |
| G4.2 | LCOB p05/p50/p95 for all candidate mill sites × S0/S1/S4 (S2 where manure data passed QA); Sobol ranking documented (docs/19 Gate 3) | Report S0/S1 only |
| G4.3 | LCOB v0 compared with the EPE / FIESP / IEA ranges, **V versions only**; every deviation explained | Leave the comparison out of the release notes |
| G4.4 | Supply curve v0 with Monte Carlo bands; Huff vs nearest-mill (network Voronoi) sensitivity documented | Label it "internal, not for circulation" |
| G4.5 | P-REG-1 interim scoring for every target month published so far (CRPS, 90 % coverage, skill vs baselines), or "0 months published" logged with the lag evidence | n/a (the result is reported as it stands) |
| G4.6 | P1 full draft (all sections, figures from `v0.1.0`) in `manuscripts/P1_mill_panel/` | Circulate methods + data sections only |

### Close-out (Fri 5 Feb 2027, W18)
`v0.2.0` bundle + GitHub Release; `docs/19` rewritten as the Feb–Jul 2027 roadmap; partner debrief using aggregated results only; P1 draft sent to co-authors.

---

## 5. Week-by-week plan

Format per week: **Goal** · **Checklist** (each item is verifiable and names an output path or a person) · **Deliverables** · **Touches** (engine modules / docs). "Prompt Pn" refers to §12.

---

### W1 · Mon 5 Oct – Fri 9 Oct 2026 · 34 h (E 26 / M 4 / W 4)
**Goal:** launch every long-lead item (LAI, lab, partners, NDAs), start the ANP vintage log and register everything already held.

#### Mon 5 Oct: "Things that take 20+ days go out today"
- [ ] 08:30 · Confirm the code state. Run `git status`, `uv run pytest -q` and list the files in `src/engine/*/`. Compare with the v0 module list in the brief. On 2026-10-04 the checked-out tree showed only `registry.py`, `ingest/inventory.py`, `ingest/pdftext.py` (untracked) and `supply/raster_h3.py`. Write the actual inventory to `docs/status/W01.md` §Code state.
- [ ] Decide D1 and create the private repo `aikiesan/sp-biomethane-engine`; push the seed + code (ACCESS_AT_HOME Option C) so `.github/workflows/ci.yml` runs.
- [ ] Fill the FAPESP project number "[nº]" in the `docs/07` template; save the per-request texts to `docs/lai/R1.md` … `docs/lai/R9.md`.
- [ ] **File on Fala.BR (federal):**
  - R1 ANP ethanol per plant.
  - **R2 ANP biomethane per plant**, extended with three added questions: (a) the **publication calendar/lag** of the monthly plant data; (b) the definition of `util_pct` (biogas vs biomethane capacity basis); (c) whether zero months mean shutdown or missing reports (C6).
  - R3 MAPA SAPCANA.
  - **R9 (new): ANP copies or index of RenovaBio certification reports / RenovaCalc data for SP units**, with an aggregated alternative. This hedges CP3. Whether ANP holds these files is itself to verify.
- [ ] Record protocol numbers, sent date, due date (+20) and extended date (+30) in a new `registry/lai_requests.csv` and in the `docs/07` table. Add calendar reminders for the due dates and for "appeal deadline = answer date + 10 days".
- [ ] Email the **LABIOEN lead**: E1 + E2 proposal (1-page extract of `docs/17`) with the harvest-window constraint stated plainly: *t0 by 13 Nov, last E2 sample ≈ 24–27 Nov*. Ask for a 30-min meeting in W2 and whether the lab is accessible during the year-end recess (needed for E1 t1/t2).
- [ ] Email the **PPBIOEN coordinator**: E3 protocol summary; ask whether vinasse / filter cake / manure can be **stocked now** (cold room/freezer, verify feasibility) for off-season pilot runs.
- [ ] Email the **UNIFAL CEMARA contact**: offer two concrete scopes (E2 replicate COD/SO₄/K analyses, or E6 BMPs on filter cake/straw) and ask what is possible before 27 Nov.

#### Tue 6 Oct: "State requests, partners, NDAs, ANP vintage"
- [ ] **File on SIC.SP:** R4 CETESB vinasse plans (PAV, P4.231), R5 CDA/SAA livestock (GEDAVE), R6 Sabesp/ARSESP sludge, R8 ARSESP TUSD-Verde. Log them in `registry/lai_requests.csv`.
- [ ] R7: email CATI/IEA asking for a cooperation agreement (termo de cooperação) for LUPA 2016/17 microdata; log the contact in `data/private/contacts_log.csv`.
- [ ] Partner emails built from `templates/PARTNER_DATA_REQUEST.md` (one message per partner, wish-list + NDA scope + "validation only, aggregated publication"):
  - **São Martinho**: monthly crush/ethanol per unit, vinasse composition, Santa Cruz plant data, **plus access to fresh filter cake + vinasse for E1/E2 and the expected end date of the 2026/27 crush at that unit**.
  - **Comgás**: confirm the network/city-gate layers CP2B holds; TUSD-Verde values; aggregated results of Chamada Pública 01/2025.
  - **Equinor**: hurdle IRR/WACC conventions; anonymized international cost benchmarks.
- [ ] Contact the university office that handles NDAs (verify which: possibly Inova UNICAMP) for the NDA template and expected processing time; log the answer in `docs/21` §Risks.
- [ ] **ANP vintage logger v0.** Download the current ANP biomethane plant monthly file (source `anp_biomethane_plants`) to `data/raw/anp_biomethane_monthly/2026-10-06/` and compute its sha256. Create `evidence/anp_vintage_log.csv` with columns `checked_on, latest_month, n_rows, sha256, months_changed_vs_prev`. Compare with the PILAR-2b snapshot in `evidence/`, which ends 04/2026, and record the latest month ANP actually has. This gives the first empirical lag estimate.

#### Wed 7 Oct: "Register everything already held"
- [ ] Run `python -m engine.ingest.inventory <folder> --out data/interim/inventory/<name>_2026-10-07.csv --yaml data/interim/inventory/<name>_stubs.yaml --module <module>` for each held folder: mill coordinates; MapBiomas cane 30 m 2008–2025; SEADE/IBGE planted vs harvested; UNICA SP 2008–2018; gas transport/distribution/city gates/injection points; rail; transmission; roads; livestock points; exclusion layers; PILAR-2b FDE; energy and fuel prices; lab characterization references.
- [ ] Merge the stubs into `registry/sources.yaml` with `status: have`, provenance (who produced it, when, from what) and license (or `unknown (verify)`). Mark private/NDA items so they never leave `data/private/`.
- [ ] Run `dvc init`, take decision D2 and add the remotes; `dvc add` the raw folders; flip ADR-0003 to Accepted with the remote choice.
- [ ] Extend `registry/parameters.csv` with the columns `page, quote, verified_by, verified_on, conditions, price_year, currency` (docs/08 §4). Add a validator rule so that **V without page + quote is an error**. Commit, then run `python -m engine.registry validate --strict`.

#### Thu 8 Oct: "RenovaBio census starts; let the model rank the verification queue"
- [ ] Get the ANP list of RenovaBio certificates in force (source `anp_renovabio_cert_panel`). Filter SP and build `registry/renovabio_units.csv` with columns `cnpj, unit, municipality_ibge, route, inspection_firm, cert_valid_from/to, consultation_url, status (listed/located/downloaded/extracted/audited), sha256`. Record *n*; it replaces "~128 [S]".
- [ ] Per-firm reconnaissance (Benri, Accenture, SGS, KPMG, Verifit, Instituto Totum): how each publishes reports (static links, JS pages, S3, or removal after the consultation period). Write the findings into `docs/06` §1.1. **No guessed URLs**: anything not found is marked `not_found`.
- [ ] **Verification ranking (model ranks, evidence decides).** Run the existing LHS Monte Carlo + Sobol (`economics/montecarlo.py`) on the *current S/K priors* for one reference mill plant. Write `data/interim/verification_ranking_W01.csv` and create `registry/verification_queue.csv` with columns `param_id, sobol_ST, flag, primary_doc, source_id, target_week, status`. Label the run "ranking only, not a result" in the run manifest.

#### Fri 9 Oct: "Primary documents in hand + first weekly release"
- [ ] Download the tier-1/2 primary documents to `data/raw/<source_id>/2026-10-09/` with sha256: EPE NT 2025-08 (+ Resumo), NT 2023-07, NT 2023-05; CNPE Res. 4/2026; ANP Res. 995, 996, 1.006/2026 and 987/2025; ARSESP Del. 744/2017, 1.342/2022, 1.765/2025; Decreto 12.614/2025. Update the `sources.yaml` entries (`accessed`, `sha256`, `local_path`).
- [ ] Confirm decisions D1–D6 and record them in `docs/99_SESSION_NOTES.md`.
- [ ] Friday review (prompt P9). Write `docs/status/W01.md` covering protocol numbers, replies received, *n* SP units, the first ANP lag reading and the top-20 queue. Push and tag `w01`.

**Deliverables W1:** 8 LAI protocols (+ R7 contact); 6 partner/lab emails + NDA enquiry; `evidence/anp_vintage_log.csv` (first row); held datasets registered; `registry/renovabio_units.csv` (listed); `registry/verification_queue.csv`; tier-1 PDFs hashed.
**Touches:** `registry.py` (validator rule), `ingest/inventory`, `economics/montecarlo` (ranking only), `docs/06`, `docs/07`, `docs/08`, `docs/17`, `docs/21`, ADR-0003.

---

### W2 · Tue 13 Oct – Fri 16 Oct 2026 (Mon 12 holiday) · 26 h (E 20 / M 3 / W 3)
**Goal:** lock the harvest-window sampling plan, start bulk RenovaBio downloads, finish verification tier 1.
- [ ] Tue: follow up every W1 email without a reply (LABIOEN, PPBIOEN, UNIFAL CEMARA, São Martinho, Comgás, Equinor, NDA office); log in `data/private/contacts_log.csv`.
- [ ] Meeting with the LABIOEN lead and the São Martinho contact (30–45 min). Output: `docs/17` §E1/E2 "2026 harvest-window protocol v1" covering sampling dates, volumes, cold chain, who collects, E1 silo variants (± compaction, ± additive, ± straw) and the timepoints t0…t7 with dates. A copy goes to `data/private/lab/E1/protocol_v1.md`. Record the mill's expected crush end date (verify).
- [ ] PPBIOEN decision on stocking E3/E4 material (what, how much, storage method). One line in `docs/17` §E3.
- [ ] RenovaBio downloaders: adapters for the first 2 firms in `src/engine/ingest/renovabio.py` (or `renovabio_harvest.py`). Unit tests run against saved HTML fixtures in `tests/fixtures/` (no network in tests). Downloads go to `data/raw/renovabio_cert_reports/<cnpj>/<date>/`. **Target: ≥ 40 % of units downloaded.** (Prompt P4.)
- [ ] Verification **tier 1** (prompt P3), about 8–10 parameters: `capex_epe`, `opex_epe` (scope, C5), `lcob_epe_sucro` (EPE NT 2025-08/2023-07); `mandate_volume` (CNPE 4/2026); the CGOB unit (ANP 995/2026, as a new parameter row); `icms_sp` (decree number). Write change-log lines in `docs/08` §7.
- [ ] Downloads + sha256: UNICA biweekly SP 2019–2026 (`unica_data`, extending the held 2008–2018; check terms of use), ANP ethanol producers (`anp_ethanol_producers`), SAPCANA (`mapa_sapcana`), BNDES operations CSV (`bndes_operacoes`).
- [ ] Restore the PILAR-2b dump into schema `pilar2b` (PostGIS 5433); confirm the municipal boundaries + IBGE 7-digit codes; register the source.
- [ ] Update the "fase atual" and watch list in `templates/ROUTINE_RADAR_BIOMETANO_PROMPT.md` (and the deployed routine) to: this plan; CNPE 2027 target (due ≈ 1 Nov, verify); renewal of the SP ICMS 12 % after 31 Dec (verify); new ANP monthly releases; locations of RenovaBio reports.
- [ ] Fri: prompt P9 → `docs/status/W02.md`; push; tag `w02`.

**Deliverables:** protocol v1 signed off by email; ≥ 40 % of reports downloaded; tier-1 parameters V; raw downloads registered.
**Touches:** `ingest/renovabio`, `registry`, `docs/06`, `docs/08`, `docs/16`, `docs/17`.

---

### W3 · Mon 19 Oct – Fri 23 Oct 2026 · 34 h (E 24 / M 6 / W 4)
**Goal:** sampling starts, RenovaBio extraction runs at scale, verification tier 2 (process), P-REG protocol drafted.
- [ ] E2 sample #1 collected and in the lab (date per protocol); metadata in `data/private/lab/E2/samples.csv`. E1 filter-cake collection date confirmed.
- [ ] Remaining downloaders (all 6 firms or a manual fallback with sha256). **Target ≥ 70 % downloaded.**
- [ ] Run the rule-based extractor + verbatim-quote verifier over every downloaded report. Raw output goes to `data/interim/extraction_raw/`; first unaudited `data/interim/mill_year_renovabio_v0.parquet`. LLM extraction is used **only** for fields the rules miss (prompt P5).
- [ ] Independent validation documents: download and register company reports (São Martinho results/sustainability, Raízen, Cocal). Later they serve as an independent check on the RenovaBio extraction (docs/13 "Independent").
- [ ] Verification **tier 2 (process)**, about 12 parameters: `vin_cod`, `vin_so4`, `vin_k2o`, `vin_ph`, `cod_removal`, `codig_bmp`, `olr_max_cstr`, `fc_ts_vs`, `fc_bmp`, `hrt_cstr`, `cod_so4_crit`, `bmp_fullscale`, from Volpi 2021, Janke 2015/2020, Fuess 2018/2024 and Moraes 2015. Reorder by the W1 Sobol rank.
- [ ] Draft `prereg/P-REG-1/protocol.md` v0 (spec in §6).
- [ ] Link-rot check over all 81 `sources.yaml` URLs. Blocked gov sites are checked by hand; results go into `notes`.
- [ ] Fri: P9 → `docs/status/W03.md`; tag `w03`.

**Deliverables:** E2 #1; ≥ 70 % of reports; `mill_year_renovabio_v0.parquet` (unaudited); about 20 parameters V cumulative; P-REG protocol v0.
**Touches:** `ingest/renovabio`, `ingest/pdftext`, `calibrate/metrics` (protocol design), `docs/08`, `docs/13`.

---

### W4 · Mon 26 Oct – Fri 30 Oct 2026 · 34 h (E 22 / M 8 / W 4) · **Gate 1**
**Goal:** facilities registry v0, normalized CAPEX table, first LAI answers, Gate 1.
- [ ] LAI: first due dates (≈ Mon 26 Oct for the 5 Oct filings; verify the counting rule and the weekend roll-over). Log answers or extensions in `registry/lai_requests.csv`. Received data → `data/raw/lai_<ID>/<date>/` + sha256 + registry entry. Prompt P7 drafts any appeals.
- [ ] Facilities registry v0 in a new `src/engine/ingest/facilities.py`. Matching order: CNPJ exact (14 digits; 8-digit root = group), then fuzzy name + municipality, then LLM adjudication proposal, then **human decision**. Outputs: `data/interim/facilities_v0.parquet`, `data/interim/facilities_match_log.csv` and an unresolved list.
- [ ] Normalize `registry/projects_capex.csv`: capacity basis (harvest-day vs annual ÷ 365), biogas vs biomethane, scope (pipeline, CO₂), price year, currency. Log C2, C3 and C8 in `docs/21`. Join the BNDES operations by CNPJ.
- [ ] E2 sample #2; **E1 t0 this week if possible** (hard latest 13 Nov).
- [ ] Verification tier 2 continued: ARSESP 1.765 (TUSD-Verde structure), ANP 1.006 (spec; HHV basis for the CLAUDE.md constant).
- [ ] Reproducibility test on a second machine or a fresh WSL distro (G1.6).
- [ ] **Fri: Gate 1** (prompt P10) → `docs/status/Gate1_2026-10-30.md`; tag `gate1`.

**Deliverables:** `facilities_v0.parquet`; normalized `projects_capex.csv`; Gate 1 report.
**Touches:** `ingest/facilities` (new), `registry` (projects_capex), `economics/capex` (input only), `docs/04`, `docs/07`, `docs/21`.

---

### W5 · Tue 3 Nov – Fri 6 Nov 2026 (Mon 2 Finados) · 27 h (E 18 / M 6 / W 3)
**Goal:** handle LAI answers and appeals, audit the extraction, build the H3 cane panel.
- [ ] LAI: extended due dates (≈ 4–5 Nov, verify). Every refusal or partial answer gets a **recurso de 1ª instância within 10 days** that cites the aggregated alternative (prompt P7 → `docs/lai/<ID>_recurso_<date>.md`).
- [ ] CNPE 2027 target (due ≈ 1 Nov 2026 [S], verify). If it is published, download the primary act and verify a new `mandate_volume_2027` row; update `docs/16`. If not, log "not published as of <date>".
- [ ] **Audit** (prompt P6): reproducible 10 % random sample + 100 % of values > 3 MAD → `data/interim/audit/renovabio_audit_2026-11-04.csv`. Fill the `auditor_ok` column by hand; compute the error rate by variable and by firm; fix extractor rules; re-run.
- [ ] H3 cane panel. For each year 2008–2025, run `python -m engine.supply.raster_h3 <mapbiomas_YYYY.tif> --class-code <sugarcane code — verify in the legend of the collection held> --year YYYY --res 8 --out data/interim/cane_area_h3r8/YYYY.parquet` (≈1–2 min/year). Then rescale with `supply/grid.py` using SEADE/IBGE harvested/planted × yield. Outputs: `data/processed/cane_t_h3r8_2008_2025.parquet` and `data/processed/diagnostics/cane_scale_factors.csv`.
- [ ] E2 sample #3.
- [ ] Fri: P9 → `docs/status/W05.md`.

**Deliverables:** appeals filed; audit round 1 + error rate; H3 cane panel 18/18 years.
**Touches:** `supply/raster_h3`, `supply/grid`, `ingest/renovabio`, `docs/07`, `docs/09`, `docs/16`.

---

### W6 · Mon 9 Nov – Fri 13 Nov 2026 · 34 h (E 18 / M 13 / W 3)
**Goal:** audited `mill_year` v1, process v0 fitted on ANP history, OSRM spike, **E1 hard deadline**.
- [ ] **Hard deadline Fri 13 Nov:** E1 filter cake in silos (t0 analyses: TS, VS, VFA, pH, BMP started) confirmed by the LABIOEN lead.
- [ ] `data/processed/mill_year_renovabio.parquet` v1 (post-audit) + coverage matrix `data/processed/diagnostics/renovabio_coverage.csv` (unit × year × variable). Ratio flags (ethanol/cane outside 70–90 L/t; vinasse/ethanol < 8 or > 16 L/L) go to `docs/21` as C1 evidence.
- [ ] ANP history: run `calibrate/anp.py` for per-plant monthly profiles of the 4 target plants (Costa Pinto, Narandiba, Santa Cruz, Paraguaçu) and the other SP plants. Write the **zero-month rule** into `docs/13` §3.2 (reported zero vs missing vs shutdown; the R2 answer refines it).
- [ ] Process v0 historical fit with `process/cstr.py` + `process/strategies.py`: S0 for Costa Pinto, S1 for Narandiba, using UNICA monthly crush shares for timing. Only V values or explicit S ranges are allowed. Outputs: `nb/030_process_anp_fit.ipynb` (outputs stripped) and `data/processed/calibration/process_v0_fit.parquet`.
- [ ] **OSRM spike (timebox 4 h):** OSM Sudeste extract (`osm_sudeste`; verify the Geofabrik subregion) + `osrm-backend` in Docker; a 1,000-cell × 10-mill table; record RAM and run time in ADR-0006 (routing engine choice, Proposed).
- [ ] Verification **tier 3**: IPCC 2019 Vol. 4 Ch. 10 (`b0_*`, manure VS; C4), FIESP 2024 (`lcob_fiesp*`), BNDES TD 159.
- [ ] E2 sample #4 if the crush continues.
- [ ] Fri: P9 → `docs/status/W06.md`.

**Deliverables:** E1 t0; `mill_year` v1 + coverage matrix; process v0 fit; ADR-0006 draft.
**Touches:** `calibrate/anp`, `process/cstr`, `process/strategies`, `supply/seasonality`, `docs/10`, `docs/13`, ADR-0006.

---

### W7 · Mon 16 Nov – Thu 19 Nov 2026 (Fri 20 Consciência Negra) · 27 h (E 10 / M 13 / W 4)
**Goal:** build the P-REG-1 predictions and baselines; facilities registry v1.
- [ ] `prereg/P-REG-1/information_set.yaml` lists every input with `source_id` + sha256. **Public data only**; partner information is excluded and the exclusion is declared.
- [ ] Predictions → `prereg/P-REG-1/predictions.parquet` (`cnpj, plant, month, q05, q25, q50, q75, q95, p_zero` for `util_pct` and `vol_biogas_m3d`):
  - Costa Pinto: S0-like.
  - Narandiba: S1-like.
  - Santa Cruz and Paraguaçu (both still at ~0 % in the PILAR-2b snapshot): ramp-up hurdle model. P(output > 0 by month) plus a conditional distribution taken from **observed analog ramp-ups** (Costa Pinto from 2024-08; Narandiba from 2025-08).
- [ ] Baselines → `prereg/P-REG-1/baselines.parquet`: seasonal naive (same month last year), plant climatology, persistence (last published month).
- [ ] Back-test sanity check (train ≤ Mar 2025, test Apr 2025 → latest published) → `prereg/P-REG-1/backtest.md`. This is **not** part of the claim.
- [ ] Send the protocol to 1–2 reviewers (CP2B coordinator/advisor and one partner-lab colleague) on Mon, asking for comments by Mon 23 Nov.
- [ ] Facilities registry v1: SAPCANA status by year (R3, if received) → `data/processed/facilities.parquet`.
- [ ] Thu: P9 → `docs/status/W07.md`.

**Deliverables:** P-REG-1 package ready to freeze; facilities v1.
**Touches:** `calibrate/anp`, `calibrate/metrics`, `process/*`, `supply/seasonality`, `ingest/facilities`, `docs/13`.

---

### W8 · Mon 23 Nov – Fri 27 Nov 2026 · 34 h (E 16 / M 10 / W 8) · **P-REG-1 freeze + Gate 2**
**Goal:** freeze the prediction before December, close the harvest window, pass Gate 2.
- [ ] Mon–Wed: incorporate the reviewers' comments (log every change in `protocol.md` §History).
- [ ] **Thu 26 Nov (Fri 27 at the latest, 18:00 BRT): freeze.** Copy the package to `prereg/P-REG-1/frozen/` and write `SHA256SUMS`. Create the git tag `prereg-1` and push. Make the external timestamped deposit (D5). Email the hash to two witnesses. From now on nothing under `frozen/` is ever edited (pre-commit hook blocks it).
- [ ] E2 final sample (#5), or the last one before the crush ends; confirm the E3/E4 material stock exists (`docs/17` §E3 line with quantities).
- [ ] RenovaBio final push: ≥ 80 % of units. For units still missing: R9 follow-up, emails to the firms, archived copies (verify availability; record provenance + sha256).
- [ ] **Fri: Gate 2** (prompt P10) → `docs/status/Gate2_2026-11-27.md`; tag `gate2`.

**Deliverables:** P-REG-1 frozen and timestamped; harvest-window samples complete; Gate 2 report.
**Touches:** `prereg/`, `ingest/renovabio`, `docs/13`, `docs/17`.

---

### W9 · Mon 30 Nov – Fri 4 Dec 2026 · 33 h (E 8 / M 21 / W 4)
**Goal:** road-network OD matrix and frequentist Huff calibration.
- [ ] **Pre-declare before fitting** in `docs/09` §3, committed with the hash recorded: the leave-region-out design (RA or EDR regions), the tolerance for Σ mills vs UNICA, `d_max`, and the train/test split.
- [ ] OSRM OD: centroids of H3 r8 cells with cane in any year → mill sites within `d_max`. Outputs: `data/interim/od/h3r8_to_mills.parquet` and a road/straight-line detour-ratio diagnostic. Code goes in a new `src/engine/supply/od_osrm.py` with a fixture test.
- [ ] Huff fit (`supply/huff.py`, frequentist) on the training mills; leave-region-out CV → `data/processed/calibration/huff_cv.parquet` (MAPE, bias by region).
- [ ] ANP vintage check + scoring of any newly published target month (prompt P8) → `prereg/P-REG-1/scores/`.
- [ ] E1 t1 (≈ +1 month) by LABIOEN, if due.
- [ ] Fri: P9 → `docs/status/W09.md`.

**Deliverables:** OD matrix; Huff CV table.
**Touches:** `supply/huff`, `supply/od_osrm` (new), `calibrate/metrics`, `docs/09`, `docs/12`.

---

### W10 · Mon 7 Dec – Fri 11 Dec 2026 · 33 h (E 8 / M 21 / W 4)
**Goal:** residue panel with uncertainty and monthly profiles.
- [ ] Huff intervals by **region-block bootstrap** (interim substitute for the Bayesian posterior) → `data/processed/calibration/huff_bootstrap.parquet`.
- [ ] Sensitivity: nearest-mill-by-road (network Voronoi) allocation; difference table in `docs/09` §Diagnostics.
- [ ] Residues Monte Carlo (`supply/residues.py`) → `mill_year` with p05/p50/p95 for vinasse **generated / applied / available (kept separate)**, filter cake and straw. Use the R4 CETESB PAV data if received; otherwise log C1 as open.
- [ ] Monthly shares (`supply/seasonality.py`) from UNICA biweekly → `data/processed/mill_month.parquet`.
- [ ] Livestock points: QA against IBGE PPM municipal herds → `data/processed/diagnostics/livestock_vs_ppm.csv` (only for the S2 manure base-load; other non-cane substrates deferred).
- [ ] LAI: second-round answers and appeals.
- [ ] Fri: P9 → `docs/status/W10.md`.

**Deliverables:** `mill_year`/`mill_month` with intervals; Voronoi sensitivity; livestock QA.
**Touches:** `supply/huff`, `supply/residues`, `supply/seasonality`, `docs/09`.

---

### W11 · Mon 14 Dec – Fri 18 Dec 2026 · 33 h (E 8 / M 15 / W 10) · **Gate 3 + `v0.1.0`**
**Goal:** release the calibrated supply panel before the recess.
- [ ] Build `exports/v0.1.0/` with `export/bundle.py`: `facilities.parquet`, `hex_supply.parquet` (cane residues), `mill_month.parquet`, `manifest.json`. Run the contract check against `docs/18` §2 and the automated "no partner data" check.
- [ ] Rewrite `docs/09_MODULE_SUPPLY.md` with the actual choices and diagnostics; set ADR-0004 to Accepted (or amend it).
- [ ] **Fri: Gate 3** (P10) → `docs/status/Gate3_2026-12-18.md`; GitHub Release `v0.1.0` (private repo).
- [ ] Recess handover: agree E1 t1/t2 dates with LABIOEN in writing; set reminders for the ANP vintage checks.

**Deliverables:** `v0.1.0`; supply method doc; Gate 3 report.
**Touches:** `export/bundle`, `docs/09`, `docs/18`, ADR-0004.

---

### W12 · Mon 21 Dec – Thu 24 Dec 2026 (Fri 25 Christmas; recess, verify) · 16 h (E 6 / M 2 / W 8)
**Goal:** low-intensity week: P1 methods text and registry hygiene.
- [ ] `manuscripts/P1_mill_panel/outline.md` + `methods.md` (census, extraction + quote verification, audit, H3 downscaling, Huff, uncertainty), assembled from `docs/08`, `docs/09` and the audit records.
- [ ] Hygiene sweep (prompt P11): every v0.1.0 input has sha256, license and accessed date.
- [ ] Licensing note for P1 redistribution (RenovaBio reports, UNICA, MapBiomas, SEADE) → `manuscripts/P1_mill_panel/data_licensing.md`. Unknowns are marked "(verify)".
- [ ] ICMS-SP 12 % (valid to 31 Dec [S], verify): check the digests and the official gazette for a renewal act.

**Deliverables:** P1 outline + methods; hygiene sweep clean; licensing note.
**Touches:** `manuscripts/P1_mill_panel/`, `registry/sources.yaml`, `docs/08`, `docs/09`, `docs/16`.

### W13 · Mon 28 Dec – Thu 31 Dec 2026 (Fri 1 Jan; recess, verify) · 13 h (E 6 / M 3 / W 4)
**Goal:** buffer week.
- [ ] Absorb any W9–W11 slippage (priority: Gate 3 FAILs).
- [ ] Tier-4 downloads (prices): MME Boletim Mensal GN, ANP fuel price survey, B3 CBIO series → `data/raw/...` + sha256.
- [ ] ANP vintage check (P8).

**Deliverables:** Gate 3 fixes closed (if any); tier-4 price files hashed; vintage log row.
**Touches:** `registry/sources.yaml`, `evidence/anp_vintage_log.csv`, `prereg/P-REG-1/scores/`.

---

### W14 · Mon 4 Jan – Fri 8 Jan 2027 · 32 h (E 12 / M 16 / W 4)
**Goal:** verified economics inputs and LCOB v0.
- [ ] ICMS status after 31 Dec → `icms_sp` gets `valid_from/valid_to` + scenarios (`docs/16`).
- [ ] Verification **tier 4 (market)**: `price_ng_ind`, `price_ng_molecule`, `price_diesel`, `price_cbio`. `price_bm_fob` (Argus, paid) stays **S → scenario only** unless access is obtained. `bndes_debt_share` is re-derived from the BNDES CSV as D-from-V.
- [ ] CAPEX: EPE anchor (V) + a **Brazil-only exploratory log-log fit** (`economics/capex.py`) on the normalized `projects_capex.csv`. Report *n* and label it exploratory; no international pooling.
- [ ] LCOB v0 (`economics/lcob.py`, `finance.py`, `revenue.py`) for all candidate mill sites × S0/S1/S4 (+ S2 where the livestock QA passed) → `data/processed/economics/lcob_v0.parquet`.
- [ ] E1 t2 (≈ +2 months) if the lab is open (verify).
- [ ] *Optional:* P-REG-2 (rolling origin) for months still unpublished. Only if P8 has already scored ≥ 1 month cleanly; it is labelled and scored separately.
- [ ] Fri: P9 → `docs/status/W14.md`.

**Deliverables:** market parameters V; `lcob_v0.parquet`; exploratory CAPEX fit note (n, caveats).
**Touches:** `economics/capex`, `lcob`, `finance`, `revenue`, `docs/11`, `docs/16`.

---

### W15 · Mon 11 Jan – Fri 15 Jan 2027 · 33 h (E 8 / M 20 / W 5)
**Goal:** Monte Carlo + Sobol on verified priors.
- [ ] LHS Monte Carlo (n ≈ 10⁴) + Morris + Sobol (SALib) via `economics/montecarlo.py` → `data/processed/economics/sobol_v0.parquet`.
- [ ] **Verification-shift table:** Sobol ranks with W1 S/K priors vs W15 V priors → `docs/status/verification_shift.md`. This is a reportable result about the evidence work itself.
- [ ] LCOB v0 vs EPE / FIESP / IEA ranges, **using only the V-verified versions**; deviations explained in `docs/11` §8.
- [ ] Go/no-go note for the **Bayesian Huff MVP** (PyMC at H3 r7). Default is **no-go** unless Gate 3 passed with margin and ≥ 10 h are free.
- [ ] Fri: P9 → `docs/status/W15.md`.

**Deliverables:** `sobol_v0.parquet`; verification-shift table; external-range comparison; Bayesian go/no-go note.
**Touches:** `economics/montecarlo`, `docs/11`.

---

### W16 · Mon 18 Jan – Fri 22 Jan 2027 · 33 h (E 6 / M 21 / W 6)
**Goal:** supply curve v0 for mill sites.
- [ ] Delivery costs:
  - Grid connection: distance from each mill to the nearest held network segment or city gate. The pipeline routing factor is flagged **D** and documented.
  - CNG trucking: OSRM distance to the nearest injection point or city gate.
  - TUSD-Verde: structure from ARSESP 1.765 (V); values from R8/Comgás if received, otherwise scenario.
- [ ] `siting/supply_curve.py` merit order with Monte Carlo bands. Overlays: 0.5 % (CNPE 4/2026, V), the 2027 target if published (V), NG parity, and parity + CGOB at 0 / 0.5 / 1.0 / 1.5 R$/m³ → `data/processed/siting/supply_curve_v0.parquet` + figure.
- [ ] Sensitivity: Huff vs nearest-mill allocation; ICMS scenario.
- [ ] `siting/facility_milp.py`: smoke run on one region only, **not reported**.
- [ ] Fri: P9 → `docs/status/W16.md`.

**Deliverables:** `supply_curve_v0.parquet` + figure (internal until Gate 4); allocation sensitivity table.
**Touches:** `siting/supply_curve`, `siting/facility_milp` (smoke only), `docs/12`.

---

### W17 · Mon 25 Jan – Fri 29 Jan 2027 · 33 h (E 8 / M 10 / W 15) · **Gate 4**
**Goal:** audit every reported number against the registry; finish the P1 draft.
- [ ] Traceability report: a script lists every parameter used by the v0.2 runs with its flag, source and page → `docs/status/traceability_v0.2.md` (G4.1).
- [ ] P-REG-1 interim report → `prereg/P-REG-1/interim_report_2027-01-29.md`: months scored, CRPS, 90 % coverage, skill vs baselines, vintage revisions observed, ANP lag measured from `evidence/anp_vintage_log.csv`.
- [ ] P1 full draft (`manuscripts/P1_mill_panel/`): results = coverage, audit error, H3 panel diagnostics, Huff validation, residue intervals.
- [ ] **Fri: Gate 4** (P10) → `docs/status/Gate4_2027-01-29.md`.

**Deliverables:** traceability report; P-REG-1 interim report; P1 full draft; Gate 4 report.
**Touches:** `calibrate/metrics`, `registry.py` (traceability script), `prereg/`, `manuscripts/P1_mill_panel/`, `docs/13`.

---

### W18 · Mon 1 Feb – Fri 5 Feb 2027 · 30 h (E 6 / M 6 / W 18) · **Close-out**
**Goal:** release `v0.2.0` and hand off to the Feb–Jul 2027 plan.
- [ ] `exports/v0.2.0/`: `lcob_results.parquet`, `supply_curve.parquet` (marked **preliminary**), manifest; GitHub Release notes.
- [ ] PILAR-2b: open an issue in `aikiesan/Pilar-2b` describing the `engine_release` contract (`docs/18` §3). Contract only, no implementation.
- [ ] Rewrite `docs/19` as the Feb–Jul 2027 roadmap: the §9 deferred list in priority order; E1 t3…t7; P-REG-1 scoring through the off-season months; full-season E2 (Apr–Nov 2027); LAI follow-ups; R7 LUPA.
- [ ] Partner debrief (São Martinho, Comgás, Equinor) using aggregated results only; send the P1 draft to co-authors with the authorship/data policy note (`docs/20`).
- [ ] Note in `docs/16` the ANP Res. 1.006/2026 transitional deadline for off-spec industrial sellers (9 Feb 2027 [S], verify), which falls just after the window.
- [ ] Fri: P9 → `docs/status/W18.md`; tag `v0.2.0`.

**Deliverables:** `v0.2.0` release; Feb–Jul 2027 roadmap (`docs/19`); PILAR-2b contract issue; P1 draft sent to co-authors.
**Touches:** `export/bundle`, `docs/16`, `docs/18`, `docs/19`, `docs/20`.

---

## 6. Pre-registered prospective prediction P-REG-1 (spec)

| Item | Specification |
|---|---|
| Question | Can a mass-balance model with documented off-season strategies predict the monthly output of SP mill-based biomethane plants **before** the data are published? (H2.1 as a prospective test) |
| Plants (CNPJ from `evidence/anp_biomethane_plants_latest_from_pilar2b.csv`) | Raízen-Geo Costa Pinto 45281972000130 · Cocal Narandiba 14788495000170 · Bioenergia Santa Cruz 51447607000155 · Cocal Paraguaçu Paulista 44191268000123 |
| Targets | Monthly `vol_biogas_m3d` and `util_pct` as published by ANP. The definition is confirmed through the R2 answer; if it stays unconfirmed, the protocol says so |
| Horizon | Every month **not yet published at freeze time** through **Mar 2027**. This includes elapsed but unpublished months, which is why the vintage log starts in W1 |
| Format | Quantiles q05, q25, q50, q75, q95 + `p_zero` per plant-month |
| Scores | CRPS (from quantiles), 90 % interval coverage, MAE of the median; **skill vs baselines** (seasonal naive, climatology, persistence) |
| Directional hypothesis (pre-declared, no numeric threshold) | Mean Dec 2026–Mar 2027 `util_pct` at Narandiba > at Costa Pinto |
| Vintage rule | Score against the **first-published** value; later revisions are logged and also scored as a secondary analysis |
| Zero months | Scored as reported; flagged separately where ANP or the operator clarifies (C6) |
| Information set | Public sources only, each with sha256 (`information_set.yaml`). Partner NDA information is **excluded**, so the result stays publishable |
| Freeze | Fri 27 Nov 2026 18:00 BRT at the latest. Git tag `prereg-1` + external timestamped deposit + hash emailed to two witnesses |
| Changes | None after the freeze. Any later prediction is a **separate** registration (P-REG-2) |
| Risk acknowledged | If the ANP lag is long, few or no off-season months are scorable by 5 Feb. Full scoring then lands in Apr–Jul 2027 and feeds paper P2 |

---

## 7. RenovaBio census pipeline (spec)

```
ANP certificate list (SP)  →  registry/renovabio_units.csv  [status: listed]
  → per-firm locator/downloader (6 adapters or manual + sha256)   [located → downloaded]
  → ingest/pdftext pages  →  rule-based extractor (ingest/renovabio)  [extracted]
  → LLM only for residual fields (schema: templates/extraction_schema_mill_year.json)
  → verbatim-quote verifier (reject if the quote is not on the stated page)
  → plausibility flags (70–90 L/t; vinasse/ethanol <8 or >16 L/L)
  → audit: 10 % random + 100 % > 3 MAD (human)                       [audited]
  → data/processed/mill_year_renovabio.parquet + coverage matrix
```
- **Weekly targets:** listed 100 % (W1) → downloaded ≥ 40 % (W2), ≥ 70 % (W3), ≥ 80 % (W8) → `cane_processed` quoted for ≥ 70 % of units (W8) → audit error ≤ 2 % (W8).
- **Throughput (estimate):** the extractor runs in minutes. The binding constraint is the **human audit** (≈ 2 min/value), so the audit sample size sets about 10 h of W5–W6.
- **Triangulation:** for units with public company reports (São Martinho, Raízen, Cocal), compare cane values as an independent check. This is not calibration data.
- **Hedges:** R9 LAI; emails to the inspection firms; archived copies with full provenance. A report that cannot be obtained is a *coverage* fact, reported in P1, never imputed silently.

---

## 8. Verification sprint mechanics (spec)

- **Queue:** `registry/verification_queue.csv`, ordered by the W1 Sobol total index (re-ranked in W15). Defaults follow `docs/08` §5 where a parameter has no Sobol rank (for example supply parameters).
- **Tiers and weeks:** T1 regulation/EPE (W2) · T2 process literature + ARSESP/ANP spec (W3–W4) · T3 IPCC/FIESP/BNDES/CAPEX announcements (W6) · T4 market prices (W13–W14). Supply parameters (`vin_gen`, `fc_gen`, `straw_*`) are verified in W3–W6 alongside the RenovaBio work.
- **Throughput (estimate):** 20–40 min per parameter when the document is in hand, which gives 8–12 parameters/week in W2–W6.
- **Counts today (registry, 2026-10-04):** 60 parameters (1 V, 7 D, 43 S, 9 K); 81 sources (2 V, 68 S, 5 K, 6 with no flag; the 6 must get a flag in W1). Re-check with `python -m engine.registry summary`. Targets: Gate 1 ≥ 12/20 top-leverage V; Gate 2 ≥ 40/60 V-or-documented-not-found; Gate 4 ≥ 80 % V among parameters actually used.
- **Rules:** LLMs locate and extract, never supply. Two V sources that disagree go to `docs/21` §1 with a resolution rule (SP-specific > national > international; recent > old; measured > estimated). Every change gets a line in `docs/08` §7.

---

## 9. Cut / deferred past Feb 2027

| Item | Status in window | Why deferred | Earliest restart |
|---|---|---|---|
| Hierarchical Bayesian CAPEX (ADR-0005) with international priors | Evidence prep only (normalized `projects_capex.csv`, BNDES ops) | Needs BIP TF4 / DEA / KTBL collection + normalization; too few verified Brazilian points by Jan | Mar 2027 |
| Bayesian Huff calibration (PyMC/brms) | Stretch goal, go/no-go W15; interim = frequentist + region-block bootstrap | Compute + modelling time; the bootstrap gives defensible intervals for v0.1 | Feb–Mar 2027 |
| Sentinel-2/Landsat harvest detection | Cut; state-level UNICA biweekly profile only | Large build; not needed for v0.1 | 2027 (before P1 final) |
| ADM1 (Level 2 process) | Cut | Needs PPBIOEN continuous data (E3) | After E3 runs |
| Full multi-period MILP with linearized process constraints, hub candidates, LNG mode | Smoke run only (not reported) | The supply curve v0 uses mill sites + merit order | Apr 2027 |
| Valhalla truck costing (axle/weight) | OSRM only | OSRM is enough for Huff distances | With the MILP |
| Non-cane substrates beyond the livestock QA (sludge/ETE/SINISA, OFMSW/CETESB RSU, SIF agro-industrial) | Register the LAI R6 output only | Not on the critical path for cane-based plants | Mar 2027 |
| PILAR-2b ingest side (`engine_release` source, migrations, API, pages) | Contract issue only | Separate repo/team; the bundle comes first | After `v0.2.0` review |
| Repo public + Zenodo DOI | Private | Policy: at first paper submission | P1 submission |
| Papers P2–P7 | P1 full draft only; P2 waits for P-REG-1 scoring | Evidence-first: the data paper is the natural first output | P2 after Mar 2027 data are published |
| Lab E3–E9 execution | E3 protocol + material stock only; E1 t3…t7 continue Feb–Jun 2027; full-season E2 Apr–Nov 2027 | Owned by the lab/pilot teams; the harvest calendar | Per lab |
| R7 LUPA microdata agreement | Started W1 | Agreement lead time | When signed |
| International partnerships (DBFZ, KTBL, IEA Task 37) | None | Capacity | Mar 2027 |
| System-level "digital shadow" dashboard | Manual scoring (P8) only | Build later on top of the P8 pipeline | After P2 |
| Yield prior from soils (Rossi 2017) / IPF refinement; ML gap-filling for uncertified mills | Cut | Huff + municipal rescaling covers v0.1 | 2027 |

---

## 10. Risk register (specific to Oct 2026 – Feb 2027)

P = probability, I = impact (H/M/L). "Watch" = the week the early signal is checked.

| ID | Risk | P | I | Early signal (watch) | Mitigation (pre-emptive) | Contingency |
|---|---|---|---|---|---|---|
| R01 | No lab or mill access before the crush ends | M | **H** | No reply from LABIOEN/São Martinho by Wed W2 | Day-1 emails; W2 meeting; UNIFAL CEMARA as a second lab | Any SP mill reachable through CP2B contacts; otherwise E1/E2 move to Apr 2027 and the Feb plan says so |
| R02 | Crush ends earlier than the end-Nov convention (rain/weather, mill decision) | M | H | Mill's stated end date (W2) | E1 t0 deadline 13 Nov, not 27 Nov | E2 series shortened; documented |
| R03 | LABIOEN closed during the recess, so E1 t1/t2 timepoints are missed | M | M | Recess dates (verify) + lab answer (W2) | Schedule t1/t2 around the recess in protocol v1 | Shift the timepoints; record the actual storage days (the φ_store curve uses actual days) |
| R04 | RenovaBio reports removed after the consultation period or behind JS | H | **H** | W1 reconnaissance | Start W1; R9 LAI; firm emails; archived copies | Calibrate on what exists; coverage reported; triangulate with company reports |
| R05 | LLM extraction errors or hallucinated values | M | H | Audit error > 2 % (W5) | Rules first; quote verifier mandatory; 10 % + outlier audit | Fix rules, re-extract, re-audit before Huff |
| R06 | ANP publication lag longer than the window | M | M | Vintage log (W1 onward) | Pre-register early (27 Nov) and include elapsed-unpublished months | Interim report in W17 with the months scored; full scoring in 2027 |
| R07 | ANP revises published months or changes the file schema | M | M | `months_changed_vs_prev` in the vintage log | Hash every vintage; the vintage rule is pre-declared | Score both vintages |
| R08 | LAI refusals or silence | H | M | Due dates (W4–W5) | Aggregated alternatives in every request; appeals ≤ 10 days | Not on the critical path; RenovaBio + open data cover v0.1 |
| R09 | NDA processing slow | H | L | Answer from the NDA office (W1–W2) | Partner data defined as validation-only | Ship without partner validation; add it in 2027 |
| R10 | Regulatory change mid-window (CNPE 2027 target ≈ 1 Nov; ICMS 12 % to 31 Dec; ANP 1.006 transition 9 Feb 2027) (all verify) | H | M | Daily digests; Monday triage | Parameters carry `valid_from/to`; scenarios, not point values | Re-run the LCOB scenarios in W14/W16 |
| R11 | Scope creep (Bayesian everything, Sentinel-2, MILP, ADM1) | H | H | Model hours > budget two weeks running | §9 cut list; WIP limit of 2 model threads; go/no-go notes | Drop the stretch goals first |
| R12 | Single-person bottleneck: illness, teaching, admin load | M | H | Two consecutive weeks < 25 h | ~15 % weekly slack; W12–W13 buffer; docs-first so Claude sessions resume cleanly | Cut order: supply curve v0 → MC/Sobol breadth → P1 results section |
| R13 | v0 code less complete than assumed (tree on 2026-10-04 shows few modules) | M | M | W1 Mon code-state check | Plan uses modules only from W5 onward | Re-sequence: evidence work continues; model weeks shift by ≤ 1 |
| R14 | OSRM build too heavy on the home WSL machine | L | M | W6 spike | Timeboxed spike; Docker memory per `docs/04` | Lab/server machine; OSRM car profile on a smaller extract |
| R15 | Facility identity ambiguity (CNPJ branches, mergers 2008–2025, idle mills) | M | M | Unresolved > 5 % (W4) | CNPJ root + branch rules; SAPCANA status; human adjudication log | Exclude from calibration, list in P1 |
| R16 | Licensing blocks redistribution in the P1 data paper (UNICA, report PDFs) | M | M | W12 licensing note | Publish derived values + citations, not source PDFs | Restricted-access deposit for the contested parts |
| R17 | Partner information leaks into P-REG or exports | L | **H** | Pre-commit and bundle grep checks | Information-set declaration; private DVC remote; automated checks | Withdraw and re-issue the bundle |
| R18 | Digest triage eats time | M | L | Triage > 30 min on Mondays | Hard 30-min cap; only "new number / new source / regulatory event" items are kept | Skip one week |
| R19 | Unresolved conflicts (C1–C8) stall verification | M | M | `docs/21` count rising | Log + resolution rule, never average | Gate counts "logged with rule" as handled for v0 |

---

## 11. Weekly rhythm

| When | What | Output |
|---|---|---|
| **Mon 09:00–10:30** | **Plan.** Digest triage (≤ 30 min, prompt P2); LAI tracker (P7); Monday plan (P1); pick 3 evidence goals + 1 model goal | `docs/status/WNN.md` §Plan |
| Mon 10:30 | ANP vintage check (P8, ≈10 min unless a target month appears) | `evidence/anp_vintage_log.csv` row |
| Tue–Thu mornings | **Evidence block:** downloads, verification (P3), emails/calls to labs, partners and agencies (gov sites and people respond in office hours) | registry diffs, contact log |
| Tue–Thu afternoons | **Model/code block** with Claude Code: small PRs, tests on fixtures, docs updated in the same change | commits |
| Wed (W2–W8) | Lab/partner touchpoint (15 min) during sampling weeks | `data/private/lab/*/samples.csv` |
| **Fri 14:00–17:00** | **Review + push + release notes** (P9): tests, validator, evidence metrics, risks, next week's top-5; gate check (P10) on gate Fridays | `docs/status/WNN.md`, tag `wNN` |
| Daily (5 min) | Skim the 00:55 and 01:50 BRT digests for **regulatory alerts only**; everything else waits for Monday | none |

**WIP rules:** at most 2 open model threads; evidence tasks are timeboxed instead. No model output is shown outside the repo before its gate. One PR = one transform + its doc update.

---

## 12. Claude Code session prompts (recurring tasks)

Paste them as written; the `WNN` / `<…>` placeholders are filled per session.

**P1: Monday plan**
```
Read docs/24_EXECUTION_PLAN_2026-10_2027-02.md (section for week WNN and the next gate),
docs/status/W<NN-1>.md, registry/lai_requests.csv, registry/verification_queue.csv,
registry/renovabio_units.csv and evidence/anp_vintage_log.csv. Report:
(a) this week's unchecked tasks, (b) overdue items from last week, (c) LAI / partner /
lab deadlines in the next 14 days with dates, (d) evidence metrics vs the next gate's
thresholds. Propose an ordered task list that fits <H> hours, evidence tasks first.
Do not write code in this session. Write the plan into docs/status/WNN.md §Plan.
```

**P2: Digest triage (daily routines)**
```
Here are this week's "CP2B Radar Biometano" and "Arquivo NIPE/CP2B" digests (search
Gmail for the subject tags, last 7 days). Classify each item as regulatory event /
new source / new number / noise. New source → draft a registry/sources.yaml stub with
status: get and confidence: S (never V). New number → add a row to
registry/verification_queue.csv pointing at the PRIMARY document; do not edit
parameters.csv. Regulatory events dated inside 2026-10-05..2027-02-05 (CNPE 2027
target, ICMS-SP after 31/12/2026, ANP 1.006 transition) → add to the docs/16 watch
list with "(verify)". Never invent URLs; if the digest lacks one, write "URL missing".
Output a 10-line summary. Stop after 30 minutes of work.
```

**P3: Verification session (S/K → V)**
```
Verify parameters <ids> in registry/parameters.csv using <data/raw/<source_id>/<date>/file>.
For each: find the value in the document; record page/table, a verbatim quote
(≤ 2 sentences), conditions (unit, basis, temperature, scale, year), price_year and
currency. Same value → flag V. Different → update the value, flag V, add a line to
docs/08 §7 change log. Not found → keep the flag and write "not found in <doc>, <date>"
in notes. If two V sources disagree, add a conflict row to docs/21 §1 with both values
and a resolution rule; never average. Then run `python -m engine.registry validate --strict`
and show me the diff before committing.
```

**P4: RenovaBio harvest batch**
```
From registry/renovabio_units.csv take units with status in {listed, located} for
inspection firm <firm>. Use (or write) the adapter in src/engine/ingest/renovabio.py,
with a unit test on a saved HTML fixture in tests/fixtures/ (no network in tests).
Download each report to data/raw/renovabio_cert_reports/<cnpj>/<YYYY-MM-DD>/, record
url, sha256, pages, accessed in the CSV and set status=downloaded. Never guess a URL:
if not found, set status=not_found with the reason. Report counts by status and firm.
```

**P5: Extraction + quote verification**
```
Run the rule-based extractor in src/engine/ingest/renovabio.py on all downloaded,
not-yet-extracted reports. Only for variables the rules miss, run LLM extraction with
templates/extraction_schema_mill_year.json; store raw output in
data/interim/extraction_raw/ with model name and prompt sha256. Pass every value
through the verbatim-quote verifier and reject any value whose quote is not on the
stated page. Write data/interim/mill_year_renovabio_v<k>.parquet and the coverage
matrix (unit × year × variable). Flag ethanol/cane outside 70–90 L/t and
vinasse/ethanol < 8 or > 16 L/L. Report rejections by reason.
```

**P6: Audit sample**
```
Draw a reproducible sample (seed = today's ISO date as an integer): 10 % of extracted
values at random + every value > 3 MAD from its variable's median ratio. Write
data/interim/audit/renovabio_audit_<date>.csv with pdf path, page, quote, value, unit
and an empty auditor_ok column. After I fill it in, compute the error rate by variable
and by firm, and open a docs/21 entry for any systematic error with its fix.
```

**P7: LAI tracker + appeals**
```
Read registry/lai_requests.csv and docs/07. For each request compute days elapsed,
the due date (20 days) and the extended date (+10) using the counting rule recorded in
docs/07; if that rule is unconfirmed, mark the dates "(verify)". For every refusal or
partial answer, draft a recurso de 1ª instância in PT-BR citing the aggregated
alternative already in the request and the research purpose; save it to
docs/lai/<ID>_recurso_<date>.md. List what must be sent today. Do not send anything.
```

**P8: ANP vintage + P-REG scoring**
```
Download the current ANP biomethane monthly plant data (source anp_biomethane_plants) to
data/raw/anp_biomethane_monthly/<date>/ and compute sha256. Append a row to
evidence/anp_vintage_log.csv (checked_on, latest_month, n_rows, sha256,
months_changed_vs_prev). If a month targeted in prereg/P-REG-1/frozen/predictions.parquet
is now published, score it with src/engine/calibrate/metrics.py (CRPS from quantiles,
90 % coverage, MAE of the median, skill vs each baseline) against the first-published
value; write prereg/P-REG-1/scores/<date>.md. Never modify anything under
prereg/P-REG-1/frozen/.
```

**P9: Friday review + release notes**
```
Run: uv run pytest; uv run ruff check src tests; uv run black --check src tests;
uv run python -m engine.registry validate --strict; uv run python -m engine.registry summary.
Compute the evidence metrics in docs/24 §13. Write docs/status/WNN.md: done/not done vs
plan, metrics table vs next gate thresholds, decisions taken, new conflicts, risk
register changes, next week's top-5. Then commit, push and tag wNN. Refuse to stage
anything under data/ (including data/private/) or any .env file.
```

**P10: Gate check**
```
Evaluate Gate <N> from docs/24 §4 criterion by criterion using files only, not memory.
For each criterion give PASS/FAIL, the number observed and the file path that proves it.
For each FAIL, quote the pre-defined fail action and list the concrete tasks it creates
for next week. Write docs/status/Gate<N>_<date>.md.
```

**P11: Registry hygiene sweep**
```
List every data path read by code under src/engine (pd.read_*, gpd.read_*,
rasterio.open, open(), pyarrow) and every folder under data/raw/. Cross-check against
registry/sources.yaml (local_path, sha256, accessed, license). Report unregistered
reads, missing sha256, missing license, missing accessed date and stale hashes
(recompute). Propose sources.yaml patches. Never invent a license; write
"unknown (verify)".
```

---

## 13. Evidence metrics reported every Friday

| Metric | Source | Gate thresholds |
|---|---|---|
| Parameters V / D / S / K by module | `python -m engine.registry summary` | G1.5, G2.7, G4.1 |
| Top-20 leverage parameters V | `registry/verification_queue.csv` | ≥ 12 (G1), 20 (G2) |
| Sources with sha256 + accessed + license | P11 | 100 % of `have` (G1); 100 % of those read by v0.1 (G3) |
| RenovaBio units listed / downloaded / extracted / audited | `registry/renovabio_units.csv` | ≥ 60 % downloaded (G1); ≥ 80 % (G2) |
| `cane_processed` quoted coverage; audit error rate | coverage matrix; audit CSV | ≥ 70 %; ≤ 2 % (G2) |
| LAI: filed / answered / appealed / data received | `registry/lai_requests.csv` | 8/8 filed (G1); 100 % handled (G2) |
| Lab: E1 timepoints done; E2 samples; E3 stock | `data/private/lab/*` (counts only in notes) | t0 + ≥ 4 E2 (G2) |
| ANP latest published month; measured lag | `evidence/anp_vintage_log.csv` | n/a (reported) |
| P-REG-1 months scored; CRPS skill vs best baseline | `prereg/P-REG-1/scores/` | reported (G4.5) |
| Conflicts open / logged with rule | `docs/21` §1 | trend only |

---

## 14. Appendix

### 14.1 New files and paths introduced by this plan
| Path | In git? | Purpose |
|---|---|---|
| `docs/24_EXECUTION_PLAN_2026-10_2027-02.md` | yes | This plan, once accepted |
| `docs/status/WNN.md`, `docs/status/GateN_<date>.md` | yes | Weekly notes / release notes, gate reports |
| `docs/lai/R1.md … R9.md`, `docs/lai/<ID>_recurso_<date>.md` | yes | Request texts and appeals (no personal data beyond the institutional signature) |
| `registry/lai_requests.csv` | yes | Machine-readable LAI tracker (mirrors the `docs/07` table) |
| `registry/renovabio_units.csv` | yes | Census frame and status of every SP certified unit |
| `registry/verification_queue.csv` | yes | Ranked S/K→V queue |
| `evidence/anp_vintage_log.csv` | yes | Empirical ANP publication lag + revisions |
| `prereg/P-REG-1/{protocol.md, information_set.yaml, predictions.parquet, baselines.parquet, backtest.md, frozen/, scores/}` | yes (small) | Pre-registration package |
| `src/engine/ingest/facilities.py`, `src/engine/supply/od_osrm.py` | yes | New modules (with tests on fixtures) |
| `data/private/lab/E1/`, `E2/`, `data/private/contacts_log.csv`, `data/private/partners/` | **no** (private DVC) | Lab and partner material |
| `manuscripts/P1_mill_panel/` | yes | P1 data paper draft |
| ADR-0006 (routing engine) | yes | Decision from the W6 spike |

### 14.2 Calendar and regulatory facts to verify
- National holidays used: Mon 12 Oct, Mon 2 Nov, Fri 20 Nov, Fri 25 Dec, Fri 1 Jan (Sun 15 Nov falls on a weekend). Campinas municipal holiday on Tue 8 Dec? (verify).
- UNICAMP year-end recess dates (verify) and LABIOEN/PPBIOEN access during the recess (verify).
- LAI deadline counting (calendar vs business days; weekend roll-over) for Fala.BR and SIC.SP (verify).
- Partner mill's 2026/27 crush end date (verify; project convention ≈ end Nov).
- ANP monthly plant data publication lag (unknown; measured from W1 and asked in R2).
- CNPE 2027 biomethane target due ≈ 1 Nov 2026 [S] (verify); SP ICMS 12 % on biomethane valid to 31 Dec 2026 [S] (verify); ANP Res. 1.006/2026 off-spec industrial sellers until 9 Feb 2027 [S] (verify).
- Count of SP RenovaBio certificates (~128 [S]; replaced by the V count in W1).
- MapBiomas sugarcane class code in the collection held (verify in its legend).
- OSF embargoed-registration option (verify) for D5; Geofabrik "Sudeste" extract availability (verify).
