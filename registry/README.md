# registry/ — the project's source of truth for data and parameters

| File | Content | Key |
|---|---|---|
| `sources.yaml` | 118 datasets/documents: URL, granularity, access, status (`have/get/lai/paid/build`), confidence | `id` |
| `parameters.csv` | 83 model parameters: central, low, high, unit, source, confidence, notes | `id` |
| `projects_capex.csv` | 20 Brazilian biomethane projects: capacity (+ basis), investment, BNDES, year, status | `id` |
| `references.csv` | 94 scientific references: bibliographic fields, `used_for` (what in the project each supports), identity double-check (`ref_check`, evidence URLs, date) and `value_check` per parameter (ADR-0013, docs/08 §8) | `ref_id` |
| `value_evidence.csv` | 141 value statements read in 7 publisher PDFs: PDF page, printed page, verbatim quote, value, unit, conditions, origin (own or cited), support for the parameter, and how the reading was checked (ADR-0015) | `evidence_id` |
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
6. A paper is cited only with a `references.csv` row (CLAUDE.md §2 rule 11). `references.csv` and `value_evidence.csv` are edited by hand from now on; the first population came from the 2026-10-06 checks, whose raw outputs are in `data/interim/extraction_raw/` (gitignored).
7. `value_evidence.csv` rows read by language models stay `llm_*` until a person compares them with the PDF and sets `check = human_audited` (docs/08 §6).

## Validate
```bash
python -m engine.registry validate    # all files; exit 1 on any error
python -m engine.registry summary     # counts by module, flag, status, ref_check and check
```
