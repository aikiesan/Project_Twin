# ADR-0008 — Tidy CSV templates as the contract between labs and the engine

- **Status:** Proposed
- **Context:** Experiments E1–E9 (LABIOEN, PPBIOEN, CEMARA) produce the parameters with the highest model leverage (storage losses, OLR limits, BMP→full-scale factor). Lab spreadsheets vary in layout and units; partner material identities are confidential.
- **Decision:** All lab/pilot data enter the engine through the CSV templates in `templates/lab/` (units in column names; one row per bottle×day, reactor×day or sample), validated by `engine.calibrate.lab`. Raw files live in `data/private/lab/<experiment_id>/`; partner names are replaced by codes. Results become registry rows with flag **V** and the experiment as source.
- **Consequences:** + reproducible parameter derivation, automatic kinetic fits and validity checks; − labs must export to the template (or a small converter per lab format).
