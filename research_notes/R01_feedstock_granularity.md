# R01 — Feedstock data: finest public/requestable granularity for SP

Flags: **V** read · **S** snippet · **K** prior knowledge. Only the Benri report was read in full (see `evidence/`).

## 1. Sugarcane mills

### 1.1 MAPA SAPCANA [S]
- Mandatory registry of sugar/ethanol units (IN MAPA 33/2009); units declare crush, production, sales, stocks.
- Public: **state/region biweekly aggregates**; historical "Relação das unidades cadastradas" (name, municipality, type). Snippets: 158 SP units (2016); 423 national (248 mixed, 159 distilleries, 16 sugar).
- Per-unit production not public → LAI (likely refused; annual crush may succeed).
- URLs: https://sistemasweb.agricultura.gov.br/pages/SAPCANA.html · https://www.gov.br/agricultura/pt-br/acesso-a-informacao/acoes-e-programas/cartas-de-servico/politica-de-agroenergia/acompanhamento-da-producao-sucroalcooleira · https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/agroenergia/acompanhamento-da-producao-sucroalcooleira/2025-2026-1/Acompanhamentodaproduo2526_010326.pdf · https://www.gov.br/agricultura/pt-br/acesso-a-informacao/acoes-e-programas/cartas-de-servico/politica-de-agroenergia/cadastro-de-unidades-industriais-cooperativas-empresas

### 1.2 ANP ethanol producers [S]
- Map of all ANP-authorized producers with location and authorized capacity (anhydrous/hydrated, m³/d); tankage per producer; monthly production 2012–2026; feedstock (cane/corn).
- **Capacity & tankage per plant; monthly production apparently by UF/feedstock** (verify). CSVs updated monthly.
- URLs: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/producao-de-biocombustiveis · https://dados.gov.br/dataset/painel-de-produtores-de-derivados-producao-de-biocombustiveis · https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/arquivos-painel-de-produtores-de-derivados-producao-de-biocombustiveis/etanol-capacidade.pdf · https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/arquivos-painel-de-produtores-de-derivados-producao-de-biocombustiveis/g-etanol-tancagem.csv/view · https://csa.anp.gov.br/downloads/manuais-isimp/MANUAL-DO-I-SIMP-PRODUTORES-DE-ETANOL.pdf

### 1.3 ANP RenovaBio certification panel & certificate list [S]
- Per certified unit: inspection firm, route (e.g. E1GC), NEEA, eligible fraction, validity; weekly.
- **128 certificates in force in SP in 2025** (MME RenovaBio annual report 2025).
- URLs: https://www.gov.br/anp/pt-br/centrais-de-conteudo/paineis-dinamicos-da-anp/paineis-dinamicos-do-renovabio/painel-dinamico-de-certificacoes-de-biocombustiveis-renovabio · https://www.gov.br/anp/pt-br/assuntos/renovabio/certificados-producao-importacao-eficiente-biocombustiveis · https://www.gov.br/anp/pt-br/assuntos/renovabio/certificacao-de-biocombustiveis · https://www.gov.br/mme/pt-br/assuntos/secretarias/petroleo-gas-natural-e-biocombustiveis/renovabio-1/relatorios-anuais-do-renovabio/relatorio-anual-renovabio-2025

### 1.4 ANP Plataforma CBIO panel [S]
- Lastro, CBIOs issued/retired, B3 trades; biweekly; apparently per issuer (verify).
- URL: https://www.gov.br/anp/pt-br/centrais-de-conteudo/paineis-dinamicos-da-anp/paineis-dinamicos-do-renovabio/painel-dinamico-da-cbio · https://www.udop.com.br/noticia/2021/06/30/anp-passa-a-divulgar-mais-informacoes-sobre-lastro-de-cbios.html

