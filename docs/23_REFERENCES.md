# 23 — References (organized by module)

Flags: **V** read · **S** seen in search/abstract · **K** prior knowledge. **Verify DOIs before citing.** Move to a `.bib` file (Zotero group "CP2B-biomethane") during Phase 0.

**`registry/references.csv` is the authoritative list** (ADR-0013, docs/08 §8). It says what each reference supports in the project (`used_for`) and how its identity was checked (`ref_check`). Entries below that carry a `ref_id` and a status in square brackets (`two_sources`, `one_source`, `unconfirmed`, `unidentified`, `pending`) mirror that file. Values read with page and quote are in `registry/value_evidence.csv` (ADR-0015). Only `two_sources` entries may be cited without a caveat.

## Policy, market, official reports
- EPE. NT-EPE-DPG-SDB-2025-08 — Investimentos e Custos O&M no Setor de Biocombustíveis 2026–2035. [S]
- EPE. NT-EPE-DPG-SDB-2023-07 (2025–2034); NT-EPE-DPG-SDB-2023-05 (2024–2033). [S]
- EPE. Plano Nacional Integrado das Infraestruturas de Gás Natural e Biometano (consulta pública). [S]
- Teixeira, C.A.N. et al. (2024). *A hora do biometano no Brasil*. BNDES Texto para Discussão 159. [S]
- FIESP-led consortium (2024). Biomethane competitiveness in SP (via Brasil Energia). [S]
- IEA (2020). *Outlook for Biogas and Biomethane: Prospects for organic growth*. [S]
- OIES (2026). *Biomethane in Europe: Why scaling up is harder than it looks* (NG203). [S]
- ACER (2026). Decarbonisation of the EU's natural gas market — Monitoring Report. [S]
- IFRI (2026). The European Biomethane Sector. [S]
- BIP Europe TF4 (2023). Insights into the current cost of biomethane production from real industry data. [S]
- World Biogas Association (2025). Market Report Brazil. [S]
- EBA (2026). *Biomethane Investment Outlook 2026* (1 Jul 2026). https://www.europeanbiogas.eu/publication/eba-biomethane-investment-outlook-2026/ [S]
- MME (2026). Consulta Pública nº 232/2026 — metas do RenovaBio 2027–2036 (15 Sep–29 Oct 2026). [S]
- Laws/regulations: Lei 14.993/2024; Decreto 12.614/2025; CNPE Res. 4/2026; ANP Res. 995, 996, 1.006/2026; ANP Res. 987/2025; ARSESP Del. 744/2017, 1.342/2022, 1.765/2025; Lei 13.576/2017; Lei 15.042/2024; MAPA IN 61/2020; CETESB P4.231. [S]

