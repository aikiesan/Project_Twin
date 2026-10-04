export const meta = {
  name: 'engine-research-sweep-2026q4',
  description: 'Online research sweep (projects/costs, parameter verification, SP data access, market/regulation) with adversarial claim verification',
  phases: [
    { title: 'Research', detail: 'one agent per topic writes research_notes/R07-R10' },
    { title: 'Verify', detail: 'skeptic re-checks every numeric claim and proposed registry row' },
  ],
}

const ROOT = '/home/user/aprenda_sobre_biometano/sp-biomethane-engine'
const COMMON = `
Project: sp-biomethane-engine (techno-economic + spatial simulation of biomethane in São Paulo State; CP2B/NIPE-UNICAMP). Root: ${ROOT}. Today is 2026-10-04.
Read first: ${ROOT}/CLAUDE.md (rules), ${ROOT}/registry/parameters.csv, ${ROOT}/registry/projects_capex.csv, ${ROOT}/registry/sources.yaml (skim ids), and the research note(s) named in your task, so you add NEW information instead of repeating.
Tools: use WebSearch (budget: at most 25 searches for you — be strategic, PT-BR and EN queries) and WebFetch (many Brazilian gov/publisher domains are blocked by the egress proxy — if a fetch fails, note it and move on; do not retry the same domain more than twice).
Confidence flags: V = you opened the primary document and read the value (record page/section and verbatim quote); S = seen only in a search snippet or secondary news; K = prior knowledge (avoid). NEVER invent numbers, URLs, DOIs or citations. Every number must have the URL where you saw it. If two sources conflict, record both (do not average).
FILE OWNERSHIP: write ONLY the file(s) named in your task. Do not edit registry files, docs, or code (other agents are working in the same tree). Do not run git commands that change state.
Write in English (PT-BR terms in parentheses where useful). Be concise and tabular.`

const OUT = {
  type: 'object',
  properties: {
    file_written: { type: 'string' },
    key_findings: { type: 'array', items: { type: 'string' } },
    claims: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' }, value: { type: 'string' }, unit: { type: 'string' },
          url: { type: 'string' }, flag: { type: 'string' }, quote_or_snippet: { type: 'string' },
        },
        required: ['claim', 'value', 'url', 'flag'],
      },
    },
    proposed_rows: { type: 'array', items: { type: 'string' }, description: 'exact CSV lines or YAML blocks ready to paste, each tagged with the target file' },
    searches_used: { type: 'integer' },
    blocked_domains: { type: 'array', items: { type: 'string' } },
    gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['file_written', 'key_findings', 'claims', 'proposed_rows', 'gaps'],
}

