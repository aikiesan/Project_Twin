# 18 — Integration with PILAR-2b

## 1. Facts about PILAR-2b (from repo inspection, 2026-10-03)
- Monorepo `aikiesan/Pilar-2b`, app in `cp2b-workspace/NewLook/` (Next.js 16 + React 19; FastAPI + PostGIS/Supabase); v3.0.3; INPI registered; GPL-3.0; public.
- Ingest framework: `backend/ingest/` (contract, gates, runner, report) with sources `aneel_siga`, `ibge_ppm`, `pam`, `pam_1612`, `pam_1613`, `snis`.
- Long-format `municipality_timeseries` (migration 024), `scenarios real/ideal` (026, CH₄ volumes), infrastructure features (023), biomass provenance (025).
- Canonical parameters: `data/canonical_parameters/feedstocks.yaml`.
- ANP biomethane plant datasets: `analysis/data/05c_anp_biometano_plants_latest.csv`, `05e_anp_biometano_plant_volume_monthly.csv`.
- Seasonality roadmap doc: `docs/data/dynamics/BIOMASS_SEASONALITY_SP.md`.

## 2. Contract: engine → PILAR-2b
Each engine release `vX.Y.Z` produces `exports/vX.Y.Z/`:
```
manifest.json            run_id, git commit, params hash, source versions, scenario list
facilities.parquet       CNPJ, name, type, status_by_year, capacity, geom (EPSG:4674)
hex_supply.parquet       h3_index, month, residue, p05, p50, p95, unit
mill_month.parquet       cnpj, month, cane_t, vinasse_m3, filter_cake_t, straw_t (+ intervals)
lcob_results.parquet     site_id, scenario, strategy, lcob_brl_nm3 (p05/p50/p95), npv, irr
sites.parquet            optimal sites, scale, mode, geom
supply_curve.parquet     scenario, cum_nm3_d, lcob
migrations/0XX_engine_tables.sql
```
- Only **public/aggregated** results; no partner data.
- Units in column names; CRS EPSG:4674.

## 3. PILAR-2b side (to implement there)
- [ ] New ingest source `engine_release` (reads a tagged bundle, runs gates: schema, units, CRS, row counts).
- [ ] Migration for tables: `facilities`, `hex_supply`, `mill_month`, `lcob_results`, `sites`, `supply_curve` (+ `engine_release_id`).
- [ ] API: `/facilities`, `/supply?h3=&month=`, `/lcob?site=&scenario=`, `/sites`, `/supply-curve`.
- [ ] Frontend: "Facilities" map layer; "Plant simulator" page (pick site + mix → precomputed results); "Supply curve" page.

## 4. Engine side reads from PILAR-2b
- `pg_dump` of PILAR-2b (schema `public` → restored as `pilar2b`).
- `feedstocks.yaml` + FDE factors.
- ANP CSVs `05c`, `05e`.

## 5. Release cadence
- v0.1 facilities + supply (end Phase 1) → v0.2 process/LCOB (Phase 2) → v0.3 economics (Phase 3) → v1.0 siting + supply curve (Phase 4).
- Each release: GitHub Release + Zenodo DOI (when public) + PR to PILAR-2b.

## Implementation status (v0 code, 2026-10)

**Implemented** (engine side of §2) in `src/engine/export/bundle.py`, with the schema in `templates/release_manifest_schema.json` (JSON Schema draft 2020-12). The CLI is `src/engine/export/__main__.py` and the tests are in `tests/test_export.py`.

**API**
- `build_bundle(tables, out_dir, *, version, run_id, params_hash, sources_used, scenarios, created_at=None, git_commit=None, crs=None, private_columns_blocklist=DEFAULT_PRIVATE_COLUMN_PATTERNS, allow_extra=False, strict=False, overwrite=False, sources_path=None, schema_path=...)`
  - For each table, writes `<table>.parquet` (pyarrow) and `<table>.csv` (UTF-8, `\n` line endings, no index).
  - Then writes `manifest.json` and returns the manifest dict.
- `verify_bundle(bundle_dir)`
  - Returns a list of problems; an empty list means the bundle is intact.
  - Checks that the manifest parses and is schema-valid.
  - For every listed file, recomputes the SHA-256 and compares byte size, row count and column names.
  - Reports unlisted files.
  - CLI: `python -m engine.export verify exports/vX.Y.Z` (exits 1 on any problem).
- Helpers:
  - `release_dir(version)` returns `exports/v<version>`.
  - `column_unit_ok(name)`.
  - `manifest_schema_errors(manifest)`.
  - `sha256_file(path)`.
  - `CONTRACT_TABLES`, `CONTRACT_KEY_COLUMNS`, `DEFAULT_PRIVATE_COLUMN_PATTERNS`.
  - `BundleError` and `BundleWarning`.

