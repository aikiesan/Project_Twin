# R05 — Spatial/logistics data and methodological foundations

Tags: [S] confirmed in search · [M] memory — verify · "verify" = snippet-only or uncertain URL/DOI.

## A. Spatial & logistics data

### SP geoportals
1. **DataGEO / IDEA-SP** (SEMIL): http://datageo.ambiente.sp.gov.br/app/?ctx=DATAGEO · https://mapas.semil.sp.gov.br/ (verify) — UCs, 2017 pedology, DER roads, ZEE; SHP/KMZ/WMS. Records: state UCs `{12408EC8-F1B9-410E-AA8C-74869C73AA2B}`, federal UCs `{C85D7EBE-E778-445E-AB61-03A33D4B7E8A}`, DER roads `{502C5011-82FA-4760-9ADC-03A9B5AD51FF}` (path `datageo.ambiente.sp.gov.br/geoportal/catalog/search/resource/details.page?uuid=…`). [S]
2. **DER-SP SRE**: https://dadosabertos.sp.gov.br/organization/departamento-de-estradas-de-rodagem-der?res_format=SHP · http://www.der.sp.gov.br/WebSite/Documentos/Mapas.aspx — SHP/KMZ/XLSX; jurisdiction, surface, km (attributes to verify). [S]
3. **DNIT SNV**: https://servicos.dnit.gov.br/vgeo/ · https://servicos.dnit.gov.br/dadosabertos/ · https://www.gov.br/dnit/pt-br/assuntos/atlas-e-mapas/pnv-e-snv [S]
4. **IGC-SP**: http://geoportal.igc.sp.gov.br/ · http://geoportal.igc.sp.gov.br/centraldownloads/ — official 1:50,000 boundaries. [S]
5. **GEOSEADE**: https://portalgeo.seade.gov.br/ · https://repositorio.seade.gov.br/group/geoseade [S]
6. **ZAA Setor Sucroenergético SP (2008)**: https://www.ciiagro.sp.gov.br/Zoneamento_Agroambiental/index.htm · https://smastr16.blob.core.windows.net/etanolverde/2011/10/mapazoneamentoagroambiental_120911.pdf · https://semil.sp.gov.br/sma/etanolverde/ — SHP **SAD-69** → reproject. [S]
7. **CAR/SICAR**: https://consultapublica.car.gov.br/publico/imoveis/index · Embrapa notes: https://www.embrapa.br/en/web/territorial/car/como-fizemos/bases-de-dados [S]
8. **Protected areas** (Fundação Florestal/SIGAM): https://sigam.ambiente.sp.gov.br/sigam3/Default.aspx?idPagina=16758 [S]
9. **ANA BHO 2017 5k** (now superseded by BHAE): https://metadados.snirh.gov.br/geonetwork/srv/api/records/f7b1fc91-f5bc-4d0d-9f4f-f4e5061e5d8f [S]
10. **IBGE BC250 2023**: https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2023/ [S]
11. **Soils**: Rossi 2017 — https://www.infraestruturameioambiente.sp.gov.br/institutoflorestal/2017/09/mapa-pedologico-do-estado-de-sao-paulo-revisado-e-ampliado/ · https://geo.cati.sp.gov.br/server/rest/services/Hosted/Pedologico_Rossi_2017/MapServer · MapBiomas Solo: https://brasil.mapbiomas.org/iniciativas-e-produtos/solo/ [S]

### DEM
- Copernicus GLO-30: https://registry.opendata.aws/copernicus-dem/ · https://copernicus-dem-30m.s3.amazonaws.com/readme.html [S]
- **FABDEM** (Hawker et al. 2022, *ERL* 17:024016, doi:10.1088/1748-9326/ac4d4f): https://gee-community-catalog.org/projects/fabdem/ — preferred [S]
- ALOS AW3D30, SRTM/NASADEM [M]

### Climate
- **BR-DWGD** (Xavier et al. 2022, *Int. J. Climatol.* 42(16):8390–8404, doi:10.1002/joc.7731) 0.1°, daily 1961–2020: https://github.com/AlexandreCandidoXavier/BR-DWGD · https://gee-community-catalog.org/projects/br_dwgd/ [S]
- **ERA5-Land** (Muñoz-Sabater et al. 2021, *ESSD* 13:4349, doi:10.5194/essd-13-4349-2021) ~9 km hourly incl. soil temperature [S]
- **CHIRPS v2** (Funk et al. 2015, *Sci. Data* 2:150066, doi:10.1038/sdata.2015.66; dataset doi:10.15780/G2RP4Q) [S]
- **INMET** stations: https://portal.inmet.gov.br/dadoshistoricos [S]

### Energy-sector geodata
- **EPE WebMap**: https://gisepeprd2.epe.gov.br/WebMapEPE/ · https://www.epe.gov.br/pt/publicacoes-dados-abertos/publicacoes/webmap-epe — pipelines, city gates, UPGN, LNG, biofuel plants, power (verify) [S]
- **ANEEL SIGEL**: https://sigel.aneel.gov.br/ · https://www.aneel.gov.br/informacoes-geograficas [S]
- **ANP biomethane panel** (see R03); SEMIL SP ~700 k m³/d end-2025: https://semil.sp.gov.br/2025/12/sao-paulo-avanca-na-descarbonizacao-e-se-aproxima-da-marca-de-700-mil-metros-cubicos-por-dia-de-producao-de-biometano/

