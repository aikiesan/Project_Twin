# ADR-0004 — Huff allocation calibrated on RenovaBio mill data

- **Status:** Proposed
- **Context:** Need cane intake per mill; only SP totals (UNICA) and municipal production (IBGE/SEADE) are complete; mill-level values exist for certified mills via RenovaBio reports.
- **Decision:** Allocate H3 cane to mills with a **Huff spatial interaction model** on road-network distance, constrained by mill capacity and activity, **calibrated (Bayesian) on RenovaBio mill-year cane**, with IBGE municipal totals as hard constraints.
- **Consequences:** + uses all public data, gives uncertainty, testable by held-out mills; − depends on extraction quality and coverage of RenovaBio reports.
- **Alternatives (kept as sensitivity):** network Voronoi; capacity-constrained transportation LP; pure ML regression (rejected as primary: few labels, poor extrapolation).
