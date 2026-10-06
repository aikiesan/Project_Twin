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

## 2026-10-05 — decisions answered, private data split, project viewer
User decisions:
1. **Backup.** Manual dated zips go into two private Google Drive folders: `Project_Twin_DVC` and `Project_Twin_DVC_private`. No DVC remote is configured (ADR-0009). The first zips are in `A:\Project_Twin\backups\`, with their sha256 values in `SHA256SUMS.txt`.
2. **ABIOVE is reusable; HARVEX and JOEL are discarded.**
   - Imported `abiove_lulc_area_series_sp_rgint`: MapBiomas-based area series for the 11 SP RGINTs, 2008–2024.
   - The HARVEX-branded matrices were not imported.
   - `joel` was added to the importer's deny list.
3. **GEE farm points.** The data was built by Lucas in `A:\Validacao_de_Dados_Cp2b\Dados_Suinocultura_Avicultura.ipynb`, from registry reports with addresses and contacts. The Earth Engine script itself was not found. The Tmax CSVs are empty.
   - `cp2b_gee_exports` and `cp2b_results_sicar` now live in `data/private/`, tracked by `data/private.dvc`.
4. **GitHub App.** Install it later. For now, work locally.

Other changes:
- **CI.** CI is pinned to Python 3.11, because Python 3.12 resolves arviz 1.x and `test_capex_hier` breaks.
  - PR #2 merged into `chore/local-setup`, because it was stacked on PR #1. PR #3 brings it into `main`.
  - Lesson: don't stack PRs, or retarget them to `main` before merging.
- **Project viewer.** `uv run python -m engine.viz --serve` serves it at http://127.0.0.1:8765 (docs/26). It shows the datasets, a map of 20 layers, the project flow and progress. Roadmap boxes that are actually done are now ticked in docs/19.

Next:
- A GitHub Pages catalogue (registry only) once the user wants it public.
- Restore the PILAR-2b dump. The schemas exist but are empty.
- The ANP comparison, `FONTES.md` factors and the 30 m MapBiomas raster, as listed above.

## 2026-10-05 (day) — UNICAMP desktop set up, held data loaded into PostGIS, viewer in Docker
Machine: the UNICAMP desktop (Windows 11 Pro, 20 CPUs, 32 GB RAM for Docker Desktop 28.4), following `docs/handoffs/2026-10-05_unicamp_desktop_setup.md` (PR #5).
- **Paths.** The repository is at `C:\Users\Lucas\Documents\Project_Twin\Project_Twin`, outside OneDrive. The Drive backup zips sit next to it, in `C:\Users\Lucas\Documents\Project_Twin\drive-download-20261005T112909Z-1-001\`.
- **Tools.** Git 2.53 and Docker Desktop were already installed. uv 0.12 was installed with winget, and DVC with `uv tool install dvc`. gh is not installed: git commands are run by hand.
- **Checks.** All tests pass on Python 3.11, and the registry validator reports 0 errors.

### Data restored from the backup zips
- Both zips match the sizes and sha256 values in ADR-0009 and `SHA256SUMS.txt`. The `raw.dvc` and `private.dvc` files in the zips are identical to the ones in git.
- Extracted into `data/`:
  - `data/raw`: 370 files, 478 MB;
  - `data/private`: 40 files, 127 MB.
- After `dvc commit -f`, `git diff` is empty and `dvc status` reports "up to date". `data/interim`, `data/processed` and `data/routing` were created.
- **Pitfall:** Git Bash's `unzip` mangled 3 accented file names (`Território`, `São Paulo`, `Termelétricas`). The sizes stayed the same, but the DVC hash of `data/raw` changed. Re-extracting with Python's `zipfile` fixed it. Never use `unzip` for these backups.

### PostGIS
- `.env` was created with a new local `PGPASSWORD` and `DATABASE_URL` (not committed).
- `docker compose up -d db` is healthy on port 5433, with PostGIS 3.4.
- A separate `cp2b-db-dev` container (database `cp2b_maps`, port 5432, stopped) exists on this PC. *Correction (later the same day): it is the `db` service of the PILAR-2b NewLook stack, and it is the source of the `pilar2b` copy below.*

### New in this change: `engine.ingest.load_postgis`
- The loader, its config (`postgis_tables.yaml`), 18 tests and docs/27 are new.
- **Loaded:** 41 tables, 184,551 rows, 0 failures, each with a row in `engine.load_log`.
  - **`engine`:** 39 tables, 31 of them with geometry (EPSG:4674, GiST).
  - **`private`:** 2 tables, the farm points (29,773 rows) and the ABIOVE series (7,943 rows). ABIOVE is `access: restricted`. The schema is revoked from PUBLIC.
  - The largest are LAPIG SP (40,273), urban areas (36,916), MapBiomas state highways (32,910) and the farm points.
- **Fixed during the first run:** geoalchemy2's automatic index names went over 63 bytes for long table names. Tables are now written to a short staging name and renamed.
- **Idempotency checked:** a rerun skips all 41 tables.
- **`layers.yaml`:** 3 `db_layer` overrides keep the table names readable.

### Viewer in Docker
- **CLI:** `python -m engine.viz` has a `--host` option. The default stays `127.0.0.1`.
- **Overview tab:** a new Database card (schemas, tables and row counts from `engine.load_log`). If the database is unreachable, the card shows the error and the page still builds.
- **Compose:** a new `viewer` service.
  - The repository and `data/` are mounted read-only, and only `exports/viewer/` is writable.
  - It is published on **127.0.0.1:8765 only**, because the build includes private layers.
- **Dockerfile:** the venv moved to `/opt/venv`, so the bind-mounted checkout does not hide it, and the `db` extra was added. A `.dockerignore` keeps `data/`, `.env`, `.venv` and `.git` out of the build context.
- **Checked:** `docker compose up -d db viewer` builds all 20 layers with no problems. All five tabs render, and several map layers were turned on.

### Not done
- **PILAR-2b dump (Step 6):** skipped by the user's choice. `pilar2b` is empty.
- **Load-log commit stamps:** the 41 tables were loaded before the commit, so `engine_commit` reads `d653c50+dirty`. Rerun with `--force` after merging to stamp the merged commit.

Next:
1. Restore the PILAR-2b dump into `pilar2b` (docs/19 Phase 0).
2. Views with unit-suffixed columns on top of the raw tables (for example ANP capacity in Nm³/d, after the reference-condition check).
3. The earlier backlog: the ANP comparison, `FONTES.md` factors and the 30 m MapBiomas raster.
4. A new backup zip is needed only after a PR that changes `data/*.dvc`. This one does not.
5. On the project PC, run `uv self update` before `uv sync`: uv 0.12 rewrote `uv.lock` in lock revision 5, and older uv releases may not read it.

## 2026-10-05 (afternoon) — PILAR-2b research tables copied into schema `pilar2b`
- **Source.** The NewLook stack (`Pilar2b/cp2b-workspace/NewLook`) runs frontend :3006 and backend :8000. Its database `cp2b-db-dev` had stopped (exit 255); it was started with the user's approval and recovered cleanly.
  - Inventory: 8 schemas.
  - `public` has 63 tables (13 GB, of which `audit_log` is 12 GB) and 16 views.
- **Excluded:**
  - Supabase-style `auth`, `storage` and `realtime`.
  - From `public`: the audit log (user e-mail and IP addresses), users, leads, subscribers, analytics, backups, and the views and sequences that depend on them.
  - Personal data is described by category only (CLAUDE.md, docs/25).
- **New:** `engine.ingest.restore_pilar2b` with 7 tests, the registry entry `pilar2b_platform_db`, and docs/27 §PILAR-2b.
- **Result:**
  - 44 tables, 12 views, 2,386,459 rows in `pilar2b`.
  - 0 personal-looking columns, and no functions or triggers.
  - The dump (409 MB) is in `Project_Twin/backups/pilar2b/`, outside the repo. It is not part of the Drive zips; rebuild it with `--replace` when needed.
- **Two restores failed and rolled back cleanly before the rules were complete:**
  - a materialized view calling `normalize_doi`;
  - a foreign key from `technology_cards.created_by` to `auth_users`.
- **Ticked:** docs/19 Phase 5 "Restore the PILAR-2b dump" and docs/04 §6.

Next:
- Compare `pilar2b.municipality_cp2b_potential` (v5.1) with `cp2b_redu_v2` (v2.0) and log the differences in docs/21 §Conflicts.
- Consider `pilar2b.municipality_timeseries` (PPM herds, PAM) as the source for the manure base-load v0, instead of the `ibge_ppm` "get".

## 2026-10-06 — first triage of the daily digests (cloud session)
Inputs: the three digests of 2026-10-06 (Radar Biometano, Arquivo NIPE-CP2B run 3, Biogas BR), pasted into the session.
- **New intake path (ADR-0012).** One note per digest day in `research_notes/digests/`, plus the running queue `registry/staging/digest_queue.csv` (27 rows today). A digest's `[V]` counts as `S` until a page and a quote are recorded. `parameters.csv` and `projects_capex.csv` were not changed.
- **Primary sites were blocked** by the session's egress proxy (curl and WebFetch: agenciasp, SIDRA, IBGE, arXiv, gov.br, Springer). Nothing was promoted to `V`.
- **Changes:**
  - docs/07: LAI **R9** (ANP RenovaBio certification data per unit), and the CP2B FAPESP number (2024/01112-1) in the template.
  - docs/16: CP 232/2026, new price rows, the TransJordano corridor (§2b), LRCAP as a revenue route, and a dated watch list (§6).
  - docs/21: conflict **C15** (scope of the EPE CAPEX value; the radar gives the price year, Dec 2024) and open questions 11–12.
  - docs/09, 12, 15 and 23: PPM 2025, layers vs broilers, OFMSW yield lead, fleet offtake points, OptBio, EBA outlook, LCFS benchmark.
  - `sources.yaml`: two stubs (`reg_mme_cp_232_2026`, `intl_eu_eba_investment_outlook_2026`); notes on `ibge_ppm`, `epe_nt_2025_08` and `anp_renovabio_cert_panel` (now `status: lai`).
  - The radar routine prompt: phase text per ADR-0010; page and quote for `[V]` numbers; registry suggestions in the queue's columns. **Copy the new prompt into the deployed routine by hand.**
- **Registry:** 0 errors, 127 warnings (unchanged from before the session).

Next, from the queue (`status: open`):
1. File LAI R9 with R1 and R2.
2. Re-export PPM 2025 (SIDRA 3939, 74 and 94) for SP municipalities on a machine that reaches SIDRA; then the manure base-load v0 of the skeleton.
3. Read EPE NT 2025-08 for `capex_epe` (page, quote, scope, price year) and close C15.
4. Download the CP 232/2026 spreadsheets before 29 Oct.
5. Ask IEE/USP, through the CP2B member there, for the OFMSW plant data.

## 2026-10-06 (later) — residues v0 and LCOB v0 for the walking skeleton
- **`engine.supply.residues`:** cane per mill and crop year → monthly vinasse, filter cake and straw, generated vs sent to AD, and the feed table for the process module. Fixed April–November profile until UNICA. docs/09 §5.
- **`engine.economics.lcob`:** CRF, CAPEX (linear or power law), annuity LCOB with components, R$/Nm³ → US$/MMBtu, and the comparison with the EPE and FIESP anchors. docs/11 §9.
- **Registry:**
  - new `K` rows `wacc_real` (10 %, 8–12), `plant_life` (20 yr) and `hhv_biomethane` (38 MJ/Nm³, 37–39);
  - `lcob_fiesp` and `lcob_fiesp_full`: the citation year was corrected to June 2025 (docs/25), with the values unchanged;
  - 0 errors, 127 warnings.
- **Checks:** 26 new tests, including one that runs the chain cane → residues → CSTR → LCOB on registry values. Full suite, ruff and black pass.
- **First chain output (not a result, ADR-0010):** 2 Mt of cane with all vinasse and cake to AD, `x_ch4` 0.6, a 40,000 Nm³/d nameplate → full output April–November, zero off-season, LCOB ≈ R$ 1.95/Nm³. That sits just above the EPE range (0.78–1.83). Against the FIESP range it depends on the exchange rate, which is not in the registry; at an illustrative 5.4 R$/US$ it falls inside.
- Roadmap: "Residues v0" and "LCOB v0" ticked.

Next for the skeleton:
1. **The two mills' inputs.** Cane crushed per crop year for Costa Pinto and Narandiba, with a source (RenovaBio report, company report or UNICA), plus their ANP nameplate (`evidence/anp_monthly_sp_plants_from_pilar2b.csv`).
2. **A runner** (`engine.skeleton`): one config per mill, `run_id` plus `param_hash`, outputs to `data/processed/skeleton/`, and a monthly comparison with the ANP series.
3. **Strategy S1 for Narandiba:** filter-cake storage with a loss factor (`fc_storage_loss` is not numeric yet, so it has to be an explicit scenario input).
4. **Manure base-load v0** from PPM herds, once PPM 2025 is re-exported.
5. **Morris screening** on the skeleton (SALib), to rank what to verify first.

## 2026-10-06 (evening) — PR #12 and the skeleton runner
- **PR [aikiesan/Project_Twin#12](https://github.com/aikiesan/Project_Twin/pull/12)** is open with the digest intake and residues/LCOB v0. This session watches it for CI and reviews.
- **`engine.skeleton`** (`python -m engine.skeleton list | run`) chains:
  - cane → residues → digester sized for the worst month → mass balance with the ANP nameplate → LCOB;
  - a monthly comparison with the ANP biogas series.

  Outputs go to `data/processed/skeleton/<run_id>/`. The `run_id` is deterministic. Only S0 is implemented. docs/13 §6.
- **`registry/skeleton_mills.yaml`** holds the inputs for Costa Pinto and Narandiba. **Cane values are empty**, so the runner refuses to run until a sourced value is entered.
- **Small API additions:**
  - `OperatingLimits.param_ids`;
  - `compare_with_anchors(brl_per_usd=None)`.
- **Diagnostic with a test cane value (not data).** Narandiba under S0 gives an off-season share of 0, against about 0.43 in ANP. Costa Pinto under S0: utilization MAE about 13 pp, off-season share 0 against 0.09. S0 cannot produce Narandiba's off-season output, which supports trying S1 (stored filter cake) next.
- Tests: 10 new in `tests/test_skeleton.py`. Full suite, ruff, black and the registry validator pass.

Next:
1. Sourced cane per crop year for both mills, entered in `skeleton_mills.yaml` by the user, from RenovaBio reports, company reports or UNICA. Then run both and log C2 and C6.
2. Strategy S1: a filter-cake storage share and a release profile, with `fc_storage_loss` as an explicit scenario input (it is not numeric in the registry).
3. Morris screening (SALib) over the skeleton's registry parameters.

### Same evening — strategy S1 (stored filter cake)
- **`engine.process.strategies`:**
  - `StorageS1` and `apply_s1_storage`: one silo pool with a constant fresh-mass loss per month, emptied over the release months;
  - `storage_balance` reports stored, released, lost and the end stock.
- **The runner:**
  - takes `--strategy S0|S1`;
  - a mill's `storage` block holds `store_frac`, the months and `loss_frac_per_month` with `loss_source`;
  - Narandiba has an empty block in `skeleton_mills.yaml`.
- **Diagnostic with test values (not data):** Narandiba's off-season share goes from 0 (S0) to about 0.25 (S1, half the cake stored, 3 %/month loss), against about 0.43 in ANP.
- **Known v0 limit:** the cake-only off-season feed fails the TS check, because digestate recirculation is not modelled.
- Tests: `tests/test_process_strategies.py`, plus S1 cases in `tests/test_skeleton.py`.