### Sugarcane maps & harvest timing
- Zheng et al. 2022 *ESSD* 14:2065 (TWDTW, 30 m harvest area 2016–2019): https://essd.copernicus.org/articles/14/2065/2022/ [S]
- Di Tommaso et al. 2024 *ESSD* 16:4931 (10 m 2019–2022, GEDI + S2): https://essd.copernicus.org/articles/16/4931/2024/ · https://zenodo.org/records/10871164 [S]
- Optical + SAR harvest monitoring, *Remote Sensing* 12(24):4080: https://www.mdpi.com/2072-4292/12/24/4080 [S]
- **cane_cycle** (no license stated): https://github.com/jfontenelli/cane_cycle [S]
- Sentinel-1 VH harvest detection (IGARSS 2019?) [verify]
- CANASAT: Rudorff et al. 2010 (doi:10.3390/rs2041057); Aguiar et al. 2011 (doi:10.3390/rs3122682) [M]

### Routing & grid
- OSM Geofabrik Sudeste: https://download.geofabrik.de/south-america/brazil/sudeste.html [M]
- OSRM (Luxen & Vetter 2011, doi:10.1145/2093973.2094062); R interface doi:10.21105/joss.04574 [S]
- Valhalla (truck costing): https://github.com/valhalla/valhalla [M]
- OSMnx (Boeing 2017, doi:10.1016/j.compenvurbsys.2017.05.004) [S]; pgRouting https://pgrouting.org [M]
- H3: https://github.com/uber/h3 · https://uber.github.io/h3-py/intro.html — res 7 ≈ 5.2 km², res 8 ≈ 0.74 km² [M]

### Costs & regulation (logistics)
- **ESALQ-LOG SIFRECA**: https://sifreca.esalq.usp.br/ · https://esalqlog.esalq.usp.br/faqsifreca — weekly freight R$/t, R$/t·km, > 500 routes; sugar, ethanol, grains, fertilizers; **no raw cane**; partly paid [S]
- Cane transport cost vs distance (ResearchGate, verify)
- **CONTRAN 882/2021**: https://www.abti.org.br/anexos/20211213_res_contran_882_limites_pesos_dimensoes.pdf · https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-contran/resolucoes/Resolucao8822021.pdf — CVC up to 74 t at 25–30 m [S]
- ANTT freight floor (Res. 5.867/2020 + updates) [M]
- **IEA-SP VTN**: https://iea.agricultura.sp.gov.br/out/precosdeterraagricolas.php · methodology https://iea.agricultura.sp.gov.br/out/Metodologia/MetodologiaValordeTerra.pdf — municipality/EDR, semiannual [S]
- **INCRA RAMT SP**: https://www.gov.br/incra/pt-br/assuntos/governanca-fundiaria/relatorio-de-analise-de-mercados-de-terras/sao-paulo · …/RAMT_SRSP_2022.pdf [S]

## B. Methodological foundations

### B1 Siting
- **Paulino, Cherri & Soler 2024**, *Energy Reports* 11:4726–4740, doi:10.1016/j.egyr.2024.04.038 — SP GIS-AHP + optimization (closest precedent) [S]
- Costa et al. 2020, *Renew. Energy* 153:911–918, doi:10.1016/j.renene.2020.01.050 [S]
- Akca et al. 2023, *Applied Energy* 352:121932, doi:10.1016/j.apenergy.2023.121932 [S]
- Blanco, Hinojosa & Zavala 2024, *ACS SCE* 12:8453–8466, doi:10.1021/acssuschemeng.4c01429 (PMC11151424) [S]
- Silva, Alçada-Almeida & Dias 2014 (*Biomass Bioenergy* 71; doi:10.1016/j.biombioe.2014.10.025 [M]); Silva et al. 2017 (*Comput. OR*; doi:10.1016/j.cor.2017.02.016 [M]); Franco et al. 2015 (*Appl. Energy*; doi:10.1016/j.apenergy.2014.11.060 [M]); Höhn et al. 2014 (*Appl. Energy* 113; doi:10.1016/j.apenergy.2013.07.005 [M]); Balaman & Selim 2014 (doi:10.1016/j.apenergy.2014.05.043 [M]); Malczewski 2006 (doi:10.1080/13658810600661508 [M]); Saaty 1990 (doi:10.1016/0377-2217(90)90057-I [M]); ReVelle & Swain 1970 (doi:10.1111/j.1538-4632.1970.tb00142.x [M])
- SP/Brazil context: doi:10.3390/en17071657 (SP sewage biomethane); doi:10.3390/methane3020017; https://www.mdpi.com/2673-8783/6/1/4; https://sites.usp.br/rcgi/ieeusp-maps-biogas-and-biomethane-production-in-sao-paulo/

