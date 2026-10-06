# registry/ — the project's source of truth for data and parameters

| File | Content | Key |
|---|---|---|
| `sources.yaml` | 118 datasets/documents: URL, granularity, access, status (`have/get/lai/paid/build`), confidence | `id` |
| `parameters.csv` | 83 model parameters: central, low, high, unit, source, confidence, notes | `id` |
| `projects_capex.csv` | 20 Brazilian biomethane projects: capacity (+ basis), investment, BNDES, year, status | `id` |
| `skeleton_mills.yaml` | Walking-skeleton inputs for the calibration mills: cane per crop year with source and flag, AD shares, strategy, ANP plant id (docs/13 §6) | mill id |
| `staging/` | Proposed rows not yet merged, and the digest queue (ADR-0012) | — |

## Confidence flags
`V` primary document read (page + quote recorded) · `S` snippet/abstract — verify · `K` prior knowledge — verify · `D` derived by us.

## Rules
1. Code reads parameters **only** from `parameters.csv` (or a scenario overlay), never hard-coded.
2. Add `page, quote, verified_by, verified_on, conditions, price_year, currency` columns when verifying (Phase 0).
3. Every downloaded dataset updates `accessed`, `sha256`, `local_path` in `sources.yaml`.
4. Partner/NDA sources: register with `access: confidential` and **no URL to private files**.
5. Conflicts → `docs/21_RISKS_AND_OPEN_QUESTIONS.md`, never silently overwrite.

## Validate
```bash
python -c "import yaml;d=yaml.safe_load(open('registry/sources.yaml'));print(len(d['sources']))"
python -c "import csv;print(sum(1 for _ in csv.DictReader(open('registry/parameters.csv'))))"
```