const TOPICS = [
  {
    key: 'R07-projects-costs',
    task: `Write ${ROOT}/research_notes/R07_projects_costs_update_2026.md.
Goal: expand the Brazilian biomethane project cost dataset (registry/projects_capex.csv has 20 rows; read it and research_notes/R02_costs_capex_opex.md first). Find projects announced/approved/commissioned 2024–Oct 2026 (BNDES approvals incl. Sep 2026 Mauá 65k Nm3/d & Vila Velha 32k Nm3/d landfill projects totalling R$245M investment / R$180.7M BNDES; FINEP; Fundo Clima; Nova Indústria Brasil; company releases: Raízen, São Martinho, Cocal, Atvos, Adecoagro, Tereos, Usina Coruripe, BP Bunge, Zilor, Orizon, Gás Verde, MDC/Ecometano, Comgás/Compass calls, Necta, Naturgy, ZEG, Bioo, Geo Biogas, Vibra/Copersucar, Ultragaz/Ultrapar, Scania/Vale…) with capacity (state basis: biomethane vs biogas, Nm3/d, harvest-day vs annual average) AND investment (R$, year). Also find any Brazilian cost-component data: upgrading unit prices, digester cost per m3, compression/CNG, grid connection (TUSD-Verde/ARSESP), O&M R$/Nm3, EPE technical notes (NT 2025-08 cost tables), FIESP/ABiogás/ABREMA cost studies, LCOB estimates 2025–2026.
In the note: a table of NEW projects (not already in projects_capex.csv) and a table of UPDATES/CONFLICTS for existing rows; then cost-component evidence; then gaps.
proposed_rows: exact CSV lines for projects_capex.csv using its header id,project,location,uf,feedstock,capacity_value,capacity_unit,capacity_basis,investment_total_R$M,bndes_R$M,year,status,source,confidence,notes (ids continue from 21), prefixed "projects_capex.csv: ".`,
  },
  {
    key: 'R08-parameter-verification',
    task: `Write ${ROOT}/research_notes/R08_parameter_verification.md.
Goal: move registry/parameters.csv rows from S/K toward V by locating PRIMARY open-access sources and, where WebFetch works, reading the actual value. Prioritise process + economics core ids: vin_gen, fc_gen, straw_gen, straw_recov, vin_cod, vin_so4, vin_k2o, vin_ph, vin_ch4_yield, cod_removal, fc_ts_vs, fc_bmp, straw_bmp, codig_bmp, olr_max_cstr, hrt_cstr, temp, cod_so4_crit, restart_days, bmp_fullscale, b0_cattle, b0_swine, b0_poultry, upg_elec_membrane, upg_ch4_recovery, fc_storage_loss, capex_epe, opex_epe, lcob_epe_sucro. Also find a verified value/range for biomethane HHV/LHV per ANP Res. 1.006/2026 or ANP 886/2022 spec (needed by the economics module) and for vinasse density/temperature if available.
Try open-access hosts that may not be blocked: pmc.ncbi.nlm.nih.gov, europepmc.org, scielo.br, repositorio.unicamp.br, teses.usp.br, repositorio.unesp.br, bv.fapesp.br, researchgate (often blocked), core.ac.uk, semanticscholar.org, doi.org redirects, epe.gov.br, ipcc-nggip.iges.or.jp (IPCC 2006/2019 Vol4 Ch10 Table 10A for B0).
In the note: one table with columns param_id | registry central [low–high] unit | value found | source (full citation + DOI if seen) | URL | page/table | verbatim quote (short) | suggested flag (V only if you read it in the primary doc) | verdict (confirmed / conflict / not found). Then a "conflicts" list and "still unverified" list.
proposed_rows: lines prefixed "parameters.csv UPDATE <id>: ..." describing exact changes (new central/low/high/source/confidence), and "parameters.csv NEW: <csv line>" for new params (e.g. hhv_biomethane) using header id,module,parameter,central,low,high,unit,source,confidence,notes.`,
  },
  {
    key: 'R09-sp-data-access',
    task: `Write ${ROOT}/research_notes/R09_sp_data_sources_access.md.
Goal: concrete, actionable access routes (exact pages, file names, update frequency, granularity, license) for SP-level data the engine needs, focusing on what is NOT yet well specified in registry/sources.yaml and research_notes/R01_feedstock_granularity.md / R05_spatial_logistics_methods.md (read them). Topics:
(a) RenovaBio: list of certified SP ethanol units (ANP list/panel file format), which inspection firms host public reports and URL patterns (Benri, SGS, Verifit, Totum, KPMG, Accenture, Fundação Vanzolini?), count of SP units; (b) ANP open data for ethanol plants (per-plant capacity/production files); (c) UNICA observatório biweekly SP series access; (d) SAPCANA/MAPA mill registry; (e) CETESB vinasse application plans / P4.231 data; (f) SP livestock: CDA/GEDAVE (Defesa Agropecuária) data, LUPA 2016/17 & new LUPA; (g) SIF slaughterhouses list (MAPA); (h) sewage sludge: SINISA/SNIS, ANA Atlas Esgotos; (i) MSW: CETESB Inventário de Resíduos; (j) gas infrastructure: ARSESP/Comgás/Necta (ex-GBD)/Naturgy SP Sul networks, city gates, EPE WebMap (gasodutos), TUSD-Verde (Deliberação ARSESP 1.765/2025) tariff values; (k) electricity tariffs A4 for SP distributors (ANEEL tariff data open data), (l) diesel/CNG prices (ANP Levantamento de Preços), (m) land values IEA-SP; (n) road network/freight (ESALQ-LOG SIFRECA, ANTT piso de frete).
In the note: a table source | exact URL | what/granularity | format | update | license | access status (fetched OK / blocked / login) | how the engine uses it. Then "quick wins for week 1" list.
proposed_rows: YAML blocks for NEW sources only (ids not already in sources.yaml), using the existing schema (id, name, publisher, url, also, module, provides, spatial, temporal, format, access, status, confidence, use, notes), prefixed "sources.yaml: ".`,
  },
  {
    key: 'R10-market-regulation',
    task: `Write ${ROOT}/research_notes/R10_market_regulation_update_2026Q3.md.
Goal: what changed in Brazilian/SP biomethane market & regulation between ~Jun and Oct 2026 (read research_notes/R03_markets_regulation.md and docs/16_REGULATION_AND_MARKET.md first; add only new/updated info). Topics: CGOB (Certificado de Garantia de Origem de Biometano) — first issuances/trades/price; mandate (Lei 14.993/2024 Combustível do Futuro, CNPE Res. 4/2026 0.5% 2026, 181.7 M m3 2026/27) compliance status, ANP regulations 2026 (995, 996, 1.006, others new), any CNPE revision for 2027; CBIO prices Aug–Sep 2026 (B3); biomethane prices (Argus, Comgás chamadas públicas, Mercado Cativo Verde), NG prices (industrial SP, Petrobras molecule), diesel price; SP ICMS on biomethane beyond 31/12/2026 (renewal decree?), IBS/CBS transition effects; ARSESP TUSD-Verde implementation; production statistics (ANP monthly biomethane production national/SP latest month; number of authorised plants; capacity); new SP plants commissioned in 2026.
In the note: dated timeline table (date | event | numbers | URL | flag), then "implications for the engine" (parameter updates, scenario ranges), then gaps.
proposed_rows: "parameters.csv UPDATE <id>: ..." lines (price_cbio, price_bm_fob, price_ng_ind, price_ng_molecule, price_diesel, cgob_threshold, mandate_volume, icms_sp …) and "parameters.csv NEW: <csv line>" with header id,module,parameter,central,low,high,unit,source,confidence,notes.`,
  },
]

