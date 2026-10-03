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