### 1.5 RenovaBio certification reports ⭐ [V for Benri / S others]
- Published by inspection firms: Benri https://www.benriratings.com/consulta/publica/ · Accenture https://www.accenture.com/br-pt/services/sustainability/consulta-publica-renovabio · also KPMG, SGS, Verifit, Totum, Intertek.
- **Read in full:** Benri, Usina Santa Adélia – Pereira Barreto/SP, RenovaCalc v7, data 2021–2023 → cane 2,329,621.65 / 2,683,176.75 / 3,551,156.27 t; anhydrous (SIMP) 178,259,431 / 207,056,006 / 225,336,933 L; hydrated 15,730,909 / 9,469,960 / 61,836,900 L; vinasse applied 1,286,435,206 / 1,469,236,638 / 1,613,510,481 L (680.0 / 669.5 / 524.5 L/t cane); eligible 98.53 %; NEEA anhydrous 62.34, hydrated 62.07 gCO₂eq/MJ; no straw recovery, no filter cake declared.
- Other reports: https://www.accenture.com/content/dam/accenture/final/accenture-com/document-2/Accenture-Rel-Validacao-v02_site.pdf · https://sgssustentabilidade.com/wp-content/uploads/2023/04/04_Relatorio_Certificacao_Biocombustiveis_Alcoazul_final.pdf · https://verifit.com.br/wp-content/uploads/2021/11/FINAL_Val-Renovabio_Otavio-Lage-1.pdf · https://assets.kpmg.com/content/dam/kpmg/br/pdf/2020/02/usina-belavista-relatorio-parcial-certifica%C3%A7%C3%A3orenovabio.pdf · https://institutototum.com.br/wp-content/uploads/2025/07/FM.REN_.14.00-Relatorio-Biometano-Essencis-parcial_compressed-1.pdf
- **Use:** near-census of mill-year data 2018–2025 by scraping ~128 SP certificates.

### 1.6 ANP RenovaBio default-parameter studies [S]
- https://www.gov.br/anp/pt-br/assuntos/renovabio/arq/arquivos-estudos-relatorio-e-seminarios/relatoriofinalcanadeacucar.pdf · https://www.gov.br/anp/pt-br/assuntos/renovabio/arq/arquivos-formularios-informes-tecnicos/informe-tecnico-02-sbq.pdf · https://www.gov.br/anp/pt-br/assuntos/renovabio/arq/arquivos-comunicados-renovabio/relatorio-etoh-melaco.pdf

### 1.7 UNICA / UNICAdata [S]
- Biweekly Centro-Sul (with SP breakdown): crush, ATR, sugar, ethanol, mix. SP ≈ **57.5 %** of Centro-Sul crush; Centro-Sul 621.88 Mt (2024/25) vs 654.45 Mt (2023/24).
- URLs: https://unicadata.com.br · https://unica.com.br/noticias/safra-2026-2027-2a-quinzena-de-abril/ · https://www.novacana.com/pdf/02102025111036_Unica-021025_NC.pdf · https://temp.unicadata.com.br/arquivos/pdfs/2020/08/8356d728835ef21f6048f6e9683057e5.pdf

### 1.8 CONAB cane survey [S]
- Area, yield, crush, ATR, sugar, ethanol by UF; 4 surveys/season. https://www.conab.gov.br/info-agro/safras · https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/safras/safra-de-cana-de-acucar/arquivos-boletins/1o-levantamento-safra-2026-27/e-book_boletim-de-safras-cana_1o-lev-2026-27.pdf

### 1.9 IEA-SP database [S]
- ~150 items (crops incl. cane, herds) by **municipality, EDR, state; annual since 1983**; ~1,800 collection points. https://iea.agricultura.sp.gov.br/out/Bancodedados.php · https://iea.agricultura.sp.gov.br/out/conceito.php · https://iea.agricultura.sp.gov.br/out/TerTexto.php?codTexto=14209

### 1.10 LUPA farm census (CATI/IEA) [S]
- 2016/17: 339,442 UPAs (334,741 rural; 20.29 Mha); rounds 1995/96, 2007/08, 2016/17; 2026/27 reportedly planned. Municipal/EDR tables public; UPA microdata restricted (agreement).
- https://www.cati.sp.gov.br/projetolupa/estudos_lupa.php · https://iea.agricultura.sp.gov.br/ftpiea/ie/2020/IE-19-2019.pdf · https://www.apta.sp.gov.br/noticias/iea-divulga-os-resultados-preliminares-do-lupa-2016-17

