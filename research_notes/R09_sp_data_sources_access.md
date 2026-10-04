# R09: SP data sources, concrete access routes (2026-10-04)

Scope: exact pages, files, update cadence, granularity and access for SP-level data the engine needs. The note adds to `registry/sources.yaml`, R01 and R05 and does not repeat what they already cover.
Flags: **V** = primary document opened and read · **S** = search snippet or secondary page only · **K** = prior knowledge · **M** = read on a third-party mirror (not the primary source).
Budget used: 25 web searches, no successful WebFetch of a Brazilian host.

## 0. Access environment (read this first)

| Finding | Evidence | Flag |
|---|---|---|
| **Every Brazilian data host returned HTTP 403 from the egress proxy** (curl and WebFetch) on 2026-10-04: www.gov.br (ANP, MAPA, ANA, Cidades, ANTT), dados.gov.br, dados.agricultura.gov.br, sistemasweb(4).agricultura.gov.br, sigsif/sistemas.agricultura.gov.br, csa.anp.gov.br, cbios.anp.gov.br, renovacalc.anp.gov.br, dadosabertos.aneel.gov.br, gisepeprd2.epe.gov.br, www.epe.gov.br, cetesb.sp.gov.br, www.cetesb.sp.gov.br, licenciamento.cetesb.sp.gov.br, iea.agricultura.sp.gov.br, ciagri.iea.sp.gov.br, cati.sp.gov.br, defesa.agricultura.sp.gov.br, dadosabertos.sp.gov.br, governoaberto.sp.gov.br, datageo.ambiente.sp.gov.br, arsesp.sp.gov.br, agenciasp.sp.gov.br, comgas.com.br, nectagas.com.br, necta.com.br, naturgy.com.br, unicadata.com.br, sifreca/esalqlog/cepea.esalq.usp.br, IBGE (sidra, apisidra, servicodados, geoftp), snirh/ana.gov.br, bcb, ipeadata, consecana, the firm sites (benriratings, sgssustentabilidade, verifit, institutototum, accenture, vanzolini, dnv.com.br, intertekservices), abegas, legisweb, novacana, udop, zenodo, archive.org, geofabrik, app.powerbi.com | proxy status log (`/__agentproxy/status`, "gateway answered 403 to CONNECT") | V (observed) |
| **Reachable from here:** `s3.amazonaws.com` (Benri report PDFs: HTTP 200 for the Santa Adélia report URL; bucket listing denied with 403) · `raw.githubusercontent.com` (third-party mirrors) | curl status codes | V (observed) |
| ANEEL's server reportedly **blocks data-center IPs (AWS/GitHub)**, so ANEEL downloads must run from a local or university machine | README of mirror repo https://raw.githubusercontent.com/diogoobs/tarifas-aneel/master/README.md: "O servidor da ANEEL bloqueia requisições de IPs de data center (AWS/GitHub)" | V (on mirror) |

**Implication:** all download scripts (`src/engine/ingest/`) must be run from the UNICAMP network or a home connection, then pushed to the DVC remote. Do not plan on CI or cloud runners fetching gov.br, ANEEL or CETESB.

## 1. Master table

Access column format: *public status per snippet* / *status in this session*. "blk" = HTTP 403 here.

### (a) RenovaBio: certified SP units and inspection-firm reports

| Source | Exact URL | What / granularity | Format | Update | License | Access | Engine use | Flag |
|---|---|---|---|---|---|---|---|---|
| ANP Painel Dinâmico de Certificações | https://www.gov.br/anp/pt-br/centrais-de-conteudo/paineis-dinamicos-da-anp/paineis-dinamicos-do-renovabio/painel-dinamico-de-certificacoes-de-biocombustiveis-renovabio | Inspection firms and certified units (per unit) | Power BI (export unverified) | **weekly** ("atualizadas semanalmente") | n/c | open / blk | Master list of SP certified units, used as the crawl seed | S |
| ANP: Consulta Pública de Proposta de Certificação (current) | https://www.gov.br/anp/pt-br/assuntos/renovabio/consulta-publica-proposta-certificacao-renovabio | ANP index of open public consultations, per unit | HTML + links | rolling | n/c | open / blk | Catches new and renewing certificates (3-year validity) | S |
| ANP: Consulta Certificação RenovaBio **(até 2023)** | https://www.gov.br/anp/pt-br/assuntos/renovabio/consulta-certificacao-renovabio-ate-2023 | Historical index of consultations up to 2023 | HTML | frozen | n/c | open / blk | Back-fills 2018–2023 mill-years | S |
| ANP RenovaCalc / certificate portal | https://renovacalc.anp.gov.br | Portal for the certificate list and systems (per snippet) | web | n/c | n/c | ? / blk | Check whether a CSV export of certificates exists | S |
| ANP Res. 984/2025 (16/06/2025), new certification rule | https://www.legisweb.com.br/legislacao/?id=479696 | Rules for certification and public consultation (likely replaces Res. 758/2018; verify) | text | — | public act | open / blk | Report structure and RenovaCalc version after 2025 | S |
| MME Relatório Anual RenovaBio 2025 | https://www.gov.br/mme/pt-br/assuntos/secretarias/petroleo-gas-natural-e-biocombustiveis/renovabio-1/relatorios-anuais-do-renovabio/relatorio-anual-renovabio-2025 | **SP 128 certificates in force** (GO 43, MG 31); end-2025: 441 authorized units, **337 certified (76.42 %)**, ethanol **286 certified (79.14 % of authorized ethanol units)** | PDF | annual | n/c | open / blk | Denominator for SP coverage of the report scrape | S |

