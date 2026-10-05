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
| ~~Agro-industry points with residue type (4,781)~~ | same `.7z` | 12 MB | **Blocked** by the team's 2026-09-24 audit: CNAE 01113 (cereals) was read as 11135 (beer), so 3,568 points are mislabelled and their biogas fields are invalid. See §5.2 |
| CETESB contaminated areas | `06_DADOS_ENERGIA_EPE\Mapeamento EPE\DATAGEO` | 1 MB | Siting constraints |
| EPE biomass thermal plants, existing and planned | `06_DADOS_ENERGIA_EPE\_ags_Download Dados Webmap EPE` | under 1 MB | Competing use of bagasse |
| MapBiomas second-crop maize rasters 2008–2024 | `A:\ILUC_NIPE\_ARQUIVO_INTERMEDIARIOS_ABIOVE_20260621` | 1.2 GB | Maize straw. Can be downloaded again from MapBiomas |
| Validation plants and co-digestion pairs | `A:\Newlook` (SQL migration), `Downloads\01_CP2B_PILAR-2B` (CSV) | KB | Calibration and process priors. The REDU `validation_plants.csv` may already cover them |
| Census 2022 households (SIDRA 4711) | `07_DADOS_GIS_BASE` | 136 KB | MSW proxy |

## 4. Reusable code seen

