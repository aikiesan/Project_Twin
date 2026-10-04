# Lab & pilot data templates (LABIOEN · PPBIOEN · CEMARA)

These CSV templates connect experiments E1–E9 (`docs/17_LAB_AND_PILOT_EXPERIMENTS.md`) to the
engine. Code: `src/engine/calibrate/lab.py` (validation, BMP kinetics fits, CSTR summaries,
proposed registry rows).

| Template | One row per | Feeds |
|---|---|---|
| `substrate_characterization_template.csv` | sample analysed | `vin_*`, `fc_ts_vs`, TS/VS/COD/SO₄/K/N for `engine.process.substrates` |
| `bmp_results_template.csv` | bottle × reading day | `fc_bmp`, `straw_bmp`, `codig_bmp`, first-order *k* (E6), storage loss curve (E1) |
| `cstr_daily_log_template.csv` | reactor × day | OLR/HRT limits, specific yield, `bmp_fullscale`, stability (E3, E4, E5, E9) |

## Rules
1. **Units are in the column names** (`cum_ch4_nml` = NmL CH₄ at 0 °C, 1 atm, dry; convert
   before entering if your gas meter reports at ambient conditions — record the method in `notes`).
2. `role` in BMP files: `sample`, `blank` (inoculum only), `positive_control` (e.g. cellulose).
3. Partner identities: use codes (`millA`), never company names, in any file that may become public.
   Raw partner data live in `data/private/lab/<experiment_id>/` (never in git — CLAUDE.md rule 6).
4. Delete the synthetic example rows before use.
5. After analysis, results enter `registry/parameters.csv` with flag **V** and source
   `CP2B <lab> <experiment_id> (internal report <date>)`; `lab.proposed_registry_rows()` drafts them.

## Validity criteria
Apply the BMP validation criteria of Holliger et al. (2016), "Towards a standardization of biomethane potential tests", *Water Sci. Technol.* (verify volume/pages before citing)
— pass the thresholds explicitly to `lab.bmp_validity()` after checking the paper; the code
does not hard-code them.
