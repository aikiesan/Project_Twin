# ADR-0009 — DVC remotes on Google Drive

- **Status:** Accepted (2026-10-04, team decision)
- **Context:** ADR-0003 left the DVC remote open (Google Drive, UNICAMP server or MinIO). Until a remote exists, `data/raw` (≈ 605 MB) lives only on the project PC.
- **Decision:** Two Google Drive folders, both private, owned by the project account:
  - `storage` (default): `gdrive://1oGBLyrlycLHNmLIFJDxXoMwCOBqB3QCm`, folder `Project_Twin_DVC`. Holds everything tracked by `data/raw.dvc`.
  - `private`: `gdrive://1XTE0MRE7HmZmQwGcizezBa0mHw3rfHDJ`, folder `Project_Twin_DVC_private`. Holds `data/private/` (partner/NDA data, CLAUDE.md rule 6), pushed with `dvc push -r private`.
  - Folder IDs are not secrets: they live in `.dvc/config` (in git). Access is controlled by Drive sharing. OAuth tokens and any custom client secret go to `.dvc/config.local` (gitignored) and never to git.
- **Consequences:** + no server to run; the team already uses Drive. − Drive has API rate limits and slow transfers for many small files; the first `dvc push` needs a browser sign-in. If Google blocks DVC's built-in OAuth app, create an OAuth client (desktop app) in a Google Cloud project and set `gdrive_client_id` / `gdrive_client_secret` with `dvc remote modify --local`.
- **Alternatives:** UNICAMP server (no admin access yet); MinIO (would need hosting). Revisit if the data passes the Drive quota or transfers become a bottleneck.

## Setup on another machine

```bash
uv tool install "dvc[gdrive]"
dvc pull            # opens a browser for Google sign-in the first time
```

## Private data
- Done 2026-10-04: farm-level points (`cp2b_gee_exports`) and CAR property data (`cp2b_results_sicar`) moved from `data/raw/` to `data/private/`. They are tracked by `data/private.dvc` and pushed only with `dvc push -r private`.
  - The farm points derive from a registry extract with addresses and contacts.
  - `scripts/ingest/import_local_sources.sh` now writes these two ids to `data/private/`.
- Never share the `private` Drive folder outside the project team.
