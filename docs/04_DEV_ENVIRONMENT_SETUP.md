# 04 — Development environment setup (step by step, at home)

Target: Windows + Docker Desktop with WSL2 (Ubuntu). On Linux or macOS, skip the WSL steps.
Last updated: 2026-10-04. These steps match the current `pyproject.toml`, `uv.lock`, `Makefile` and `docker-compose*.yml`.

## 0. Two warnings
- ⚠️ **Never put the repository or `data/` inside OneDrive** (or any other sync folder). Syncing `.git` and rasters that run to several GB corrupts both.
- ⚠️ Keep the code and data **inside the WSL filesystem** (`~/projects/...`), not on `C:\` (`/mnt/c/...`). Raster I/O through `/mnt/c` is many times slower.

## 1. Local directory layout

```
WSL (Ubuntu)  ~/projects/cp2b/
├── aprenda_sobre_biometano/        git clone (branch ccr-35b12b87-0r0g25) — until migration (§7)
│   └── sp-biomethane-engine/       ← THE PROJECT: work here
│       ├── src/engine/             code (ingest · supply · process · economics · siting · calibrate · export)
│       ├── tests/                  pytest (no network)
│       ├── registry/               sources.yaml · parameters.csv · projects_capex.csv
│       ├── docs/  docs/decisions/  methods, plan, ADRs
│       ├── evidence/               small primary documents already acquired (RenovaBio PDF, ANP extracts)
│       ├── research_notes/         raw research sweeps R00–R10
│       ├── templates/              lab CSVs, manifest schema, extraction schema, ADR/method templates
│       ├── scripts/                routing (OSRM), gee (Earth Engine)
│       ├── data/                   ← gitignored, DVC-managed (create it, §4)
│       │   ├── raw/                immutable downloads (MapBiomas, IBGE, ANP, RenovaBio PDFs, OSM pbf …)
│       │   ├── interim/            intermediate transforms
│       │   ├── processed/          model-ready tables (H3, mill-year, …)
│       │   ├── routing/            OSRM graph (built by `make routing`)
│       │   └── private/            partner / NDA data — never committed, private DVC remote only
│       ├── exports/vX.Y.Z/         release bundles for PILAR-2b (gitignored, built by engine.export)
│       ├── nb/                     exploration notebooks (numbered, outputs stripped)
│       └── r/                      R scripts (brms cross-checks), renv
└── pilar-2b/                       git clone of aikiesan/Pilar-2b (reference + integration PRs)

