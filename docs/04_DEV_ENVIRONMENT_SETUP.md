# 04 — Development environment setup (step by step, at home)

Two supported routes:
- **Native Windows with an MSYS2 UCRT64 or Git Bash terminal.** This is the route tested on the project PC on 2026-10-04, at `A:\Project_Twin`. See §0b.
- **WSL2 (Ubuntu).** Use it if you need Linux-only tools, such as OSRM builds outside Docker or osmium. See §1–§8. On Linux or macOS, follow §1–§8 and skip the WSL steps.
Last updated: 2026-10-04. These steps match the current `pyproject.toml`, `uv.lock`, `Makefile` and `docker-compose*.yml`.

## 0. Two warnings
- ⚠️ **Never put the repository or `data/` inside OneDrive** (or any other sync folder). Syncing `.git` and rasters that run to several GB corrupts both.
- ⚠️ Keep the code and data **inside the WSL filesystem** (`~/projects/...`), not on `C:\` (`/mnt/c/...`). Raster I/O through `/mnt/c` is many times slower.

## 0b. Native Windows quick path (tested 2026-10-04, MSYS2 UCRT64, `A:\Project_Twin`)

Paste **one block at a time** and wait for the `$` prompt. When several lines are pasted at once, a long-running Windows program such as `uv` can swallow the lines queued behind it. `| tail` hides all progress until the command ends, so leave it off for long runs.

```bash
# 1. uv (Python manager). The system Python does not matter: uv brings 3.11 for the project
/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
echo 'export PATH="$(cygpath "$USERPROFILE")/.local/bin:$PATH"' >> ~/.bashrc
echo 'export UV_LINK_MODE=copy' >> ~/.bashrc          # uv cache on C:, project on A: (no hardlinks)
echo 'export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"' >> ~/.bashrc   # Docker Desktop CLI
source ~/.bashrc && uv --version
```
```bash
# 2. clone (autocrlf=false keeps evidence files byte-identical, so their sha256 hashes match)
mkdir -p /a/Project_Twin && cd /a/Project_Twin
git clone -c core.autocrlf=false https://github.com/aikiesan/Project_Twin.git
cd Project_Twin
mkdir -p data/{raw,interim,processed,routing,private} ../materiais/{01_artigos,02_relatorios_tecnicos,03_renovabio_laudos,04_lab,05_parceiros_NDA,06_apresentacoes}
```
```bash
# 3. environment + tests (about 2 min; everything passes; CI also runs the registry validator)
uv sync --python 3.11 --extra dev --extra geo --extra stats
uv run pytest -p no:warnings
```

Notes from the first install:
- **PyMC without a C compiler.**
  - Windows has no `g++`, so PyTensor would fall back to very slow pure-Python ops.
  - `import engine` therefore sets `PYTENSOR_FLAGS="mode=NUMBA,cxx="` on Windows when no `g++` is found, using `engine.configure_pytensor_defaults`. Import `engine` before `pymc` in notebooks.
  - In the terminal you can export the same variable in `~/.bashrc`.
  - Measured on the project PC: the Bayesian tests pass in 20 s and 34 s.
- **Ctrl+C in MSYS2 can leave a Python process running.** Check with `tasklist | grep -i python` and stop it with `taskkill //PID <pid> //F`.
- **Docker Desktop** must be running. Then run `cp .env.example .env` and `docker compose up -d db` to start PostGIS on port 5433.
- **Getting updates:** run `git pull` in `Project_Twin/`. Work goes through branches and pull requests against `main`.

## 1. Local directory layout

```
WSL (Ubuntu)  ~/projects/cp2b/
├── Project_Twin/                   ← THE PROJECT: git clone of aikiesan/Project_Twin (engine at the root)
│   └── (contents below)
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
git clone https://github.com/aikiesan/Project_Twin.git
git clone https://github.com/aikiesan/Pilar-2b.git pilar-2b
cd Project_Twin

make setup            # = uv sync --extra dev --extra geo --extra stats  (creates .venv from uv.lock)
make test             # full pytest suite (Bayesian tests take ~1 min)
make registry         # registry validator + summary (known open errors: see docs/21)
cp .env.example .env  # then edit PGPASSWORD (never commit .env)
uv run pre-commit install
code .                # VS Code with the "WSL" extension opens the folder inside WSL
```

To pick up later work: `git pull` on `main`; new work goes on a branch and is merged through a pull request.

## 4. Data folders + DVC

```bash
mkdir -p data/{raw,interim,processed,routing,private}
dvc init                               # done 2026-10-04 (repo root); cache.type = hardlink,copy
dvc add data/raw                       # done: data/raw.dvc is the only file under data/ that git tracks
dvc remote add -d storage gdrive://1oGBLyrlycLHNmLIFJDxXoMwCOBqB3QCm     # done 2026-10-04 (public-safe data)
dvc remote add private gdrive://1XTE0MRE7HmZmQwGcizezBa0mHw3rfHDJ       # done (partner / NDA data, data/private/)
git add .dvc .dvcignore && git commit -m "Init DVC"
```
- `dvc.yaml` and `params.yaml` are added once their stages run end to end. `cane_area_h3` needs the MapBiomas sugarcane class code to be verified first, and `renovabio_extract` needs the batch extractor.
- Remote: Google Drive, two private folders (ADR-0009). The first `dvc push` / `dvc pull` opens a browser for Google sign-in.

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
- [ ] Copy the PILAR-2b files into `data/raw/` with `bash scripts/ingest/import_local_sources.sh <PILAR-2b folder>`. On the project PC the folder is `/a/Pilar-2b`.
  - It brings in `feedstocks.yaml`, the ANP and ANEEL CSVs, the FDE factors, the municipal mesh, the MapBiomas tables and rasters, and the infrastructure layers.
  - It is read-only on the source and never overwrites. See `scripts/ingest/README.md`.
- [ ] Run `python -m engine.ingest.inventory data/raw ...` to get sha256 hashes, then register each folder in `registry/sources.yaml`.
- [ ] The PILAR-2b ingest adapter for engine releases is planned but not written yet. It is designed in `docs/99_SESSION_NOTES.md` (2026-10-04) and docs/18 §3.

## 7. Own repository (done 2026-10-04)
`sp-biomethane-engine/` was split out with its history and pushed as `main` of **`aikiesan/Project_Twin`**. The repository is public, unlike the private repo this section planned.
```bash
cd aprenda_sobre_biometano
git subtree split -P sp-biomethane-engine -b project-twin-main
git push https://github.com/aikiesan/Project_Twin.git project-twin-main:main
```
- On the project PC the clone is `A:\Project_Twin\Project_Twin`. `data/` and `.env` were moved there from the old folder.
- `docker-compose.yml` pins `name: sp-biomethane-engine`, so the existing `pgdata` volume is reused whatever the folder is called.
- `.github/workflows/ci.yml` now runs, because it sits at the repository root.
- Still to do: install the Claude GitHub App on `Project_Twin` if cloud sessions should push there.
- Because the repository is public: partner/NDA material, personal data and `.env` must never be committed (CLAUDE.md rules 5–6).

## 8. Done when
- [ ] `make test` passes, and `make registry` prints the summary.
- [ ] `make up` starts the db and Jupyter, and `psql -h localhost -p 5433 -U engine engine -c '\dn'` shows `engine` and `pilar2b`.
- [ ] `dvc status` works.
- [ ] `C:\cp2b\materiais\` exists with its sub-folders.