### B2 Supply chains with seasonality/storage
- Yue, You & Snyder 2014, doi:10.1016/j.compchemeng.2013.11.016 · De Meyer et al. 2014, doi:10.1016/j.rser.2013.12.036 · Ghaderi et al. 2016, doi:10.1016/j.indcrop.2016.09.027 · Energies 10:1895, doi:10.3390/en10111895 · Egieya et al. 2018/2019 (multi-period biogas networks; DOIs verify) · Jonker et al. 2016, doi:10.1016/j.apenergy.2016.04.069 [S]

### B3 Mill catchments
- Typical SP haul 20–30 km (≈ 25 km; max ~50 km) — grey literature: https://sucroenergetico.revistaopinioes.com.br/en/revista/detalhes/8-logistica-de-transporte-da-cana-de-acucar-desafi/ · https://anaisonline.uems.br/index.php/ecaeco/article/download/2803/2873/3492 [S] → gap
- Lamsal, Jones & Thomas 2017, doi:10.1287/trsc.2015.0650 (instances Zenodo 13256049) [S]
- Branco et al. 2019, *Biomass Bioenergy* 127:105249 (https://www.sciencedirect.com/science/article/abs/pii/S0961953419301898) [S]
- Granco et al. 2018, doi:10.1016/j.biombioe.2018.02.001 [S]
- Huff 1964 (doi:10.1177/002224296402800307 [M]); Okabe et al. 2008 network Voronoi (doi:10.1080/13658810701587891 [M]); arXiv 2512.01795 (Euclidean Voronoi misallocates ~15 %) [S]
- Recommended: network Voronoi baseline → Huff/logit calibrated → capacity-constrained LP; report sensitivity.

### B4 Downscaling
- You & Wood 2006 (doi:10.1016/j.agsy.2006.01.008) · Yu et al. 2020 SPAM (doi:10.5194/essd-12-3545-2020; mapspamc https://michielvandijk.github.io/mapspamc/) · You et al. 2014 (doi:10.1016/j.agsy.2014.01.002 [M]) · Joglekar et al. 2019 (doi:10.1371/journal.pone.0212281) · Mennis 2003 (doi:10.1111/0033-0124.10042) · Gilbert et al. 2018 GLW3 (doi:10.1038/sdata.2018.227) · arXiv 2407.11173 · *Sci. Data* 2025 s41597-025-05572-x [S]

### B5 TEA & uncertainty
- Zimmermann et al. 2020, doi:10.3389/fenrg.2020.00005 [S]; Langhorst et al. 2022 v2 [M]; NETL QGESS [M]; AACE 18R-97 [M]; Short, Packey & Holt 1995 NREL/TP-462-5173 (https://www.nrel.gov/docs/legosti/old/5173.pdf) [M]; IEA 2020 (https://iea.blob.core.windows.net/assets/5b757571-c8d0-464f-baad-bc30ec5ff46e/OutlookforBiogasandBiomethane.pdf) [S]
- Saltelli et al. 2010 (doi:10.1016/j.cpc.2009.09.018), SALib (doi:10.21105/joss.00097), Saltelli et al. 2019 (doi:10.1016/j.envsoft.2019.01.012), JCGM 101:2008 [M]

### B6 Supply/cost curves
- IEA 2020; Gas for Climate/Guidehouse 2019, 2022 [M]; ICCT 2018 [M]; AGF/ICF 2019 [M]; US DOE Billion-Ton 2023 [M]; NREL 2013 [M]; WBA Market Report Brazil 2025: https://www.worldbiogasassociation.org/wp-content/uploads/2025/04/WBA-Market-Report-Brazil-2025.pdf [S]

### B7 Reproducibility
- FAIR (Wilkinson 2016, doi:10.1038/sdata.2016.18) · Pfenninger et al. 2017 (doi:10.1016/j.enpol.2016.11.046), 2018 (doi:10.1016/j.esr.2017.12.002) · Mölder et al. 2021 Snakemake · **PyPSA-Eur** (https://github.com/PyPSA/pypsa-eur; Zenodo doi:10.5281/zenodo.3520874; Hörsch et al. 2018 doi:10.1016/j.esr.2018.08.012; PyPSA doi:10.5334/jors.188) · DVC https://dvc.org [M/S]

## C. Recommended stack
PostgreSQL + PostGIS + pgRouting + h3-pg · EPSG:4674 storage, EPSG:31982/31983 metric · geopandas, shapely 2, pyogrio, rasterio, rioxarray, xarray/dask, exactextract, h3-py · Valhalla/OSRM on Geofabrik Sudeste + DER/SNV attributes · GEE or Planetary Computer STAC (stackstac/odc-stac) · Pyomo/linopy + HiGHS (Gurobi academic) · SALib + LHS (scipy.stats.qmc) · Snakemake or DVC; manifest with URL, date, SHA256, license; conda-lock/Docker; pre-commit; CITATION.cff.

## D. Gaps
No peer-reviewed SP haul distance; SIFRECA lacks cane/vinasse/digestate; DER attribute schema unchecked; ZAA dated (SAD-69); CAR self-declared; cane_cycle license; many [M] DOIs; EPE WebMap/ANP panel snippet-only; no SP point manure inventory with herd sizes beyond CP2B points.
