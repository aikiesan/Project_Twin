# ADR-0001 — Separate engine repository; PILAR-2b as public face

- **Status:** Accepted (planning session, 2026-10-03)
- **Context:** PILAR-2b is a production, INPI-registered, public (GPL-3.0) platform with fast request-time queries (p95 < 3 s, rate limits). The new work needs heavy offline compute (routing, Bayesian calibration, MILP, Monte Carlo), heavy dependencies, fast research iteration, and may use confidential partner data.
- **Decision:** Develop the simulation engine in a **separate private repository**. Shared raw layers stay owned by PILAR-2b; the engine reads them via a database dump and publishes **versioned result bundles** that PILAR-2b ingests through a new `engine_release` source.
- **Consequences:** + production stability, independent releases, confidentiality; − need a clear contract (`docs/18_PILAR2B_INTEGRATION.md`) and sync of canonical parameters (`feedstocks.yaml`).
- **Alternatives considered:** engine inside PILAR-2b backend (rejected: risk to production, dependency bloat); monorepo sibling folder (possible later if the team prefers single-repo CI).
