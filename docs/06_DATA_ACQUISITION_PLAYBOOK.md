# 06 — Data acquisition playbook (step by step per source)

General procedure for **every** source:
1. Confirm entry exists in `registry/sources.yaml` (add if missing).
2. Download with a script in `src/engine/ingest/<source_id>.py` (no manual downloads except where noted).
3. Save to `data/raw/<source_id>/<YYYY-MM-DD>/`; compute `sha256`; write `accessed`, `sha256`, `local_path` back to the registry.
4. `dvc add data/raw/<source_id>`; commit the `.dvc` pointer.
5. Write a 5-line `data/raw/<source_id>/README.md`: what, when, how, license, known issues.
6. Run the source's validation checks (below) and log results in `docs/21_RISKS_AND_OPEN_QUESTIONS.md` if anything is odd.

> Network note: some government sites block automated clients or require JS (Power BI). For those, download manually once, place the file in `data/raw/…`, and still register checksum + date.

---

## Priority 1 (Phase 0, week 1–2)

### 1.1 RenovaBio certification reports → mill-year panel ⭐
- **Where:** inspection-firm consultation pages (Benri `benriratings.com/consulta/publica/`, Accenture, SGS, KPMG, Verifit, Totum) + ANP certificate list (to know which mills/firms exist).
- **Steps:**
  1. Get ANP list of certified units (CNPJ, firm, validity) → list of SP units (~128).
  2. For each unit/firm, locate the consultation report (PDF) and RenovaCalc spreadsheet if published.
  3. Download all; store under `data/raw/renovabio_cert_reports/<cnpj>/`.
  4. Extract with `pdfplumber`/`pymupdf` + LLM structured extraction (schema `templates/extraction_schema_mill_year.json`), **with verbatim quote and page per value**.
  5. Manually audit a random 10 % of extracted values; record audit result.
- **Checks:** ethanol (L) / cane (t) ≈ 70–90 L/t; vinasse applied vs ethanol ratio flagged if < 8 or > 16 L/L (expect anomalies — log them).
- **Output:** `data/interim/mill_year_renovabio.parquet` (cnpj, year, cane_t, anhydrous_L, hydrated_L, vinasse_applied_L, filter_cake_t?, straw_t?, bagasse, electricity_MWh, neea, source_id, page, quote).

### 1.2 ANP ethanol producers (capacity, tankage, production)
- **Where:** ANP open data "Produção de biocombustíveis" + Painel Dinâmico de Produtores de Etanol (CSV downloads).
- **Checks:** SP plant count vs SAPCANA/NovaCana (~150–170); capacity units (m³/d).
- **Output:** `data/interim/anp_ethanol_plants.parquet` with CNPJ + coordinates.

### 1.3 ANP biomethane producers (capacity + monthly volume)
- **Where:** already in PILAR-2b (`analysis/data/05c_*`, `05e_*`); refresh from ANP panel.
- **Checks:** biogas vs biomethane capacity fields; `util_pct` definition; zero months = shutdown or missing report?

### 1.4 BNDES financing operations
- **Where:** `dadosabertos.bndes.gov.br/dataset/operacoes-financiamento` → CSV "operações não automáticas" (`;`, Windows-1252, decimal comma, ODbL).
- **Steps:** filter `descricao_do_projeto` for `biometano|biogás|biogas|vinhaça|purificação`; join CNPJ to facilities.
- **Output:** `data/interim/bndes_biomethane_ops.parquet` (value, rate, cost base, grace, term).

### 1.5 EPE technical notes (costs) and key regulations
- **Download PDFs:** EPE NT 2025-08 (+ Resumo), NT 2023-07, NT 2023-05; CNPE Res. 4/2026; ANP Res. 995, 996, 1.006/2026, 987/2025; ARSESP Del. 744/2017, 1.342/2022, 1.765/2025; Decreto 12.614/2025.
- **Action:** read and verify parameters (see `08_VERIFICATION_PROTOCOL.md`).

## Priority 2 (Phase 1)

| Source | Steps | Output |
|---|---|---|
| MAPA SAPCANA registry | Download full institution base (PDF/XLSX); parse | `sapcana_units.parquet` |
| UNICA biweekly (SP) 2008–2026 | Download quinzenal reports/tables; parse SP rows | `unica_sp_biweekly.parquet` |
| IBGE PPM (SIDRA 3939, 74) | SIDRA API by municipality, SP, 2008–2024 | `ppm_sp.parquet` |
| IEA-SP database | Query cane & herds by municipality | `ieasp_mun.parquet` |
| LUPA 2016/17 tables | Download municipal/EDR tables | `lupa_mun.parquet` |
| ANA ETE 2019 | Download SHP; filter SP | `ete_sp.gpkg` |
| SINISA | Download sewage & RSU modules | `sinisa_sp.parquet` |
| CETESB Inventário RSU | Download annual PDF annex; parse table | `rsu_sp.parquet` |
| MAPA SIF + SIGSIF | Download CSV; geocode SP | `sif_sp.gpkg` |
| Company reports | São Martinho, Raízen, Cocal sustainability/results | Validation table |

## Priority 3 (Phase 2–4)

| Source | Notes |
|---|---|
| MME Boletim Mensal Gás Natural | Monthly PDFs → parse price tables by distributor/segment |
| ARSESP tariffs | Tariff tables per concessionaire and adjustment |
| ANP fuel price survey | Weekly station-level CSV (diesel, GNV) — check what CP2B already has |
| B3 CBIO prices | Daily series |
| IEPUC/PUC-Rio biomethane bulletin | Monthly PDFs since Jul 2026 |
| IEA-SP land prices (VTN) | By municipality/EDR, semiannual |
| CONTRAN 882/2021, ANTT freight floor | Payloads, minimum freight |
| DER-SP SRE, DNIT SNV, OSM Sudeste | Routing graph |
| CAR/SICAR (SP) | Property polygons per municipality |
| ZAA sucroenergético | Reproject SAD-69 → SIRGAS 2000 |
| Rossi 2017 soils; MapBiomas Solo | Yield prior; digestate land capacity |
| FABDEM / Copernicus DEM | Slope |
| BR-DWGD, ERA5-Land, CHIRPS, INMET | Climate for heat balance & harvest interruptions |
| Zheng 2022 / Di Tommaso 2024 ESSD maps | Validate MapBiomas cane |
| International (`intl_*`) | See `15_INTERNATIONAL_BENCHMARKS.md` |

## Already held by CP2B (register them!)
Mill coordinates & data · MapBiomas cana 30 m 2008–2025 · SEADE/IBGE planted vs harvested 2008–2025 · UNICA SP totals 2008–2018 · gas transport/distribution/city gates/injection points · railways · transmission lines · roads · livestock points (state body) · exclusion layers · PILAR-2b FDE competing uses · energy consumption & prices · fuel prices · lab characterization references.
- [ ] For each: create registry entry with `status: have`, record provenance (who produced, when, from what).
