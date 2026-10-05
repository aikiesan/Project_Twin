# 27 — Loading the held data into PostGIS

`engine.ingest.load_postgis` copies the datasets on disk into the local PostGIS database
(`docker compose up -d db`, port 5433), unchanged except for reprojection. It loads:

- every map layer in `src/engine/viz/layers.yaml`, plus the table behind each choropleth;
- the key tables in `src/engine/ingest/postgis_tables.yaml`:
  - CP2B REDU v2;
  - ANP `05c`/`05e` and the ANP open-data series;
  - the Census 2022 population table;
  - CETESB ICTEM;
  - LAPIG pasture vigour (SP rows);
  - the IBGE 2025 municipal mesh;
  - all 15 MapBiomas infrastructure layers;
  - the ABIOVE `tidy_todas_fontes` sheet.

A file listed in both configs is loaded once.

## Run it

```bash
docker compose up -d db
uv run python -m engine.ingest.load_postgis --dry-run   # plan: tables, schema, files (no database)
uv run python -m engine.ingest.load_postgis             # load what changed
uv run python -m engine.ingest.load_postgis --force --only 'raw_mapbiomas_infra__*'
```

- `DATABASE_URL` comes from the environment or from `.env`, for example `postgresql://engine:<PGPASSWORD>@localhost:5433/engine`.
- `--no-private` skips private tables.
- The exit code is 1 when any table failed. The report lists every table with its status (`loaded`, `skipped` or `failed`), row count and error.
- A full load takes about 45 s on the UNICAMP desktop.

## Rules

| Rule | How it is applied |
|---|---|
| Registered only (CLAUDE.md rule 3) | `source_id` is the `data/raw/<source_id>/` folder. If any id is missing from `registry/sources.yaml`, the run stops before touching the database. Paths matching HARVEX/JOEL/CP2B_Maps_V3 are refused. |
| Naming | `<schema>.raw_<source_id>__<layer>`. `layer` is the file stem, lower-cased and ASCII-folded, unless the config sets `layer` (key tables) or `db_layer` (viewer layers). A name over 63 bytes is cut and given a 6-hex hash suffix. |
| Source columns kept | Columns are never renamed. Units go into views (CLAUDE.md §2 rule 8). Loader-added columns start with `_`: `_source_file` when several files are concatenated, and `_rgint_code` (ABIOVE, taken from the file name). |
| Private data | Files under `data/private/`, **and** sources marked `access: restricted` in the registry, go to schema `private`. That schema is owned by `engine`, and PUBLIC has no rights on it. |
| CRS | Geometries are reprojected to **EPSG:4674** on load. Point CSVs (lat/lon, WGS 84) become point geometries. A layer without a CRS fails. Every geometry column gets a GiST index, and every table is `ANALYZE`d. |
| Load log | `engine.load_log` has one row per table: `table_name, source_id, file_relpath, file_sha256, n_rows, crs, loaded_at_utc, engine_commit`. `file_sha256` is the file's own sha256. For a shapefile or several files, it is the sha256 of the sorted `relpath  sha256` lines. |
| Idempotent | A table is replaced only when its input hash changed, the table is missing, or `--force` is given. Each table is written to a short staging name and renamed in one transaction, so a failure leaves the previous version in place. |

## Data handling notes

- **ANP open data and Census.** These use decimal commas (`"8000,00"`). `decimal_comma` converts such text columns to numbers. Identifier-like columns stay text: any column with a leading-zero value (CNPJ, codes) or listed in `text_columns`.
- **LAPIG.** The national CSVs are filtered to `uf = SP`. `geocod_mun` is a float in the source and is cast to integer. The first, unnamed column is a pandas row index and is dropped.
- **ABIOVE.** It lands in **`private`**, because the registry marks it `access: restricted` (team reuse only).
  - Each workbook covers one RGINT, and `_rgint_code` records which.
  - `CONAB (UF)` rows are state totals repeated in every file. Never sum `escala = UF` rows with `escala = RGINT` rows.
- **MapBiomas infra.** `__MACOSX/._*` files are skipped.
  - The thermal-power file name has an accent (`Termelétricas`). Extract the backup zips with Python's `zipfile`, not `unzip`: Git Bash's `unzip` mangles such names, which changes the DVC hash of `data/raw`.
- **Viewer filters.** Raw tables ignore the viewer's display filters (`filter`, `clip_sp`, `simplify`). For example, the EPE ethanol plants table keeps all of Brazil.

## First load (2026-10-05, UNICAMP desktop)

41 tables, 184,551 rows, 0 failures:
- 39 tables in `engine` (31 with geometry);
- 2 in `private`: farm points, 29,773 rows, and ABIOVE, 7,943 rows.

Check with:

```sql
select table_name, n_rows, crs, loaded_at_utc from engine.load_log order by 1;
```

## Tests

`tests/test_load_postgis.py` covers:
- table-name mapping and truncation;
- private-schema routing (by path and by `access: restricted`);
- the registry check and the refusal of unregistered ids;
- deduplication;
- the idempotency rule, the shapefile-sidecar hash and decimal-comma parsing;
- the real config's plan.

The live load-and-skip test runs only when `DATABASE_URL` is set. It writes two throw-away `pytest_*` tables and drops them afterwards.
