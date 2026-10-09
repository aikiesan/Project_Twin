# ADR-0013 — A references registry: every paper tied to project values, every source double-checked

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** project lead (request of 2026-10-06: "always tie the reference of scientific paper to the project, to values and data, always need to have a valid double-checked source")

## Context
- **Where papers were cited.** Scientific papers appeared in three places: `docs/23_REFERENCES.md`, the free-text `source` column of `parameters.csv`, and the digests. None of them said which project values a paper supports.
- **How they were flagged.** Most papers carried `S` or `K`. None had been checked, not even for whether its DOI was the right one.
- **A known mismatch.** One error was already on record: the vinasse review's DOI differs between this repository and PILAR-2b (docs/21 C14).
- **What this session can reach.** Its network blocks doi.org, Crossref and publisher pages. Only web search is reachable, which is enough to cross-check bibliographic identity across independent sites but not to read the papers.

## Decision
1. **`registry/references.csv` is the single list of scientific references.** Each row has:
   - the bibliographic fields;
   - `used_for` (what in the project it supports);
   - the outcome of an identity check (`ref_check`), with the evidence URLs and the date;
   - `value_check`, per parameter value.
2. **Two levels, kept apart (docs/08 §8).**
   - **Identity:** double-checked by two independent sources.
   - **Value:** the page and a verbatim quote, which is what makes a parameter `V`.

   An identity check never upgrades a value's flag.
3. **The registry validator enforces the links and the evidence.**
   - Errors: unknown parameter ids, `two_sources` without two evidence domains, no check date.
   - Warnings: parameters citing papers with no reference row, references not double-checked, `V` parameters resting on unchecked references.
4. **The first population of `references.csv` comes from a three-pass check.** Each reference was checked by an agent, re-checked by an adversarial agent with its own searches, and sent to a third tie-break agent when the two did not both confirm it. A row is `two_sources` only when the passes agree and two domains confirm it.
   *As run (2026-10-06):* the verify and tie-break passes ran out of search budget for most rows. Identity was then established by two more routes, each needing two independent sources: the first page of a publisher PDF in hand, and the reference lists of those PDFs (docs/08 §8 rule 6). Rows that no route covered stay `pending`, `unconfirmed` or `unidentified`.
5. **CLAUDE.md §2 gains rule 11.** The digest intake (ADR-0012) and the radar prompt require a DOI and the two-source check before a paper enters `docs/23`.

## Consequences
- \+ Every number in the registry can be traced to a paper whose identity was confirmed, and the gap to `V` is visible per parameter.
- \+ Wrong DOIs and authors are caught before they are cited (C14 is the first case).
- − One more registry file to maintain; references without a DOI (grey literature, standards) can only reach `one_source` or `unconfirmed` until someone with library access checks them.
- **Follow-up:** read the papers behind the top-ranked parameters of the Morris screen (ADR-0010) to move their values to `V`. Many of them are in the local holdings (docs/25).

## Alternatives considered
- **A BibTeX/Zotero library** (as docs/23 once planned): kept as an export option. It cannot express `used_for` or the check outcome, which are the point.
- **Adding a `ref_ids` column to `parameters.csv`:** rejected for now, because it changes the parameter schema and the loader. The link lives in `references.csv` (`used_for`), and the validator reads it in both directions.
