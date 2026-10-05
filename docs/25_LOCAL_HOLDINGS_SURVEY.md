# 25 — Survey of data already held on the project PC (2026-10-04)

This survey asked which folders on the project PC (`A:\` and `C:\Users\…\Downloads`) hold data the engine can use, and which hold data that must stay out. It was read-only: no origin file was changed. Personal and confidential files are described here by **category only**, because this repository is public.

## 1. Imported

The first group came from `A:\Pilar-2b` (13 folders), using `scripts/ingest/import_local_sources.sh`. The second group came from other folders (9 folders), using `scripts/ingest/local_holdings.yaml` and `python -m engine.ingest.local_import`. Each folder has its own entry in `registry/sources.yaml`, which records its origin.

| id | What | Why it matters |
|---|---|---|
| `cp2b_redu_v2` | CP2B's own published dataset, v2.0 (REDU, CC BY 4.0) | The citable version of BMP, TS/VS, availability factors, CH4 by municipality and stream, and parameter provenance |
| `anp_mapa_ethanol_biodiesel_plants` | Ethanol plants (448) with anhydrous and hydrated capacity; biodiesel plants (77) | Size of vinasse and filter-cake sources |
| `conab_mills_2025` | Conab active ethanol and sugar mills 2025 (points) | The most recent mill locations |
| `conab_cane_series_costs` | Conab cane series by UF (cane, sugar, ethanol, ATR); crop production costs | Calibration of cane to vinasse; crop opportunity cost |
| `anp_biomethane_open_data_2026_04` | ANP biomethane plant capacity and production, monthly to 04/2026 | A newer copy than the one vendored in PILAR-2b. Compare the two before use |
| `cetesb_ictem_2023` | CETESB ICTEM 2023 sewage index per municipality | Sewage supply, together with ETEs 2019 |
| `ibge_censo_2022_pop_sp` | Census 2022 population per SP municipality | Per-capita urban waste and sewage |
| `seade_geo_ambiente_transporte` | Protected areas, indigenous lands, INCRA settlements, UGRHI, power distributors, rail, dry ports | Siting exclusions, tariff areas, logistics |
| `lapig_pasture_vigor_col9` | LAPIG pasture vigour per municipality, 2008–2023 | Degraded pasture as land for energy crops |

## 2. Not imported, by decision

| Category | Where (folder level) | Reason |
|---|---|---|
| Origin–destination interviews | `A:\CP2B_Maps_V3` | Personal data under LGPD. Never accessed |
| Farm registry with addresses and contacts | `A:\Validacao_de_Dados_Cp2b` | Personal data. If ever needed, only a municipal aggregate goes in `data/private/` |
| Full ANEEL distributed-generation registry | `Downloads\06_DADOS_ENERGIA_EPE` | Holds CPF/CNPJ and owner names. The biogas subset is already held (`aneel_biogas_gd`) |
| Engineering balance of a named mill | `Downloads\06_DADOS_ENERGIA_EPE` | Possibly under NDA. Ask the owner before any use |
| HARVEX/JOEL material: HARVEX-branded ILUC transition matrices and any HARVEX/JOEL indicator | `A:\ILUC_NIPE`, `Downloads\02_ABIOVE_ILUC` | Discarded by the team on 2026-10-04 and on the deny list. The MapBiomas-based ABIOVE area series for SP were imported as `abiove_lulc_area_series_sp_rgint` |
| Personal and administrative documents (invoices, declarations, CVs, photos, notes) | several | Not research data |
| Duplicates of held layers (pipelines, lines, substations, municipal meshes, MapBiomas 90 m) | `A:\CP2B_Maps`, `A:\Newlook`, `Downloads\07_DADOS_GIS_BASE` | Already in `data/raw/` |
| `A:\Project_Twin\materiais\*` | — | All six sub-folders were empty on 2026-10-04 |
| Broken files: `IBGE_2022_POP.xlsx` (56 B) and `Matriz_de_Insumo_Produto_2015_Nivel_67.xls` (5.9 KB) | `A:\CP2B_Maps`, `Downloads\02_ABIOVE_ILUC` | Stubs. Download them again from IBGE if needed |

## 3. Candidates for later (public, not yet needed)

| Candidate | Where | Size | Use |
|---|---|---|---|
| MapBiomas 2024 land cover, 30 m, Brazil | `Downloads\07_DADOS_GIS_BASE\brazil_coverage_2024.tif` | 1.16 GB | Replaces the 90 m screening raster (docs/21 C9). Clip to SP |
| DNIT road network (SNV) 2025-07 | `07_DADOS_GIS_BASE\dataverse_files\02_GEOSPATIAL-1.7z` | about 126 MB | Logistics, alongside OSRM |
| Agro-industry points with residue type (4,781) | same `.7z` | 12 MB | Industrial residues. Check the fields for contact data first |
| CETESB contaminated areas | `06_DADOS_ENERGIA_EPE\Mapeamento EPE\DATAGEO` | 1 MB | Siting constraints |
| EPE biomass thermal plants, existing and planned | `06_DADOS_ENERGIA_EPE\_ags_Download Dados Webmap EPE` | under 1 MB | Competing use of bagasse |
| MapBiomas second-crop maize rasters 2008–2024 | `A:\ILUC_NIPE\_ARQUIVO_INTERMEDIARIOS_ABIOVE_20260621` | 1.2 GB | Maize straw. Can be downloaded again from MapBiomas |
| Validation plants and co-digestion pairs | `A:\Newlook` (SQL migration), `Downloads\01_CP2B_PILAR-2B` (CSV) | KB | Calibration and process priors. The REDU `validation_plants.csv` may already cover them |
| Census 2022 households (SIDRA 4711) | `07_DADOS_GIS_BASE` | 136 KB | MSW proxy |

## 4. Reusable code seen

- `A:\ILUC_NIPE\data_pipeline\` has source adapters for PAM, CONAB, LAPIG, MapBiomas and TerraClass, plus area-conservation validators and tests.
- `A:\understanding_biogas_and_bioproducts\FONTES.md` lists sugarcane per-tonne factors and SP reference prices, with page-cited sources (Atlas de Bioenergia SP 2020). These are candidates for `registry/parameters.csv` after verification (S until the pages are read).