**Inspection firms: where reports live and their URL patterns** (S unless stated):

| Firm | Public consultation page | Report-file URL pattern (from known examples) | Notes |
|---|---|---|---|
| Benri | https://www.benriratings.com/consulta/publica/ (blk) | `https://s3.amazonaws.com/benri.site/media/arquivos/<uuid>/<file>.pdf` (**reachable here, V**) | Page lists per-unit RenovaCalc, certificate(s) and partial report. Santa Adélia CP ran 17 Oct to 16 Nov 2024 (S). Harvest UUIDs from the page on a local network, then fetch from anywhere |
| SGS | `https://sgssustentabilidade.com/consulta_publica/consulta-publica-renovabio-<usina-slug>/`, e.g. …/consulta-publica-renovabio-usina-frutal-bioenergia-ltda/, …/renovabio-usina-moema-bioenergia-s-a-unidade-monte-verde/ | `https://sgssustentabilidade.com/wp-content/uploads/YYYY/MM/<file>.pdf` | One WordPress page per unit, so a sitemap crawl is feasible |
| Accenture | https://www.accenture.com/br-pt/services/sustainability/consulta-publica-renovabio | `https://www.accenture.com/content/dam/accenture/final/accenture-com/document-2/<file>.pdf` | — |
| Verifit | https://verifit.com.br/renovabio/ | `https://verifit.com.br/wp-content/uploads/YYYY/MM/<file>.pdf` | — |
| Instituto Totum | https://institutototum.com.br/totum-services/programa-renovabio/ | `https://institutototum.com.br/wp-content/uploads/YYYY/MM/<file>.pdf` | Also certifies biomethane (Essencis) |
| KPMG | no index page found | `https://assets.kpmg.com/content/dam/kpmg/br/pdf/YYYY/MM/<file>.pdf` (e.g. …/2020/10/fs-relatorio-parcial-certificacao-renovabio.pdf) | Probably older reports only |
| Fundação Vanzolini | https://vanzolini.org.br/organizacoes/certificacoes/renovabio/ | n/c | Accredited. CP nº 650/2023 (20/12/2023 to 20/01/2024) |
| **DNV** (not in R01) | https://www.dnv.com.br/supplychain/publications/renovabio-consulta-publica/ | n/c | Newly identified firm |
| Green Domus | none found | n/c | Credentialed by Despacho ANP 23, 10/01/2019. CP nº 647/2023 |
| Intertek | none found | flowchart only: https://webapp.intertekservices.com.br/mkt/renovabio-fluxograma-completo.pdf | — |

