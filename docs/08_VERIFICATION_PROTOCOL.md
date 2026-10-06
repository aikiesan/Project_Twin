# 08 — Verification protocol (how S/K becomes V)

## 1. Why
Most of the registry was compiled from search snippets and prior knowledge because primary sites were unreachable during planning. Papers and policy outputs must rest on **read, cited, page-referenced** values.

## 2. Flags
| Flag | Definition | Allowed in results? |
|---|---|---|
| **V** | Primary document opened; value, page/table and quote recorded | Yes |
| **S** | Seen in search snippet/abstract/secondary press | Only in sensitivity ranges, with caveat |
| **K** | Prior knowledge, not re-checked | No — verify first |
| **D** | Derived by us from other values | Yes if all inputs are V and the derivation is in code |

## 3. Procedure per parameter
1. Open the primary document (not a news article about it).
2. Find the value; record **page/table/figure** and a **verbatim quote** (≤ 2 sentences).
3. Record **conditions** (units, basis, temperature, scale, year, currency, price year).
4. Compare with registry value:
   - same → set flag `V`, add `page` and `quote`;
   - different → update value, set `V`, add a line to the **change log** below;
   - not found → keep `S/K`, note "not found in [doc]".
5. If two V sources disagree → **do not average**; add to `21_RISKS_AND_OPEN_QUESTIONS.md` §Conflicts and choose a rule (e.g. SP-specific > national > international; recent > old; measured > estimated).

## 4. Extended columns for `parameters.csv` (add during Phase 0)
`page`, `quote`, `verified_by`, `verified_on`, `conditions`, `price_year`, `currency`.

## 5. Verification order (highest leverage first)
1. EPE NT 2025-08 & 2023-07 (CAPEX factor, OPEX scope, LCOB ranges)
2. CNPE Res. 4/2026; ANP Res. 995/996/1.006/2026 (CGOB mechanics, spec)
3. ARSESP Del. 1.765/2025 (TUSD-Verde)
4. Volpi et al. 2021; Janke et al. 2015/2020; Fuess et al. 2018/2024; Moraes et al. 2015 (process)
5. IPCC 2019 Vol. 4 Ch. 10 (manure VS, B₀)
6. FIESP 2024 SP study (original report)
7. BNDES TD 159
8. Project announcements in `projects_capex.csv` (normalize capacity basis)
9. International: BIP TF4, DEA catalogue, Biogas-Messprogramm III

**Within the skeleton's parameters (from 2026-10-06), follow the Morris priority** (docs/13 §7, `priority.csv` of the latest `python -m engine.sensitivity morris` run). On the synthetic case the first rows are:
1. `vin_cod`;
2. `capex_epe`;
3. `wacc_real`;
4. `vin_gen`;
5. `cod_removal`;
6. `vin_ch4_yield`;
7. the filter-cake rows.

`ethanol_yield` needs a sourced range first (docs/21 Q13). Rows with no effect in the current chain (straw, OLR/HRT limits, SO₄ and K) can wait. A row becomes `V` only through its page and quote. The reference behind it must be `two_sources` in `references.csv` (§8).

## 6. LLM-assisted extraction rules
- Use LLMs to **locate and extract**, never to **supply** values.
- Output must include `source_id`, `page`, `quote`; reject rows without a quote.
- Human audit: random 10 % sample + all outliers (> 3 MAD).
- Keep the raw LLM output in `data/interim/extraction_raw/` for traceability.

## 7. Change log
| Date | Parameter id | Old | New | Flag | Source/page | By |
|---|---|---|---|---|---|---|
| | | | | | | |

## 8. References: tie to the project, double-check the source (2026-10-06, ADR-0013)
Every scientific reference has one row in `registry/references.csv`. There are two levels of checking, and they are not the same thing:

