# ADR-0005 — Hierarchical Bayesian CAPEX model with international priors

- **Status:** Proposed
- **Context:** Only ~20 Brazilian projects with heterogeneous capacity bases and scopes; thousands of European/US plants with better cost data but different contexts.
- **Decision:** Fit log(CAPEX) ~ log(capacity) + feedstock + scope + country random effect, pooling Brazilian and international data; Brazil offset estimated from Brazilian projects; priors on scale exponent ~ N(0.65, 0.1).
- **Consequences:** + honest uncertainty, borrows strength, defensible; − requires careful normalization (price year, FX, scope, capacity basis).
- **Alternatives:** single six-tenths rule from EPE anchor (kept as baseline); bottom-up component model only (used for structure and validation).