**Manifest fields**
- `manifest_schema_version`, `contract`, `engine{name,version}`
- `version`: SemVer, without the leading `v`.
- `run_id`
- `created_at`: ISO 8601 with an offset.
- `git_commit`: a 7–40 character hex sha, or null.
- `params_hash`: the output of `engine.registry.param_hash()`.
- `sources_used`: registry ids.
- `source_versions`: `{id: {accessed, sha256}}`, copied from `sources.yaml` (null where not recorded).
- `scenarios`
- `crs`
- `extra_tables`
- `files`: one entry per file with `table`, `format`, `path`, `sha256`, `bytes`, `rows`, `columns[{name, dtype, arrow_type}]` and `geometry_columns`.
- `warnings`

The JSON is written with sorted keys. With the same inputs, `created_at` and `git_commit`, and the same library versions, the files and the manifest are byte-identical (tested).

**Gates.** A `BundleError` lists every failure, and nothing is written.
- **Tables**
  - Table names must be in {facilities, hex_supply, mill_month, lcob_results, sites, supply_curve}. Any other snake_case name is allowed only with `allow_extra=True` and is then listed in `extra_tables`.
  - A table with `attrs["private"]` or `attrs["confidential"]` set is refused.
  - A table or column name that matches the blocklist is refused. The blocklist is case-insensitive regex: `private`, `confidential`, `proprietary`, and the `_`-delimited tokens `partner(s)`, `nda` and `secret`, so `calendar_month` and `mandate_volume_nm3` pass.
  - A named index is refused, as are duplicate or non-string column names.
- **Geometry and identifiers**
  - A `geom` or `geometry` column requires `crs="EPSG:4674"`; any other CRS is refused. The schema also enforces the same rule.
  - A `df.attrs["crs"]` that differs from EPSG:4674 is refused.
  - `scenario` values must be declared in `scenarios`.
  - `h3_index` values must be valid H3 cells (string or integer).
  - `sources_used` must exist in `registry/sources.yaml`.
- **Run metadata**
  - The version must be SemVer.
  - `created_at` must be timezone-aware ISO 8601. If it is `None`, `datetime.now(UTC)` is used.
  - `git_commit=None` runs a read-only `git rev-parse HEAD`; the result is null if that fails.
- **Output folder**
  - A folder that already exists is refused, because releases are immutable.
  - `overwrite=True` replaces only an empty folder or an earlier bundle.
  - The bundle is written to a sibling temp folder and renamed into place only when it is complete.
- **Warnings** (`BundleWarning`, also recorded in `manifest["warnings"]`; `strict=True` turns them into errors)
  - A column with no unit suffix that is not a known identifier. Examples that pass: `cane_t`, `ch4_nm3_d`, `capex_brl_2025`, `lcob_brl_nm3_p50` and `irr_frac`. Bare `p05/p50/p95` pass only when the table has a `unit` column.
  - A contract column listed in §2 is missing.
  - `cnpj` values that are not 14-digit strings.
  - Column names that are not snake_case.
  - Empty tables.
  - A source registered with `access: confidential` (aggregation must be confirmed by a person; CLAUDE.md §2 rule 6).

**Assumptions and limitations**
- Geometry values are not parsed, because there is no shapely or geopandas.
  - Export them as WKT text or WKB bytes. WKB is written as hex in the CSV.
  - No GeoParquet `geo` metadata is written, because its CRS must be PROJJSON and we do not produce it without pyproj. PILAR-2b should take the CRS from `manifest.crs`.
- The blocklist checks names and flags only. It cannot detect partner data that sits under an innocuous column name, so aggregation remains a human review step.
- The Parquet bytes, and so the hashes, depend on the pyarrow and pandas versions, which are embedded in the file metadata.

**§2 points that are still ambiguous** (the code only warns; to be settled with PILAR-2b)
- Several listed columns carry no unit: `capacity` (facilities), `npv` and `irr` (lcob_results), `lcob` (supply_curve) and `scale` (sites).
- `sites` has no id column, although `lcob_results` refers to `site_id`.
- The format of `month` (`YYYY-MM` or 1–12) is not specified.
- "(+ intervals)" in `mill_month` has no column naming. We suggest `<col>_p05` and `<col>_p95`.
- `status_by_year` has no type defined.

**What remains**
- Generating `migrations/0XX_engine_tables.sql` from the manifest column schemas.
- Per-table required-column schemas once §2 is settled.
- A pipeline step (`dvc.yaml`) that calls `build_bundle` with `param_hash()`.
- The PILAR-2b `engine_release` ingest source (§3), which should call the equivalent of `verify_bundle` as its first gate.
