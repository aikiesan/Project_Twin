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

## 2026-10-04 (evening) — local PC set up, moving to local Claude Code
State on the project PC (`A:\Project_Twin\aprenda_sobre_biometano\sp-biomethane-engine`, MSYS2 UCRT64):
- uv, Python 3.11 and Docker Desktop are installed, and all tests pass there: 118 fast, 2 xfail and 5 Bayesian with Numba.
- PostGIS was started with `docker compose up -d db`; health has not been confirmed yet.
- Work now continues in a local Claude Code session, so the files on `A:` can be inspected directly.

Where the existing data lives, from a `find` on the PC:
- **`A:\Pilar-2b`** holds the SP primary data. It is on branch `fix/test-harness-docker`, with uncommitted edits to `analysis/data/05_biogas_plants_brazil.*`, so treat it as read-only.
- **`A:\CP2B_Maps_V3`** holds the Amasa O-D interviews, which are personal data under LGPD. Never import anything from it.
- **`A:\cp2b_fun`** is the CP2B website and is not needed.
- Other `A:\` folders (Paranapiacaba, Maringa, CAGED …) are unrelated projects.

New tooling and findings:
- `scripts/ingest/import_local_sources.sh` copies the SP-relevant datasets into `data/raw/<source_id>/` (README in `scripts/ingest/`). It was tested on a mock tree. The run on the real PC is still pending.
- docs/21 C9: the PILAR-2b MapBiomas raster is a ~90 m resample, labelled "Collection 8" with year 2024, so use it for screening only.
- `params.yaml` now notes that PILAR-2b metadata gives 20 = sugarcane (S-flag). The value stays TODO until it is checked against the official legend.

Next steps, in order, for the local session:
1. `DRY_RUN=1 bash scripts/ingest/import_local_sources.sh /a/Pilar-2b`, then the real run.
2. Run the inventory (`scripts/ingest/README.md`), then write one `registry/sources.yaml` entry per `data/raw/` folder, with publisher, URL, license and sha256. Commit the small inventory CSV to `registry/staging/`.
3. `docker compose ps`, then `psql \dn`, which should list the schemas `engine` and `pilar2b`.
4. `dvc init --subdir`, then choose the remote and record it in an ADR.
5. Continue the backlog under "Known open issues" above. Also re-run the failed build and verification agents when wanted.

## 2026-10-04 (night) — local session: PILAR-2b data imported and registered
Steps 1–2 of the list above are done.
- **Import.** `import_local_sources.sh` ran on `A:/Pilar-2b` (git `1d24ada5+dirty`, read-only). It copied 330 files, about 510 MB, into 13 folders under `data/raw/`, with none missing. The PILAR-2b checkout was not modified.
- **Importer fix.** PILAR-2b has two Drive export parts named `GEE_Exports-*`. The old `first_match` helper copied only the first part, which holds the pig farms. Now every part is copied, so the poultry farms, the complete farms, the web GeoJSON and the Tmax CSVs are imported as well.
- **Dirty file imported.** `analysis/data/05h_aneel_biogas_gd_summary.csv` has uncommitted edits in PILAR-2b. `git diff` shows the change is a row reorder only, with identical values, so it was imported. The note is in `aneel_biogas_gd`.
- **Inventory.** 145 datasets. `engine.ingest.inventory` gained `sha256_tree`, `folder_manifest` and `--folders-out`, with 2 new tests. The dated inventory CSVs are in `registry/staging/`.
- **Registry.** `sources.yaml` now has one entry per `data/raw/` folder. 10 are new, and 3 existing ones were updated in place: `ibge_pam_seade`, `pilar2b_fde` and `anp_biomethane_plants`. Each carries a publisher, a URL, a license, the folder sha256, `local_path` and `accessed`. No new validator errors; 3 earlier errors are fixed. 69 errors remain from before, mostly older entries missing `publisher`.

Open from this step:
- **URLs not recorded in PILAR-2b**, left as `TODO`: the MapBiomas Collection 10 municipal statistics and the MapBiomas 10.1 infrastructure vectors. `cp2b_results_sicar` and `cp2b_gee_exports` are internal and use `url: local`.
- **Licenses still TODO:** MapBiomas (believed CC BY 4.0, K), ANP and ANEEL open data, the Pilar-2b repository, and the IBGE MMD Nota Metodológica (cited, not yet read). `project_map` states Proprietary.
- **Sensitive data:** `cp2b_results_sicar` holds CAR property codes and polygons, and `cp2b_gee_exports` holds farm points with herd size. Both are marked `access: restricted`: aggregate them before any export to PILAR-2b.
- **Unknown provenance:** how the GEE farm points were made and the source of the Tmax grid are not documented. Ask the author.
- **Candidates for a later import, not yet inspected:** `C:/Users/Lucas/Downloads/06_DADOS_ENERGIA_EPE` and `07_DADOS_GIS_BASE`. Do not open `A:/CP2B_Maps_V3` (LGPD). Ask before reading `A:/CP2B_Maps`.
- **Repository:** the user created `aikiesan/Project_Twin` (public, empty) as the new home for this project. The move is pending a decision on layout and history.

Next: steps 3–5 above (PostGIS check, DVC init + remote ADR, backlog).

## 2026-10-04 (late night) — new repo, local clone, DVC, second import
- **Repository.** The engine now lives in `aikiesan/Project_Twin`. It was split out with `git subtree split`, keeping its history. The clone on the project PC is `A:\Project_Twin\Project_Twin`; `data/` and `.env` were moved there. The old `aprenda_sobre_biometano/sp-biomethane-engine` copy is frozen. Work goes through PRs against `main`.
- **PostGIS.** Healthy. `\dn` lists `engine` and `pilar2b`, and the PostGIS extension is 3.4.3. `docker-compose.yml` pins `name: sp-biomethane-engine`, so the volume is reused.
- **DVC.** 3.67 is installed with `uv tool install dvc`. `dvc init` was run at the repo root, and `data/raw.dvc` tracks `data/raw`. The remote is still undecided (ADR-0003).
- **Line endings.** The clone uses `core.autocrlf=false` (docs/04), so the `evidence/` hashes match.
- **Survey of other local folders.** Read-only, done by three agents; written up in `docs/25_LOCAL_HOLDINGS_SURVEY.md`. It found that `materiais/` is empty, along with several personal-data and NDA risks, which are kept out.
- **Second import.** `scripts/ingest/local_holdings.yaml` plus `engine.ingest.local_import` (manifest-driven, with a deny list, 9 tests) imported 9 folders, 69 files, 70 MB. `sources.yaml` now has 100 entries. The Pilar-2b-derived entries are GPL-3.0, per its LICENSE.

User decisions pending:
1. The DVC remote, both public-safe and private: Google Drive, a UNICAMP server or MinIO. Until one is chosen, `data/` exists only on this PC.
2. Reuse rights for the ABIOVE/HARVEX ILUC matrices, and whether the named-mill balance file is under NDA.
3. Whether to install the Claude GitHub App on `Project_Twin`, so cloud sessions can push there.
4. Provenance of the CP2B GEE farm points and the Tmax grid.

Next technical steps:
- Compare `anp_biomethane_open_data_2026_04` with `anp_biomethane_plants` and log any conflict.
- Move `FONTES.md` (Atlas SP 2020 factors) into `parameters.csv` as S rows, then verify against the pages.
- Use the 30 m MapBiomas 2024 raster (1.16 GB, in `07_DADOS_GIS_BASE`) to replace the 90 m screening raster.
- Registry validator: 0 errors since the fix in PR #1 (publishers filled).
