# Registry staging — proposed rows NOT yet merged

`projects_capex_proposed_R07.csv` holds 13 projects (ids 21–33) from research sweep R07 (`research_notes/R07_projects_costs_update_2026.md`).
- Every row is **S** (a search snippet or secondary news). No primary document could be opened, because the egress proxy blocked them.
- The adversarial verification pass did not run, because the session hit its usage limit.
- Merge a row into `../projects_capex.csv` only after checking its source. The MME REIDI portarias are the best primary source for paired capacity and CAPEX.
- Then run `make registry`.

`inventory_raw_2026-10-04.csv` (one row per dataset, per-file sha256) and `inventory_raw_folders_2026-10-04.csv` (one row per `data/raw/<source_id>/`, folder digest from `engine.ingest.inventory.sha256_tree`) record the 2026-10-04 imports: from `A:/Pilar-2b` (git `1d24ada5+dirty`, 13 folders) and from other local folders via `scripts/ingest/local_holdings.yaml` (9 folders).
- The folder digests are the `sha256` values in `../sources.yaml`.
- These are records, not proposals: re-run the inventory and compare to detect any change in `data/raw/`.

`digest_queue.csv` is the running queue of leads from the daily digests (ADR-0012; columns in `../../research_notes/digests/README.md`).
- A digest's `[V]` is kept as `digest_flag`; `our_flag` stays `S` until someone records a page and a verbatim quote.
- Rows with `status: open` still need an action. Numbers move to `../parameters.csv` or `../projects_capex.csv` only after their source is read.