- `A:\ILUC_NIPE\data_pipeline\` has source adapters for PAM, CONAB, LAPIG, MapBiomas and TerraClass, plus area-conservation validators and tests.
- `A:\understanding_biogas_and_bioproducts\FONTES.md` lists sugarcane per-tonne factors and SP reference prices, with page-cited sources (Atlas de Bioenergia SP 2020). These are candidates for `registry/parameters.csv` after verification (S until the pages are read).

## 5. Second survey: ten folders under `C:\Users\…\Documents` (2026-10-05)

Folders: `CP2B`, `ILUC_NIPE`, `Reposicionamento_Submissão_ESD`, `Pilar2b`, `40_Pesquisa_Dados_e_Referencias`, `50_Codigo_Modelos_e_Design`, `PILAR-2b Design System`, `Constelacao_dos_Residuos`, `Input_Output_Ideas`, and a poster folder. Not counting the folders left unopened, they hold about 263 GB in 55,000 files, of which ILUC_NIPE alone is 206 GB of MapBiomas rasters. The survey was read-only. `CP2B_Maps_V3`, `Mapa_Amasa_Artigo_01` and anything named HARVEX or JOEL were never opened. Files that might hold personal data were read for column names and row counts only. The items marked **imported** were copied on 2026-10-05 with `local_holdings.yaml` (root `docs`) and registered; nothing else was copied.

### 5.1 Files that fill a registry entry still marked `get`

| Registry id | Where (folder level) | What is there | Note |
|---|---|---|---|
| `fiesp_sp_biomethane_2024` | `40_Pesquisa…\REFERENCIAS_PILAR2B\Organized_Papers` | The original report: *O biometano em São Paulo: potencial e medidas para alavancar a produção*, June 2025, 180 p. Led by FIESP and prepared by Instituto 17, PSR and Amplum Biogás. Its terms permit non-commercial redistribution with citation | The registry entry says 2024 and "original report not yet located". Correct the year. A second 180-page copy without a text layer is in `CP2B\Validacao_dados\02_LITERATURA` |
| `sinisa` | `Reposicionamento…\00_Primary_Data_Sources_PILAR2b\03_SNIS_Series` | SNIS ConsolidadoMunicipio 2008–2022, one CSV per year, Brazil, about 320 MB | 2022 is the last SNIS year before SINISA. Clip to SP |
| `cetesb_rsu_inventory` (IQR layer) | `Reposicionamento…\DADOS_ESPACIAIS` | CETESB IQR 2022–2024 polygons (645 municipalities, with `Dispoe_em` = where each municipality disposes its waste), IGR 2023–2025, IQC 2022–2024, ICTEM 2024 | Each folder holds a `wfsrequest.txt` that records the WFS query. ICTEM 2024 is newer than `cetesb_ictem_2023` |
| `dnit_snv` | `CP2B\DNIT_MULTIMODAL` (plus three copies) | SNV 202507A shapefile, KML, XLS, and the 202504A→202507A diff GeoPackages | Already listed in §3 |
| `epe_webmap` | `Mapa_Poster_*\Dados_Webmap_EPE`, `…\geojson` | EPE WebMap downloads (July 2026): biomethane, ethanol and biodiesel plants, LPG bases, transmission lines, substations, gas pipelines, SIN subsystems | The download date is in the file timestamps only |
| `ibge_ppm` | `Reposicionamento…\00_Primary…\04_IBGE_Tabelas` | SIDRA 3939 (herds) and 74 (animal products) for 2008–2024. Also 94 (milked cows) and 3940 (aquaculture) | |
| `intl_de_dbfz_resources` | `40_Pesquisa…\Organized_Papers`, `Reposicionamento…\DBFZ_REFERENCES` | DBFZ Biomass Monitor CSV v6.3 (2024-12-01), `BIOMASSEPOTENZIALE_BASISDATEN.xlsx` with readme, `Data_regional_DE.csv`, DBFZ Report 41 | |
| `osm_sudeste` (partial) | `CP2B\Validacao_dados\02_LITERATURA\PROTOCO_CODIGESTAO\sudeste-260112-free.shp` | Sudeste OSM extract as shapefiles, dated 2026-01-12 | OSRM needs the `.pbf`, so this does not replace the routing download |
| `der_sre` (to confirm) | `Pilar2b\BiogasSP.gdb`, layer `rodovias_estaduais` | 4,138 state-road segments with DER-style attributes | The origin is not stated. Confirm before using it as DER-SRE |
| `aneel_sigel` (related) | `Reposicionamento…\Benchmarks_Brasil`, `CP2B\Validacao_dados\01_DADOS_BRUTOS` | ANEEL SIGA generation projects, 25,133 rows (Brazil) | This is SIGA, not SIGEL. Drop the owner column (`DscPropriRegimePariticipacao`) on import, because it can name individuals |

### 5.2 New datasets, not yet in the registry

| Candidate | Where | Size | Use |
|---|---|---|---|
| CP2B method v5.1 outputs (2026-09-24): potential per municipality × substrate at levels L1–L4 (32,895 rows), state levels, mill allocation (160 mills), v4→v5 reconciliation, co-digestion variants, Data in Brief v5.1 tables | `Reposicionamento…\Metodo_CP2b\outputs_v5`, `…\Pacote_CP2b_v5.1`; platform copy in `Pilar2b\…\NewLook\backend\data\raw\cp2b_potential\2026` | about 60 MB | Newer than `cp2b_redu_v2`. Log differences in docs/21 §Conflicts; do not average |
| Biogas plant validation audit (2026-09-16): 31 reconciled plants with company CNPJ, coordinate precision, ANP monthly production observations, source URLs | `CP2B\VALIDACAO_DE_USINAS_BIOGAS\auditoria_camada_validacao_20260916` | under 0.2 MB | Calibration of capacity factor and plant positions |
| Industrial points of interest built from the public RAIS establishment file: 1,059 prioritised and 2,268 aggregated coordinates by CNAE, with probable residues. The staging table has 41,562 establishments | `Reposicionamento…\DADOS_ESPACIAIS` | about 12 MB | Industrial residues. No names or CNPJ. Coordinates are postcode-level (`coord_precisao`) |
| ~~Agro-industry points (4,781), listed in §3~~ | `CP2B\Residuos_Industriais` | 0.4 MB | **Do not use.** No contact fields, but the team's audit (README in `rais_industrial_coordinates_sp_2026_09`) blocks it: CNAE mix-up, 561 points outside SP, invalid biogas and power fields |
| GEDAVE cattle, aggregated per municipality × system × purpose (4,677 rows; records and head count) | `Reposicionamento…\Metodo_CP2b\inputs` | 0.2 MB | An aggregate, with no personal data. The file does not state its origin; ask the team how it relates to the `cda_gedave_gta` request |
| IBGE input–output matrix 2015, level 67 (`.xls` 1.28 MB and `.ods`) | `Input_Output_Ideas` | 2 MB | A working copy of the file listed as broken in §2 |
| BEN annexes IX and X, 1970–2024 | `40_Pesquisa…\Balanco_Energetico_BEN` | 56 MB | National energy balance |
| Atlas de Bioenergia SP 2020, full PDF | `40_Pesquisa…\Atlas_Bioenergia` | 208 MB (8.7 MB compressed copy) | Read the pages cited in FONTES.md (§4) to move its factors from S to V |
| EPE *Panorama do Biometano — Setor Sucroenergético* (Dec 2023); ABiogás note *Mapeamento de plantas de biometano até 2032* (Dec 2024); CIBiogás Panorama 2021, 2022 and 2024 | `Reposicionamento…\Benchmarks_Brasil`, `40_Pesquisa…\Organized_Papers` | about 80 MB | Benchmarks and the planned-plant pipeline |
| Literature library: about 1,500 PDFs sorted by residue (citrus, cane, vinasse, poultry, swine, cattle, slaughterhouses, viscera, breweries, MSW, sewage sludge, eucalyptus, coffee, maize), with exported reference tables | `CP2B\Validacao_dados\02_LITERATURA` | 13.8 GB | Source documents for V-flag verification. Not data to import as is. Skip the administrative sub-folders (see §5.3) |
| MapBiomas Collection 10 annual coverage for Brazil 2008–2024, transitions, and secondary and primary vegetation | `ILUC_NIPE\02_DADOS_PROJETO_ABIOVE`, `…\NOVOS_DOWNLOADS_MAPBIOMAS` | about 64 GB | Only needed for land-use dynamics. Can be downloaded again. The 2024 raster is already in §3 |
| MapBiomas 10.1 territorial vectors (protected areas by sphere, indigenous lands, quilombos, settlements, UGRHI, basins, Atlantic Forest law, priority areas) | `Reposicionamento…\00_Primary…\SHAPEFILES_MAPBIOMAS_10.1` | about 4 GB with zips | Compare with `exclusion_layers` and `seade_geo_ambiente_transporte` |
| CONAB cane survey series by UF (`LevantamentoCana.txt`) | `ILUC_NIPE\02_DADOS_PROJETO_ABIOVE` | 0.1 MB | Probably the same as `conab_cane_series_costs`. Compare before use |
| CONAB warehouses (16,742, Brazil) | same | 3 MB | Low priority. Drop the phone and e-mail columns |

### 5.3 Not imported, by decision

| Category | Where (folder level) | Reason |
|---|---|---|
| Poultry and pig farm registries with address, postcode, a contact field and coordinates (about 18,600 and 13,000 rows), in four copies, plus derived point layers (29,773 farms with herd size and exact coordinates) | `CP2B\Validacao_dados`, `CP2B\_DATA_FILES`, `CP2B\Streamlit_*`, `Reposicionamento…\00_Primary…` | Personal data. These are probably the origin of `livestock_points_sp`, whose publisher is still TODO. If so, record the publisher and keep only municipal aggregates in `data/private/` |
| Interview transcriptions, including a folder of non-anonymised products | `40_Pesquisa…\Produto_4_CEPAL` | Personal data |
| Participant lists, certificates, personal declarations, CVs, invoices, bills, installers | `…\02_LITERATURA\PROTOCO_CODIGESTAO`, `CP2B\Projeto_CP2B_PoC`, `PILAR-2b Design System` | Not research data |
| A credit-bureau folder | `ILUC_NIPE\02_DADOS_PROJETO_ABIOVE\00_PRIMARY_DATA_SOURCES` | Not opened. Out of scope |
| `ANP_ISIMP` export | `40_Pesquisa…\ANP_ISIMP` | This is the ANP lubricant product registry, not biomethane |
| Unrelated projects: city-budget georeferencing, Paranapiacaba, ATLAS 3.3, SDG toolbox, a poster on care facilities, presentations and videos | `50_Codigo…`, poster folder, `PILAR-2b Design System` | Outside the engine's scope |
| Duplicates: `Pilar2b` analysis and canonical files (sha256 identical to held copies), municipal meshes, MapBiomas infrastructure (`mapbiomas_infra`), PAM 1612/1613 (`ibge_pam_seade`), LAPIG vigour, worktree copies, `_REVISAO_DUPLICATAS_QUARENTENA` | several | Already held |

### 5.4 Code and derived work seen

- `Pilar2b\BiogasSP.gdb` holds the PILAR-2b ArcGIS analysis: LISA clusters, priority tiers, proximity tables, 910 ETE points, and 428 + 425 biogas plant points. These are derived outputs, kept for reference only.
- `50_Codigo…\Modelos_ILUC_GAMS` holds GTAP-BIO/AEZ GAMS models. They belong to the ILUC side and are not needed by the engine now.

### 5.5 Imported on 2026-10-05

Sixteen registry ids, 249 files, about 920 MB in `data/raw/`. Each copy is logged with its sha256 in `data/interim/import_local_holdings_log.tsv`:

| Registry id | Status before | Files | Size |
|---|---|---|---|
| `fiesp_sp_biomethane_2024` | get | 1 | 43.9 MB |
| `sinisa` (SNIS 2008–2022) | get | 16 | 316.7 MB |
| `cetesb_datageo_waste_indices` (IQR, IGR, IQC) | new | 57 | 222.4 MB |
| `cetesb_ictem_2024` | new | 7 | 27.7 MB |
| `ibge_ppm` | get | 4 | 17.7 MB |
| `dnit_snv` | get | 9 | 133.6 MB |
| `epe_webmap` | get | 56 | 10.6 MB |
| `cp2b_method_v5_1` | new | 64 | 57.9 MB |
| `cp2b_plant_validation_audit_2026_09` | new | 11 | 0.2 MB |
| `rais_industrial_coordinates_sp_2026_09` | new | 12 | 12.2 MB |
| `ibge_io_matrix_2015` | new | 1 | 1.3 MB |
| `epe_ben_2025` | new | 3 | 56.3 MB |
| `atlas_bioenergia_sp_2020` | new | 1 | 8.7 MB |
| `intl_de_dbfz_resources` | get | 5 | 7.7 MB |
| `epe_panorama_biometano_2023` | new | 1 | 1.0 MB |
| `abiogas_mapeamento_biometano_2032` | new | 1 | 0.4 MB |

The deny list in `engine.ingest.local_import` now also refuses the poultry and pig farm registries and the point layers derived from them, the origin–destination interview folder, the CEPAL transcriptions, participant lists and the credit-bureau folder.

Still open:

- Find the download URLs that the files do not record (IO matrix, BEN, EPE panorama, ABiogás note, Atlas). Until then the registry keeps `TODO`.
- Log `cp2b_method_v5_1` against `cp2b_redu_v2` in docs/21 §Conflicts.
- Extract FIESP values with page and verbatim quote.
- Not copied yet, by choice: the SIGA file (owner column), the MapBiomas annual rasters, the literature library and the OSM shapefiles.
- `data/raw/` changed, so `dvc add data/raw` and a new backup zip are needed.
