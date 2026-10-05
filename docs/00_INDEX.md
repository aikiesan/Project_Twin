# 00 — Index and reading order

## A. Orientation (read first, ~1 h)
| # | Document | What you get |
|---|---|---|
| 01 | [Context & motivation](01_CONTEXT_AND_MOTIVATION.md) | Why this project, mandate status, evidence from ANP data, naming |
| 02 | [Research questions & hypotheses](02_RESEARCH_QUESTIONS_AND_HYPOTHESES.md) | RQs, testable hypotheses, expected outputs |
| 03 | [Architecture](03_ARCHITECTURE.md) | Two-repo design, modules, data flow |

## B. Getting set up at home (~half a day)
| # | Document | What you get |
|---|---|---|
| 04 | [Dev environment setup](04_DEV_ENVIRONMENT_SETUP.md) | WSL2, Docker Desktop, repo, uv, DVC, PostGIS, PILAR-2b dump |

## C. Data (Phase 0–1)
| # | Document | What you get |
|---|---|---|
| 05 | [Data catalog](05_DATA_CATALOG.md) | Every source by module, granularity, access, confidence |
| 06 | [Data acquisition playbook](06_DATA_ACQUISITION_PLAYBOOK.md) | Step-by-step download/scrape per source |
| 07 | [LAI requests](07_LAI_REQUESTS.md) | Ready-to-send access-to-information requests (PT-BR) |
| 08 | [Verification protocol](08_VERIFICATION_PROTOCOL.md) | How S/K becomes V; provenance schema |

## D. Methods (one per module)
| # | Document |
|---|---|
| 09 | [Supply module](09_MODULE_SUPPLY.md) |
| 10 | [Process module](10_MODULE_PROCESS.md) |
| 11 | [Economics module](11_MODULE_ECONOMICS.md) |
| 12 | [Siting & logistics module](12_MODULE_SITING_LOGISTICS.md) |
| 13 | [Calibration & validation](13_MODULE_CALIBRATION_VALIDATION.md) |
| 14 | [ML & AI roles](14_ML_AND_AI_ROLES.md) |

## E. Context knowledge
| # | Document |
|---|---|
| 15 | [International benchmarks](15_INTERNATIONAL_BENCHMARKS.md) |
| 16 | [Regulation & market](16_REGULATION_AND_MARKET.md) |
| 17 | [Lab & pilot experiments](17_LAB_AND_PILOT_EXPERIMENTS.md) |
| 18 | [PILAR-2b integration](18_PILAR2B_INTEGRATION.md) |

## F. Execution & reference
| # | Document |
|---|---|
| 19 | [**Roadmap — step by step**](19_ROADMAP_STEP_BY_STEP.md) ← the working checklist |
| 20 | [Publications plan](20_PUBLICATIONS_PLAN.md) |
| 21 | [Risks, conflicts & open questions](21_RISKS_AND_OPEN_QUESTIONS.md) |
| 22 | [Glossary (PT/EN)](22_GLOSSARY.md) |
| 23 | [References](23_REFERENCES.md) |
| 24 | [Four-month plan — two drafts to merge](plan_drafts/README.md) (5 Oct 2026 – 5 Feb 2027) |
| 25 | [Survey of data held on the project PC](25_LOCAL_HOLDINGS_SURVEY.md) (what was imported, what stays out and why) |
| 26 | [Project viewer](26_PROJECT_VIEWER.md) (local web page: datasets, map, project flow, progress) |
| 99 | [Session notes — how we got here](99_SESSION_NOTES.md) |

## G. Raw material
- `../research_notes/` — R00–R10 full research reports (all URLs, numbers, flags; R07–R10 S-flagged, verification pending)
- `../research_notes/raw/` — structured workflow results (claims, proposed rows, validation report)
- `../registry/staging/` — proposed registry rows not yet merged
- `../tools/agent_workflows/` — Claude Code multi-agent workflow scripts used to build the project
- `../evidence/` — primary documents and data extracts (V-level)

## H. Decisions
`decisions/ADR-0001` … — see [decisions/README.md](decisions/README.md).
