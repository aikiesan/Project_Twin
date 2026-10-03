# 14 — Where ML and AI help (and where they don't)

## Principle
**ML/statistics estimate "what is"** (states we cannot observe directly). **Mechanistic models answer "what if"** (new plants, new mixes, new prices). Supervised ML needs labels; mass balances are engineering, not patterns to learn.

## Ranked roles

| # | Role | Method | Data / labels | Value |
|---|---|---|---|---|
| 1 | **Document harvesting** | LLM structured extraction with verbatim quote + page | RenovaBio reports, BNDES descriptions, ANP/ARSESP acts, company reports, project news | ★★★ saves months |
| 2 | **Entity resolution** | CNPJ keys + fuzzy matching + LLM adjudication | ANP, SAPCANA, RenovaBio, BNDES, CP2B list | ★★★ |
| 3 | **Remote sensing** | Rule-based/DL harvest detection on Sentinel-2/1, Landsat | MapBiomas, UNICA totals for validation | ★★★ seasonality + mill activity |
| 4 | **Downscaling with aggregate constraints** | Bayesian hierarchical / Huff calibration; IPF/cross-entropy | IBGE municipal, RenovaBio mill-year | ★★★ core of supply |
| 5 | **Gap-filling** | Mixed-effects or gradient boosting for mills without RenovaBio | RenovaBio mills as labels (~100) | ★★ (compare with hierarchical Bayes) |
| 6 | **Cost model** | Hierarchical Bayesian regression | Brazilian + international projects | ★★ |
| 7 | **Surrogates** | Gaussian process / boosting emulating LCOB | Simulator runs | ★★ speed for web app & Sobol |
| 8 | **Anomaly detection** | Robust z-scores, isolation forest | ANP monthly, extracted tables | ★ QA |

## What ML must NOT do here
- Invent missing ground truth (no labels → no supervised model).
- Learn stoichiometry or mass balances.
- Extrapolate to plant configurations that don't exist in data.
- Supply parameter values from an LLM's memory (LLMs extract, never source).

## LLM extraction pipeline (sketch)
```
PDF → text/tables (pdfplumber, pymupdf) → chunk by page
    → LLM with JSON schema (templates/extraction_schema_mill_year.json)
    → validator: units, ranges, quote present, page present
    → human audit 10 % + outliers → data/interim/*.parquet
```
- Keep model name/version and prompt hash in run manifest.
- Use a Claude model via API for extraction (choose the current model at implementation time).

## Remote sensing pipeline (sketch)
```
GEE or STAC (Planetary Computer) → S2 L2A cloud-masked NDVI, B8A, B11 (+ S1 VH)
    → per-field/per-H3 time series → harvest event detection
    → monthly harvested area per mill catchment → validate vs UNICA
```
