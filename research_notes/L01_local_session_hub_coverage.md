# L01 — Brief for a local Claude Code session: hub coverage on the PC (2026-10-09)

Paste into Claude Code on the PC: *"Read `research_notes/L01_local_session_hub_coverage.md` and do it."*

Why local: the inputs (N3 grid gpkg, candidate grid, ESD code and outputs) live only on this PC and
stay out of git. The cloud session keeps the registry and evidence work; both push to the same branch.

## Before anything
- `git pull origin claude/tender-babbage-ykpb2r`, then `uv sync`. Pull again before every push.
- Read `CLAUDE.md`, `docs/decisions/ADR-0018-greedy-hub-coverage-min-scale.md` and the hub coverage
  subsection of `docs/12_MODULE_SITING_LOGISTICS.md` (Step 1).
- `PYTHONPATH=src uv run pytest -q tests/test_siting_coverage.py` must pass.
- Run commands as `PYTHONPATH=src uv run python …` in Git Bash.

## Guardrails (on top of CLAUDE.md)
- **LGPD.** Never open, merge or export the GEDAVE registers (`Relatorio_0082803826_granjas_aves_UNICAMP.xlsx`,
  `Relatorio_0082804098_granjas_sui_UNICAMP.xlsx`, the GEDAVE cattle register), `farms_for_gee.csv`, or
  anything under `Serasa_Danilo_Milho2`. The N3 farm columns (AVES_CORTE, AVES_POSTURA, SUINOS, BOV_LEITE,
  BOV_CONFINADO) leave the PC only aggregated per hub with the script's k = 3 rule; never per cell.
- Do not open `06_DOCUMENTOS_ADMINISTRATIVOS` or the ILUC/ABIOVE material (`05_ILUC_Fontes_Primarias`):
  partner data until the terms are confirmed.
- Nothing from `data/` goes into git. Never paste the database password or commit `.env`.
- Do not change `src/engine/siting/coverage.py` or the script without a test and a docs/12 update in the
  same commit. Do not merge `registry/inbox/` rows into the registry.
- ESD values are flag **S** (no external source). Do not present them as sourced.

## Tasks, in order
1. **List.** `scripts/siting/hub_coverage_v0.py "$GPKG" "$GRID/suitability_grid_v0.parquet" --list`.
   Note the residue names and the `tipo` values (which one is the mills).
2. **Class mapping from the ESD.** In `Metodo_CP2b/fl_espacial/config_fl.yaml` (and the code that reads it),
   find how each residue gets its class (liquid / wet solid / dry solid) and how straw is handled. Write
   `registry/inbox/esd_residue_classes.csv` with columns `residue,class,source_file,lines,quote`
   (verbatim YAML lines). If a gpkg residue has no class in the ESD, leave it out and say so.
3. **Runs** (outputs stay in `$GRID`), with the ESD values, flag S:
   - med: `--classes registry/inbox/esd_residue_classes.csv --radius <liquid>=5:15 --radius <wet>=15:30
     --radius <dry>=10:25 --q-min 1500 --detour-factor 1.295 --scenario med --tag _esdmed`, plus the
     straw handling the ESD uses (if straw is its own class with percentile radii: med P75/P95 =
     27.17:41.68 km, registry `straw_mill_road_km_p75`/`p95`, D; `--only-to PALHA=<mill tipo>`);
   - the same without straw (`--skip PALHA`, `--tag _esdmed_nostraw`);
   - min (radii 3:10, 10:20, 5:15; q_min 3200; straw 19.51:35.22) and max (10:20, 20:45, 15:40; q_min 500;
     straw 35.22:53.8) if the med runs finish in reasonable time.
   Use the class names from step 2 in `--radius`. If memory runs out, report it; do not change the defaults.
4. **Compare with the ESD `mclp.csv`** (v5.1 med). Record its path, header and row count. Benchmarks read in
   the inventory (`docs/inbox/esd_inventory.md` §2 M1): 455 hubs (423 grid + 32 existing); with straw at the
   mills 16 / 114 hubs for 50 / 80 % of total N3; without straw 55 / 143. Put ours next to theirs.
5. **Q24 (detour factor).** Find the ESD code that writes `tortuosidade_resumo.csv`. Record the file, line
   numbers and the verbatim lines that compute the denominator: planar distance in EPSG:5880, haversine,
   or geodesic.
6. **Existing biogas plants.** Find the file behind the ESD's 133 existing biogas plant candidates: path,
   origin, columns. Do not use it in a run until it is registered in `registry/sources.yaml`.

## What to commit
- `registry/inbox/esd_residue_classes.csv`.
- `docs/inbox/hub_coverage_v0_<scenario><tag>_meta.json` and `_hubs.csv` for each run. They are per hub with the
  k = 3 rule. Copy them from `$GRID`, do not move them.
- `docs/inbox/hub_coverage_vs_esd.md`: steps 1, 4, 5 and 6 (residue list, comparison table, the Q24
  lines, the biogas plant file), with run_ids and the parameter hashes from the meta files.
- Before the commit: `PYTHONPATH=src uv run python -m engine.registry validate`, `pytest -q`,
  `ruff check . && black --check .`. Then pull, commit, `git push -u origin claude/tender-babbage-ykpb2r`.
