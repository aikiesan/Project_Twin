# R04 — Process & technical parameters (CSTR co-digestion of vinasse, filter cake, straw, manure)

Tags: [S] snippet/abstract — verify number in full text · [PK] prior knowledge — must verify · [C] our calculation. No paper could be read in full.

## 1. Substrate characterization

### Vinasse
- Overview tables (CETESB/Elia Neto-type; ScienceDirect Topics; MDPI Fermentation 2023): **sulfate** juice 600–760, mixed 3,700–3,730, molasses ~6,400 mg/L; mixed vinasse pH 4.4–4.6, K₂O 3,340–4,600 mg/L; compilation COD 25.2–103 g/L, SO₄ 340–2,993 mg/L; pH 3.5–5.0; sulfate 3,500 ± 2,500 mg/L [S].
- **Fuess, Garcia & Zaiat 2018**, *STOTEN* 634:29–40 — seasonal characterization of SP vinasse (key SP reference; values not retrieved) [S].
- **Fuess et al. 2024**, *CEJ* (https://www.sciencedirect.com/science/article/abs/pii/S1385894723061636) — SO₄ ~2 g/L; vinasse available 7–8 months/yr [S].
- **Janke et al. 2015**, *IJMS* 16:20685, doi:10.3390/ijms160920685 — TS 16.2 g/L, VS 8.7 g/L; 5–11 Nm³ CH₄/t FM; vinasse 438–1,038 L/t cane; high-rate reactors recommended [S].
- **Moraes, Zaiat & Bonomi 2015**, *RSER* 44:888–903, doi:10.1016/j.rser.2015.01.023 — review; 4.5 L UASB at 30 & 41.2 g COD/L → 0.19 → 0.25 L CH₄/g COD removed [S].
- **Kiyuna, Fuess & Zaiat 2017**, *Bioresour. Technol.* 232:103–112 — COD/SO₄ 12 → 7.5 cut CH₄ potential 35 % (H₂S at pH > 8) [S].
- **Melo et al. 2024**, *Methane* 3(2), doi:10.3390/methane3020017 — SP mesoregion mapping; biomethane replacing diesel avoids 45.4×10⁶ kg CO₂eq/d; probable source of 0.291–0.309 m³ CH₄/kg COD [S].
- Fuess & Garcia 2014, *J. Environ. Manage.* 145:210–229 (stillage land disposal) [PK]; CETESB P4.231 dose by soil K (≤ 5 % of CEC) [PK]; 10–13 L/L ethanol [PK].

### Filter cake
- **Janke et al. 2015** (IJMS) — **50–58 Nm³ CH₄/t FM**; 35–40 kg/t cane; TS ~28.9 %, VS ~74.2 % TS; wax/oil 9–14 %, protein 10–18 %, cellulose 11–17 %, hemicellulose 15–27 %, lignin 9–14 % (dry) [S].
- **Volpi et al. 2022**, *BioEnergy Res.*, doi:10.1007/s12155-021-10293-1 (preprint 10.1101/2021.02.19.432018) — lowest BMP **260 NmL/g VS**, ≤ 40 % digestibility; co-digestion with vinasse + deacetylation liquor +37.7 %, up to 605–618 NmL/g VS (thermophilic) [S].
- **Janke et al. 2020**, *Renew. Energy* (https://www.sciencedirect.com/science/article/abs/pii/S0960148119306883) — BMP untreated 185, autoclaved 174, autoclaved + NaOH 222 mL/g VS; **semi-continuous CSTR steady state 224 mL/g VS for all** (no pre-treatment benefit) [S].
- Janke et al. 2016, *Bioresour. Technol.* 199:235–244 (urea/NaOH hydrolysis) [S].

### Straw
- **Janke et al. 2017**, *Energy Convers. Manage.* (https://www.sciencedirect.com/science/article/abs/pii/S0196890416308913) — milled 2 mm; NaOH 0–12 g/100 g: BMP **260 → 291 mL/g VS** (+11.9 %); CSTR HRT > 35 d [S].
- **Janke et al. 2018**, *Bioresour. Technol.* (https://www.sciencedirect.com/science/article/abs/pii/S0960852417313895) — straw + filter cake: N +17 %, N+P+S +44 % methane [S].
- *Ind. Crops Prod.* 2021 (https://sciencedirect.com/science/article/abs/pii/S0926669021004763) — trash 161.8 ± 4, bagasse 187.9 ± 2.4 NmL/g VS; hydrothermal 120 °C 1 h → 191 (+98 %) [S].

### Manure [PK — verify IPCC 2006/2019 Vol. 4 Ch. 10]
VS excretion LatAm: dairy ~2.9, other cattle ~2.5, swine ~0.3, poultry 0.01–0.02 kg VS/head/d; B₀ dairy (developing) 0.13, swine 0.29, poultry ~0.24–0.39 m³ CH₄/kg VS; lab BMP cattle 200–300, swine 300–450, poultry litter 200–300 NL/kg VS. Use SIRENE/MCTI factors or Embrapa (Kunz et al. 2019).

### Co-digestion with manure
- Vinasse + dairy wastewater, two UASBs in series: doi:10.1007/s12155-023-10614-6 [S]
- Molasses vinasse + three manures: https://www.sciencedirect.com/science/article/abs/pii/S0959652622032097 [S]

## 2. CSTR design & operation
- **Volpi, Brenelli, Mockaitis, Rabelo, Franco, Moraes 2021**, *Appl. Microbiol. Biotechnol.*, doi:10.1007/s00253-021-11635-x (preprint 10.1101/2021.02.24.432031) — s-CSTR **55 °C**, vinasse + filter cake + DL; **max OLR 4.80 g VS/L·d** without collapse (yield 59 % lower than optimum at lower OLR); **~230 NmL CH₄/g VS**; removal 83 ± 13 %; thermophilic community from mesophilic seed; filter cake enables year-round operation [S].
- Volpi et al. 2023, *Appl. Nano* 4(3):14, doi:10.3390/applnano4030014 (Fe₃O₄, sulfide mitigation); Volpi et al. 2022, *Biomass* 2(4):24, doi:10.3390/biomass2040024 (metaproteomics) [S].
- **Janke et al. 2015**, *IJMS* 16:23210, doi:10.3390/ijms161023210 — mesophilic CSTR filter cake (+bagasse): **VFA accumulation at OLR 3.0–4.0 g VS/L·d** [S].
- Ferraz Jr. et al. 2016, *Renew. Energy* 89:245–252 (thermophilic raw vinasse; hot vinasse ~85–90 °C [PK]) — https://www.sciencedirect.com/science/article/abs/pii/S0960148115304808 [S].
- Fuess et al. 2017, *Appl. Energy* (ASTBR, stable 240 d at OLR up to 30 kg COD/m³·d) — https://sciencedirect.com/science/article/abs/pii/S0306261916318323 [S].
- Fuess 2024 CEJ — sulfidogenic pre-stage; OLR 20 kg COD/m³·d; CH₄ ≥ 80 %; ≥ 330 NmL CH₄/g COD [S].
- Thermophilic UASB vinasse + filter cake + recirculation (2017): https://www.sciencedirect.com/science/article/pii/S0960852417312221 [S].
- AFBR vinasse:molasses 1:1, *Appl. Biochem. Biotechnol.* 2024, doi:10.1007/s12010-024-05078-z — best 7.5 kg COD/m³·d; removal 56–84 % [S].

### Inhibition & stability
- Sulfide: COD/SO₄ < ~10 penalizes (Kiyuna 2017); biogas H₂S up to ~9 % in thermophilic vinasse reactors [S]; free H₂S inhibitory ~50–250 mg/L [PK; Chen, Cheng & Creamer 2008, doi:10.1016/j.biortech.2007.01.057].
- Ammonia: TAN 1.7–14 g/L for 50 % inhibition (acclimation); FAN > ~0.15–0.7 g N/L [PK].
- Potassium: moderate inhibition ~2.5–4.5 g K/L [PK] — vinasse near threshold (gap).
- Alkalinity: pH ~4.5 → alkalinization/recirculation.
- FOS/TAC: < 0.3 stable; 0.3–0.4 optimal; > 0.5 overload; IA/IP < 0.3 (Ripley 1986) [PK].
- Restart after off-season: UASB to 19 kg COD/m³·d in **30 days** (10.24 L CH₄/L·d; 0.40 L/g COD removed) — Barbosa et al. 2022 [S].
- General wet CSTR [PK; FNR/KTBL]: TS ≤ 10–12 %; OLR 2–4 kg VS/m³·d (meso); HRT 20–40 d; parasitic 5–10 %; mixing 5–10 W/m³; start-up 1–3 months.

### SP mill plants — technology [S]
- **Raízen Bonfim (Guariba)** (Raízen–Geo): vinasse + filter cake; 2 × 8,000 m³ vertical + 1 × 18,000 m³ horizontal digesters (Geo); 21 MW; up to 135,000 MWh/yr; since 2020; Geo patents US 11,085,058 & 11,713,473.
- **Raízen Costa Pinto**: biomethane; 150 kt/yr filter cake; 1.9 Mm³/yr vinasse.
- **Cocal Narandiba**: Geo; vinasse, filter cake, straw; ~25,000 m³/d; start late 2021 or Jul 2022 (conflicting); Necta/GasBrasiliano pipeline.
- **Cocal Paraguaçu Paulista** (2025): R$ 216 M; up to 60,000 m³/d in harvest; poultry manure + Granja Shida wastewater.
- Not explicitly "CSTR" in sources — stirred vertical tanks + horizontal digester (inference).
- Full-scale methanogenic UASB on vinasse in Brazil: doi:10.1007/s13399-021-01281-8 [S].
- Links: https://www.geobiogas.tech/en/plantas/raizen-geo-biogas · https://www.geobiogas.tech/en/plantas/metanol · https://bioenergyinternational.com/raizen-inaugurates-first-biogas-power-plant/ · https://www.canaonline.com.br/conteudo/cocal-planeja-expandir-atuacao-no-biogas-e-biometano-a-partir-de-abril.html · https://www.brasilagro.com.br/conteudo/cocal-inaugura-planta-de-biogas-com-residuos-de-cana-e-esterco-de-aves.html · https://ideas.repec.org/a/ags/ifaamr/335093.html

## 3. Off-season strategies
- Geo/Cocal: filter cake (and straw) **stored in silos**, fed off-season; reactors can run on solids alone; vinasse storage uneconomic [S].
- Paraná TEA *Biomass* 5(1):10 (2025), doi:10.3390/biomass5010010 — synergy: 24.2 vs 18.8 ×10⁶ m³/yr [S].
- Concept vinasse in season + stored/ensiled filter cake off-season — Frontiers 2020, doi:10.3389/fenrg.2020.579577 [S].
- **Hoffstadt et al. 2020**, *Agronomy* 10(6):821, doi:10.3390/agronomy10060821 (energy cane proxy) — ensiling losses **6–16 % (Baserga) / 13–22 % (batch) at 4 months; ~20–27 % at 6 months** [S].
- **Barbosa et al. 2022**, *J. Water Process Eng.* (https://www.sciencedirect.com/science/article/abs/pii/S2214714422001076) — switching UASB vinasse → molasses cut CH₄ 69.7 % (3.10 L/L·d); back to vinasse 1.19 L/L·d; **shutdown + restart (30 d) beat switching** [S].
- Fuess 2024 — year-round (sulfate-free vinasse in season, molasses off-season) +50 % energy recovery [S].
- Glycerol off-season: https://www.sciencedirect.com/science/article/abs/pii/S0960148122009685 · vinasse + molasses two-stage: https://www.sciencedirect.com/science/article/abs/pii/S0959652619323911 [S].

## 4. Upgrading, H₂S, spec [PK]
| Tech | kWh el/Nm³ raw | CH₄ slip | CH₄ % |
|---|---|---|---|
| Membranes | 0.18–0.35 | < 0.5–2 % | 96–98 |
| PSA | 0.20–0.30 | 1.5–3 % (old up to 10) | 96–98 |
| Water scrubbing | 0.20–0.30 | 1–2 % | 96–98 |
| Amine | 0.05–0.15 + 0.5–0.75 kWh heat | < 0.1 % | > 99 |
- Anchors: Angelidaki et al. 2018 (doi:10.1016/j.biotechadv.2018.01.011); Bauer et al. 2013 (SGC 270); Sun et al. 2015 (*RSER* 51:521–532).
- H₂S: biological (air 2–6 % or biotrickling), FeCl₃, iron oxide, activated carbon polishing; DTI (Allegue & Hinge 2014) costs [PK]; microalgal-bacterial H₂S abatement: https://www.sciencedirect.com/science/article/pii/S0304389425024586 [S].
- Spec: old ANP 8/2015 CH₄ ≥ 96.5 % (S/SE/CO); one case 11.66 Nm³ biomethane (~96.5 %) per m³ vinasse [S]; ANP 886/2022 recollection CH₄ ≥ 90 %, CO₂ ≤ 3 %, H₂S ≤ 10 mg/m³, S ≤ 70 mg/m³ — **superseded by Res. 1.006/2026; verify**.
- Compression 200–250 bar: +0.25–0.35 kWh/Nm³ [PK]. Vinasse upgrading-route TEA: https://www.researchgate.net/publication/310752932 [S].

## 5. Digestate
- AD keeps K, P; N → NH₄⁺; COD −60–85 %; pH → 7–8; volume ≈ vinasse input; P4.231 still governs [PK].
- Refs: https://www.sciencedirect.com/science/article/abs/pii/S0959652621028845 · doi:10.1007/s10163-020-01029-y · Moraes, Petersen, Zaiat, Sommer & Triolo 2017, *Appl. Energy* 189:21–30 [PK]. No SP digestate NPK data retrieved (gap).

## 6. Models
- ADM1: Batstone et al. 2002 (IWA STR 13) [PK]; ADM1 + sulfate for cane-molasses vinasse: Barrera et al. 2015, *Water Res.* 71:42–54 [PK].
- Simplified vinasse models: doi:10.1007/s10098-018-1496-4 [S]; "Does sugarcane vinasse composition variability affect bioenergy yield?" https://www.researchgate.net/publication/335205851 [S].
- First-order k (not retrieved): use 0.05–0.15 d⁻¹ lignocellulosics, 0.2–0.4 d⁻¹ manure [PK] until lab fits.
- BMP protocol: Holliger et al. 2016, doi:10.2166/wst.2016.336 [PK]; full-scale 5–34 % below lab (snippet, source unclear); suggested factor 0.85 (0.70–1.0).

## 7. Real plant data
- Bonfim 21 MW / 135 GWh/yr → **capacity factor ≈ 73 %** [C].
- Full-scale vinasse: 20.68 Nm³ biogas (55 % CH₄)/m³ ≈ 11.4 Nm³ CH₄/m³ (implies COD ~40 g/L) [S].
- 0.343 and 0.35 Nm³ CH₄/kg COD removed [S]; 5.1 kWh/d per m³ vinasse [S].

## 8. Recommended parameters → see `registry/parameters.csv`
## 9. Review anchors
Moraes et al. 2015 (RSER); Moraes et al. 2014 (*Appl. Energy* 113:825–835) [PK]; Fuess et al. 2018; Fuess et al. 2025 *Rev. Environ. Sci. Biotechnol.* doi:10.1007/s11157-025-09744-4; MDPI Fermentation 2023 9(4):349 (https://www.mdpi.com/2311-5637/9/4/349); Janke et al. 2015; Frontiers 2020; Angelidaki 2018; Chen 2008; Batstone 2002 + Barrera 2015; Holliger 2016; Guedes 2026 doi:10.1002/tqem.70450.

## 10. Lab/pilot gaps → `docs/17_LAB_AND_PILOT_EXPERIMENTS.md`
Other URLs: https://doi.org/10.1021/acsomega.5c06244 · https://doi.org/10.3390/en16134919 · https://link.springer.com/article/10.1007/s12649-019-00811-w · https://link.springer.com/article/10.1007/s12649-020-00964-z · https://www.researchgate.net/publication/380724706 · https://www.arsesp.sp.gov.br/Documentosgerais/G%C3%A1s%20no%20transporte_Plantas%20de%20Biometano%202.pdf
Not covered: full Moraes publication list (Lattes/Scopus), Brazilian manure VS/head, H₂S removal costs, Brazilian upgrading performance data.
