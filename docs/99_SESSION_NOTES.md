# 99 — Session notes: how we got here (2026-10-03)

A record of the planning conversation, so the reasoning isn't lost.

1. **Started from "digital twin of a biogas plant."** Clarified levels: digital model → digital shadow → digital twin. Without live plant data we build a model first. Discussed ADM1/AM2, Python stack, web options (Streamlit/Dash/Shiny, FastAPI, Pyodide).
2. **Reframed** to what CP2B needs: a **techno-economic + spatial simulation** — cost, production, sale price, location, CAPEX/OPEX, CSTR co-digestion, seasonality of cane residues.
3. **Policy context:** CNPE set 0.5 % for 2026 (not a "failure" of a 1 % target in practice, but a downward adjustment due to supply).
4. **Data reality:** UNICA mill data only at SP-total level; mill data not accessible → considered ML. Concluded: ML where labels exist; mechanistic for "what if"; calibration = inverse modeling.
5. **Found mill-level labels:** RenovaBio certification reports (public consultation) give per-mill annual cane, ethanol, vinasse applied (one read in full: Usina Santa Adélia–Pereira Barreto).
6. **Inspected PILAR-2b:** mature platform (v3.0.3, INPI, FastAPI + PostGIS + Next.js, ingest framework, time series). Its ANP monthly file revealed **low capacity factors and off-season collapse** at Costa Pinto vs partial off-season output at Narandiba.
7. **Decided architecture:** separate engine repo (private), PILAR-2b as public face; versioned release bundles; one ingest owner per layer; Docker + WSL; DVC; not in OneDrive.
8. **Research sweep (5 parallel tracks):** feedstock granularity, costs, markets/regulation, process, spatial/methods → registry of 63 sources, 60 parameters, 20 projects. Most values snippet-level (sandbox blocked primary sites) → Phase 0 verification sprint.
9. **International benchmarks:** DBFZ, MaStR, KTBL, Biogas-Messprogramm III, DEA catalogue, Swedish stats, Lidköping LBG, French ODRÉ, BioNorrois (beet pulp seasonal analog), BIP TF4, OIES 2026, AgSTAR, IEA Task 37 → 18 more sources; use as priors via hierarchical Bayesian pooling.
10. **This seed** (CLAUDE.md, PROJECT.md, docs 00–23, ADRs, templates, registry) committed temporarily on branch `ccr-35b12b87-0r0g25` of `aprenda_sobre_biometano`; to be moved into its own private repo.

## Decisions still pending (user)
- Engine repo **name** and confirm **private** until first paper.
- **DVC remote** (Google Drive / UNICAMP server / MinIO).
- Which partner data can be requested and under what NDA.
- Who leads lab (E1–E2) and pilot (E3) experiments.
