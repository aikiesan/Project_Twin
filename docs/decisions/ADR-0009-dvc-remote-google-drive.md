# ADR-0009 — Data backup: manual zips on Google Drive

- **Status:** Accepted (2026-10-04, team decision)
- **Context:** ADR-0003 left the DVC remote open (Google Drive, UNICAMP server or MinIO). Until a backup exists, `data/` (≈ 605 MB) lives only on the project PC.
- **Decision:** Back up to Google Drive **by hand**. The team uploads dated zips to two private Drive folders owned by the project account. No DVC remote is configured for now.
  - `Project_Twin_DVC` (https://drive.google.com/drive/folders/1oGBLyrlycLHNmLIFJDxXoMwCOBqB3QCm) holds `Project_Twin_data_raw_<date>.zip`: `data/raw/` plus `raw.dvc`.
  - `Project_Twin_DVC_private` (https://drive.google.com/drive/folders/1XTE0MRE7HmZmQwGcizezBa0mHw3rfHDJ) holds `Project_Twin_data_private_<date>.zip`: `data/private/` (partner/NDA and farm/property-level data, CLAUDE.md rule 6) plus `private.dvc`.
  - The zips are built in `A:\Project_Twin\backups\` (outside the repository). `SHA256SUMS.txt` sits next to them.
- **Integrity:** `data/raw.dvc` and `data/private.dvc` (in git) record the md5 of every tracked file. After restoring a zip into `data/`, `dvc status` shows whether the files match the committed state.
- **Consequences:**
  - \+ No OAuth setup, and nothing runs against the Drive API.
  - − Backups depend on someone remembering to upload them. Make a new zip after every import PR that changes `data/*.dvc`.
- **Alternatives:**
  - DVC `gdrive://` remotes. They need a browser OAuth sign-in and possibly a custom Google Cloud OAuth client. Switch to them if manual uploads become a burden; the folders above can be reused with a fresh, empty sub-folder.
  - UNICAMP server or MinIO.

## Private data
- Done 2026-10-04: farm-level points (`cp2b_gee_exports`) and CAR property data (`cp2b_results_sicar`) moved from `data/raw/` to `data/private/`, tracked by `data/private.dvc`.
  - The farm points derive from a registry extract with addresses and contacts.
  - `scripts/ingest/import_local_sources.sh` now writes these two ids to `data/private/`.
- Never share the `Project_Twin_DVC_private` folder outside the project team.
