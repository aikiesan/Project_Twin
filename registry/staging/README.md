# Registry staging — proposed rows NOT yet merged

`projects_capex_proposed_R07.csv` holds 13 projects (ids 21–33) from research sweep R07 (`research_notes/R07_projects_costs_update_2026.md`).
- Every row is **S** (a search snippet or secondary news). No primary document could be opened, because the egress proxy blocked them.
- The adversarial verification pass did not run, because the session hit its usage limit.
- Merge a row into `../projects_capex.csv` only after checking its source. The MME REIDI portarias are the best primary source for paired capacity and CAPEX.
- Then run `make registry`.
