# 04 — Development environment setup (step by step, at home)

Target: Windows + Docker Desktop (WSL2 backend). Linux/macOS: skip the WSL steps.

## 0. Before you start — two warnings
- ⚠️ **Do not put the repository or data inside OneDrive** (or any sync folder). Syncing `.git` and multi-GB rasters causes conflicts and corruption.
- ⚠️ Keep the repo **inside the WSL filesystem** (`~/projects/...`), not on `C:\`. Bind mounts from `C:\` are many times slower for raster I/O.

## 1. Create the real repository (move this seed out)
- [ ] On GitHub, create a **private** repo (name suggestion: `sp-biomethane-engine` or `pilar2b-engine`).
- [ ] Copy this folder's contents into it:
```bash
# inside WSL
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/aikiesan/aprenda_sobre_biometano.git seed-tmp
cd seed-tmp && git checkout ccr-35b12b87-0r0g25
cp -r sp-biomethane-engine ~/projects/sp-biomethane-engine
cd ~/projects/sp-biomethane-engine
git init && git add . && git commit -m "Seed: docs, registry, templates"
git remote add origin https://github.com/aikiesan/<NEW-REPO>.git
git push -u origin main
rm -rf ~/projects/seed-tmp
```

## 2. WSL2 + Docker Desktop
- [ ] Install WSL2 + Ubuntu 22.04/24.04 (`wsl --install -d Ubuntu`).
- [ ] Docker Desktop → Settings → General: *Use the WSL 2 based engine* ✔.
- [ ] Settings → Resources → WSL integration: enable for Ubuntu.
- [ ] Settings → Resources: memory **12–16 GB**, CPUs ≥ 6, disk ≥ 150 GB.
- [ ] Test: `docker run --rm hello-world` inside WSL.

## 3. Python toolchain
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # uv
uv python install 3.12
uv init --package engine   # first time only (or use provided pyproject.toml)
uv add geopandas pyogrio shapely rasterio rioxarray xarray dask h3 \
       pandas pyarrow duckdb sqlalchemy psycopg[binary] geoalchemy2 \
       pyomo highspy salib scipy numpy-financial pymc arviz \
       pydantic pyyaml httpx tenacity pdfplumber pymupdf \
       matplotlib plotly folium
uv add --dev pytest ruff black nbstripout pre-commit ipykernel
```

## 4. DVC (data versioning)
```bash
uv add "dvc[gdrive]"        # or dvc[s3] for MinIO/UNICAMP server
dvc init
dvc remote add -d storage gdrive://<FOLDER_ID>        # public-safe data
dvc remote add private gdrive://<PRIVATE_FOLDER_ID>   # partner/NDA data
```
- Decide remote: Google Drive (simple), UNICAMP server (institutional), or MinIO in Docker (local S3).

## 5. docker-compose.yml (starting point)
```yaml
services:
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: engine
      POSTGRES_USER: engine
      POSTGRES_PASSWORD: ${PGPASSWORD:-change-me}
    ports: ["5433:5432"]           # 5433 to avoid clashing with PILAR-2b local DB
    volumes: ["pgdata:/var/lib/postgresql/data", "./sql:/docker-entrypoint-initdb.d"]
  jupyter:
    build: .
    command: uv run jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token=''
    ports: ["8888:8888"]
    volumes: [".:/work"]
    working_dir: /work
    depends_on: [db]
volumes: { pgdata: {} }
```
- `sql/000_extensions.sql`: `CREATE EXTENSION postgis; CREATE EXTENSION h3; CREATE EXTENSION h3_postgis; CREATE EXTENSION pgrouting;` (h3-pg and pgrouting may need a custom image — see ADR when decided).

## 6. Bring PILAR-2b data in (read-only)
- [ ] From the PILAR-2b environment: `pg_dump -Fc -n public $PILAR2B_DATABASE_URL > pilar2b.dump`
- [ ] Restore: `pg_restore -d postgresql://engine:...@localhost:5433/engine --schema=public pilar2b.dump`
- [ ] Keep it in schema `pilar2b` (rename after restore) and create schema `engine` for our tables.
- [ ] Copy `feedstocks.yaml` and ANP CSVs (`05c`, `05e`) into `data/raw/pilar2b/` and register them.

## 7. Quality gates
```bash
pre-commit install   # ruff, black, nbstripout, check-yaml, detect-private-key
pytest -q
```

## 8. Optional services (later)
- Valhalla (truck routing) container with Geofabrik *sudeste* extract.
- MinIO (S3) for DVC if not using Drive.
- Google Earth Engine account (Sentinel-2 harvest detection, MapBiomas aggregation).

## 9. Done when
- [ ] `docker compose up -d` starts db + jupyter.
- [ ] `psql` shows schemas `pilar2b` and `engine`.
- [ ] `dvc status` works; `pytest` passes (even with zero tests).
