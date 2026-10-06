# research_notes/digests/ — triage of the daily digests

Procedure: `docs/decisions/ADR-0012-daily-digest-intake.md`. One note per digest day (`YYYY-MM-DD.md`); every item taken also gets a row in `registry/staging/digest_queue.csv`.

## Checklist for one day
1. Read the day's digests: Radar Biometano, Arquivo NIPE-CP2B, Biogas & biomethane BR.
2. Skip the 🔁 items unless a number, date or status changed.
3. Classify each remaining item and send it to its destination:

| Kind | Destination | Rule |
|---|---|---|
| `parameter` | queue → `parameters.csv` after reading the primary source | Never straight into `parameters.csv`. A digest `[V]` is our `S`. If the source is a paper, it needs its `references.csv` row first |
| `project` | queue → `projects_capex.csv` after reading the source | Capacity with its basis (feed t/d, biogas or biomethane, harvest or annual); investment total separate from financing |
| `source` | stub in `sources.yaml` (`status: get`, `confidence: S`), or a note on the existing entry | No download link → LAI request in `docs/07` |
| `regulation` | watch list in `docs/16` §6 | Date, body, what it changes in the engine |
| `market_price` | snapshot in `docs/16` §3 | Keep the basis: retail, distribution, excluding taxes, FOB |
| `method` | `registry/references.csv` first (ADR-0013), then `docs/23` and the module doc that will use it | Two-source check of DOI, title, first author, year and journal; `used_for` names what it supports |
| `context` | this note; `docs/21` if it raises a question or a conflict | — |

4. Two sources disagree → `docs/21` §1, never an average.
5. Run `uv run python -m engine.registry validate`. It must report 0 errors.

## Queue columns (`registry/staging/digest_queue.csv`)
| Column | Meaning |
|---|---|
| `qid` | `YYYYMMDD-NN`, the digest date plus a running number |
| `digest_date`, `digest` | `radar`, `arquivo` or `biogas_br`; several are separated by `; ` |
| `kind` | `parameter`, `project`, `source`, `regulation`, `market_price`, `method`, `context` |
| `item`, `value`, `unit`, `basis_date` | What the digest says, in English, with units and the date or period of the value |
| `source_url` | The link given by the digest, or `URL missing` |
| `digest_flag` | The digest's own flag (`V` or `S`) |
| `our_flag` | Our flag under `docs/08`. Stays `S` until a page and a verbatim quote are recorded |
| `target` | File and id that the item will change |
| `action` | Next step |
| `status` | `open` (something left to do), `watch` (a dated event to follow), `hold` (a lead, no action now), `done`, `rejected` (reason in `action`) |
| `notes` | Anything else: inconsistencies, alternative URLs |

## Notes
| Date | Digests | Items queued |
|---|---|---|
| [2026-10-06](2026-10-06.md) | Radar (Tuesday, feedstock theme), Arquivo NIPE-CP2B (run 3), Biogas BR | 27 |