## Feedstock & supply
- Moraes, B.S., Zaiat, M., Bonomi, A. (2015). Anaerobic digestion of vinasse from sugarcane ethanol production in Brazil: Challenges and perspectives. *Renewable and Sustainable Energy Reviews* 44:888-903. doi:10.1016/j.rser.2015.01.023 `moraes2015` [two_sources] DOI confirmed through three reference lists; PILAR-2b's .022 is wrong (docs/21 C14). Publisher PDF read twice (ADR-0015, 2026-10-07).
- Fuess, L.T., Garcia, M.L., Zaiat, M. (2018). Seasonal characterization of sugarcane vinasse: Assessing environmental impacts from fertirrigation and the bioenergy recovery potential through biodigestion. *Science of the Total Environment* 634:29-40. doi:10.1016/j.scitotenv.2018.03.326 `fuess2018` [two_sources] Publisher PDF read twice (ADR-0015, 2026-10-07); identity also from the reference list of Buller et al. 2021.
- Buller, L.S. et al. (2021). A spatially explicit assessment of sugarcane vinasse as a sustainable by-product. *Science of the Total Environment* 765:142717. doi:10.1016/j.scitotenv.2020.142717 `buller2021` [two_sources] So far used only as the second identity source for `fuess2018`.
- de Melo, L.R. et al. (2024). Methane Production from Sugarcane Vinasse Biodigestion: An Efficient Bioenergy and Environmental Solution for the State of São Paulo, Brazil. *Methane* 3(2). doi:10.3390/methane3020017 `melo2024` [one_source]
- Zheng, Y. et al. (2022). Sugarcane harvest-area maps for Brazil. *ESSD* 14:2065. doi:10.5194/essd-14-2065-2022 [S]
- Di Tommaso, S. et al. (2024). 10 m sugarcane maps. *ESSD* 16:4931. doi:10.5194/essd-16-4931-2024 [S]
- Monitoring of Sugarcane Harvest in Brazil Based on Optical and SAR Data (2020). *Remote Sensing* 12(24):4080. [S]
- You, L., Wood, S. (2006). Entropy approach to spatial disaggregation of agricultural production. *Agric. Syst.* 90:329–347. doi:10.1016/j.agsy.2006.01.008 [S]
- Yu, Q. et al. (2020). SPAM2010. *ESSD* 12:3545. doi:10.5194/essd-12-3545-2020 [S]
- Joglekar, A. et al. (2019). Pixelating crop production. *PLOS ONE*. doi:10.1371/journal.pone.0212281 [S]
- Mennis, J. (2003). Generating surface models of population using dasymetric mapping. *Prof. Geogr.* 55(1):31–42. doi:10.1111/0033-0124.10042 [S]
- Gilbert, M. et al. (2018). GLW3. *Sci. Data* 5:180227. doi:10.1038/sdata.2018.227 [S]
- IBGE (2026). *Pesquisa da Pecuária Municipal 2025*, v. 53 (informativo). https://biblioteca.ibge.gov.br/visualizacao/periodicos/84/ppm_2025_v53_br_informativo.pdf [S]
- Carvalho, R.A., Torres, J.L.R. et al. (2026). [Title not confirmed; cane yield and ATR prediction with Sentinel-2 and ALOS/PALSAR-2 by phenological stage.] *Smart Agricultural Technology*. doi:10.1016/j.atech.2026.102464 [S]
- IPCC (2019). Refinement to the 2006 Guidelines, Vol. 4 Ch. 10 (manure management). [K]