| Level | What is checked | Recorded as | Enough for |
|---|---|---|---|
| **1 — identity** | The cited work exists as cited. Its DOI, title, first author, year and container (journal, report series) are confirmed by **two independent sources** from different domains, for example the publisher page and a bibliographic index | `ref_check = two_sources`, the evidence URLs in `check_evidence`, and the date in `checked_on` | Citing the work in docs |
| **2 — value** | The value the project takes from it is found in the document | The parameter's `page` and `quote` (§3); `value_check = <id>=page_quote` on the reference | Flag `V` on the parameter |

Rules:
1. **`used_for` is mandatory.** It names what the reference supports: `parameters.csv:<id>`, a dataset (`sources.yaml:<id>`), a method or code path (`src/engine/...`), or a docs section. A reference that supports nothing in the project does not belong in the registry.
2. **Two sources means two different domains.** Two search results from the same site count as one. Search engines' generated summaries are not sources.
3. **Mismatches are fixed, not averaged.** When the DOI and the citation disagree (wrong suffix, wrong authors, wrong year), correct the row. Log the case in `docs/21` §1 when another file (for example PILAR-2b) carries the other version.
4. **Vague citations** ("AFBR 2024", "overview tables", "Embrapa") get `ref_check = unidentified`, with the candidate works listed in `notes`. The parameters that rest on them keep their flag and a note. Never pick a candidate by guess.
5. **`value_check`** records, per parameter, whether the value was seen:
   - `page_quote`: read in the document;
   - `seen_in_abstract`: in the abstract or a search snippet. This is still `S`;
   - `not_seen`;
   - `contradicted`: a different value for the same quantity. Log it in `docs/21` §1.
6. **The validator enforces the structure** (`python -m engine.registry validate`).
   - Errors: an unknown parameter id, `two_sources` without two evidence domains, a missing check date.
   - Warnings: a parameter citing a paper ("et al." or a DOI) with no reference row, a reference not double-checked, a `V` parameter whose references are not double-checked.

## Implementation status (v0 code, 2026-10)

**Implemented** in `src/engine/registry.py`. The loaders `load_parameters`, `get_param`, `load_sources` and `load_projects_capex` are unchanged. Tests are in `tests/test_registry.py`.

| Function | What it does |
|---|---|
| `validate_parameters(path)` | Checks `parameters.csv` and returns `list[Issue]` |
| `validate_sources(path)` | Checks `sources.yaml` and returns `list[Issue]` (line numbers come from the YAML node tree) |
| `validate_projects_capex(path)` | Checks `projects_capex.csv` and returns `list[Issue]` |
| `validate_all(registry_dir)` | Runs all three validators |
| `Issue(level, file, row, id, message)` | `level` is `error` or `warning`. `row` is the 1-based line in the file. `str(issue)` gives `ERROR file:line [id]: message` |
| `summary_markdown(registry_dir)` | Parameters: module × flag. Sources: module × status, and counts by flag. Projects: feedstock × flag. Also the validation counts |
| `param_hash(params=None, *, path, length=12)` | Short SHA-256 of `parameters.csv` (CRLF is normalised to LF), or of a dict of overrides as canonical JSON (keys sorted; `Param` and numpy scalars converted; `1` ≠ `1.0`) |
| `main(argv)` / `python -m engine.registry validate [--strict] \| summary \| hash [--registry-dir DIR]` | `validate` prints errors, then warnings. It exits 1 on any error, and also on warnings when `--strict` is given |

**Rules.** Anything not marked "warning" is an error.
- **parameters.csv**
  - The file has no BOM (a BOM breaks `load_parameters`), has all 10 columns, and every row has the header's number of fields.
  - `id` is non-empty, snake_case and unique.
  - `confidence` is exactly one of V/S/K/D. A compound flag such as `S/D` is an error.
  - `unit` and `source` are non-empty.
  - Numeric `low`, `central` and `high` satisfy `low <= central <= high` for **every pair that is numeric**. When only some values are numeric, the check still applies between those values, so `central=5, high=3` is an error even when `low` is blank.
  - Warnings: non-numeric `central`, `low` or `high` text (the raw text is kept in `Param.raw_*`); a blank `central`; a `V` flag without a non-empty `page` and `quote` (§3–4); an empty `module` or name.
