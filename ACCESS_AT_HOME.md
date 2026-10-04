# How to access everything at home

Everything from the planning session lives in this folder:

- **GitHub:** repository `aikiesan/aprenda_sobre_biometano` → branch **`ccr-35b12b87-0r0g25`** → folder **`sp-biomethane-engine/`**
- Browse online: https://github.com/aikiesan/aprenda_sobre_biometano/tree/ccr-35b12b87-0r0g25/sp-biomethane-engine

## Option A — just read (no setup)
Open the link above in a browser. Start with `PROJECT.md`, then `docs/19_ROADMAP_STEP_BY_STEP.md`.

## Option B — set it up on your machine (recommended)
Follow **`docs/04_DEV_ENVIRONMENT_SETUP.md`**: §1 is the folder layout, §2 the one-time setup, and §3 the project itself.
The short version (WSL Ubuntu, not OneDrive):
```bash
mkdir -p ~/projects/cp2b && cd ~/projects/cp2b
git clone -b ccr-35b12b87-0r0g25 https://github.com/aikiesan/aprenda_sobre_biometano.git
cd aprenda_sobre_biometano/sp-biomethane-engine && make setup && make test
```
Run `git pull` to receive what later Claude sessions push.

## Option C — give it its own repository (when coding full-time)
Use `git subtree split` so the history is kept. See `docs/04_DEV_ENVIRONMENT_SETUP.md` §7.

## What's where
| Folder | Content |
|---|---|
| `PROJECT.md`, `CLAUDE.md`, `README.md` | Charter, working rules, orientation |
| `docs/` | 00–23 + 99: the organized plan and methods |
| `registry/` | sources (81), parameters (60), projects (20) |
| `research_notes/` | Full research findings R00–R10 (R07–R10: S-flagged, verification pending) |
| `evidence/` | RenovaBio report PDF + text; ANP monthly SP extract |
| `templates/` | ADR, method doc, partner request, extraction schema |