### 1.11 CETESB P4.231 vinasse application plans (PAV) [S/K]
- Annual PAV per mill by 2 April with spreadsheets/maps: volume, K₂O, dose per area; simplified PAV (2020); new procedure (2023). Not published → LAI/partnership.
- https://cetesb.sp.gov.br/wp-content/uploads/2024/09/Norma-Tecnica-Cetesb-P4.231-Vinhaca-Criterios-e-procedimentos-para-aplicacao-no-solo-agricola.pdf · https://smastr16.blob.core.windows.net/home/2025/06/VIII-CETESB-v2-1.pdf

### 1.12 Company disclosures [S]
- São Martinho: 4 mills (São Martinho/Pradópolis ~10 Mt/season; Iracema; Santa Cruz; Boa Vista-GO), ~24 Mt capacity; fiscal year Apr–Mar. https://ri.saomartinho.com.br/Download.aspx?Arquivo=FOnPFpXzSWi6kttDvxB7Dg%3D%3D · https://www.saomartinho.com.br/show.aspx?idMateria=rk2CGXH5SOIFTobanx1b+g%3D%3D · https://www.saomartinho.com.br/Download.aspx?Arquivo=awGf5yddj8JEw+wej3QRMQ%3D%3D&IdCanal=E%2F5CI5hbGiTfjZ7mhu2y5w%3D%3D
- Raízen Bonfim (Guariba) 21 MW from vinasse + filter cake (Oct 2020); Costa Pinto biomethane 26 Mm³/yr, contracts Yara (20,000 m³/d) and VW (50,000 m³/d). https://www.canalenergia.com.br/noticias/53151138/raizen-inaugura-usina-de-21-mw-a-partir-de-biogas · https://revistarpanews.com.br/raizen-ja-comecou-a-utilizar-biometano-no-transporte-de-cana/

### 1.13 NovaCana database [S]
- 170 SP mills; group, municipality, capacity, products, seals; partly paid. https://www.novacana.com/usinas_brasil/estados/sao-paulo · https://data.novacana.com/usinas_brasil/estado/SP · https://www.novacana.com/usinas_brasil/ranking/moagem · https://www.novacana.com/usinas_brasil/mapa

### 1.14 Other registries [S]
- Protocolo Agroambiental certified mills (2014): https://smastr16.blob.core.windows.net/home/2024/04/Lista_Usinas_certificadas_site-03_04_14.pdf · CONSECANA-SP: https://www.consecana.com.br/industriasd.asp?id=122 · SEADE: https://informa.seade.gov.br/sao-paulo-lidera-producao-de-etanol-no-pais/
- ESALQ/PECEGE cane cost of production [K].

