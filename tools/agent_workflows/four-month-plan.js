export const meta = {
  name: 'four-month-plan',
  description: 'Judge-panel design of an 18-week (Oct 2026 - Feb 2027) step-by-step execution plan for the SP biomethane engine',
  phases: [
    { title: 'Draft', detail: 'three independent plans from different angles' },
    { title: 'Synthesize', detail: 'judge scores drafts and writes docs/24_FOUR_MONTH_PLAN.md' },
    { title: 'Critique', detail: 'completeness critic checks against all project docs and fixes gaps' },
  ],
}

const ROOT = '/home/user/aprenda_sobre_biometano/sp-biomethane-engine'
const SCRATCH = '/tmp/claude-0/-home-user-aprenda-sobre-biometano/a54bf28f-e5f7-5156-98b3-cf0d329bf4a6/scratchpad'

const CONTEXT = `
Project: sp-biomethane-engine — techno-economic + spatial simulation of biomethane production in São Paulo State (CP2B / NIPE-UNICAMP). Owner: Lucas (researcher; Python, advanced R statistics, geoprocessing), working mostly alone with Claude Code, plus lab partners (UNIFAL CEMARA, CP2B LABIOEN, PPBIOEN pilot plant) and company partners with running experiments (São Martinho, Comgás, Equinor). Data already held: mill coordinates, MapBiomas sugarcane 30 m 2008–2025, SEADE/IBGE planted vs harvested 2008–2025, UNICA SP state totals 2008–2018, infrastructure (gas transport/distribution, city gates, injection points, rail, transmission, roads), livestock point locations (state body), exclusion shapefiles, PILAR-2b competing-use factors, energy/fuel prices, lab characterization references. No access to mill data (RenovaBio public certification reports are the mill-level substitute).
Read these files in ${ROOT}: PROJECT.md, CLAUDE.md, docs/00_INDEX.md, docs/19_ROADMAP_STEP_BY_STEP.md (current ~30-week roadmap that must be COMPRESSED to 4 months), docs/02, docs/07_LAI_REQUESTS.md, docs/09–13 (module methods), docs/17_LAB_AND_PILOT_EXPERIMENTS.md, docs/18_PILAR2B_INTEGRATION.md, docs/20_PUBLICATIONS_PLAN.md, docs/21_RISKS_AND_OPEN_QUESTIONS.md, docs/decisions/*.md. Skim others as needed.
STATE OF CODE (being built today, 2026-10-04, v0 with unit tests): src/engine/registry.py (registry loader + validator CLI), ingest/renovabio.py (rule-based RenovaBio report extractor + verbatim-quote verifier for LLM outputs), ingest/inventory.py (hash & register locally held datasets → sources.yaml stubs), supply/raster_h3.py (MapBiomas class raster → area per H3 cell, ~1–2 min per statewide year), supply/{huff,residues,seasonality,grid}.py (Huff allocation + frequentist calibration, residue rules with MC, biweekly→monthly shares, rescale to municipal totals), process/{substrates,cstr,strategies}.py (Level-1 CSTR mass balance + constraints + strategies S0–S5), economics/{finance,capex,revenue,lcob,montecarlo}.py (CRF/NPV/IRR, LCOB, CAPEX scaling & exploratory log-log fit, LHS MC, Sobol via SALib), siting/{facility_milp,supply_curve}.py (multi-period facility-location MILP via scipy/HiGHS; merit-order supply curve), calibrate/{anp,metrics}.py (ANP monthly SP plant utilization analysis, MAPE/CRPS/coverage), export/bundle.py (release bundle + manifest for PILAR-2b). Docker (PostGIS 5433 + Jupyter), pre-commit, CI file. NOT yet done: real data ingestion, H3 cane panel, Bayesian calibration (PyMC/brms), hierarchical CAPEX model, road-network OD matrices (OSRM/Valhalla), Sentinel-2 harvest detection, ADM1, PILAR-2b ingest side.
CALENDAR FACTS (computed; use them): plan window Mon 2026-10-05 → Fri 2027-02-05 = 18 weeks (W1 starts Oct 5; W2 Oct 12 — Mon Oct 12 national holiday; W5 Nov 2 — Mon Nov 2 holiday (Finados); W7 Nov 16 — Fri Nov 20 holiday (Consciência Negra); W12 Dec 21 — Fri Dec 25; W13 Dec 28 — Fri Jan 1 2027; Carnival 2027 is Feb 8–9, just after the window). UNICAMP year-end recess around late Dec–early Jan (verify exact dates). Sugarcane: project convention harvest ≈ Apr–Nov, off-season Dec–Mar → fresh filter cake and vinasse are only available until ~end of Nov 2026, so lab sampling (E1 filter-cake storage, E2 vinasse composition) must start in Oct/Nov; the Dec 2026–Mar 2027 off-season happens INSIDE the window → opportunity for a PRE-REGISTERED prospective prediction of ANP monthly plant output (Costa Pinto, Narandiba, Santa Cruz, Paraguaçu) made before the data are published, then scored as data arrive (ANP publication lag: unknown — to verify). Regulatory dates inside window (flag S, verify): CNPE 2027 biomethane target due ~1 Nov 2026; SP ICMS 12 % on biomethane valid to 31 Dec 2026. LAI requests take ≥20 (+10) days → file in week 1. Daily automated research routines (00:55 and 01:50 BRT) already exist and email digests.
Rules: never invent numbers/URLs; any date you are unsure about mark "(verify)". Write in English; PT-BR terms in parentheses where useful.`

