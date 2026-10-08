# ESD N3 supply grid (1 km): read-only inventory

- **Date:** 2026-10-08. Read by Claude; nothing was copied out of the ESD folder.
- **Folder:** `C:\Users\Lucas\Documents\Reposicionamento_Submissão_ESD\Metodo_CP2b\fl_espacial\`.
- **Note from Lucas (2026-10-08):** the project's final data are the CP2b method v5.1 and v5.2 outputs in this folder, not the REDU v2 dataset. This matters for docs/21 C35: the grid below is CP2b v5.1.

## 1. The file

| Item | Value |
|---|---|
| Path | `Metodo_CP2b/fl_espacial/outputs/grade_oferta_1km.gpkg` |
| Written by | `fl_espacial/02_oferta.py`, lines 430–439 (v5.1 run of 2026-09-24) |
| Format | GeoPackage, two layers: `celulas` (1 km squares) and `pontos` (facility points) |
| Size | 62,459,904 bytes |
| sha256 | `c4bfbc72e83e81bff4b52061fc759c2d1cfa9129d0e63e65ac559cdc165303cf` |
| CRS | EPSG:5880 (SIRGAS 2000 / Brazil Polyconic); `config_fl.yaml` line 7 |
| Cell size | 1,000 m (`config_fl.yaml` line 57, `grade.celula_oferta_m`) |
| `celulas` | 189,887 polygons; bounds x 5,094,000–6,010,000, y 7,196,000–7,807,000 m |
| `pontos` | 456 points: mills, active non-lagoon sewage plants, juice factories |

An older copy, `outputs_v5.0_bak/grade_oferta_1km.gpkg` (63,725,568 bytes), is the v5.0 run, before citrus pulp moved to the juice factories. Do not use it.

**Link to `fl_comum.Bacias`.** `Bacias` does not read the gpkg. It reads the per-km histograms `cache/hist_F.npy` and `cache/hist_D.npy`, which `04_bacias_fl.py` builds from the same supply in `cache/oferta_wide.pkl` and `cache/oferta_locais.pkl`. The gpkg is the written, aggregated form of that supply.

## 2. Columns and units

- **Keys:**
  - `celulas`: `cell_id`, the 1 km grid id, `iy * nx + ix` (`fl_comum.Grade`);
  - `pontos`: `loc` (negative id), `tipo`, `ref`, `nome`, `ibge`.
- **Values:** 48 columns `<RESIDUE>__<scenario>`, 16 residues × `min` / `med` / `max`.
- **Unit:** **Nm³ CH₄ per day**, N3 (mobilisable) potential. `02_oferta.py`, line 4: "N3 municipal (Nm³ CH4/ano ÷ 365)". `config_fl.yaml`, line 3: "oferta em Nm³ CH4/dia". The value is methane, not biogas or biomethane, per residue; there is no total column.
- **Closure:** each municipality's N3 is shared out by weight. Grid sums equal municipal sums within 0.01% (`config_fl.yaml` line 113; `outputs/oferta_totais_verificacao.csv`, `dif_rel` = 0.0).

**Totals I summed from the file:**

| Layer | min | med | max |
|---|---:|---:|---:|
| `celulas` | 4,830,862 | 11,691,311 | 27,662,312 |
| `pontos` | 2,900,410 | 7,491,890 | 16,210,586 |
| **Both** | 7,731,272 | **19,183,201** | 43,872,898 |

The med total matches N3 med = 19.183 M Nm³ CH₄/d in `outputs_v5/artigo/T1_state_levels.csv`.

`BOV_PASTO_MISTO` is not in the grid. `config_fl.yaml` line 102 marks it `ignorar`: N3 = 0 in min and med, and the max keeps the yaml FL. So the max total above is 1,087,771 Nm³/d short of T1's 44,960,669. *Correction 2026-10-08:* this note first gave the max total as 44,872,898 and the gap as 87,771. 27,662,312 + 16,210,586 = 43,872,898, and `urban_ceiling.py` sums the gpkg max to 43,872,898.1 (`docs/inbox/urban_ceiling_run.txt`). Whether `BOV_PASTO_MISTO` alone explains the 1.09 M gap in T1's max has not been checked.

## 3. What feeds each residue (from `config_fl.yaml` lines 88–105 and `02_oferta.py`)

| Residue | Layer | Where it sits | Weight inside the municipality | Source |
|---|---|---|---|---|
| VINHACA | pontos | mills | ethanol capacity | EPE/MapBiomas `usina_etanol.shp` |
| TORTA_FILTRO, BAGACO | pontos | mills | cane capacity class | same |
| BAGACO_CITROS | pontos | juice factories, one point per municipality | RAIS jobs, CNAE 1033-3/01, ≥ 100 jobs | RAIS staging (anonymous) |
| LODO_ETE | pontos | sewage plants | equal shares | PILAR `ETEs_2019_SP.shp` |
| PALHA | celulas | cane pixels | MapBiomas 2024 class 20 area | MapBiomas 10.1 |
| PALHA_MILHO | celulas | pixels | classes 41 + 2nd-crop 41 | MapBiomas |
| PALHA_SOJA | celulas | pixels | class 39 | MapBiomas |
| CASCA_CAFE | celulas | pixels | class 46 | MapBiomas |
| RSU_ORGANICO, PODA_URBANA | celulas | urban area | urban area | PILAR `Areas_Urbanas_SP.shp` |
| AVES_CORTE, AVES_POSTURA | celulas | **farm points summed per 1 km cell** | max. housing capacity | **GEDAVE poultry register** (`Relatorio_0082803826_granjas_aves_UNICAMP.xlsx`) |
| SUINOS | celulas | **farm points summed per cell** | estimated herd (`plantel`) | **`farms_for_gee.csv`** (outside the folder) |
| BOV_LEITE, BOV_CONFINADO | celulas | **farm points summed per cell** | herd stock (`SALDO_GERAL`) | **GEDAVE cattle register of 2025-11-03** (outside the folder; it holds CPF/CNPJ and owner names) |

**Fallback when a municipality has N3 but no weight point** (`completar`, `02_oferta.py` line 194; counts from `outputs/oferta_fallback_casos.csv`):
- poultry: any poultry farm in the municipality, used for 231 (broiler) and 282 (layer) municipalities; otherwise the farm-land centroid, 52 each;
- cattle: any cattle record, 4 (feedlot) and 2 (dairy) municipalities; farm-land centroid, 1 (dairy);
- swine: farm-land centroid, 21; municipal centroid, 1;
- coffee: centroid, 67; straw: 36; maize: 7; soybean: 7; sewage sludge: urban centroid, 26.

## 4. LGPD: the poultry, swine and cattle columns come from farm-level registers

**Yes.** Five columns (AVES_CORTE, AVES_POSTURA, SUINOS, BOV_LEITE, BOV_CONFINADO, each × 3 scenarios) are municipal N3 shared out in proportion to the capacity or herd of individual georeferenced farms.
- `w_pontos` (line 180) sums the points per 1 km cell, so no single point is written. But a cell holding one farm carries a value proportional to that farm's own capacity, inside a known municipality.
- Farm-level counts, as logged in `logs/02_oferta.log` (the registers were not opened here):
  - poultry: 17,164 valid establishments, of which broiler 2,617 and layer 671;
  - swine: 12,547 farms;
  - cattle: 115,351 points, of which dairy or mixed 37,463 and feedlot 424.
- Cells with a value > 0 in the grid (med):
  - AVES_CORTE 4,584; AVES_POSTURA 3,389;
  - SUINOS 9,064;
  - BOV_LEITE 26,767; BOV_CONFINADO 661.
  - These counts include fallback cells, so they are not farm counts.

**Cells with exactly one farm: not determined.** The gpkg stores aggregated values only. Counting farms per cell needs the point registers (GEDAVE xlsx, the GEDAVE cattle csv, `farms_for_gee.csv`), and I was told not to open them.
- The feedlot case shows the risk: 424 feedlot records spread over 661 cells with a value. Many cells must hold a single feedlot, or fallback weight.
- The count should be made by someone allowed to read the registers.
- Until then, treat these five residues in the grid as personal-data derived. They are usable in the engine only after aggregation to a coarser unit (H3 res 7, or the 30 km sums of the suitability grid), with a minimum-count rule such as k ≥ 3 farms. They should never be exported cell by cell.

## 5. Use in Project_Twin (proposal, not done)

- Replacing the four feedstock criteria of `score_grid_v0.py` with one "N3 CH₄ within 30 km" criterion (ADR-0017 discussion) can use this grid.
- Register it in `sources.yaml` as a derived dataset (flag D, sha256 above, CP2b v5.1).
- The register-derived residues would enter only after the aggregation rule in §4. The non-farm residues (straw, vinasse, filter cake, bagasse, MSW, sludge, crops) carry no personal data.
