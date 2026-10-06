# ADR-0012 — Intake of the daily digests into the repository

- **Status:** Accepted
- **Date:** 2026-10-06
- **Deciders:** project lead, with the AI-assisted session of 2026-10-06

## Context
Three automated digests arrive by e-mail every day:

- **CP2B Radar Biometano SP** (routine prompt in `templates/ROUTINE_RADAR_BIOMETANO_PROMPT.md`): regulation, prices, projects, data, science, tools, funding calls.
- **Arquivo NIPE-CP2B** (`templates/ROUTINE_ARQUIVO_NIPE_CP2B_PROMPT.md`): an institutional history of NIPE and CP2B.
- **Biogas & biomethane BR**: a short news digest.

They carry useful leads: new numbers, new data releases, dated regulatory events and projects. They also repeat items from earlier days, mix primary and secondary sources, and include derivations made by the routine itself. Without a fixed path into the repository, leads get lost or numbers enter `parameters.csv` without verification (CLAUDE.md §2 rules 1–2).

## Decision
1. **One dated triage note per digest day:** `research_notes/digests/YYYY-MM-DD.md`. It records every item taken, where it went, and the items not taken, each with a one-line reason.
2. **One running queue:** `registry/staging/digest_queue.csv`. Every new number, project, data source, method or dated event from a digest gets one row, with its URL, the digest's flag and our flag, the target file, the next action and a status. Column definitions are in `research_notes/digests/README.md`.
3. **A digest's `[V]` counts as `S` for us.** The routine reads the page but records no page number or verbatim quote, so the value does not meet `docs/08` §3. It becomes `V` only after someone records the page and quote.
4. **Numbers never go straight into `parameters.csv` or `projects_capex.csv`.** They wait in the queue until the primary document is read. The exceptions are notes on existing rows that say where a verification target stands.
5. **Each type of item has a fixed destination:**
   - dated regulatory events and deadlines → the watch list in `docs/16` §6;
   - price points → the snapshot in `docs/16` §3, with their basis (retail, distribution, excluding taxes);
   - new datasets → a stub in `registry/sources.yaml` (`status: get`, `confidence: S`);
   - data that is not downloadable → a LAI request in `docs/07`;
   - conflicts → `docs/21` §1;
   - method papers → `docs/23` and the module doc that will use them.
6. **Arquivo NIPE-CP2B:** only facts the engine uses are taken: grant numbers for LAI and partner requests, team members who are a route to data, and overlapping projects. The institutional history stays in that routine's own files.
7. **Never invent a missing URL.** When a digest gives no link for a number, the queue row says `URL missing`.

## Consequences
- \+ Every digest lead can be traced from the digest to the queue row to the registry change.
- \+ Verification effort stays with ADR-0010: a queued number is verified first when it feeds a top-ranked parameter, and otherwise when its module is built.
- − One more file to maintain each day. Triage of one day's three digests takes about 30–60 minutes.
- **Follow-up:** the radar prompt now asks for page and verbatim quote on `[V]` numbers, which makes the step from `S` to `V` faster. The deployed routine has to be updated by hand with the same text.

## Alternatives considered
- **Add digest numbers to `parameters.csv` as `S` rows right away.** Rejected: they would enter model runs and change `param_hash` before anyone read the source, and many are context, not parameters.
- **Weekly instead of daily triage (plan draft 24B, prompt P-8).** Kept as an option: on quiet days, triage can wait and cover several days in one note. Each note still lists its digest dates.
