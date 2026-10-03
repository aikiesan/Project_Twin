# SP Biomethane Engine — seed repository

Techno-economic and spatial simulation of biomethane production in São Paulo (CP2B / NIPE-UNICAMP).

> **This folder is a seed.** It was drafted in a planning session and committed temporarily inside
> `aikiesan/aprenda_sobre_biometano` (branch `ccr-35b12b87-0r0g25`) so it would not be lost.
> **Move it to its own private repository** before development starts — see `docs/04_DEV_ENVIRONMENT_SETUP.md` §1.

## Read in this order

1. `PROJECT.md` — charter: problem, questions, scope, deliverables
2. `CLAUDE.md` — rules and conventions (for Claude Code and humans)
3. `docs/00_INDEX.md` — map of all documents
4. `docs/19_ROADMAP_STEP_BY_STEP.md` — the checklist to execute

## What is already here

| Path | Content |
|---|---|
| `docs/` | 24 numbered documents: context, architecture, setup, data catalog, acquisition playbook, LAI templates, verification protocol, one methods doc per module, ML roles, international benchmarks, regulation/market, lab & pilot experiments, PILAR-2b integration, roadmap, publications, risks, glossary, references |
| `docs/decisions/` | First architecture decision records (ADRs) |
| `registry/sources.yaml` | 81 data sources with access route, granularity and confidence |
| `registry/parameters.csv` | 60 model parameters with central/range/unit/source/confidence |
| `registry/projects_capex.csv` | 20 Brazilian biomethane projects (capacity + investment) |
| `templates/` | Method-doc, ADR, partner data request and LLM extraction (JSON schema) templates |

## Confidence flags (used everywhere)

`V` read in primary source · `S` seen in snippet — verify · `K` prior knowledge — verify · `D` derived by us.
Most entries are **S/K** today; Phase 0 turns them into **V**.