## Process
- Volpi, M.P.C., Ferraz Junior, A.D.N., Franco, T.T., Moraes, B.S. (2021). Operational and biochemical aspects of co-digestion (co-AD) from sugarcane vinasse, filter cake, and deacetylation liquor. *Applied Microbiology and Biotechnology* 105:8969-8987. doi:10.1007/s00253-021-11635-x `volpi2021` [two_sources] Publisher PDF read twice (ADR-0015): `codig_bmp` and `temp` page-quoted.
- Volpi, M.P.C., Brenelli, L.B., Mockaitis, G., Rabelo, S.C., Franco, T.T., Moraes, B.S. (2022). Use of Lignocellulosic Residue from Second-Generation Ethanol Production to Enhance Methane Production Through Co-digestion. *BioEnergy Research* 15(1):602-616. doi:10.1007/s12155-021-10293-1 `volpi2022` [two_sources]
- Janke, L., Leite, A., Nikolausz, M., Schmidt, T., Liebetrau, J., Nelles, M., Stinner, W. (2015). Biogas Production from Sugarcane Waste: Assessment on Kinetic Challenges for Process Designing. *International Journal of Molecular Sciences* 16(9):20685-20703. doi:10.3390/ijms160920685 `janke2015_ijms_a` [two_sources] Publisher PDF read twice (ADR-0015, 2026-10-07).
- Leite, A.F., Janke, L., Lv, Z., Harms, H., Richnow, H.-H., Nikolausz, M. (2015). Improved Monitoring of Semi-Continuous Anaerobic Digestion of Sugarcane Waste: Effects of Increasing Organic Loading Rate on Methanogenic Community Dynamics. *International Journal of Molecular Sciences* 16(10):23210-23226. doi:10.3390/ijms161023210 `leite2015` [one_source] Cited in the repo as "Janke et al. 2015" with another paper's title (docs/21 C23).
- Janke, L., Leite, A.F., Nikolausz, M., Radetski, C.M., Nelles, M., Stinner, W. (2016). Comparison of start-up strategies and process performance during semi-continuous anaerobic digestion of sugarcane filter cake co-digested with bagasse. *Waste Management* 48:199-208. doi:10.1016/j.wasman.2015.11.007 `janke2016_wm` [two_sources] The `olr_max_cstr` central 3.0 matches it, as cited by Volpi 2021.
- Janke, L., Leite, A., Batista, K., Weinrich, S., Sträuber, H., Nikolausz, M., Nelles, M., Stinner, W. (2016). Optimization of hydrolysis and volatile fatty acids production from sugarcane filter cake: Effects of urea supplementation and sodium hydroxide pretreatment. *Bioresource Technology* 199:235-244. doi:10.1016/j.biortech.2015.07.117 `janke2016_bt` [one_source]
- Janke, L., Weinrich, S., Leite, A.F., Terzariol, F.K., Nikolausz, M., Nelles, M., Stinner, W. (2017). Improving anaerobic digestion of sugarcane straw for methane production: Combined benefits of mechanical and sodium hydroxide pretreatment for process designing. *Energy Conversion and Management* 141:378-389. doi:10.1016/j.enconman.2016.09.083 `janke2017` [one_source]
- Janke, L., Weinrich, S., Leite, A.F., Schüch, A., Nikolausz, M., Nelles, M., Stinner, W. (2017). Optimization of semi-continuous anaerobic digestion of sugarcane straw co-digested with filter cake: Effects of macronutrients supplementation on conversion kinetics. *Bioresource Technology* 245:35-43. doi:10.1016/j.biortech.2017.08.084 `janke2017_bt` [two_sources]
- Janke, L., Weinrich, S., Leite, A.F., Sträuber, H., Nikolausz, M., Nelles, M., Stinner, W. (2019). Pre-treatment of filter cake for anaerobic digestion in sugarcane biorefineries: Assessment of batch versus semi-continuous experiments. *Renewable Energy* 143:1416-1426. doi:10.1016/j.renene.2019.05.029 `janke2019` [two_sources] Cited as "Janke 2020" until 2026-10-06. Publisher PDF read twice (ADR-0015).
- Janke, L. et al. (2018). [Repo paraphrase: macronutrients / trace elements in sugarcane residue AD.] *Bioresour. Technol.* `janke2018` [unidentified] Candidates are listed in `references.csv`.
- Kiyuna, L.S.M., Fuess, L.T., Zaiat, M. (2017). Unraveling the influence of the COD/sulfate ratio on organic matter removal and methane production from the biodigestion of sugarcane vinasse. *Bioresource Technology* 232:103-112. doi:10.1016/j.biortech.2017.02.028 `kiyuna2017` [two_sources]
- Fuess, L.T., Kiyuna, L.S.M., Ferraz Jr., A.D.N., Persinoti, G.F., Squina, F.M., Garcia, M.L., Zaiat, M. (2017). Thermophilic two-phase anaerobic digestion using an innovative fixed-bed reactor for enhanced organic matter removal and bioenergy recovery from sugarcane vinasse. *Applied Energy* 189:480-491. doi:10.1016/j.apenergy.2016.12.071 `fuess2017` [two_sources]
- Fuess, L.T., Rodrigues, I.J., Garcia, M.L. (2017). Fertirrigation with sugarcane vinasse: Foreseeing potential impacts on soil and water resources through vinasse characterization. *Journal of Environmental Science and Health, Part A* 52(11):1063-1072. doi:10.1080/10934529.2017.1338892 `fuess2017_jesh` [two_sources] Publisher PDF read twice (ADR-0015, 2026-10-07). Not the Applied Energy paper above.
- Fuess, L.T. et al. (2024). [Repo paraphrase: solution to vinasse seasonality.] *Chem. Eng. J.* `fuess2024` [unidentified] Two CEJ candidates are listed in `references.csv`; which one was meant is an open question (docs/21 Q15).
- Fuess, L.T., Lens, P.N.L., Garcia, M.L., Zaiat, M. (2022). Exploring Potentials for Bioresource and Bioenergy Recovery from Vinasse, the "New" Protagonist in Brazilian Sugarcane Biorefineries. *Biomass* 2(4):374-411. doi:10.3390/biomass2040025 `fuess2022` [two_sources] Publisher PDF read twice (ADR-0015).
- Ferraz Júnior, A.D.N., Koyama, M.H., de Araújo Júnior, M.M., Zaiat, M. (2016). Thermophilic anaerobic digestion of raw sugarcane vinasse. *Renewable Energy* 89:245-252. doi:10.1016/j.renene.2015.11.064 `ferraz2016` [two_sources]
- Barbosa, M.Y.U., Alves, I., Del Nery, V., Sakamoto, I.K., Pozzi, E., Damianovic, M.H.R.Z. (2022). Methane production in a UASB reactor from sugarcane vinasse: shutdown or exchanging substrate for molasses during the off-season? *Journal of Water Process Engineering* 47:102664. doi:10.1016/j.jwpe.2022.102664 `barbosa2022` [two_sources]
- de Barros, V.G., Duda, R.M., Vantini, J.S., Omori, W.P., Ferro, M.I.T., de Oliveira, R.A. (2017). Improved methane production from sugarcane vinasse with filter cake in thermophilic UASB reactors, with predominance of Methanothermobacter and Methanosarcina archaea and Thermotogae bacteria. *Bioresource Technology* 244:371-381. doi:10.1016/j.biortech.2017.07.106 `barros2017` [one_source] Publisher PDF read twice (ADR-0015).
- Sica, P., Carvalho, R., Das, K.C., Baptista, A.S. (2020). Biogas and biofertilizer from vinasse: making sugarcane ethanol even more sustainable. *Journal of Material Cycles and Waste Management* 22:1427-1433. doi:10.1007/s10163-020-01029-y `sica2020` [two_sources] Publisher PDF read twice (ADR-0015).
- Silva Neto, J.V., Gallo, W.L.R. (2021). Potential impacts of vinasse biogas replacing fossil oil for power generation, natural gas, and increasing sugarcane energy in Brazil. *Renewable and Sustainable Energy Reviews* 135:110281. doi:10.1016/j.rser.2020.110281 `silvaneto2021` [two_sources] Publisher PDF read twice (ADR-0015).
- Aguiar, A.B.S., Volpi, M.P.C., de Souza, L.G.A., Leguisamo, A.M., da Silveira, J.M.J., Santos, N.B.C., Sambusiti, C., Moraes, B.S. (2026). Prospecting substrates and co-substrates for year-round biogas production in Brazilian sugarcane mills: Innovative arrangements scenarios. *Biomass and Bioenergy* 208:108828. doi:10.1016/j.biombioe.2025.108828 `aguiar2026` [two_sources] Publisher PDF read twice (ADR-0015).
- Hoffstadt, K. et al. (2020). Challenges and Prospects of Biogas from Energy Cane as Supplement to Bioethanol Production. *Agronomy* 10(6):821. doi:10.3390/agronomy10060821 `hoffstadt2020` [one_source]
- Chen, Y., Cheng, J.J., Creamer, K.S. (2008). Inhibition of anaerobic digestion process: A review. *Bioresource Technology* 99:4044-4064. doi:10.1016/j.biortech.2007.01.057 `chen2008` [two_sources]
- Angelidaki, I. et al. (2018). Biogas upgrading and utilization. *Biotechnol. Adv.* 36:452–466. doi:10.1016/j.biotechadv.2018.01.011 [K]
- Bauer, F. et al. (2013). Biogas upgrading — review of commercial technologies. SGC Rapport 2013:270. [K]
- Holliger, C. et al. (2016). Towards a standardization of BMP tests. *Water Sci. Technol.* 74:2515. doi:10.2166/wst.2016.336 [K]
- Batstone, D.J. et al. (2002). ADM1. IWA STR No. 13. [K]
- Barrera, E.L. et al. (2015). ADM1 with sulfate reduction for vinasse. *Water Res.* 71:42–54. [K]
- Cisneros de la Cueva et al. (2026). [Title not recorded by the digest; solid-state co-digestion of cattle manure with molasses.] *Waste Biomass Valor.* doi:10.1007/s12649-026-03540-z [S]
- Authors not seen (2026). Effects of acid pre-treatment of waste activated sludge on the biochemical methane potential of co-digestion with sugarcane vinasse. *Bioresour. Technol. Rep.* PII S2589014X26003750 (DOI not seen) [S]

