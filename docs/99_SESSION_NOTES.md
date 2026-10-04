# 99 — Session notes: how we got here (2026-10-03)

A record of the planning conversation, so the reasoning isn't lost.

1. **Started from "digital twin of a biogas plant."** Clarified levels: digital model → digital shadow → digital twin. Without live plant data we build a model first. Discussed ADM1/AM2, Python stack, web options (Streamlit/Dash/Shiny, FastAPI, Pyodide).
2. **Reframed** to what CP2B needs: a **techno-economic + spatial simulation** — cost, production, sale price, location, CAPEX/OPEX, CSTR co-digestion, seasonality of cane residues.
3. **Policy context:** CNPE set 0.5 % for 2026 (not a "failure" of a 1 % target in practice, but a downward adjustment due to supply).
4. **Data reality:** UNICA mill data only at SP-total level; mill data not accessible → considered ML. Concluded: ML where labels exist; mechanistic for "what if"; calibration = inverse modeling.
5. **Found mill-level labels:** RenovaBio certification reports (public consultation) give per-mill annual cane, ethanol, vinasse applied (one read in full: Usina Santa Adélia–Pereira Barreto).
6. **Inspected PILAR-2b:** mature platform (v3.0.3, INPI, FastAPI + PostGIS + Next.js, ingest framework, time series). Its ANP monthly file revealed **low capacity factors and off-season collapse** at Costa Pinto vs partial off-season output at Narandiba.
7. **Decided architecture:** separate engine repo (private), PILAR-2b as public face; versioned release bundles; one ingest owner per layer; Docker + WSL; DVC; not in OneDrive.
8. **Research sweep (5 parallel tracks):** feedstock granularity, costs, markets/regulation, process, spatial/methods → registry of 63 sources, 60 parameters, 20 projects. Most values snippet-level (sandbox blocked primary sites) → Phase 0 verification sprint.
9. **International benchmarks:** DBFZ, MaStR, KTBL, Biogas-Messprogramm III, DEA catalogue, Swedish stats, Lidköping LBG, French ODRÉ, BioNorrois (beet pulp seasonal analog), BIP TF4, OIES 2026, AgSTAR, IEA Task 37 → 18 more sources; use as priors via hierarchical Bayesian pooling.
10. **This seed** (CLAUDE.md, PROJECT.md, docs 00–23, ADRs, templates, registry) committed temporarily on branch `ccr-35b12b87-0r0g25` of `aprenda_sobre_biometano`; to be moved into its own private repo.

## Decisions still pending (user)
- Engine repo **name** and confirm **private** until first paper.
- **DVC remote** (Google Drive / UNICAMP server / MinIO).
- Which partner data can be requested and under what NDA.
- Who leads lab (E1–E2) and pilot (E3) experiments.

---

# Session 2026-10-04 — engine v0 code, research sweep, plan drafts (handoff)

## Done and pushed (branch `ccr-35b12b87-0r0g25`)
- **Code, all tested:**
  - `ingest/inventory`, `ingest/pdftext`, `ingest/renovabio` (single-report extractor; it runs on the Santa Adélia evidence)
  - `supply/raster_h3`, `supply/harvest_detect`
  - `siting/routing` (OSRM)
  - `calibrate/lab` (BMP/CSTR), `calibrate/bayes_huff` (PyMC)
  - `economics/capex_hier` (hierarchical Bayesian)
  - `registry` (validator/summary/param_hash CLI), `export/bundle` (release bundle and manifest schema)
- **Infrastructure:**
  - Docker (PostGIS 5433 + Jupyter), OSRM compose and setup script
  - `uv.lock`, Makefile, pre-commit, CI file (it only runs once the engine is at a repository root)
- **Docs and templates:**
  - ADR-0006/7/8; lab CSV templates
  - docs/04 rewritten as the home setup guide
- **Research:** research notes R07–R10, all S-flagged because primary sites were blocked by the proxy. 13 proposed projects are in `registry/staging/`.
- **Plan:** two plan drafts in `docs/plan_drafts/`.

## Failed because of the usage limit (re-run first, see `tools/agent_workflows/README.md`)
- Build agents: economics (finance/capex/revenue/lcob/montecarlo), process (substrates/cstr/strategies), supply (huff/residues/seasonality/grid), siting (facility_milp/supply_curve), calibrate-anp (anp/metrics), and the RenovaBio tests.
- The review of registry/export.
- R07/R08 claim verification.
- The plan's third draft, its judge synthesis and the completeness critic.

## Known open issues
- `python -m engine.registry validate` reports 73 errors: `publisher` is missing in 70 sources, there are url/status/confidence gaps, and project 12 is flagged `S/D`. Decide whether `publisher` is required; see the open questions in `research_notes/raw/2026-10-04_engine_build_workflow_results.json`.
- `dvc.yaml` stage `renovabio_extract` needs `engine/ingest/renovabio_batch.py`.
- `cane_area_h3` needs the MapBiomas sugarcane class code in `params.yaml`.
- `pyproject` declares `engine = engine.cli:main`, but `cli.py` is not written yet.
- The docs/18 §2 contract is still ambiguous: unit-less columns, `site_id` in `sites`, the `month` format and the geometry encoding.

## Design of the PILAR-2b `engine_release` ingest adapter (not yet written)
- Lives in PILAR-2b at `backend/ingest/sources/engine_release/`:
  - `bundle_io.py` (stdlib + pandas + pyarrow only, with no dependency on the engine)
  - `source.py` (`make_source(table)`)
  - one 3-line module per contract table, registered in `runner.SOURCES` as `engine_release_<table>`
- `fetch(year, raw_dir)` never downloads. It finds `data/raw/engine_release/<year>/vX.Y.Z/manifest.json`, choosing either the single release folder or the one named in a `RELEASE` file.
- `load` verifies every file's sha256, size, rows and columns against the manifest, reads the Parquet, and adds a composite `row_key`, because the coverage gate skips non-municipal keys. It also adds `engine_release_version` and `engine_run_id`.
- `validate` runs the standard battery plus gates for:
  - bundle integrity, engine name and schema version;
  - CRS = EPSG:4674 when a geometry column exists;
  - `scenario` ⊆ manifest scenarios;
  - p05 ≤ p50 ≤ p95;
  - units, using the engine's `UNIT_TOKENS`, with a drift test in the engine repo;
  - the confidentiality blocklist, applied a second time.
- Proposal: the engine writes per-table `totals` into the manifest so the PILAR-2b aggregation gate becomes meaningful.

## User actions outstanding
- Enable the Gmail and Google Drive connectors on the two daily routines.
- Allow the network domains the routines need: gov.br, geofabrik, mapbiomas and others.
- Create an empty private repository for the migration (docs/04 §7).
- Install DVC and R, and set up an Earth Engine account.