## 2. Livestock
- **IBGE PPM** tables 3939 (herds 1974–2024, municipal) & 74 (products): https://sidra.ibge.gov.br/pesquisa/ppm/tabelas [S]
- **Censo Agro 2017** (confinement, size classes): https://www.ibge.gov.br/estatisticas/economicas/agricultura-e-pecuaria/21814-2017-censo-agropecuario.html [S/K]
- **CDA-SP GEDAVE / e-GTA** (property registration, herd balance, animal transit, mandatory since 28/04/2015): https://www.defesa.agricultura.sp.gov.br/www/servicos/?%2Fcadastro-de-propriedade-e-atividade-produtiva-pecuaria%2F=&cod=120 · https://www.defesa.agricultura.sp.gov.br/arquivos/gedave/animal/GEDAVE-Manual_de_GTA_e_Controle_de_Saldo_de_Aves_1.1.pdf · http://gedave.defesaagropecuaria.sp.gov.br/ → LAI for aggregates.
- **MAPA SIF/SIGSIF**: ~3,139 establishments CSV; monthly slaughter by species/UF (PGA-SIGSIF reliable from Feb 2021): https://dados.agricultura.gov.br/dataset/servico-de-inspecao-federal-sif · https://sistemas.agricultura.gov.br/pga_sigsif/pages/view/sigsif/abatemensalespecieporuf/indexAbateMensalEspeciePorUf.xhtml · https://sigsif.agricultura.gov.br/sigsif_cons/!ap_abate_estaduais_cons?p_select=SIM · Embrapa mapping: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1117116/1/CNPC-2019-Doc135.pdf
- **SISP** (state inspection; ~762 establishments, 360 meat — historical): https://www.defesa.agricultura.sp.gov.br/noticias/2024/sisbi-abatedouros-de-sao-paulo-sao-liberados-para-solicitar-adesao-ao-sistema-brasileiro-de-inspecao-de-produtos-de-origem-animal,2121.html · https://servicos.sp.gov.br/fcarta/03F4D561-25B3-43E0-8E04-E8A059E77C2E
- **Bastos layers** (~19.7 M birds; ~17.6 M laying; ~14.5 M eggs/d; ~14,000 t manure sold/month — possibly dated; conflicting "11 M hens"): https://www.agrimidia.com.br/negocios/mercado-interno/bastos-produz-166-ovos-por-segundo/ · https://www.gazetasp.com.br/turismo/cidade-do-interior-de-sp-tem-mais-de-11-milhoes-de-galinhas-e-virou-a/

## 3. Other substrates
- **ANA Atlas Esgotos / ETE 2019** (SHP/CSV/GeoJSON): https://www.ana.gov.br/atlasesgotos/ · https://dados.ana.gov.br/pt_PT/dataset/estacoes-de-tratamento-de-esgoto-2019/resource/f28bf7c8-8827-41f9-b7aa-91f91bddb4d5 · https://metadados.snirh.gov.br/geonetwork/srv/api/records/1d8cea87-3d7b-49ff-86b8-966d96c9eb01
- **SINISA** (ex-SNIS): https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/resultados-sinisa-2025
- **Sabesp**: ETE Barueri 16 m³/s capacity, >14 m³/s avg (2022), new 10,000 m³ digesters; per-ETE data generally not published: https://www.institutodeengenharia.org.br/site/wp-content/uploads/2024/04/SABESP-INSTITUTO-BARUERI-ARTIGO.pdf
- **CETESB RSU inventory 2023** (604 municipalities = 93.5 % adequate disposal): https://cetesb.sp.gov.br/residuossolidos/wp-content/uploads/sites/26/2024/05/Inventario-Estadual-de-Residuos-Solidos-Urbanos-no-Estado-de-Sao-Paulo-2023.pdf · IQR layer: https://datageo.ambiente.sp.gov.br/geoportal/catalog/search/resource/details.page?uuid=%7B669FA098-FA29-4B48-AB81-5708D3FED900%7D
- Agro-industrial (citrus pulp, dairy, brewery, corn vinasse): no open per-plant source confirmed [K: SIF, CETESB licences, CitrusBR/Fundecitrus, SIPEAGRO].
- Straw: CNPEM/LNBR SUCRE: https://cnpem.br/en/palha-da-cana-pode-gerar-355-twh-de-energia/ · https://lnbr.cnpem.br/residuo-da-colheita-de-cana-palha-protege-o-solo-e-tem-alto-potencial-gerador-de-bioenergia/

## 4. Seasonality sources
UNICA biweekly (SP) · SAPCANA biweekly (UF) · ANP monthly (UF/feedstock) · SIGSIF monthly · CONAB 4×/season · MapBiomas annual only · INPE Canasat (~2003–2013) [K] · no ready monthly harvest map → build with Sentinel-2.