## Economics & uncertainty
- AACE International RP 18R-97 — Cost estimate classification. [K]
- NETL QGESS — Cost estimation methodology. [K]
- Short, W., Packey, D., Holt, T. (1995). Manual for economic evaluation of energy efficiency and renewable energy technologies. NREL/TP-462-5173. [K]
- Zimmermann, A.W. et al. (2020). Techno-economic assessment guidelines for CO₂ utilization. *Front. Energy Res.* 8:5. doi:10.3389/fenrg.2020.00005 [S]
- Saltelli, A. et al. (2010). Variance based sensitivity analysis. *Comput. Phys. Commun.* 181:259–270. doi:10.1016/j.cpc.2009.09.018 [K]
- Herman, J., Usher, W. (2017). SALib. *JOSS* 2(9):97. doi:10.21105/joss.00097 [K]
- Saltelli, A. et al. (2019). Why so many published sensitivity analyses are false. *Environ. Model. Softw.* 114:29–39. [K]
- Biomass (2025). TEA of vinasse + filter cake co-digestion, Paraná. doi:10.3390/biomass5010010 [S]
- Biomass (2026). Brazil's biogas–biomethane potential: techno-economic inventory. MDPI 2673-8783/6/1/4 [S]

## Siting & logistics
- Paulino, E.J., Cherri, A.C., Soler, E.M. (2024). Suitability model and optimal location of biodigesters in the state of São Paulo. *Energy Reports* 11:4726–4740. doi:10.1016/j.egyr.2024.04.038 [identity two_sources]
- Costa, F.R. et al. (2020). GIS applied to location of bioenergy plants in tropical agricultural areas. *Renew. Energy* 153:911–918. doi:10.1016/j.renene.2020.01.050 [identity two_sources; study area Triângulo Mineiro, MG]
- Akca et al. (2023). *Applied Energy* 352:121932. doi:10.1016/j.apenergy.2023.121932 [S]
- Blanco, Hinojosa, Zavala (2024). The waste-to-biomethane logistic problem. *ACS Sustain. Chem. Eng.* 12:8453. doi:10.1021/acssuschemeng.4c01429 [S]
- Yue, You, Snyder (2014). Biomass-to-bioenergy supply chain optimization. *Comput. Chem. Eng.* 66:36–56. doi:10.1016/j.compchemeng.2013.11.016 [S]
- De Meyer et al. (2014). *RSER* 31:657–670. doi:10.1016/j.rser.2013.12.036 [S]
- Ghaderi, Pishvaee, Moini (2016). *Ind. Crops Prod.* 94:972–1000. doi:10.1016/j.indcrop.2016.09.027 [S]
- Jonker et al. (2016). *Applied Energy* 173:494–510. doi:10.1016/j.apenergy.2016.04.069 [S]
- Lamsal, Jones, Thomas (2017). Sugarcane harvest logistics in Brazil. *Transp. Sci.* 51(2):771–789. doi:10.1287/trsc.2015.0650 [S]
- Granco et al. (2018). Mill location spatial probit. *Biomass Bioenergy*. doi:10.1016/j.biombioe.2018.02.001 [S]
- Branco et al. (2019). Optimal locations for new sugarcane mills (MINLP). *Biomass Bioenergy* 127:105249. [S]
- Monteiro, C., Fanzeres, B., Kelman, R., Sampaio, R.A., Gaspar, L., Bacellar, L., Garcia, J.D. (2026). Integrated Investment and Operational Planning for Sugarcane-Based Biofuels and Bioelectricity under Market Uncertainty (OptBio). arXiv:2603.06823 [S]
- Huff, D.L. (1964). Defining and estimating a trading area. *J. Marketing* 28(3):34–38. [K]
- Malczewski, J. (2006). GIS-based MCDA survey. *IJGIS* 20(7):703–726. [K]
- Luxen, D., Vetter, C. (2011). OSRM. ACM SIGSPATIAL. doi:10.1145/2093973.2094062 [S]
- Boeing, G. (2017). OSMnx. *CEUS* 65:126–139. doi:10.1016/j.compenvurbsys.2017.05.004 [S]

## Climate, terrain
- Xavier, A.C. et al. (2022). BR-DWGD. *Int. J. Climatol.* 42(16):8390–8404. doi:10.1002/joc.7731 [S]
- Muñoz-Sabater, J. et al. (2021). ERA5-Land. *ESSD* 13:4349. doi:10.5194/essd-13-4349-2021 [S]
- Funk, C. et al. (2015). CHIRPS. *Sci. Data* 2:150066. doi:10.1038/sdata.2015.66 [S]
- Hawker, L. et al. (2022). FABDEM. *Environ. Res. Lett.* 17:024016. doi:10.1088/1748-9326/ac4d4f [S]
- Rossi, M. (2017). Mapa Pedológico do Estado de São Paulo. Instituto Florestal. [S]

## Reproducibility
- Wilkinson, M.D. et al. (2016). FAIR principles. *Sci. Data* 3:160018. [K]
- Pfenninger, S. et al. (2017; 2018). Open energy modelling. *Energy Policy*; *Energy Strategy Rev.* [K]
- Hörsch, J. et al. (2018). PyPSA-Eur. *Energy Strategy Rev.* 22:207–215. [K]
- Mölder, F. et al. (2021). Sustainable data analysis with Snakemake. *F1000Research* 10:33. [K]
