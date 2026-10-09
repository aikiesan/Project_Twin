# research_notes/ — raw research reports from the planning session (2026-10-03)

These are the **full findings** of the research sweeps that fed `docs/05_DATA_CATALOG.md` and `registry/`. They are kept so nothing is lost and every claim can be traced.

## How they were produced
- Five parallel research agents (feedstock, costs, markets/regulation, process, spatial/methods) + direct web searches (initial context, international benchmarks).
- The research environment **blocked direct access** to most primary sites (gov.br, epe.gov.br, bndes, arsesp, cetesb, sciencedirect, mdpi, ibge, …) and hit a **search quota**, so most values come from **search snippets**.
- Flags: **V** document read · **S** snippet — verify · **K** prior knowledge — verify · **D** derived.

## Files
| File | Topic |
|---|---|
| `R00_initial_searches.md` | First searches: EPE costs, CNPE 0.5 %, MDPI inventory, ANP/SAPCANA/RenovaBio access, remote sensing |
| `R01_feedstock_granularity.md` | Mills, livestock, other substrates, seasonality; coefficients |
| `R02_costs_capex_opex.md` | EPE/BNDES costs, project list, cost methodology |
| `R03_markets_regulation.md` | Prices, CGOB/CBIO, ARSESP, regulatory checklist |
| `R04_process_technical.md` | Vinasse/filter cake/straw/manure, CSTR limits, upgrading, models |
| `R05_spatial_logistics_methods.md` | Geodata, routing, climate, land price; method references |
| `R06_international_benchmarks.md` | DBFZ, MaStR, KTBL, DEA, Sweden, France, EU, US |
| `R11_cocal_narandiba_research_prompt.md` | Deep-research prompt for the reference plant Cocal Narandiba (repo values to confirm, rules, questions) |
| `digests/` | Daily digest triage from 2026-10-06 on, one note per day (ADR-0012) |

**Use rule:** treat every number here as a lead to verify (see `docs/08_VERIFICATION_PROTOCOL.md`), not as a citable fact.
