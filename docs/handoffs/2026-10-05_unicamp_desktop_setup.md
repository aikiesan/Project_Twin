# Handoff: set up the UNICAMP desktop (clone, data from Drive, Docker, PostGIS, viewer)

Paste everything below the line into a new Claude Code session on the desktop PC, opened in the folder that will hold the project (for example `D:\Project_Twin`).

---

You are continuing the **SP biomethane engine** (repository `aikiesan/Project_Twin`, public) on a second machine, the UNICAMP desktop. The project PC at home is already set up. Today's goal is to bring this desktop to the same state, then go one step further: load all held data into PostGIS (Docker Desktop) and serve the project viewer from Docker.

## Rules (read before acting)
- Read `CLAUDE.md`, `docs/99_SESSION_NOTES.md` (last two sections), `docs/decisions/ADR-0009-dvc-remote-google-drive.md` and `docs/26_PROJECT_VIEWER.md` first.
- Never invent numbers, URLs or citations. Every dataset must be in `registry/sources.yaml` before code reads it. `data/raw/` is immutable.
- **Never commit `data/`, `.env` or credentials.** The repository is public.
- **Private data stays private.** `data/private/` holds farm points (from registry reports with addresses and contacts) and CAR property data. In the database these go into their own schema, `private`, never into `engine` or `pilar2b`. They must never appear in anything that leaves this PC.
- HARVEX and JOEL material is discarded (team decision). Never import it.
- Work on a branch, open a PR against `main`, and don't stack PRs (a stacked PR once merged into its base branch instead of `main`).
- If a step needs something only the user has (a password, a dump file, a decision), ask instead of guessing.

