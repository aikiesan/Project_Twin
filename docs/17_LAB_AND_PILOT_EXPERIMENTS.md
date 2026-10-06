# 17 — Lab (LABIOEN) and pilot (PPBIOEN) experiments

Purpose: close the **parameter gaps** that most affect the model and that no public source covers. Each experiment lists the model parameter it feeds.

## E1 — Filter cake storage losses (LABIOEN) ★★★
- **Gap:** only energy-cane silage data exist (6–27 % loss over 4–6 months; Hoffstadt 2020). Cocal reportedly stores filter cake in silos.
- **Design:** fresh filter cake from 2–3 mills; storage in sealed lab silos (± compaction, ± additive, ± mixing with straw) at ambient SP temperature; sampling at 0, 1, 2, 3, 4, 5, 6, 7 months; measure TS, VS, VFA, pH, BMP (Holliger 2016 protocol).
- **Feeds:** `fc_storage_loss` (φ_store curve), storage design in siting MILP.

## E2 — Monthly vinasse composition (LABIOEN + partner mills) ★★★
- **Design:** biweekly sampling over one season at 2–3 mills (juice/mixed/molasses mix); COD, BOD, SO₄, K, N, P, pH, TS/VS, temperature at discharge.
- **Feeds:** `vin_cod`, `vin_so4`, `vin_k2o`; COD/SO₄ constraint; seasonal variation (cf. Fuess 2018).

## E3 — Season switching protocol (PPBIOEN) ★★★
- **Question:** best transition from vinasse-led (harvest) to filter cake + manure (off-season) and back.
- **Design:** continuous CSTR at 55 °C (and 37 °C arm if possible); phases: vinasse + filter cake → ramp to stored filter cake + manure → back; OLR ramps 0.5 → 4.8 g VS/L·d; monitor FOS/TAC, VFA, TAN, K, H₂S, biogas, CH₄; compare with shutdown/restart (30 d).
- **Feeds:** OLR limits per mix, restart time, transition losses; ADM1 calibration data.

## E4 — Thermophilic tolerance to ammonia + potassium (LABIOEN/PPBIOEN) ★★
- **Design:** factorial TAN × K at 55 °C in semi-continuous reactors with poultry manure + vinasse.
- **Feeds:** `tan_inhib`, `k_inhib`.

## E5 — Sulfur mass balance & H₂S control (PPBIOEN) ★★
- **Design:** COD/SO₄ gradient; compare in-situ Fe dosing vs micro-aeration; measure biogas H₂S, sulfide in liquid.
- **Feeds:** `h2s_biogas`, H₂S removal OPEX.

## E6 — BMP → CSTR correction & kinetics (LABIOEN + PPBIOEN) ★★
- **Design:** BMP (37 & 55 °C) and continuous yields for filter cake, straw, manures; fit first-order k (or two-pool).
- **Feeds:** `bmp_fullscale`, k per substrate.

## E7 — Digestate N/P/K & P4.231 dose (LABIOEN) ★★
- **Design:** characterize digestate from E3; compute fertirrigation dose under P4.231 vs raw vinasse.
- **Feeds:** digestate value, land constraint.

## E8 — Straw pre-treatment at continuous scale (PPBIOEN) ★
- **Design:** milled vs NaOH-treated straw in CSTR (for filter cake, Janke et al. 2019 report BMP 223–251 mL CH₄/g VS across pre-treatments but only 218–223 in semi-continuous CSTRs, PDF p. 10; `registry/value_evidence.csv`).
- **Feeds:** straw BMP, pre-treatment CAPEX/OPEX.

## E9 — Parasitic energy at pilot scale (PPBIOEN) ★
- Measure mixing, pumping, heating energy → scale-up factors.

## Data handling
- Every experiment writes a tidy dataset + metadata (method, units, dates) to `data/private/lab/<exp_id>/` until published; then to Zenodo.
- Results update `registry/parameters.csv` with flag `V` and the internal report as source.
