# 03 — Architecture

## 1. Two repositories, one contract

```
┌─────────────────────── PILAR-2b (public, production) ─────────────────────┐
│ ingest/sources/   aneel_siga · pam · ibge_ppm · snis  (existing)           │
│                   + anp_biometano · anp_etanol · sapcana · cbio · bndes    │
│                   + engine_release (loads engine bundles)                  │
│ PostGIS           municipalities · municipality_timeseries · residuos ·   │
│                   infrastructure  + facilities · hex_supply · lcob_results │
│ FastAPI           + /facilities  /supply  /lcob  /sites                    │
│ Next.js           + "Plant simulator" & "Supply curve" pages               │
└──────────────▲──────────────────────────────────────┬─────────────────────┘
               │ versioned release bundles             │ pg_dump + feedstocks.yaml
┌──────────────┴──────────────────────────────────────▼─────────────────────┐
│ ENGINE (this repo, private until first paper)                              │
│  ingest → supply → process → economics → siting → calibrate → export     │
└────────────────────────────────────────────────────────────────────────────┘
```

**Ownership rule:** each raw layer is ingested in exactly one place.
- PILAR-2b owns shared spatial layers (municipalities, infrastructure, exclusions, MapBiomas/IBGE series, livestock points).
- The engine owns simulated outputs (facilities registry, H3 supply, process results, LCOB, sites).
- The engine reads PILAR-2b layers from a **database dump** restored into its local PostGIS — never re-imports shapefiles.
- One source of truth for residue parameters: PILAR-2b `data/canonical_parameters/feedstocks.yaml` (+ engine-specific extras in `registry/parameters.csv`).

## 2. Modules

| Module | Input | Output | Doc |
|---|---|---|---|
| `ingest` | `registry/sources.yaml` | `data/raw/*` with checksums | 06 |
| `supply` | MapBiomas, IBGE/SEADE, mills, RenovaBio, UNICA, livestock, ETEs, RSU | `hex_supply` (H3 × month × residue), `mill_year`, `mill_month` | 09 |
| `process` | substrate mix per site × month, parameters | CH₄, biogas, biomethane, digestate, constraint flags | 10 |
| `economics` | process output, CAPEX/OPEX models, prices, finance | LCOB, NPV, IRR, cash flows (Monte Carlo) | 11 |
| `siting` | candidate sites, OD matrices, exclusions, grid | optimal sites/scales/modes; supply curve | 12 |
| `calibrate` | ANP monthly plant output, RenovaBio | posterior parameters, fit metrics | 13 |
| `export` | results | bundle (GeoParquet + manifest + SQL) | 18 |

## 3. Data flow & storage

```
data/raw/        immutable downloads (DVC)              ← ingest
data/interim/    cleaned, harmonized (CRS, units, CNPJ) ← ingest/supply
data/processed/  model-ready tables (H3, mill-month)    ← supply/process
data/private/    partner/NDA data (private DVC remote) ← never exported raw
exports/vX.Y.Z/  release bundle for PILAR-2b
```

- **Pipeline:** `dvc.yaml` stages, one per transform; `dvc repro` rebuilds only what changed.
- **Database:** local PostGIS (Docker) with PILAR-2b schema (run PILAR-2b migrations) + `engine` schema.
- **Formats:** GeoParquet for vectors, COG GeoTIFF for rasters, Parquet for tables, YAML/CSV for registry.

## 4. Run provenance

Each run writes `runs/<run_id>/manifest.json`:
```json
{
  "run_id": "2026-11-02T14-03-11_ab12cd",
  "git_commit": "…",
  "params_hash": "sha256 of parameters.csv + config",
  "sources": {"renovabio_cert_reports": "sha256…", "mapbiomas_cana": "collection 10.1"},
  "scenario": "baseline",
  "seed": 42
}
```

## 5. Technology choices (see ADRs)

| Concern | Choice | ADR |
|---|---|---|
| Repo split | Engine separate from PILAR-2b | ADR-0001 |
| Spatial grid | H3 resolution 8 | ADR-0002 |
| Data versioning & pipeline | DVC | ADR-0003 |
| Supply allocation | Huff model calibrated on RenovaBio + IBGE constraints | ADR-0004 |
| CAPEX model | Hierarchical Bayesian with international priors | ADR-0005 |
| Routing | Valhalla (truck costing) or OSRM; pgRouting for in-DB | — |
| Optimization | Pyomo or linopy + HiGHS | — |
| Uncertainty | LHS Monte Carlo + SALib Sobol | — |
| Stats in R | brms / lme4 allowed (`r/`, renv) | — |