## Step 1: tools
Check, and install what is missing (ask before installing system software):
- Git
- uv (Python manager)
- Docker Desktop (WSL2 engine, at least 8 GB RAM for Docker)
- the `gh` CLI (optional; used for PRs and the viewer's PR list)
- DVC, installed with `uv tool install dvc`

Native Windows with Git Bash works; see `docs/04_DEV_ENVIRONMENT_SETUP.md` §0b. Ask the user which drive or folder to use, and keep the code and data **outside OneDrive**.

## Step 2: clone or update the repository
```bash
git clone -c core.autocrlf=false https://github.com/aikiesan/Project_Twin.git   # if the folder is not there yet
cd Project_Twin && git config core.autocrlf false && git pull
uv sync --python 3.11 --extra dev --extra geo --extra stats --extra db
uv run pytest -q -p no:warnings && uv run python -m engine.registry validate
```
- `autocrlf=false` keeps the `evidence/` files byte-identical, so their sha256 hashes match.
- Python **3.11** is required: on 3.12, arviz 1.x breaks `test_capex_hier`.
- All tests must pass and the validator must report 0 errors before you go on.

## Step 3: data from the Google Drive backup
The backup is two dated zips that the user uploaded by hand (ADR-0009):

| Drive folder | File | Bytes | sha256 |
|---|---|---|---|
| `Project_Twin_DVC` (https://drive.google.com/drive/folders/1oGBLyrlycLHNmLIFJDxXoMwCOBqB3QCm) | `Project_Twin_data_raw_2026-10-04.zip` | 478265154 | `6b23faa51535964107b12a0440ed06473dbdec4d945e2c0437136fee003b9087` |
| `Project_Twin_DVC_private` (https://drive.google.com/drive/folders/1XTE0MRE7HmZmQwGcizezBa0mHw3rfHDJ) | `Project_Twin_data_private_2026-10-04.zip` | 126798822 | `cb03de1741269369d5ed1c8998c3b6aca85591754472b6f02a5fe8266ad20533` |

1. Ask the user to download both zips from Drive in their browser into a `backups/` folder **next to** the repository, not inside it. A Drive connector, if available, can confirm the files are there, but large files are better downloaded in the browser.
2. Check each zip's size and sha256 against the table. If one does not match, stop and tell the user.
3. Each zip holds `raw/…` + `raw.dvc` (or `private/…` + `private.dvc`). Extract both into `Project_Twin/data/`.
4. Before overwriting, compare the extracted `raw.dvc` and `private.dvc` with the ones in git. If the git versions are newer, data was imported after this backup: tell the user which `.dvc` file differs.
5. Check integrity: `dvc status` should report no changes for `data/raw.dvc` or `data/private.dvc`.
6. Fill the local cache with `dvc commit -f data/raw.dvc data/private.dvc`. Then `git diff` must be empty: the `.dvc` files must not change.
7. Expect `data/raw` to hold about 370 files (≈ 478 MB) and `data/private` 40 files (≈ 127 MB).
8. Create `data/interim`, `data/processed` and `data/routing` if they are missing.

## Step 4: Docker and PostGIS
```bash
cp .env.example .env      # then set PGPASSWORD to a new local value; never commit .env
docker compose up -d db   # postgis/postgis:16-3.4 on localhost:5433; compose project name sp-biomethane-engine
```
- `sql/000_extensions.sql` runs on first start and creates PostGIS plus the schemas `engine` and `pilar2b`.
- Check with:
  ```bash
  docker compose exec db psql -U engine -d engine -c '\dn'
  docker compose exec db psql -U engine -d engine -c 'select postgis_version()'
  ```
- Port 5433 avoids a clash with any local PILAR-2b database on 5432.

## Step 5: load the held data into PostGIS (new code: branch `feat/load-postgis`)
Write `src/engine/ingest/load_postgis.py`, a CLI run as `uv run python -m engine.ingest.load_postgis`, plus tests and a short method doc. Then run it.
- **What to load:**
  - every map layer declared in `src/engine/viz/layers.yaml`;
  - the key tables:
    - CP2B REDU v2 `municipalities.csv` and `ch4_real_by_municipality_by_stream.csv`
    - ANP `05c` / `05e` from `anp_biomethane_plants` and the ANP open-data series
    - the Census 2022 population table
    - CETESB ICTEM
    - LAPIG pasture vigour (SP rows only)
    - the IBGE 2025 municipal mesh
    - the MapBiomas infrastructure layers
    - the ABIOVE SP land-use series (`tidy_todas_fontes` sheet)
- **Where tables go:**
  - Name tables `engine.raw_<source_id>__<layer>`.
  - Store geometries in **EPSG:4674** (CLAUDE.md §3); reproject on load. Keep the source column names and add explicit unit suffixes only in views, never by renaming raw columns.
  - Anything from `data/private/` goes to schema **`private`**. Create the schema, and do not grant it to any role other than `engine`.
- **Load log.** Write one row per table to `engine.load_log`: `table_name, source_id, file_relpath, file_sha256, n_rows, crs, loaded_at_utc, engine_commit`.
  - Refuse any file whose `source_id` is not in `registry/sources.yaml`.
  - Use the registry `sha256` or the file sha256 so each table can be traced to its file.
- **Idempotent.** Re-running replaces a table only when the file hash changed.
- **Tests.** Cover the table-name mapping, the private-schema routing, the registry check and the refusal of unregistered ids. Use small fixtures and no live database in CI: mock the engine, or skip the tests when `DATABASE_URL` is unset.
- **Spatial indexes.** Create a GiST index on every geometry column, and `ANALYZE` after loading.
- **Report.** List each table with its row count and say which layers failed and why.
- **Docs.** Add the doc (e.g. `docs/27_POSTGIS_LOAD.md`) and an index line in `docs/00_INDEX.md`.

## Step 6: PILAR-2b database (only if the user has it)
`docs/04` §6 and `docs/19` Phase 0 need the PILAR-2b dump restored into schema `pilar2b`.
1. Ask the user for either the `PILAR2B_DATABASE_URL` (put it in `.env`, read-only use) or a `.dump` file.
2. Restore it:
   ```bash
   pg_dump -Fc -n public "$PILAR2B_DATABASE_URL" > pilar2b.dump
   pg_restore -d engine ...
   ```
3. Rename the schema to `pilar2b`.
4. Never write back to the PILAR-2b source, and treat any Pilar-2b checkout as read-only.
5. When it is done, tick that box in `docs/19_ROADMAP_STEP_BY_STEP.md`.

## Step 7: the viewer in Docker
- **Bind address.** The viewer (`python -m engine.viz`) currently binds `127.0.0.1`. Add a `--host` option, defaulting to `127.0.0.1`, so a container can use `0.0.0.0`.
- **Compose service.** Add a `viewer` service to `docker-compose.yml` that builds and serves `exports/viewer/` on port **8765**. Reuse the existing `Dockerfile` (the `jupyter` service builds from it), and mount the repository read-only plus `data/`.
- **Database status.** Optionally, add a "Database" card to the viewer's Overview tab when `DATABASE_URL` is set. It would list the schemas and tables with row counts, read from `engine.load_log`. If the database is unreachable, the viewer must still build.
- **Check.** Run `docker compose up -d db viewer` and open http://localhost:8765 in the browser pane. Check every tab and turn on several map layers.
- **Docs.** Update `docs/26_PROJECT_VIEWER.md`.

## Step 8: wrap up
- `ruff check src tests`, `black --check src tests`, `pytest` and the registry validator are all clean.
- Append a dated section to `docs/99_SESSION_NOTES.md`: machine, paths, what was loaded (table count, row totals), what failed, and the next steps.
- Commit (end the message with `Co-Authored-By: Claude …`), push the branch and open **one** PR against `main`. Never use `--no-verify`.
- Remind the user of two things:
  - the next backup zip is due after any PR that changes `data/*.dvc`;
  - `data/private` and the `private` schema must never leave the PC.

## Known pitfalls
- In Git Bash, paste long commands one block at a time.
- Windows Python cannot read `/tmp`: use a scratch folder.
- Heredocs mangle `\0` and `\n` escapes. Write files with an editor or tool instead.
- Shapefiles from SEADE and the CP2B GEE exports need `encoding="latin1"` (or the `.cpg`). MapBiomas infra folders contain `__MACOSX/._*` junk; skip it.
- `geocod_mun` in LAPIG is a float: cast it to int.
- Conab UF rows in the ABIOVE series must not be summed with RGINT rows.
- The basemap uses openstreetmap.org tiles, because CARTO now needs an API key.