Windows  C:\cp2b\materiais\          Cowork/working library — NOT a git repo, NOT in OneDrive
├── 01_artigos\                     papers (PDF)
├── 02_relatorios_tecnicos\         EPE, ANP, BNDES, CETESB, reports
├── 03_renovabio_laudos\            certification reports downloaded by hand (copy final ones to data/raw/)
├── 04_lab\                         BMP / CSTR spreadsheets (fill the templates/lab/*.csv format)
├── 05_parceiros_NDA\               São Martinho, Comgás, Equinor … (confidential; never into git)
└── 06_apresentacoes\
```

Why two places: the repository holds code, registry and small evidence, while `materiais` is the human reading library that Cowork and you work from.
- WSL sees the library at `/mnt/c/cp2b/materiais`. That path is slow, but PDFs are small.
- Windows Explorer sees the repository at `\\wsl.localhost\Ubuntu\home\<user>\projects\cp2b`.
- When a document becomes model input, copy it into `data/raw/<source_id>/` and register it in `registry/sources.yaml` with its sha256 (CLAUDE.md §2 rule 3).

## 2. One-time machine setup (≈ 30 min)

```powershell
# PowerShell (admin), only if WSL is not installed yet
wsl --install -d Ubuntu
```
- Docker Desktop:
  - Settings → General → *Use the WSL 2 based engine* ✔
  - Settings → Resources → WSL integration → Ubuntu ✔
  - Settings → Resources: memory 12–16 GB, CPUs ≥ 6, disk ≥ 150 GB. OSRM for the Sudeste region needs about 8–12 GB RAM while it builds.

```bash
# Ubuntu (WSL)
sudo apt update && sudo apt install -y git make curl poppler-utils gdal-bin osmium-tool
curl -LsSf https://astral.sh/uv/install.sh | sh && exec "$SHELL"   # uv (Python manager)
uv tool install "dvc[gdrive]"                                       # data versioning CLI
git config --global user.name "Lucas ..." && git config --global user.email lucasnc@unicamp.br
docker run --rm hello-world                                         # Docker reachable from WSL
```
Optional: R 4.4+ with `brms` and `renv` (Bayesian cross-checks, ADR-0007), and an Earth Engine account (`scripts/gee/`).

## 3. Get the project (≈ 5 min)

```bash
mkdir -p ~/projects/cp2b && cd ~/projects/cp2b
git clone -b ccr-35b12b87-0r0g25 https://github.com/aikiesan/aprenda_sobre_biometano.git
git clone https://github.com/aikiesan/Pilar-2b.git pilar-2b
cd aprenda_sobre_biometano/sp-biomethane-engine

make setup            # = uv sync --extra dev --extra geo --extra stats  (creates .venv from uv.lock)
make test             # full pytest suite (Bayesian tests take ~1 min)
make registry         # registry validator + summary (known open errors: see docs/21)
cp .env.example .env  # then edit PGPASSWORD (never commit .env)
uv run pre-commit install
code .                # VS Code with the "WSL" extension opens the folder inside WSL
```

To pick up later work pushed by Claude sessions: `git pull` (same branch).

## 4. Data folders + DVC

```bash
mkdir -p data/{raw,interim,processed,routing,private}
dvc init --subdir                      # --subdir because the engine is a sub-folder of the seed repo;
                                       # after migration (§7) use plain `dvc init`
dvc remote add -d storage gdrive://<FOLDER_ID>            # public-safe data
dvc remote add private gdrive://<PRIVATE_FOLDER_ID>       # partner / NDA data (data/private/)
git add .dvc .dvcignore && git commit -m "Init DVC"
```
- `dvc.yaml` and `params.yaml` are added once their stages run end to end. `cane_area_h3` needs the MapBiomas sugarcane class code to be verified first, and `renovabio_extract` needs the batch extractor.
- Remote choice (Google Drive, a UNICAMP server or MinIO) is an open decision. Record it as an ADR.

## 5. Services (Docker)

```bash
make up        # PostGIS 16 on localhost:5433 (db engine/engine) + JupyterLab on http://localhost:8888
make routing   # downloads Geofabrik sudeste pbf (~0.8 GB), builds the OSRM car graph, serves :5000
make down
```
- Port 5433 avoids clashing with a local PILAR-2b database on 5432.
- `sql/000_extensions.sql` creates PostGIS and the schemas `engine` and `pilar2b`.
- The routing setup is described in `scripts/routing/README.md` and ADR-0006.

## 6. Bring PILAR-2b data in (read-only)
- [ ] `pg_dump -Fc -n public $PILAR2B_DATABASE_URL > pilar2b.dump`, then `pg_restore` into localhost:5433 and rename the schema to `pilar2b`.
- [ ] Copy `data/canonical_parameters/feedstocks.yaml` and the ANP CSVs (`05c`, `05e`) from `../pilar-2b/` into `data/raw/pilar2b/`, then register them with sha256.
- [ ] The PILAR-2b ingest adapter for engine releases is planned but not written yet. It is designed in `docs/99_SESSION_NOTES.md` (2026-10-04) and docs/18 §3.

## 7. Migrate to its own repository (when you start coding full-time)
This keeps the full history of `sp-biomethane-engine/`:
```bash
cd ~/projects/cp2b/aprenda_sobre_biometano
git subtree split --prefix=sp-biomethane-engine -b engine-main
# create an EMPTY private repo on github.com, e.g. aikiesan/sp-biomethane-engine
git push https://github.com/aikiesan/sp-biomethane-engine.git engine-main:main
cd .. && git clone https://github.com/aikiesan/sp-biomethane-engine.git
```
Then:
- install the Claude GitHub App on the new repository, so cloud sessions push there instead of the seed branch;
- move `.github/workflows/ci.yml` into effect. It only runs at a repository root, so CI does not run in the seed repo.

## 8. Done when
- [ ] `make test` passes, and `make registry` prints the summary.
- [ ] `make up` starts the db and Jupyter, and `psql -h localhost -p 5433 -U engine engine -c '\dn'` shows `engine` and `pilar2b`.
- [ ] `dvc status` works.
- [ ] `C:\cp2b\materiais\` exists with its sub-folders.
