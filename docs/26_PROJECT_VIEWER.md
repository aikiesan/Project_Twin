# 26 — Project viewer (local web page)

A single page that shows everything the project gathers, in five tabs:
- **Overview:** registry counts, data on disk, parameters by confidence, merged PRs, and a **Database** card when `DATABASE_URL` is set.
- **Map:** 20 layers covering supply, infrastructure and constraints, each tied to its registry `source_id`.
- **Datasets:** the full `registry/sources.yaml`, searchable and filterable, with on-disk size.
- **Project flow:** the pipeline steps with their code, tests, method doc and source coverage.
- **Progress:** the roadmap checklist from docs/19, the ADRs, pull requests and commits.

## Run it

```bash
uv run python -m engine.viz --serve      # builds exports/viewer/ and serves http://127.0.0.1:8765
```

- A build takes about 20 s, mostly the map layers. `--no-layers` rebuilds only the tables.
- In the Claude desktop app, the `viewer` entry in `A:\Project_Twin\.claude\launch.json` opens the page in the browser pane.
- The page loads Leaflet from cdnjs and the basemap from openstreetmap.org. Everything else is local.
- `--host` sets the bind address. It defaults to `127.0.0.1`; use `0.0.0.0` only inside a container.

### In Docker

```bash
docker compose up -d db viewer      # builds the image on first use; then open http://localhost:8765
docker compose restart viewer       # rebuild the page after a code or data change
docker compose logs -f viewer
```

- The `viewer` service reuses the `Dockerfile` (as `jupyter` does). The image keeps its venv in `/opt/venv`, so the bind-mounted checkout and its Windows `.venv` do not hide it.
- **Mounts.** The repository is mounted read-only at `/work`, and `data/` read-only too. Only `exports/viewer/` is writable.
- **Port.** It is published on **127.0.0.1:8765 only**, because the default build includes private layers. Don't change it to `0.0.0.0` on a shared network.
- **PRs.** The container has no `gh` CLI and runs with `--no-prs`. Build on the host to see the PR list.
- **Database card.** The container reads `DATABASE_URL` pointing at the `db` service.

## How it is built

`src/engine/viz/build.py` reads the repository, `data/` and (optionally) the database:
- `registry/sources.yaml` and `registry/parameters.csv`;
- `docs/19_ROADMAP_STEP_BY_STEP.md` (its `- [x]` / `- [ ]` boxes) and `docs/decisions/README.md`;
- `git log`;
- `gh pr list`, when the gh CLI is available;
- `engine.load_log` and the schema list, when `DATABASE_URL` is set (docs/27).
  - If the database is unreachable, the card shows the error and the rest of the page still builds.
  - `--no-private` leaves out the `private.*` rows.

Map layers are declared in `src/engine/viz/layers.yaml`.
- Each layer names its registry `source_id`. A layer whose source is not registered is skipped and reported (CLAUDE.md rule 3).
- Layers are reprojected to EPSG:4326, clipped to SP where they are national, simplified for display and rounded to about 1 m.
- **Do not measure on the viewer.** Areas and distances come from the raw data in the model CRS (CLAUDE.md §3).
- Choropleths use quintile classes. The CH₄ potential layer joins CP2B REDU v2 `municipalities.csv` to the IBGE 2025 municipal mesh on the 7-digit code.

## Privacy

- The default build includes layers from `data/private/`, such as the farm points. The page then shows a warning banner, and the build stays in the gitignored `exports/viewer/` on this PC.
- `--no-private` leaves those layers out. Use it for any build that leaves this PC.
- A public GitHub Pages version would also need every layer's license checked first, because many are still `TODO`. Until then, only the registry catalogue (already public in the repo) is safe to publish.

## Keeping it current

- The progress tab is only as good as docs/19. Tick a box (`- [x]`) in the same PR that finishes the work.
- Add a layer by adding an entry to `layers.yaml`. Register the dataset first.