- **sources.yaml**
  - Required, non-empty keys: `id, name, publisher, url, module, status, confidence`.
  - `id` is unique. A non-snake_case id is only a warning.
  - No duplicate keys inside an entry.
  - `status` is one of `have|get|lai|paid|build`.
  - `confidence` is one of V/S/K/D, after stripping any trailing `# comment`.
  - `url` is `http(s)://…`. An explicit placeholder (`TBD`, `confidential`, `<…>`, …) is a warning; anything else is an error.
  - Warnings: an `also:` item that is not http(s); missing `access` or `license`; `status: have` without `accessed`, `sha256` and `local_path` (CLAUDE.md §2 rule 3); a missing top-level `schema_version` or `updated`.
- **projects_capex.csv**
  - `id` is unique and non-empty.
  - `capacity_value`, when present, is numeric, > 0 and has a unit.
  - `confidence` is a single V/S/K/D flag.
  - `investment_total_R$M` and `bndes_R$M` are numeric and ≥ 0 when present.
  - `source` is non-empty.
  - Warnings: a `capacity_unit` that is not a gas flow (e.g. `MW`, `t/yr`); a flow in `m3` without the `N` reference basis; BNDES > total investment; a BOM (pandas tolerates it).

**State of the real registry on 2026-10-04:** 73 errors and 111 warnings. Nothing was edited. These are data gaps to fill from the sources, never by guessing.
- **sources.yaml: 72 errors.** All are missing required keys:
  - `publisher` is absent in 70 entries.
  - `url` is absent in 13: `ibge_pam_seade`, `mapbiomas_cana`, `essd_zheng_2022`, `s2_harvest_detection`, `livestock_points_sp`, `pilar2b_fde`, `anp_biomethane_plants`, `reg_lei_14993_2024`, `reg_cnpe_4_2026`, `reg_arsesp_744_1342`, `infra_gas_rail_power_roads`, `exclusion_layers` and `era5_land`.
  - `status` is absent in 7 of the 8 `reg_*` entries (all except `reg_lei_14993_2024`).
  - `confidence` is absent in 6: `ibge_pam_seade`, `mapbiomas_cana`, `livestock_points_sp`, `pilar2b_fde`, `infra_gas_rail_power_roads` and `exclusion_layers`.
- **sources.yaml: 91 warnings.**
  - 81 entries are missing `access` and/or `license`.
  - 10 `status: have` sources have an incomplete download record (`accessed`, `sha256`, `local_path`).
- **projects_capex.csv: 1 error.** Project 12 is flagged `S/D`.
- **projects_capex.csv: 13 warnings.** 12 capacities are in `m3/d` or `m3/yr` without a stated basis. Project 20 is in `MW`.
- **parameters.csv: 0 errors, 7 warnings.**
  - `vin_ts_vs`, `fc_ts_vs` and `fc_storage_loss` have non-numeric values.
  - `capacity_factor` has a blank `central`, and is flagged V without a page or quote.
- **Consequences.**
  - `python -m engine.registry validate` exits 1 today. The CI step that runs it fails until `sources.yaml` and project 12 are fixed.
  - `tests/test_registry.py::test_real_registry_has_no_validation_errors` passes for all three files since 2026-10-04, when the missing `publisher` and `status` fields were filled. If a registry error comes back, the test xfails and lists every error, and CI fails at the `engine.registry validate` step.

**Limitations.**
- No network access, so URLs and DOIs are checked only for form, not for whether they resolve.
- A `V` flag is checked only for the presence of `page` and `quote`, not their content.
- For a CSV record that spans several lines, the line number is the record's last line.
- The `access` and `license` "optional key" list is our choice. The registry header only names `accessed`, `sha256` and `local_path`.

**What remains.**
- Fill the missing `publisher`, `url`, `status` and `confidence` fields from the primary sources.
- Pick a single flag for project 12.
- Add the §4 extended columns (`page`, `quote`, `verified_by`, …). Once they exist, the V check becomes meaningful.
- Optionally, generate the §7 change log from diffs of `param_hash` and the CSV.
