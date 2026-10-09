# WebGIS: suitability explorer

`aptidao_biometano_sp.html` is a single-file map for the suitability screen v0 (ADR-0016,
docs/12 Step 2). Open it in a browser straight from disk. It holds no data: it opens on a
**synthetic example** (clearly labelled), and you load the real grid with the file picker.

1. Build the grid on the PC (`suitability_grid_v0.parquet`, cells at H3 res 7).
2. `uv run python scripts/siting/score_grid_v0.py <folder with the parquet>` writes
   `suitability_map_v0.csv` (plus scores, bounds, sensitivity tables and a meta JSON) next to it.
3. In the page, choose `suitability_map_v0.csv`.

What it does, all in the browser:
- per-criterion weight sliders (0 = left out) and an equal-weights button; the score is the
  weighted linear combination of the `n_*` columns, as `engine.siting.suitability.score`;
- robustness: Dirichlet weight draws around the current weights (draws, top-k, concentration,
  seed), coloured by the share of draws in which a cell is in the top k;
- excluded cells (state protected areas, indigenous territories) are shown and never scored;
- click or hover a cell for its values; the table lists the 15 best cells.

CSV contract: `h3_index`, `ibge_code`, optional `municipio` (name, from `score_grid_v0.py --names`), `lat`, `lon`, `excluded` (0/1), one `n_<criterion>`
column per criterion in [0, 1] (1 = best); any other column shows in the tooltip.

Needs `h3-js` from cdn.jsdelivr.net (without it, cells draw as squares and hover is off).
The CSV stays on your machine; nothing is uploaded. The map is a screen, not a site choice:
distances are straight-line, the gas layer is a trunk summary (docs/21 Q17), and exclusions
are incomplete (urban, water, APP, slope still to add).
