# How to access everything at home

Everything from the planning session lives in this folder:

- **GitHub:** repository `aikiesan/aprenda_sobre_biometano` → branch **`ccr-35b12b87-0r0g25`** → folder **`sp-biomethane-engine/`**
- Browse online: https://github.com/aikiesan/aprenda_sobre_biometano/tree/ccr-35b12b87-0r0g25/sp-biomethane-engine

## Option A — just read (no setup)
Open the link above in a browser. Start with `PROJECT.md`, then `docs/19_ROADMAP_STEP_BY_STEP.md`.

## Option B — copy to your machine
```bash
# inside WSL (not OneDrive!)
mkdir -p ~/projects && cd ~/projects
git clone --branch ccr-35b12b87-0r0g25 --single-branch https://github.com/aikiesan/aprenda_sobre_biometano.git seed-tmp
cp -r seed-tmp/sp-biomethane-engine ~/projects/sp-biomethane-engine
rm -rf seed-tmp
```

## Option C — give it its own repository (recommended before coding)
1. On github.com create an **empty private** repo, e.g. `aikiesan/sp-biomethane-engine` (no README).
2. Then:
```bash
cd ~/projects/sp-biomethane-engine
git init -b main && git add . && git commit -m "Seed from planning session 2026-10-03"
git remote add origin https://github.com/aikiesan/sp-biomethane-engine.git
git push -u origin main
```
(Or ask Claude in a new session that has the new repo connected to do the push.)

## What's where
| Folder | Content |
|---|---|
| `PROJECT.md`, `CLAUDE.md`, `README.md` | Charter, working rules, orientation |
| `docs/` | 00–23 + 99: the organized plan and methods |
| `registry/` | sources (81), parameters (60), projects (20) |
| `research_notes/` | Full research findings R00–R06 |
| `evidence/` | RenovaBio report PDF + text; ANP monthly SP extract |
| `templates/` | ADR, method doc, partner request, extraction schema |