The 8 firms accredited by Oct 2019 were Green Domus, SGS, Totum, Vanzolini, KPMG, Benri, Verifit and Intertek (novacana snippet: https://www.novacana.com/noticias/firmas-inspetoras-opinam-conflito-interesse-durante-certificacao-renovabio-031019). Accenture and DNV appear later.

### (b) ANP ethanol plants

| Source | Exact URL | What / granularity | Format | Update | License | Access | Engine use | Flag |
|---|---|---|---|---|---|---|---|---|
| Painel Dinâmico de Produtores de Etanol | https://www.gov.br/anp/pt-br/centrais-de-conteudo/paineis-dinamicos-da-anp/paineis-e-mapa-dinamicos-de-produtores-de-combustiveis-e-derivados/painel-dinamico-de-produtores-de-etanol | Map of all ANP-authorized producers; authorized capacity (anhydrous and hydrated, m³/d) per plant; regional production; feedstock; tankage. "Tables with the data used are also available" | Power BI + tables | base **updated 18/8/2026** | legal basis Decreto 8.777/2016 (open-data policy) | open / blk | Mill nodes (location, capacity) and cane vs corn split | S |
| Open-data folder | `https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/arquivos-painel-de-produtores-de-derivados-producao-de-biocombustiveis/` + `etanol-capacidade.pdf` (dictionary or table, unverified), `g-etanol-tancagem.csv` | Capacity CSV: per economic agent, anhydrous m³/d and hydrated m³/d | CSV/PDF | monthly | n/c | open / blk | Capacity per plant to CNPJ, then join to SAPCANA and RenovaBio | S |

Per-plant **monthly production** is still not confirmed as public; R01 suspects UF/feedstock only. That remains an LAI item.

### (c) UNICA

| Source | Exact URL | What | Format | Update | License | Access | Use | Flag |
|---|---|---|---|---|---|---|---|---|
| UNICAdata Histórico de Produção e Moagem | https://unicadata.com.br/historico-de-producao-e-moagem.php?idMn=32&tipoHistorico=4 | Query by safra, product and **state** (crush, sugar, ethanol; area) | HTML query (export unverified) | per safra / biweekly | terms n/c | open / blk | SP biweekly seasonality profile and annual check | S |
| Biweekly report pages | `https://unica.com.br/noticias/safra-YYYY-YYYY-<n>a-quinzena-de-<mes>/` (e.g. …/safra-2025-2026-1a-quinzena-de-novembro/) | Centro-Sul + SP biweekly | HTML/PDF | biweekly | n/c | open / blk | Extends the SP series beyond 2018 (registry `unica_data` has 2008–2018) | S |
| Legacy PDF listings | `https://temp.unicadata.com.br/listagem.php?idMn=<n>` (idMn=14 CONSECANA-SP; idMn=92 Relatório final safra 2015/16) | Historical reports | PDF | frozen | n/c | open / blk | Back-fill | S |

Check value: SP crush 2023/24 **387.60 Mt** vs 314.51 Mt (2022/23, +23.24 %). This was seen in a search summary. It came from either the unicadata histórico page or https://www.brasilagro.com.br/conteudo/cana-safra-202324-tem-recordes-de-moagem-e-fabricacao-de-etanol-e-acucar.html; the attribution is unconfirmed (S).

### (d) SAPCANA / MAPA mill registry

| Source | Exact URL | What | Format | Update | Access | Use | Flag |
|---|---|---|---|---|---|---|---|
| SAPCANA full cadastral base ("Base Completa Instituição") | https://sistemasweb4.agricultura.gov.br/sapcana/downloadBaseCompletaInstituicao.action (legacy http://sistemasweb.agricultura.gov.br/sapcana/downloadBaseCompletaInstituicao.action) | All units registered as producers, cooperatives or traders (name, CNPJ, municipality, type) | **PDF and spreadsheet** | **auto-regenerated overnight** whenever any unit changes its record; last seen **16/07/2025** | open / blk | Authoritative mill registry joined to ANP and RenovaBio via CNPJ; operating or closed status | S |
| Legal basis | IN MAPA 33/2009 https://www.legisweb.com.br/legislacao/?id=78092 · roteiro (IN 52/2009) https://www.gov.br/agricultura/pt-br/assuntos/sustentabilidade/agroenergia/arquivos/roteiro-de-cadastramento.pdf | Mandatory fields and declarations | PDF | — | open / blk | Defines which per-unit fields MAPA holds and can be requested by LAI | S |

### (e) CETESB vinasse (P4.231 / PAV)

| Source | Exact URL | What | Access | Use | Flag |
|---|---|---|---|---|---|
| P4.231, 3rd ed. (Feb 2015), 2nd version | https://cetesb.sp.gov.br/wp-content/uploads/2013/11/P4.231_Vinhaca_-Criterios-e-procedimentos-para-aplicacao-no-solo-agricola-3a-Ed-2a-VERSAO.pdf (older: https://cetesb.sp.gov.br/wp-content/uploads/sites/21/2013/12/P4_231.pdf) | Norm text: K₂O-based dose, storage, PAV content | open / blk | Rules for the vinasse "applied" vs "available" split | S |
| DD 045/2015/C (DOE 13/02/2015) | https://cetesb.sp.gov.br/wp-content/uploads/2013/11/DD-045-2015-C.pdf | Approves P4.231 3rd ed. | open / blk | — | S |
| DD 023/2020/P, "aplicação dirigida" | news: https://www.novacana.com/noticias/aplicacao-vinhaca-dirigida-regulamentada-cetesb-200320 · https://unica.com.br/noticias/aplicacao-de-vinhaca-dirigida-e-regulamentada-pela-cetesb/ | Targeted application rule | open / blk | Possible higher application rates near the mill, which reduce vinasse available for AD | S |
| **DD 096/2023/E/C (20/12/2023)**, new PAV procedure | index: https://www.cetesb.sp.gov.br/cetesb/institucional/diretoria/decisoes_de_diretoria | New procedure for submitting the PAV; amends the "Regra de Aplicação" of DD 23/2020/P. PAV is filed as an **electronic spreadsheet from the CETESB site**, filled in by the mill's technical lead | open / blk | Defines the **exact fields to request by LAI** (volume, K₂O, areas) | S |
| CETESB licensing map | https://licenciamento.cetesb.sp.gov.br/mapa_ugrhis/ | Licences by UGRHI (map) | open / blk | Find licensed biogas/biomethane plants and mills; check whether it exports | S |
| Per-mill PAV data | — | Not published | **LAI** (state e-SIC, K) | Vinasse volume per mill per year | — |

Note: CETESB is moving files to a new DAM portal (`https://www.cetesb.sp.gov.br/dx/api/dam/v1/collections/<uuid>/items/<uuid>/renditions/<uuid>?binary=true`). Old `wp-content` URLs may stop working, so the registry should store both URLs and the sha256.

### (f) SP livestock: CDA/GEDAVE, LUPA

| Source | Exact URL | What / granularity | Format | Update | Access | Use | Flag |
|---|---|---|---|---|---|---|---|
| LUPA on **Dados Abertos SP** | https://dadosabertos.sp.gov.br/dataset/levantamento-censitario-das-unidades-de-producao-agropecuaria-do-estado-de-sao-paulo-lupa (resource `af5d9891-ce18-4703-8739-f923186de3e1`); mirror http://catalogo.governoaberto.sp.gov.br/dataset/673-lupa-levantamento-censitario-das-unidades-de-producao-agropecuaria-do-estado-de-sao-paulo | >300k UPAs; municipal/EDR tables | n/c (CKAN) | **metadata updated 28/11/2025** | open / blk | Herd and farm-size distributions per municipality (prior for downscaling) | S |
| LUPA (SAA page) | https://agricultura.sp.gov.br/cati/lupa-levantamento-censitario-das-unidades-de-producao-agropecuaria-do-estado-de-sao-paulo/ | Survey runs **every ~10 years**; status of the 2026/27 round unconfirmed ("SP lança Projeto LUPA": https://revistacultivar.com.br/noticias/sp-lanca-projeto-lupa, date n/c) | HTML | — | open / blk | Watch for new-round microdata | S |
| GEDAVE open data (tag GEDAVE) | https://dadosabertos.sp.gov.br/dataset/?_tags_limit=0&tags=GEDAVE | Datasets: Veterinários Cadastrados/Habilitados; **Estabelecimentos SISP e seus Produtos**; Solicitação de Evento de Concentração Animal. **No municipal herd dataset found** | CKAN (CSV likely) | n/c | open / blk | SISP slaughterhouses (see g) | S |
| GEDAVE herd declaration | https://gedave.defesaagropecuaria.sp.gov.br · manuals https://www.defesa.agricultura.sp.gov.br/www/sistemas/gedave/ | **Annual herd update campaign** (deadline 7 June, year not in snippet, per https://braganca.sp.gov.br/produtores-rurais-deverao-atualizar-rebanhos-ate-7-de-junho-no-sistema-gedave; 2026 campaign opened May 2026 per https://popmundi.com.br/2026/05/atualizacao-de-rebanhos-no-gedave-ja-esta-liberada-para-produtores-rurais-em-sao-paulo/); all species (cattle, buffalo, swine, poultry, sheep, goats, fish…) per property | system (**login**) | annual (May–June) | **LAI** for municipality × species aggregates | Best property-level herd census in SP. Ask for anonymized H3/municipal aggregates | S |

### (g) Slaughterhouses (SIF / SISP)

| Source | Exact URL | What | Format | Update | Access | Use | Flag |
|---|---|---|---|---|---|---|---|
| MAPA: Estabelecimentos Registrados no SIF | https://dados.agricultura.gov.br/dataset/062166e3-b515-4274-8e7d-68aadd64b820/resource/97277e92-264a-4dc0-9aea-f87b8ea93798/download/sigsifestabelecimentosregistradosnosif.csv | SIF establishments (name, address, municipality, activity) | CSV | file **updated 02/08/2026** | open / blk | Point layer of slaughter and dairy agro-industry; filter UF = SP | S |
| MAPA: SIGSIF relatório estabelecimentos | https://dados.agricultura.gov.br/dataset/062166e3-b515-4274-8e7d-68aadd64b820/resource/7d02af92-e3cf-4ae4-af8a-0dad334ffdfa/download/sigsifrelatorioestabelecimentos.csv | Second establishment export (fields n/c) | CSV | n/c | open / blk | Cross-check | S |
| **SISP (state) establishments** | https://dadosabertos.sp.gov.br/dataset/gedave-area-animal-estabelecimentos-sisp-e-seus-produtos/resource/ffc27a76-7865-4185-8b88-633685c76424 | State-inspected establishments and products | CKAN | n/c | open / blk | Fills the R01 gap "SISP list" | S |
| ABRAFRIGO list (secondary) | https://www.abrafrigo.com.br/wp-content/uploads/2022/03/Rela%C3%A7%C3%A3o-de-Abatedouros-Frigor%C3%ADficos.pdf | MAPA list of abattoirs (2022) | PDF | frozen | open / blk | Fallback only | S |

### (h) Sewage sludge

| Source | Exact URL | What | Format | Update | Access | Use | Flag |
|---|---|---|---|---|---|---|---|
| SINISA 2025 (reference year **2024**), Esgotamento Sanitário report | https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/009_RELATORIO_SINISA_ESGOTAMENTO_SANITARIO_2025_defeso.pdf | National/UF report; the results page also has **"planilhas de informações e indicadores"** per module (by municipality and provider) | PDF + spreadsheets | annual (collection deadline 15 July; 2026 cycle collecting now) | public and free / blk | Sewage collected/treated per municipality, then ETE inflow, then sludge | S |
| SINISA 2024 (ref. 2023) report | https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa/RELATORIO_SINISA_ESGOTAMENTO_SANITARIO_2024.pdf | as above | PDF | — | open / blk | Time series | S |
| ANA ETE base | https://metadados.snirh.gov.br/geonetwork/srv/api/records/1d8cea87-3d7b-49ff-86b8-966d96c9eb01 | **3,668 ETEs in 2,007 municipalities** (2020 update, ref. 2019; 206 process typologies). ANA news "ANA amplia base com informações sobre ETEs" (https://www.gov.br/ana/pt-br/assuntos/noticias-e-eventos/noticias/ana-amplia-base-com-informacoes-sobre-estacoes-de-tratamento-de-esgotos-em-todo-o-brasil) may point to a newer release, date n/c | SHP/CSV | irregular | open / blk | ETE points with process type (UASB vs activated sludge drives the sludge yield) | S |

### (i) MSW

| Source | Exact URL | What | Access | Use | Flag |
|---|---|---|---|---|---|
| CETESB Inventário RSU 2023 (new DAM URL) | https://www.cetesb.sp.gov.br/dx/api/dam/v1/collections/0b8dab59-e525-4b4b-9a0d-c6e0835f53f3/items/167ea629-ce2a-4dba-afb1-c68c333cd21c/renditions/aab4597d-72af-44ac-87fc-5c96ab426775?binary=true | 645 municipalities; t/d per municipality, landfill destination, IQR | open / blk | Landfill gas and OFMSW supply; existing landfill-biomethane plants | S |
| Edition tracker | https://cetesb.sp.gov.br/blog/tag/inventario-estadual-de-residuos-solidos-urbanos/ | No 2024/2025 edition found in search; check here | open / blk | — | S |

### (j) Gas infrastructure, tariffs, TUSD-Verde

| Source | Exact URL | What | Format | Update | Access | Use | Flag |
|---|---|---|---|---|---|---|---|
| ARSESP tariff tables (pattern) | http://www.arsesp.sp.gov.br/ArquivosRegulamentacao/Tarifas/Gas/tabela%20de%20tarifas-comgas_dez.pdf | Comgás tariffs by segment and volume band (fixed R$/month + variable R$/m³) | PDF | quarterly adjustments + annual | open / blk | Gas-grid sales netback, industrial NG benchmark | S |
| ARSESP quarterly-adjustment technical note | https://www.arsesp.sp.gov.br/Documentosgerais/SEI_0098855904_Nota_Tecnica%20_%20Ajuste%20Trimestral%20Mar%C3%A7o%202026%20-%20Comg%C3%A1s.pdf | Cost of gas + transport breakdown (Mar 2026) | PDF | quarterly | open / blk | Molecule vs margin split | S |
| Deliberations mirrored by Comgás | e.g. https://www.comgas.com.br/media/tgud04p3/delibera%C3%A7%C3%A3o-arsesp-n%C2%BA-1709-errata-3-2509.pdf (Del. ARSESP 1.709 of 9 Sep; year not in snippet) | Tariff deliberations | PDF | — | open / blk | Fallback host if arsesp.sp.gov.br is down | S |
| **Cativo Verde tariff (Sep 2026)** | seen in search summary for https://www.abegas.org.br/arquivos/101830 and https://www.agenciasp.sp.gov.br/arsesp-mantem-tarifas-de-gas-para-residenciais-e-comerciais-e-atualiza-valores-para-os-demais-segmentos/ (both blk) | Biomethane molecule **R$ 2.25/m³**; environmental attribute **R$ 1.40/m³**; gas + transport cost incl. PIS/Cofins **R$ 4.009694/m³** ("cativo verde" segment). Concessionaire not stated in the snippet (probably Comgás) | — | quarterly | open / blk | **A regulated price point for biomethane plus attribute in SP**; compare with Argus FOB R$ 3.28/m³ (R03) | S |
| TUSD-Verde (Del. 1.765/2025) | https://www.lexology.com/library/detail.aspx?g=711ca788-f0f0-4461-be4d-747a54ea7f29 · CP docs (R03) | **No R$/m³ value is published.** New segment "Plantas de Biometano Interconectadas – **TUSD-v**", in R$/m³, computed per interconnection from **CAPEX-Verde, OPEX-Verde and BRR-Verde**, using the P0/WACC method and kept separate from the conventional P0 | PDF | per project | open / blk | **Model TUSD-v endogenously**: annuity of (pipe km × R$/km + Bio-Citygate) at the ARSESP WACC ÷ injected m³. Caieiras is the first case (~5.3 km, R03) | S |
| Comgás interconnection plan | https://eixos.com.br/gas-natural/mercado-de-gas/comgas-recebe-propostas-para-plano-de-interconexao-de-plantas-de-biometano-a-rede/ | Comgás call for interconnection proposals (Plano de Negócios Verde) | HTML | — | open / blk | Pipeline of candidate injection points | S |
| ARSESP concession-area map (Jun 2019) | http://www.arsesp.sp.gov.br/Documentosgerais/Mapa_Gas_Junho_2019.pdf · sector profile https://www.arsesp.sp.gov.br/Paginas/gas/gas-canalizado.aspx | 3 concessions (Comgás east, Naturgy SP Sul south, Necta northwest) covering 645 municipalities | PDF | static | open / blk | Assign H3 cells to a distributor (tariff, TUSD-v rules) | S |
| **GeoSampa: Rede de Distribuição de Gás COMGÁS** | https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/09f717e9-66be-48c9-a868-df44ccc1f25f | Comgás network, **São Paulo city only**; PostGIS / OGC WMS; **EPSG:31983** | WMS/PostGIS | n/c | open / blk | Only open vector of a distribution network found (municipality only) | S |
| Comgás network viewer | www.comgas.com.br/nossarede | Georeferenced network for works planning (no download) | web | — | open / blk | Visual QA only | S |
| Distributor disclosures | Naturgy SP Sul 2023 statements https://www.naturgy.com.br/wp-content/uploads/2024/03/Gas-Natural-Sao-Paulo-Sul_2023.pdf · Necta https://nectagas.com.br/ · Comgás Plano de Negócios (2019) http://www.arsesp.sp.gov.br/ConsultasPublicasBiblioteca/OFCR132-19%20-%20PLano%20de%20Negocios%20Comgas.pdf | Search summary (S): **Comgás** >14,000 km in 87 municipalities; **Naturgy SP Sul** 93 municipalities, 53,000 km², ~1.9 thousand km of network serving 18 municipalities (end 2023), 100k customers (Sep 2025); **Necta** 375 municipalities in concession, network in 42 municipalities, ~1,300 km, ~45k customers | PDF | annual | open / blk | Served-municipality flag; network-density check of the existing infra layer | S |
| EPE WebMap gas layers | https://gisepeprd2.epe.gov.br/WebMapEPE/ (info page https://www.epe.gov.br/pt/publicacoes-dados-abertos/publicacoes/webmap-epe) | Shapefile download (down-arrow tool, top right) for the "Infraestrutura de Gás Natural" theme: **distribution pipelines, transport pipelines, delivery points (city gates)**, terminals, processing plants, compression stations. WMS sharing; per-layer metadata. Mostly **digitized from Google Earth Pro** and public documents | SHP / WMS | n/c | open / blk | Pipelines and city gates for siting; positional accuracy is coarse, so buffer them | S |
| EPE layers re-hosted (ES clip) | https://ide.geobases.es.gov.br/layers/geonode:epe_gasodutos_de_distribuicao | GeoNode copy of EPE layers (ES only, it seems) | WFS | — | open / blk | Schema preview only | S |

### (k) Electricity tariffs, A4 (SP distributors)

| Source | Exact URL | What | Format | Update | Access | Use | Flag |
|---|---|---|---|---|---|---|---|
| ANEEL: tarifas-homologadas-distribuidoras-energia-eletrica.csv | https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica/resource/fcf2906c-7c32-4b9b-a637-054e7a5234f4 · dictionary https://dadosabertos.aneel.gov.br/dataset/5a583f3e-1646-4f67-bf0f-69db4203e89e/resource/2d3478e0-8aa0-4cd4-81a7-5f8967cd8804/download/dd-tarifas-por-distribuidora.pdf | TE + TUSD per distributor × subgroup (A1…A4, AS, B…) × modality (azul, verde, branca…) × time slot (posto); **~89 MB, 328,293 rows, 17 cols, validity 2010-02-03 → 2026-09-22, 115 distributor CNPJs; updated 24/08/2026** | CSV | per tariff event | open (data-center IPs reportedly blocked) / blk | Upgrading and compression power OPEX by plant location (A4 Verde: R$/kW demand + R$/MWh ponta/fora ponta) | S |
| Mirror used for schema discovery | https://raw.githubusercontent.com/diogoobs/tarifas-aneel/master/data/tarifas_aneel.csv (sha256 `c6cc16db…0e66`, 12,541 lines) | Columns: `sigla;reh;vigencia_inicio;vigencia_fim;subgrupo;modalidade;classe;subclasse;detalhe;acessante;posto;unidade;vlr_tusd;vlr_te;vlr_total` | CSV | ad hoc | reachable | **Do not use for values**: the decimal separator is lost (e.g. CPFL Paulista A4 Verde fora ponta TUSD "16416.0 R$/MWh") and scaling is inconsistent (CPFL Santa Cruz demand 214.0 vs CPFL Paulista 1653.0). Several 2026 resolutions are missing | M |

SP distributors and latest REH in the mirror (M; check against the ANEEL CSV):

| Distributor | REH | Validity |
|---|---|---|
| CPFL Paulista | REH 3.579, 22/04/2026 | 2026-04-08 → 2027-04-07 |
| CPFL Santa Cruz | REH 3.580, 22/04/2026 | 2026-04-22 → 2027-04-21 |
| CPFL Piratininga | REH 3.543, 21/10/2025 | → 2026-10-22 |
| EDP SP | REH 3.541, 14/10/2025 | → 2026-10-22 |
| Enel SP | REH 3.477, 01/07/2025 | → 2026-07-03 (**2026 REH missing**) |
| Neoenergia Elektro | REH 3.510, 19/08/2025 | → 2026-08-26 (**2026 REH missing**) |
| Energisa Sul Sudeste | REH 3.480, 01/07/2025 | → 2026-07-11 (**2026 REH missing**) |

Small SP permissionárias and cooperatives are not enumerated here. Map plants to distributors with the ANEEL concession-area layer (SIGEL, already registered).

### (l) Diesel / CNG prices (ANP)

| Source | Exact URL | What | Format | Update | Access | Use | Flag |
|---|---|---|---|---|---|---|---|
| Série histórica do Levantamento de Preços (summary) | https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/precos-revenda-e-de-distribuicao-combustiveis/serie-historica-do-levantamento-de-precos | **Weekly and monthly** averages by Brazil/region/UF/municipality: gasoline, hydrated ethanol, diesel, **diesel S-10, GNV**, LPG P13; also distribution prices | XLSX | weekly | open / blk | Diesel S-10 for haul OPEX; GNV retail for the vehicle-fuel netback (SP municipalities) | V (URL cited in README of https://github.com/DaviSRodrigues/Precos-Combustiveis-Brasil, read via raw.githubusercontent.com) |
| Station-level open data | https://dados.gov.br/dataset/serie-historica-de-precos-de-combustiveis-por-revenda (legacy: https://legado.dados.gov.br/dataset/serie-historica-de-precos-de-combustiveis-por-revenda) | Per station; semiannual files plus monthly files (e.g. "GLP P13 – Fevereiro/2022"; "diesel S-10 + GNV" resources) | CSV | monthly/semiannual | open / blk | Spatial price surface (registry `anp_precos_combustiveis` = this) | S |

### (m) Land values (IEA-SP)

| Source | Exact URL | What | Update | Access | Use | Flag |
|---|---|---|---|---|---|---|
| IEA VTN query (Precor) | http://ciagri.iea.sp.gov.br/nia1/precor.aspx?cod_tipo=5&cod_sis=12 | Bare-land value (VTN, Valor da Terra Nua) by **EDR / CATI Regional** and land class ("terra de cultura de primeira", second class, pasture, …), R$/ha | **June and November surveys**; latest seen: survey 15/11/2024–31/01/2025, reference 01/01/2025 | open / blk | Land cost for the plant site and digestate area | S |
| Tables + method | https://iea.agricultura.sp.gov.br/out/publicacoes/pdf/ESTATISTICA-TERRA.PRN.pdf (Tabela 10, VTN) · http://www.iea.agricultura.sp.gov.br/out/TerTexto.php?codTexto=14127 | Long series; method | semiannual | open / blk | — | S |
| Municipal ITR VTN (alternative) | e.g. https://www.pilardosul.sp.gov.br/itr/download/10/ | Municipality-declared VTN by aptitude class (lavoura boa/regular/restrita…) for ITR | annual | open / blk | Municipal granularity where IEA only gives EDR | S |

### (n) Freight / road

| Source | Exact URL | What | Access | Use | Flag |
|---|---|---|---|---|---|
| ANTT minimum freight floor | Res. ANTT **6.076 (19/01/2026)** changes the coefficient method of Res. 5.867/2020; Res. ANTT **6.084/2026** updates the tables (published "Friday 17", month not in snippet). Summaries: https://www.totvs.com/blog/fiscal-clientes/antt-atualiza-regras-e-coeficientes-do-piso-minimo-do-frete-em-2026/ · https://www.transp.net/blog/posts/tabela-frete-antt-2026-resolucao-6076/ | Floor = distance (km) × CCD + CC (Lei 13.703/2018); tables by cargo type (**granel líquido** for vinasse/digestate, **granel sólido** for filter cake, **granel pressurizado**, …) and by axle count, counting **all axles incl. suspended** | open / blk (gov.br) | Lower bound for third-party haul cost per t·km; compare with SIFRECA and the in-house mill fleet | S |
| SIFRECA, DER, DNIT, OSM | already in registry (`sifreca`, `der_sre`, `dnit_snv`, `osm_sudeste`) | — | blk | — | — |

## 2. Suggested edits to existing registry entries (for the registry owner; not applied)

| id | Suggested change |
|---|---|
| `anp_renovabio_cert_panel` | add `also:` the two consultation pages (current, até 2023) and renovacalc.anp.gov.br; `temporal: weekly` confirmed by snippet |
| `renovabio_cert_reports` | add DNV, SGS per-unit page pattern, Vanzolini; note Benri PDFs on S3 are reachable from restricted networks |
| `anp_ethanol_producers` | add panel URL (painel-dinamico-de-produtores-de-etanol); base updated 18/8/2026 |
| `mapa_sapcana` | `format: PDF + spreadsheet`; regenerated nightly; legacy URL |
| `cetesb_pav` | add DD 096/2023/E/C and DD 023/2020/P; note the electronic-spreadsheet PAV, which fixes the LAI fields |
| `lupa_2016_17` | add Dados Abertos SP dataset URL (metadata 28/11/2025) |
| `cda_gedave_gta` | add the annual herd-update campaign (May–June) and the Dados Abertos GEDAVE tag; URL to https |
| `mapa_sif` | add the two direct CSV URLs (file updated 02/08/2026) |
| `sinisa` | add SINISA 2025 (ref. 2024) report URL; spreadsheets per module |
| `cetesb_rsu_inventory` | add the new DAM URL (old wp-content may break) |
| `anp_precos_combustiveis` | add summary-series URL (weekly municipal); confidence K → S |
| `aneel_ccee` | split out the tariff CSV (new id below); note the data-center IP block |
| `epe_webmap` | layers: distribution pipelines and delivery points; Google-Earth digitization caveat |

## 3. Quick wins for week 1 (run from UNICAMP or home network)

1. **SAPCANA full base** (spreadsheet), **ANP ethanol capacity/tankage CSVs** and **ANP certification panel export**. Join on CNPJ to build the SP mill master table (target: about 128 SP certificates, 170 NovaCana mills).
2. **RenovaBio crawl seed**: from the panel and the two ANP consultation pages, list each SP unit's firm. Scrape Benri (S3 PDFs, which work even in restricted runners), SGS (one WordPress page per unit), Verifit, Totum and Accenture. Extract with `templates/extraction_schema_mill_year.json`.
3. **SIF CSV** (both files) + **SISP CSV** (Dados Abertos SP) to build the slaughterhouse point layer for SP.
4. **ANEEL tariff CSV** (89 MB): filter SP distributors × A4 × Verde/Azul to get the power-price table `tariff_a4_brl_mwh` with REH and validity. Do not use the GitHub mirror values.
5. **ANP weekly municipal prices** for diesel S-10 and GNV in SP, 2013–2026, to build the haul OPEX and GNV netback series.
6. **EPE WebMap shapefiles** (gas distribution, transport, delivery points) to diff against the existing `infra_gas_rail_power_roads` layer. Add the GeoSampa Comgás WMS for the capital.
7. **SINISA 2025 spreadsheets** (sewage, by municipality) + **ANA ETE SHP** to build the ETE supply nodes.
8. **IEA VTN** (latest Jan 2025 reference) by EDR to build the land-cost raster.
9. **ARSESP**: download the current Comgás/Necta/Naturgy tariff tables and the Cativo Verde deliberation, then verify R$ 2.25 + 1.40 and R$ 4.009694/m³ (currently S).
10. **File LAI requests in week 1** (they take 20+10 days): CETESB (PAV volumes per mill per year, DD 096/2023 spreadsheet fields), CDA (GEDAVE herd by species × municipality, 2015–2026), MAPA (SAPCANA per-unit crush by safra), ANP (per-plant monthly ethanol production, SIMP).

## 4. Gaps and open questions

- No TUSD-v value in R$/m³ is public. Model it from CAPEX. Ask ARSESP for the Caieiras TUSD-v calculation sheet.
- Format of the ANP certificate list (XLSX/CSV?) and whether the Power BI panels allow export: unverified.
- No public vector of Necta or Naturgy SP Sul networks. EPE layers are coarse, so a partner request (Comgás is a partner, so its data is confidential, rule 6) or LAI is needed.
- UNICAdata licence and terms of use: unknown. Store only derived SP aggregates in git.
- No 2024/2025 edition of the CETESB RSU inventory found. Status of a new LUPA round unknown. ANA ETE update after 2019 unconfirmed.
- Month of publication of ANTT Res. 6.084/2026 and its coefficient values: not retrieved.
- License fields: none of the federal or state open-data pages could be opened to read the stated licence (dados.gov.br datasets usually declare one; record it at download).