const ANGLES = [
  { key: 'evidence-first', angle: 'EVIDENCE & DATA FIRST: optimise for a defensible evidence base — data acquisition, verification sprint (S/K→V), LAI, RenovaBio collection at scale (~128 SP certificates), registry hygiene, then models. Risk-first: identify the critical path and long-lead items and front-load them.' },
  { key: 'deliverable-first', angle: 'DELIVERABLES & PUBLICATIONS FIRST: optimise for tangible outputs by Feb 2027 — PILAR-2b releases (v0.1 supply, v0.2 process/LCOB, v0.3 economics, v1.0 siting+supply curve), manuscript drafts (P1 data descriptor, P2 capacity factor, P3/P4 started), a demo for partners. Work backwards from the deliverables; cut scope ruthlessly where needed (state what moves after Feb 2027).' },
  { key: 'calendar-experiments-first', angle: 'SEASON & EXPERIMENT CALENDAR FIRST: optimise around the hard external clocks — end of harvest (sampling windows for E1/E2/E3), the off-season Dec–Mar (pre-registered prospective prediction of ANP plant output as the flagship "digital shadow" test), regulatory dates, holidays and recess, partner meeting cadence, LAI response times. Make sure nothing time-critical is missed.' },
]

const DRAFT = (a) => `${CONTEXT}

Write a complete 18-week execution plan from the angle: ${a.angle}
Format: Markdown. For EACH week: dates, goal (one line), checklist of concrete tasks (each a verifiable action with a file/output path or a person to contact), deliverable(s), and which engine module/doc it touches. Week 1 broken down day by day (Mon–Fri). Monthly gates with measurable pass criteria (adapted from docs/19 gates). A critical-path list, a "what is cut / deferred past Feb 2027" list, a risk register specific to the 4 months, a weekly rhythm (e.g. Monday plan / Friday review + push + release notes), and suggested Claude Code session prompts for recurring tasks. Be realistic for ONE researcher (~30–35 h/week on this) with Claude Code.
Write it to ${SCRATCH}/plan_draft_${a.key}.md (create the folder if needed). Return the file path and a 10-bullet summary of the plan's distinctive choices.`

const drafts = await parallel(ANGLES.map(a => () => agent(DRAFT(a), { label: `draft:${a.key}`, phase: 'Draft' })))
const ok = drafts.filter(Boolean)
log(`${ok.length}/3 drafts written`)

const synth = await agent(`${CONTEXT}

You are the JUDGE and SYNTHESIZER. Three independent 18-week plans were drafted:
${ANGLES.map(a => `- ${SCRATCH}/plan_draft_${a.key}.md (${a.key})`).join('\n')}
Draft summaries: ${JSON.stringify(ok)}
1. Read all three fully. Score each 1–10 on: realism for one researcher, critical-path correctness (long-lead items first, harvest-window sampling, LAI), scientific defensibility (verification, pre-registration, validation design), deliverable value (releases, papers, PILAR-2b), clarity/actionability (every task verifiable). Put a short scoring table at the very end of the doc in an appendix "How this plan was built".
2. Write the FINAL plan to ${ROOT}/docs/24_FOUR_MONTH_PLAN.md, taking the strongest draft as backbone and grafting the best ideas of the others. Required sections: 0 How to use this plan (with docs/19 as the long-form roadmap; this doc is the 4-month execution layer) · 1 Targets by 5 Feb 2027 (measurable) · 2 Calendar overview table (W1–W18 with dates, theme, gate/release) · 3 Week-by-week checklists (W1 day by day) · 4 Monthly gates with pass criteria · 5 Critical path & long-lead items · 6 Pre-registered off-season prediction protocol (what is predicted, when frozen, where stored e.g. a git tag + hash, how scored with CRPS/coverage from engine.calibrate.metrics) · 7 Lab/pilot sampling calendar (E1–E3 windows tied to harvest end) · 8 Releases to PILAR-2b and manuscripts · 9 Weekly rhythm & Claude Code session prompts · 10 Deferred beyond Feb 2027 · 11 Risks specific to the window · Appendix: How this plan was built.
Use checkboxes "- [ ]" for tasks. Reference real repo paths/modules. Do not invent numbers; mark uncertain dates "(verify)". Keep it long enough to be complete but scannable (tables + checklists).
Only write that one file. Return a summary of what you took from each draft.`, { label: 'judge-synthesize', phase: 'Synthesize' })

const critic = await agent(`${CONTEXT}

You are a COMPLETENESS CRITIC. Read ${ROOT}/docs/24_FOUR_MONTH_PLAN.md (just written) and check it against PROJECT.md (RQs, deliverables D1–D7, success criteria), docs/19 (every phase item: is it scheduled in the 18 weeks or explicitly deferred?), docs/07 (all LAI requests R1–R8 scheduled?), docs/17 (E1–E9 placed or deferred?), docs/18 (PILAR-2b contract steps), docs/20 (P1–P7), docs/21 (each conflict C1–C8 and open question has an owner week), docs/06 acquisition items, and the CALENDAR FACTS above (holidays respected, harvest-end sampling before Dec, pre-registration frozen BEFORE Dec data exist, LAI in W1). Also check internal consistency (week dates, gate weeks matching the calendar table, no task depends on something scheduled later) and realism (no week with > ~35 h of work for one person — flag overloaded weeks and rebalance).
Fix every gap directly in ${ROOT}/docs/24_FOUR_MONTH_PLAN.md (you own it now). Append a short "Appendix: completeness check (critic pass)" listing what you changed and anything deliberately left out. Return the list of changes.`, { label: 'completeness-critic', phase: 'Critique' })

return { drafts: ok, synth, critic }
