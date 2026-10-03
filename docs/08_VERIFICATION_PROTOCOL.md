# 08 — Verification protocol (how S/K becomes V)

## 1. Why
Most of the registry was compiled from search snippets and prior knowledge because primary sites were unreachable during planning. Papers and policy outputs must rest on **read, cited, page-referenced** values.

## 2. Flags
| Flag | Definition | Allowed in results? |
|---|---|---|
| **V** | Primary document opened; value, page/table and quote recorded | Yes |
| **S** | Seen in search snippet/abstract/secondary press | Only in sensitivity ranges, with caveat |
| **K** | Prior knowledge, not re-checked | No — verify first |
| **D** | Derived by us from other values | Yes if all inputs are V and the derivation is in code |

## 3. Procedure per parameter
1. Open the primary document (not a news article about it).
2. Find the value; record **page/table/figure** and a **verbatim quote** (≤ 2 sentences).
3. Record **conditions** (units, basis, temperature, scale, year, currency, price year).
4. Compare with registry value:
   - same → set flag `V`, add `page` and `quote`;
   - different → update value, set `V`, add a line to the **change log** below;
   - not found → keep `S/K`, note "not found in [doc]".
5. If two V sources disagree → **do not average**; add to `21_RISKS_AND_OPEN_QUESTIONS.md` §Conflicts and choose a rule (e.g. SP-specific > national > international; recent > old; measured > estimated).

## 4. Extended columns for `parameters.csv` (add during Phase 0)
`page`, `quote`, `verified_by`, `verified_on`, `conditions`, `price_year`, `currency`.

## 5. Verification order (highest leverage first)
1. EPE NT 2025-08 & 2023-07 (CAPEX factor, OPEX scope, LCOB ranges)
2. CNPE Res. 4/2026; ANP Res. 995/996/1.006/2026 (CGOB mechanics, spec)
3. ARSESP Del. 1.765/2025 (TUSD-Verde)
4. Volpi et al. 2021; Janke et al. 2015/2020; Fuess et al. 2018/2024; Moraes et al. 2015 (process)
5. IPCC 2019 Vol. 4 Ch. 10 (manure VS, B₀)
6. FIESP 2024 SP study (original report)
7. BNDES TD 159
8. Project announcements in `projects_capex.csv` (normalize capacity basis)
9. International: BIP TF4, DEA catalogue, Biogas-Messprogramm III

## 6. LLM-assisted extraction rules
- Use LLMs to **locate and extract**, never to **supply** values.
- Output must include `source_id`, `page`, `quote`; reject rows without a quote.
- Human audit: random 10 % sample + all outliers (> 3 MAD).
- Keep the raw LLM output in `data/interim/extraction_raw/` for traceability.

## 7. Change log
| Date | Parameter id | Old | New | Flag | Source/page | By |
|---|---|---|---|---|---|---|
| | | | | | | |