const VERIFY = (t, r) => `${COMMON}
You are an ADVERSARIAL VERIFIER for research note ${r && r.file_written}. Topic task was: ${t.task}
The researcher returned these claims and proposed rows: ${JSON.stringify(r)}
Assume each claim may be wrong (misread snippet, wrong year, wrong unit/basis, biogas vs biomethane confusion, nominal vs annual capacity, investment vs BNDES loan confusion, hallucinated URL). For EVERY numeric claim and EVERY proposed row: re-check via an independent WebSearch query (different wording) or WebFetch of the URL. Budget: at most 30 searches. Prioritise proposed rows, then the largest-impact numbers.
Then EDIT the note file (${r && r.file_written}) — you own it now — adding a final section "## Verification (adversarial pass, 2026-10-04)" with a table claim | verdict (confirmed / corrected / unconfirmed / refuted) | evidence URL | comment; and correct or strike (~~text~~) refuted items in the body. Return the schema: claims = only the claims that survived (confirmed or corrected, with corrected values), proposed_rows = only rows that survived (corrected where needed), gaps = refuted/unconfirmed items + remaining gaps, key_findings = the most important verified findings.`

const results = await pipeline(
  TOPICS,
  (t) => agent(`${COMMON}\n\nTASK ${t.key}:\n${t.task}\n\nReturn the schema when the file is written.`, { label: `research:${t.key}`, phase: 'Research', schema: OUT }),
  (r, t) => r ? agent(VERIFY(t, r), { label: `verify:${t.key}`, phase: 'Verify', schema: OUT }).then(v => ({ key: t.key, research: r, verified: v })) : null,
)
return results.filter(Boolean)
