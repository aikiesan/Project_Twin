# ADR-0003 — DVC for data versioning and pipeline

- **Status:** Proposed
- **Context:** Multi-GB rasters and many derived tables; results must be traceable to exact data + code; collaborators on Windows/WSL.
- **Decision:** Use **DVC** for data versioning (remote: Drive/UNICAMP/MinIO — to decide) and `dvc.yaml` stages for the pipeline. Separate **private** remote for partner data.
- **Consequences:** + one tool for data and DAG; git stays light; reproducible `dvc repro`. − learning curve; remote credentials management.
- **Alternatives:** Snakemake + Zenodo bundles (PyPSA-Eur style; strong in energy modeling — revisit if pipeline grows complex); Git LFS (not for multi-GB).
