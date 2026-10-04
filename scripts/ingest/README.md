# scripts/ingest — bring data the team already holds into `data/raw/`

## `import_local_sources.sh`

This script copies the São Paulo datasets that sit in a local PILAR-2b checkout (`A:\Pilar-2b` on the project PC) into `data/raw/<source_id>/`.

```bash
DRY_RUN=1 bash scripts/ingest/import_local_sources.sh /a/Pilar-2b   # list what would be copied
bash scripts/ingest/import_local_sources.sh /a/Pilar-2b             # copy (~400 MB)
WITH_SECOND_CROP=1 bash scripts/ingest/import_local_sources.sh /a/Pilar-2b   # + 2nd-crop rasters (~1.3 GB)
```

- **Read-only on the source.** It never writes to, moves or deletes anything in the PILAR-2b folder.
- **Never overwrites.** Files already in `data/raw/` are skipped, so re-running the script is safe.
- **Logs every copy.** Each copied file gets a line with its origin path, size in bytes and the PILAR-2b commit (`+dirty` when that checkout has uncommitted changes). The log is `data/interim/import_local_sources_log.tsv`, kept outside `data/raw/` so the inventory scan does not count it.

| `data/raw/` folder | From (relative to the PILAR-2b folder) | Note |
|---|---|---|
| `ibge_malha_municipal_sp_2025/` | `00_Fontes_Primarias-…/SP_Municipios_2025/` | municipal mesh 2025 |
| `mapbiomas_col10_municipal/` | `…/00_Fontes_Primarias/MapBiomas_col10/` | municipal statistics table |
| `mapbiomas_agropecuaria_sp_2024/` | `cp2b-workspace/NewLook/backend/data/mapbiomas/` | ~90 m resampled raster, screening only (docs/21 C9) |
| `mapbiomas_infra/` | `…/backend/data/shapefiles/mapbiomas_infra/` | gas distribution, state highways |
| `cp2b_project_map/` | `…/backend/data/shapefiles/project_map_source/data/` | CP2B `project_map` layers: SP 2024 municipalities, gas pipelines, urban areas, … |
| `ibge_pam_seade/` | `…/00_Fontes_Primarias/PAM_1612_1613/`, `…/Agro_PAM_CONAB/` | IBGE PAM tables (sub-folders kept) |
| `cp2b_results_sicar/` | `00_Fontes_Primarias-…/CP2B_Results-*/CP2B_Results/` | CP2B internal results |
| `cp2b_gee_exports/` | `00_Fontes_Primarias-…/GEE_Exports-*/GEE_Exports/` | every export part is copied (there are two); provenance to be documented |
| `pilar2b_fde/` | `fde_residue_availability.csv`, `…/backend/data/FDE_Disponibilidade_Residuos_CP2B.xlsx` | FDE availability factors |
| `pilar2b_canonical_parameters/` | `cp2b-workspace/NewLook/data/canonical_parameters/` | `feedstocks.yaml`, BMP corpus, SP totals |
| `pilar2b_residue_streams_sp/` | `analysis/data/00–04` (SP files only) | municipal residue streams 2023 |
| `anp_biomethane_plants/` | `analysis/data/05c–05f`, `analysis/data/sources/anp/` | ANP plants, monthly volumes |
| `aneel_biogas_gd/` | `analysis/data/05g–05h`, `analysis/data/sources/aneel/` | ANEEL biogas distributed generation |
| `mapbiomas_second_crop/` | `…/00_Fontes_Primarias/MapBiomas_Segunda_Safra/` | only with `WITH_SECOND_CROP=1` |

**Never copied:**
- TerraClass AMZ, `MG_*` layers and silviculture, which are out of scope.
- `analysis/data/05_biogas_plants_brazil.*`, which has local uncommitted edits in the PILAR-2b checkout.
- Anything from `A:\CP2B_Maps_V3`. Its Amasa origin–destination interviews are personal data under LGPD.

**After copying**, run the inventory to get one row per dataset with its sha256, then register each folder in `registry/sources.yaml` (CLAUDE.md rule 3):

```bash
uv run python -m engine.ingest.inventory data/raw --out data/interim/inventory_raw.csv \
    --yaml data/interim/inventory_raw_stubs.yaml --folders-out data/interim/inventory_raw_folders.csv \
    --private-substr partner --private-substr nda
```

`--folders-out` writes one row per `data/raw/<source_id>/` with a folder digest (`sha256_tree`: sorted relative paths + per-file sha256). That digest is the `sha256` in each `sources.yaml` entry. The dated copies of both CSVs are in `registry/staging/`.