## 5. Published coefficients
| Parameter | Value | Source | Flag |
|---|---|---|---|
| Vinasse | 10–15 L/L ethanol | Moraes, Zaiat & Bonomi 2015 (https://www.researchgate.net/publication/276305196) | S |
| Vinasse applied, Santa Adélia | 680 / 669.5 / 524.5 L/t cane | Benri report | V |
| Vinasse applied ÷ ethanol 2023 | ≈ 5.6 L/L | derived | V/D |
| Ethanol yield 2023 | ≈ 80.9 L/t | derived | V/D |
| Filter cake | 30–40 kg/t cane | CBQ 2019 https://www.abq.org.br/cbq/2019/trabalhos/9/1232-26531.html | S |
| Straw | 140 kg DM/t cane; 50 % recoverable (≥ 7 t DM/ha/yr left) | CNPEM/LNBR | S |
| Vinasse CH₄ (SP avg COD) | 0.291–0.309 m³/kg COD | vinasse literature (Moraes context) | S |
| UASB vinasse | 0.289 m³ CH₄/kg COD removed at 12.5 kg COD/m³·d; COD removal 66–85 % | literature | S |
| Theoretical | ≈ 0.35 m³ CH₄/kg COD removed | stoichiometry | S |
| Vinasse BMP (Maranhão) | 398.89 ± 19.37 NmL/g VS | https://ojs.revistadelos.com/ojs/index.php/delos/article/view/7710 | S |
| Raw vinasse | 185 NmL/g COD (2,628 NmL/L); co-fermentation 343–386 NmL/g COD | unclear | S |
| Swine full cycle | 150–170 (alt. 100) L/sow/d | Embrapa Circ. 32 https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/487548/1/Circ32.pdf | S |
| Swine piglet unit | 35–40 (alt. 60) L/sow/d | Embrapa | S |
| Swine finishing | 13–15 (alt. 7.5) L/animal/d; DM 1.7–3.5 % | Embrapa | S |
| Dairy cow manure | 45–48 kg/d (~10 % body weight) | Embrapa | S |
| Confined beef | 30–35 kg/head/d | Embrapa | S |
| B₀ dairy / swine | 0.24 / 0.48 m³ CH₄/kg VS (IPCC 2019 per snippet; inconsistent) | verify IPCC Vol 4 Ch 10 | S |
| Vinasse-to-power SP | 33 % of municipalities viable; 659 GWh/yr | https://www.sciencedirect.com/science/article/abs/pii/S0959652620310659 | S |
| SP share of Brazil biogas potential | ≈ 31 % | https://www.mdpi.com/2673-8783/6/1/4 | S |

EPE coefficient sources (blocked): DEA 15/14 Inventário Energético de Resíduos Rurais · NT PR 04/18 · Informe biogás pecuária bovina (URLs in `registry/sources.yaml` / original report).
Additional: https://doi.org/10.3390/methane3020017 · https://doi.org/10.3390/biomass5010010 · https://www.sciencedirect.com/science/article/abs/pii/S0959652621044462 · https://link.springer.com/article/10.1007/s10163-020-01029-y · https://sciencedirect.com/science/article/pii/S2589014X23003699 · https://www.researchgate.net/publication/349468075 · https://www.mdpi.com/2227-9717/14/19/3092 · https://www.ipcc-nggip.iges.or.jp/public/gp/bgp/4_3_CH4_Animal_Manure.pdf · https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1103097/1/Mariliarenovacalc.pdf

## 6. Top 10 (ranked)
1 RenovaBio reports · 2 ANP producer panel/open data · 3 ANP RenovaBio panel · 4 UNICA biweekly · 5 CETESB PAV (LAI) · 6 IBGE PPM + LUPA · 7 ANA ETE + SINISA · 8 CETESB RSU + IQR · 9 SIF/SIGSIF · 10 IEA-SP + SAPCANA.

## 7. Gaps
Per-plant monthly crush/ethanol (LAI) · per-mill vinasse (CETESB) · farm-level livestock (CDA/CATI) · SISP list · per-ETE sludge · agro-industrial per plant · monthly harvest maps (build) · straw recovery per mill · IPCC VS/B₀ verification.
