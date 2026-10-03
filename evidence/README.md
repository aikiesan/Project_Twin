# evidence/ — primary documents and data extracts acquired during planning (2026-10-03)

Small files kept in git on purpose (they are the only **V**-level evidence so far). Larger data goes to DVC.

| File | What | Source | sha256 |
|---|---|---|---|
| `renovabio_cert_report_usina_santa_adelia_pereira_barreto.pdf` | RenovaBio certification report (Benri), Usina Santa Adélia S/A – Pereira Barreto/SP, route E1GC, data years 2021–2023, public consultation 17/10–16/11/2024 | https://s3.amazonaws.com/benri.site/media/arquivos/f2040d9a-9980-4519-bf16-5d8dc9b2a5f5/Relatorio%20de%20Certificacao%20RenovaBio_E1GC_rev06_PB.pdf | de1d60ea…24eb9 |
| `renovabio_cert_report_usina_santa_adelia_pereira_barreto.txt` | Text extraction of the PDF (pdftotext layout) | derived | 0b6c4acb…eceeae |
| `anp_monthly_sp_plants_from_pilar2b.csv` | ANP monthly biogas volume & utilization, **SP plants only** (215 rows) | extracted from `aikiesan/Pilar-2b` `analysis/data/05e_anp_biometano_plant_volume_monthly.csv` (GPL-3.0) | 6a315052…b1e |
| `anp_biomethane_plants_latest_from_pilar2b.csv` | ANP authorized biomethane plants, latest month (04/2026), with CNPJ, capacity, utilization | copy of PILAR-2b `analysis/data/05c_anp_biometano_plants_latest.csv` | 51f0921d…b6c |

## Verified values (flag V) from the Santa Adélia report

| Item | 2021 | 2022 | 2023 | Text line (in .txt) |
|---|---|---|---|---|
| Cane processed (t) | 2,329,621.65 | 2,683,176.75 | 3,551,156.27 | ~589–591 ("Cana processada") |
| Vinasse (L), agricultural-phase table | 1,286,435,205.88 | 1,469,236,638.21 | 1,613,510,480.74 | ~1500–1503 |
| Anhydrous ethanol 2023 (L) | | | 225,336,933 | ~2157 |
| Hydrated ethanol 2023 (L) | | | 61,836,900 | ~2206 |
| NEEA anhydrous | 62.34 gCO₂eq/MJ | | | ~125 |
| Eligible volume | 98.53 % (previous 96.90 %) | | | ~140, 614 |

Notes:
- The report repeats cane values elsewhere with unit **"Kg"** (line ~2102) — an obvious unit typo in the source; the "ton" reading is consistent with ethanol volumes (~81 L/t in 2023). Log as a source-quality note, not a conflict.
- Vinasse ÷ ethanol (2023) ≈ 1,613.5 M L / 287.2 M L ≈ **5.6 L/L**, far below literature 10–15 L/L → conflict **C1** (generated vs applied vs reporting basis).

## ANP monthly — what the SP extract shows
- Raízen Costa Pinto: off-season ~0–12 %, peak 56–58 % (Jul–Aug 2025).
- Cocal Narandiba: **0 % every month Jul 2022–Jul 2025**, then 30–49 % from Aug 2025, including off-season months → conflict **C6**.
- `util_pct` = biogas volume ÷ biogas capacity (verify definition with ANP).
