# CLAUDE.md — Working instructions for Claude Code on this project

This file tells any Claude Code session (and any human contributor) how to work in this repository.
Read `PROJECT.md` for the *why*; this file is the *how*.

## 1. What this project is

A **techno-economic and spatial simulation engine for biomethane production in São Paulo State (SP), Brazil**,
developed at CP2B / NIPE-UNICAMP. It answers:

> *Where, at what scale, and with which year-round substrate mix can a CSTR biomethane plant in SP produce at the lowest cost — and is it viable?*

It is the **research engine** that feeds results into **PILAR-2b** (the public platform, `aikiesan/Pilar-2b`).
It is **not** a real-time digital twin. See `docs/01_CONTEXT_AND_MOTIVATION.md` §"Naming".

## 2. Non-negotiable rules

1. **Never invent a number, URL, DOI or citation.** If a value is not in `registry/parameters.csv` or a cited document, say so and add it to `docs/21_RISKS_AND_OPEN_QUESTIONS.md`.
2. **Every parameter carries a confidence flag** — `V` (primary document read, page/table recorded), `S` (seen in snippet/abstract), `K` (prior knowledge), `D` (derived). Only `V` values may appear in a paper without a caveat. See `docs/08_VERIFICATION_PROTOCOL.md`.
3. **Every dataset is registered** in `registry/sources.yaml` *before* code reads it (id, URL, access date, sha256, license, local path).
4. **Raw data is immutable.** `data/raw/` is written only by download scripts; transformations go to `data/interim/` or `data/processed/`.
5. **Large data never goes into git.** Use DVC (`data/` is gitignored). Git holds code, registry, docs, small tables (< 5 MB).
6. **Partner data is confidential** (São Martinho, Comgás, Equinor, any NDA source). It lives only in `data/private/` + private DVC remote, is never committed, and never appears un-aggregated in exports to PILAR-2b.
7. **Conflicting sources are logged, not averaged.** Record them in `docs/21_RISKS_AND_OPEN_QUESTIONS.md` §Conflicts with both values and sources.
8. **Units are explicit everywhere.** Column names carry units (`capex_brl_2025`, `ch4_nm3_d`, `cane_t`). Monetary values carry currency *and* price year.
9. **Distinguish generated vs applied vs available** for every residue (e.g. vinasse generated ≠ vinasse applied in fertirrigation ≠ vinasse available for AD).
10. **Distinguish biogas vs CH₄ vs biomethane**, and nameplate capacity vs actual production (capacity factor).
11. **Every scientific reference is tied to the project and double-checked.** A paper or report enters the docs or the registry only with a row in `registry/references.csv`. The row says what the reference supports (`used_for`: parameter ids, datasets, methods, docs sections). It also records a two-source check of its identity: DOI, title, first author, year and journal, confirmed by two independent sources (`ref_check: two_sources`). A value taken from a reference stays `S` until its page and a verbatim quote are recorded (`V`). A reference that cannot be double-checked is labelled as such, never cited as settled. See `docs/08_VERIFICATION_PROTOCOL.md` §8.

## 3. Conventions

### Units & constants
- Gas volumes: **Nm³ at 0 °C, 1 atm** unless stated. Convert other bases explicitly.
- Energy: MJ, kWh, MWh; MMBtu only for price comparison (1 MMBtu = 1.055 GJ).
- Biomethane HHV ≈ 37–39 MJ/Nm³ (ANP spec basis — verify against Res. ANP 1.006/2026).
- Money: `BRL_<year>` real terms for modeling; nominal only in raw tables. Escalate with IPCA (general), INCC-M (civil), CEPCI (imported equipment, USD).

### Spatial
- Storage CRS: **EPSG:4674** (SIRGAS 2000 geographic).
- Area/distance CRS: **EPSG:31982 / 31983** (SIRGAS 2000 UTM 22S/23S) or an SP Albers equal-area.
- Analysis grid: **H3 resolution 8** (~0.74 km²); res 7 for statewide overviews.
- Distances: **road-network** (OSRM/Valhalla), never Euclidean for logistics.
- Legacy SAD-69 layers (e.g. ZAA): reproject with the official IBGE transformation.

### Identifiers
- Facilities keyed on **CNPJ** (14 digits; root 8 digits = company).
- Municipalities keyed on **IBGE 7-digit code** (same as PILAR-2b).
- Every model run has a `run_id` and a parameter hash.

### Code
- Python ≥ 3.11, managed with **uv**. Style: ruff + black, type hints, docstrings with units.
- Tests with pytest on small fixtures in `tests/fixtures/` (no network in tests).
- Pipelines declared in `dvc.yaml` (one stage per transform).
- Notebooks are for exploration only, numbered (`nb/010_supply_explore.ipynb`), outputs stripped (nbstripout).
- R is welcome for statistics (brms/lme4); keep R scripts in `r/` with `renv`.

## 4. Repository layout (target)

```
CLAUDE.md  PROJECT.md  README.md
docs/            numbered method & planning docs (start at docs/00_INDEX.md)
docs/decisions/  ADRs (architecture decision records)
registry/        sources.yaml · parameters.csv · projects_capex.csv (in git)
templates/       method-doc, ADR, LAI, extraction schemas
src/engine/      ingest · supply · process · economics · siting · calibrate · export
data/            raw · interim · processed · private   (gitignored, DVC)
exports/         release bundles for PILAR-2b
tests/  nb/  r/
docker-compose.yml  pyproject.toml  dvc.yaml
```

## 5. Common commands (once scaffolded)

```bash
docker compose up -d            # PostGIS + engine + Jupyter
uv sync                         # install deps
dvc pull                        # fetch data
dvc repro                       # run pipeline
pytest -q                       # tests
ruff check . && black --check .
```

## 6. How Claude should work here

- Start every session by reading `docs/19_ROADMAP_STEP_BY_STEP.md` to find the current phase and the next unchecked box.
- Before modeling, check the parameter's flag in `registry/parameters.csv`. If `S`/`K`, propose verifying first.
- When extracting data from PDFs with an LLM, always store `source_id`, `page`, and the **verbatim quote** per value (schema: `templates/extraction_schema_mill_year.json`).
- When citing a paper anywhere (docs, registry, code comments, digests), first add or update its `registry/references.csv` row, with `used_for` and the double-check. Run `python -m engine.registry validate` before committing.
- When adding a method, write/update its doc in `docs/` **in the same change** as the code.
- When a decision is made (tool, resolution, method), add an ADR in `docs/decisions/`.
- Prefer small, verifiable steps; show intermediate tables/maps before scaling up.
- Never push partner data, credentials or `.env` files.

## 7. Related repositories

- `aikiesan/Pilar-2b` — public platform (Next.js + FastAPI + PostGIS). Owner of shared spatial layers and municipal data. Integration contract: `docs/18_PILAR2B_INTEGRATION.md`.
- PILAR-2b files reused here: `data/canonical_parameters/feedstocks.yaml`, FDE factors, `analysis/data/05c_*` and `05e_*` (ANP biomethane plants, monthly).
