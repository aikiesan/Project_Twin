# ADR-0003 — DVC for data versioning and pipeline

- **Status:** Accepted (backup: manual zips on Google Drive, see ADR-0009)
- **Context:** Multi-GB rasters and many derived tables; results must be traceable to exact data + code; collaborators on Windows/WSL.
- **Decision:** Use **DVC** for data versioning (remote: Drive/UNICAMP/MinIO — to decide) and `dvc.yaml` stages for the pipeline. Separate **private** remote for partner data.
- **Consequences:** + one tool for data and DAG; git stays light; reproducible `dvc repro`. − learning curve; remote credentials management.
- **Alternatives:** Snakemake + Zenodo bundles (PyPSA-Eur style; strong in energy modeling — revisit if pipeline grows complex); Git LFS (not for multi-GB).

## Update 2026-10-04
- DVC 3.67 is initialised at the root of `aikiesan/Project_Twin`.
- `cache.type = hardlink,copy`: files in `data/raw/` are hardlinked read-only from `.dvc/cache`, which also enforces raw-data immutability (CLAUDE.md rule 4).
- `data/raw` is tracked by `data/raw.dvc`: 330 files, 533 MB. `.gitignore` ignores `/data/**` except `/data/*.dvc`.
- **Backup chosen 2026-10-04:** manual dated zips on Google Drive; no DVC remote yet. See ADR-0009.
