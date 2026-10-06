# ADR-0015 — Value evidence: page and quote per value, read twice from the publisher PDF, audited by a person

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** project lead (requests of 2026-10-06: "always tie the reference of scientific paper to the project, to values and data, always need to have a valid double-checked source"; "keep working … propose and follow more steps")

## Context
- **The gap to `V`.** ADR-0013 separated two checks: the *identity* of a reference and the *value* the project takes from it. Only a page and a verbatim quote make a parameter `V` (docs/08 §3–4). On 2026-10-06 no process parameter had them.
- **Papers in hand.** Seven publisher PDFs behind the top-ranked process parameters of the Morris screen (ADR-0014) were in the project's Google Drive:
  - Janke et al. 2019;
  - Fuess et al. 2022;
  - Volpi et al. 2021;
  - Silva Neto et al. 2021;
  - Barros et al. 2017;
  - Aguiar et al. 2026;
  - Sica et al. 2020.
- **What one reading cannot carry.** One paper gives many numbers for one parameter: its own measurements, values it cites from others, ranges, and other bases (COD vs VS, Nm³ vs NL, mesophilic vs thermophilic). A single `page`/`quote` cell in `parameters.csv` holds one of them. It cannot hold the bounds, the rival values, or the values a paper cites from elsewhere.
- **The reader.** The readings were made by language models. They can misplace a page, scramble a quote extracted from a two-column PDF, or label a value as supporting when it does not.

## Decision
1. **`registry/value_evidence.csv` holds one row per value statement read in a reference.**
   - Columns: `evidence_id`, `param_id`, `ref_id`, `pdf_page`, `printed_page`, `location`, `quote`, `value`, `unit`, `conditions`, `origin`, `support`, `check`, `cited_ref`, `notes`.
   - `pdf_page` is the page of the file. `printed_page` is the journal's number.
   - The first population is 141 statements from the seven PDFs above.
2. **Each statement was read twice, independently.**
   - An extraction agent read the PDF (text and page numbers from Google Drive) and proposed a quote, value, page, origin and support per parameter.
   - A second agent re-read the same PDF without trusting the first. It returned `confirmed`, `misquoted` or `misread`, and judged origin and support separately.
   - `check` records the outcome:
     - `llm_double_read` (128 rows): both reads agree on quote, page, origin and support.
     - `llm_support_disputed` (10 rows): the quote is right, but the support label was disputed. The verifier's reason is in `notes`.
     - `llm_corrected` (3 rows, all Volpi et al. 2021): the second read corrected the quote, page or value. The row carries the corrected reading, and `notes` keeps what was wrong.
     - `human_audited`: reserved for a person who has checked the row against the PDF. None yet.
3. **`human_audited` is the only check that meets docs/08 §6.** Until a person audits a row, a parameter that rests on it may be moved to `V` only with `verified_by` saying "LLM … human audit pending". The validator emits one warning for every file that has rows not yet audited.
4. **`origin` and `cited_ref` keep borrowed numbers apart.**
   - `origin=cited` means the paper reports another work's value.
   - `cited_ref` transcribes that other work's reference as the paper prints it. It is **not** a project citation, and it is not double-checked. A value taken from it needs its own `references.csv` row and its own check (rule 11).
5. **`value_check` in `references.csv` judges the parameter's *central* value only.**
   - `page_quote`: the central value is printed on a recorded page.
   - `contradicted`: the paper's own value for the same quantity differs.
   - `not_seen`: the paper does not state the central value.
   - Bounds, related values and other bases go to `value_evidence.csv`. When they disagree with the registry, they go to docs/21 as a conflict and are not averaged (rule 7).
6. **What is not written.**
   - The second reader also listed 52 statements the first had missed. They stay in the raw run output (`data/interim/extraction_raw/pdf_value_check_raw.json`, gitignored). They are not in the registry, because no second read checked them.
   - No parameter value is changed by this ADR. Mismatches are logged in docs/21 (C16–C26) as proposals for the registry owner.
7. **The validator enforces the shape** (`validate_value_evidence`, run by `python -m engine.registry validate`).
   - `evidence_id` is unique.
   - `param_id` and `ref_id` exist.
   - `pdf_page` is a positive integer.
   - `quote` is non-empty.
   - `origin`, `support` and `check` are in their enums.

## Consequences
- \+ Every value a reviewed paper gives for a registry parameter is traceable to a page and a verbatim quote, including the ones that disagree.
- \+ Two parameters (`codig_bmp`, `temp`) can move to `V` with an explicit "human audit pending" caveat.
- \+ The reading surfaced mismatches the free-text `source` column hid (docs/21 C16–C26). Examples:
  - a mis-dated Janke reference;
  - a vinasse TS/VS central that equals an inoculum's;
  - a CH₄ yield whose central the cited papers do not print.
- − 141 rows wait for a human audit (docs/08 §6): every row behind a `V` parameter, all outliers, and a 10 % random sample, with the PDF open beside the CSV.
- − Text extracted from two-column PDFs can interleave columns. The three corrected rows show that a quote must be compared with the printed page, not with the extraction.
- **Follow-up:**
  - **PDF pass 2:** the papers behind the remaining top-ranked `S` parameters (Moraes 2015, Fuess 2018, Melo 2024, Leite/Janke 2015 IJMS, Kiyuna 2017, Ferraz 2016), once their PDFs are in hand.
  - **Audit sheet:** a short human-audit checklist per paper.

## Alternatives considered
- **More columns in `parameters.csv` (`page2`, `quote2`, …):** rejected. One row per value statement is the natural grain, and it keeps the parameter schema stable.
- **Accepting single LLM readings:** rejected. The second read corrected 3 of the 141 statements and disputed the support label of 10 more.
- **Promoting every confirmed central value to `V` at once:** rejected. Only `codig_bmp` and `temp` have their central value printed. The others are `not_seen` or `contradicted` for the central value, even where the range is supported.
