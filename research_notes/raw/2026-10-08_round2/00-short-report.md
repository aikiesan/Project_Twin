# Relatório curto — Cocal Biometano, Narandiba (SP)

**Data de corte:** 08/10/2026. **Escopo:** versão reduzida para preservar recursos. A coleta foi interrompida depois de quatro relatórios de pesquisa concluídos. Não foram inventados valores; as questões sem extração concluída estão marcadas como **not found**.

## Q1 — Autorizações ANP

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| not found | — | Texto integral das autorizações 422/2022, 547/2022, alterações e atos de Paraguaçu não foi extraído na versão curta | — | — | — | — | — | — | — | — |

## Q2 — Unidade e definições dos dados ANP

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| Volume Processado de Biogás | m³/d | Unidade impressa no cabeçalho; a fonte não define se “por dia” é média diária mensal, medição instantânea ou outra base | série mensal; exemplo 08/2026 | Biometano_DadosAbertos_CSV_Capacidade.csv | ANP | base/ZIP datado de 17/09/2026 | https://www.gov.br/anp/pt-br/assuntos/producao-e-fornecimento-de-biocombustiveis/biometano/biometano-dados-abertos.zip | cabeçalho CSV | “Volume Processado de Biogás (m³/d)” | PRIMARY |
| 11.596,000 | m³/d | Volume processado reportado; não é capacidade autorizada | 08/2026 | Biometano_DadosAbertos_CSV_Capacidade.csv | ANP | 17/09/2026 | https://www.gov.br/anp/pt-br/assuntos/producao-e-fornecimento-de-biocombustiveis/biometano/biometano-dados-abertos.zip | linha COCAL/NARANDIBA | `08/2026,...,NARANDIBA,"27112,00",51600,"11596,000",22` | PRIMARY |
| 27.112,00 | m³/d | Capacidade autorizada de produção de biometano; não é produção observada | 08/2026 | Biometano_DadosAbertos_CSV_Capacidade.csv | ANP | 17/09/2026 | https://www.gov.br/anp/pt-br/assuntos/producao-e-fornecimento-de-biocombustiveis/biometano/biometano-dados-abertos.zip | cabeçalho e linha COCAL/NARANDIBA | “Capacidade Autorizada de Produção de Biometano (m³/d)” | PRIMARY |
| 51.600 | m³/d | Capacidade de processamento de biogás; não é volume efetivamente processado | 08/2026 | Biometano_DadosAbertos_CSV_Capacidade.csv | ANP | 17/09/2026 | https://www.gov.br/anp/pt-br/assuntos/producao-e-fornecimento-de-biocombustiveis/biometano/biometano-dados-abertos.zip | cabeçalho e linha COCAL/NARANDIBA | “Capacidade Processamento de Biogás(m³/d)” | PRIMARY |
| 5.505.729,718 | m³ | Produção estadual agregada de BIOMETANO; não identifica Narandiba | 08/2026 | Biometano_DadosAbertos_CSV_Producao.csv | ANP | 17/09/2026 | https://www.gov.br/anp/pt-br/assuntos/producao-e-fornecimento-de-biocombustiveis/biometano/biometano-dados-abertos.zip | linha São Paulo/BIOMETANO | `08/2026,SUDESTE,São Paulo,BIOMETANO,5505729.718` | PRIMARY |
| reporte mensal até o dia 15 | prazo | Declaração via SIMP/DPP; a fonte não demonstra que o campo m³/d seja média diária mensal | mensal | Manual para o envio dos dados SIMP dos produtores de biometano | ANP/CSA | versão 12/2025 | https://csa.anp.gov.br/downloads/manuais-isimp/MANUAL-DO-I-SIMP-PRODUTORES-DE-BIOMETANO.pdf | p. 2, seção 1.1 | “O envio dos dados ao SIMP até o dia 15 de cada mês é obrigatório.” | PRIMARY |
| 20 °C e 1 atm | °C; atm | Referência publicada para quantidade em kg; não foi encontrada como referência dos m³ dos CSVs | cada movimentação | Manual para o envio dos dados SIMP dos produtores de biometano | ANP/CSA | versão 12/2025 | https://csa.anp.gov.br/downloads/manuais-isimp/MANUAL-DO-I-SIMP-PRODUTORES-DE-BIOMETANO.pdf | p. 4, campo 9 | “Quantidade correspondente do produto declarado na operação expresso em quilogramas (Kg), considerando a temperatura de 20ºC e a pressão de 1 atm.” | PRIMARY |

**Conclusão limitada de Q2:** não foi encontrada publicação da ANP dizendo que operadores reportam em mil m³/d, nem metodologia que defina o campo como média diária mensal, nem histórico público de correções/revisões.

## Q3 — Caso Paques Cocal Energia

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| 5.200 | Nm³/h | Fluxo de biogás bruto; a Paques não classifica como design, medido, autorizado ou média | não indicado | Biogas desulfurization with THIOPAQ® at Cocal Energia in Brazil | Paques Biotechnology | não indicada | https://www.paquesglobal.com/cases/biogas-desulfurization-with-thiopaq-at-cocal-energia | Facts and figures / Process | “Biogas flow - 5.200 Nm³/h” | PRIMARY |
| 12.000 | ppmV | H₂S na entrada da dessulfurização | não indicado | mesmo título | Paques Biotechnology | não indicada | mesma URL | Biogas H₂S Plant Effluent | “Inlet - 12,000 ppmV” | PRIMARY |
| < 80 | ppmV | H₂S na saída da dessulfurização | não indicado | mesmo título | Paques Biotechnology | não indicada | mesma URL | Biogas H₂S Plant Effluent | “Outlet - less than 80 ppmV” | PRIMARY |
| 5 | MW | Capacidade instalada de energia elétrica; não é produção | não indicado | mesmo título | Paques Biotechnology | não indicada | mesma URL | Capacity and contribution | “The unit boasts an installed capacity of 5 MW of electrical energy” | PRIMARY |
| 25.000 | Nm³/day | Capacidade adicional de biometano; não é produção efetiva | não indicado | mesmo título | Paques Biotechnology | não indicada | mesma URL | Capacity and contribution | “and an additional 25,000 Nm³/day of biomethane.” | PRIMARY |

## Q4 — Geo Biogás

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| 26 mil | Nm³/dia | Capacidade de produção de biometano; não é produção medida | página vigente | Cocal Geo Biogás | Geo bio gas&carbon | 10/09/2026, campo HTML PublicationDate | https://www.geobiogas.tech/plantas/cocal-geo-biogas | Narandiba / Nossos números | “26 mil Nm³/dia BIOMETANO” | PRIMARY |
| 120 mil | Nm³/dia | Capacidade de gerar biogás bruto; não é biometano nem produção real | 2022/23 | Sustainability Report Net Zero Now! 2022/23 | Geo Energética Participações S.A. / Geo bio gas&carbon | 11/06/2024, metadado do PDF | https://irp.cdn-website.com/21a24f49/files/uploaded/GEO_RS2022-23_EN_VFinal_11jun24_web.pdf | p. 29 | “It has the capacity to generate 120 thousand Nm³/day of biogas.” | PRIMARY |
| 2 verticais × 8 mil; 4 horizontais × 18 mil | m³ por biodigestor | Volumes nominais dos biodigestores, não vazões | projeto Narandiba | Cocal Geo Biogás | Geo bio gas&carbon | 10/09/2026 | https://www.geobiogas.tech/plantas/cocal-geo-biogas | infraestrutura | “composta por dois biodigestores verticais de 8 mil m³” / “e quatro biodigestores horizontais de 18 mil m³” | PRIMARY |
| 3,7 milhões; 7,5 milhões | Nm³ | Produção de biometano, respectivamente 2022 e 2023; não capacidade | anos civis | Sustainability Report Net Zero Now! 2022/23 | Geo Energética Participações S.A. / Geo bio gas&carbon | 11/06/2024 | mesma URL | p. 30 | “2022 3.7 MILLION Nm3 BIOMETHANE” / “2023 7.5 MILLION Nm3 BIOMETHANE” | PRIMARY |
| 889 mil; 1.294 mil | m³ | Vinhaça processada, respectivamente 2022 e 2023; não é volume total gerado nem fertirrigação | anos civis | Sustainability Report Net Zero Now! 2022/23 | Geo Energética Participações S.A. / Geo bio gas&carbon | 11/06/2024 | mesma URL | p. 30 | “889 THOUSAND m³” / “1,294 THOUSAND m³” | PRIMARY |
| 91 mil; 124 mil | t | Torta de filtro processada, respectivamente 2022 e 2023 | anos civis | mesmo título | Geo Energética Participações S.A. / Geo bio gas&carbon | 11/06/2024 | mesma URL | p. 30 | “91 THOUSAND t” / “124 THOUSAND t” | PRIMARY |

## Q5 — Upgrading e CO₂

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| Pressure Swing Adsorption (PSA) | — | Tecnologia anunciada pelo fornecedor para projeto do Grupo Cocal; o release não identifica explicitamente Narandiba | anúncio de 07/07/2020 | Greenlane Renewables Signs New $2.4 Million System Supply Contract with Grupo Cocal of Brazil | Greenlane Renewables Inc. | 07/07/2020 | https://www.greenlanerenewables.com/investors/news/2020/greenlane-renewables-signs-new-two-point-four-million-system-supply-contract-with-grupo-cocal-of-brazil | primeiro parágrafo | “Greenlane will supply its Pressure Swing Adsorption (“PSA”) biogas upgrading system for this first-of-its-kind renewable natural gas (“RNG”) project.” | PRIMARY |
| CO₂ removido → liquefação | — | Destino declarado do CO₂ separado no upgrading; não é capacidade | 2022/23 | Sustainability Report Net Zero Now! 2022/23 | Geo bio gas&carbon | 11/06/2024 | https://irp.cdn-website.com/21a24f49/files/uploaded/GEO_RS2022-23_EN_VFinal_11jun24_web.pdf | p. 29 | “During the upgrade process, the removed CO2 is sent to a liquefaction plant” | PRIMARY |
| indústrias químicas e de alimentos | — | Setores abastecidos; compradores individuais não identificados | 2022/23 | mesmo título | Geo bio gas&carbon | 11/06/2024 | mesma URL | p. 29 | “that primarily supplies the chemical and food industries.” | PRIMARY |
| 50 | t/dia | CO₂ biogênico mostrado pela Geo; a base (capacidade/medição/média) não é qualificada | página vigente | Cocal Geo Biogás | Geo bio gas&carbon | 10/09/2026 | https://www.geobiogas.tech/plantas/cocal-geo-biogas | Nossos números | “50 t/dia CO₂ BIOGÊNICO” | PRIMARY |
| 16 mil | t | CO₂ verde declarado pela Cocal; o texto não separa Narandiba nem informa período/base | não indicado | CO2 Verde / Green CO2 | Cocal | não indicada | https://www.cocal.com.br/negocios/co2/ | primeiro bloco | “Produzimos 16 mil toneladas de CO2 verde” | PRIMARY |

**Não encontrado em Q5:** methane slip; fornecedor e capacidade classificados da liquefação; comprador individual; confirmação inequívoca de que o PSA do release Greenlane foi instalado em Narandiba.

## Q6 — Licenças CETESB

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| not found | — | A extração foi interrompida antes da consulta completa do portal CETESB por CNPJ/município | — | — | — | — | https://licenciamento.cetesb.sp.gov.br/ | — | — | — |

## Q7 — Cana e resíduos

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| not found | t; m³ | Cana esmagada, etanol, vinhaça total gerada, fertirrigação versus digestores e palha recuperada não foram extraídos de forma completa | safras 2019/20–2025/26 | — | — | — | — | — | — | — |
| 889 mil; 1.294 mil | m³ | Vinhaça **processada** na unidade Geo; não substitui vinhaça gerada nem divisão fertirrigação/digestores | 2022; 2023 | Sustainability Report Net Zero Now! 2022/23 | Geo Energética Participações S.A. / Geo bio gas&carbon | 11/06/2024 | https://irp.cdn-website.com/21a24f49/files/uploaded/GEO_RS2022-23_EN_VFinal_11jun24_web.pdf | p. 30 | “889 THOUSAND m³” / “1,294 THOUSAND m³” | PRIMARY |
| 91 mil; 124 mil | t | Torta de filtro processada | 2022; 2023 | mesmo título | Geo Energética Participações S.A. / Geo bio gas&carbon | 11/06/2024 | mesma URL | p. 30 | “91 THOUSAND t” / “124 THOUSAND t” | PRIMARY |

## Q8 — RenovaBio

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| 3.276 | CBIOs | Créditos gerados; não é volume de gás | 2023 | Sustainability Report Net Zero Now! 2022/23 | Geo Energética Participações S.A. / Geo bio gas&carbon | 11/06/2024 | https://irp.cdn-website.com/21a24f49/files/uploaded/GEO_RS2022-23_EN_VFinal_11jun24_web.pdf | p. 29 | “In 2023, 3,276 CBIOS were generated.” | PRIMARY |
| certifier, certificate number, CI, fraction eligible, validity and renewals | — | not found in shortened extraction | — | — | — | — | — | — | — |

## Q9 — CCEE/MME LRCAP 2026

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| not found | — | Resultado oficial e portarias MME não foram extraídos antes da interrupção | LRCAP 2026 | — | — | — | — | — | — | — |

## Q10 — Escala mínima na Alemanha e Suécia

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| not found | — | Pesquisa comparativa e verificação de DOI não foram executadas na versão curta | — | — | — | — | — | — | — | — |

## Q11 — Mandato de biometano

| value | unit | basis | period | source title | publisher/author | date | URL | page/table/section | verbatim quote | PRIMARY/SECONDARY |
|---|---|---|---|---|---|---|---|---|---|---|
| not found | — | Lei 14.993/2024, Decreto 12.614/2025 e CNPE 4/2026 não foram extraídos na versão curta | — | — | — | — | — | — | — | — |

## Conflitos preservados

1. **Capacidade de biometano:** Geo: **26 mil Nm³/dia**; Paques: **25.000 Nm³/day**. São capacidades publicadas por fornecedores/grupos diferentes; não foram combinadas.
2. **Biogás:** Geo: **120 mil Nm³/dia de capacidade**; Paques: **5.200 Nm³/h de fluxo**, sem classificação design/medido. Não houve conversão.
3. **Produção:** Geo: **3,7 milhões Nm³ em 2022** e **7,5 milhões Nm³ em 2023**; Cocal/relatório usado no Q5: **7,9 milhões Nm³ na safra 2023/24**. Períodos diferentes.
4. **CO₂:** Geo: **50 t/dia** na unidade; Cocal: **16 mil t** de CO₂ verde sem escopo/período no texto. Não são diretamente comparáveis.

## Not-found e locais pesquisados na versão curta

- Q1: Diário Oficial da União/in.gov.br e páginas de autorização ANP; ato integral não extraído.
- Q6: portal de licenciamento CETESB, planejado por CNPJ `14.788.495/0001-70` e município; consulta não concluída.
- Q7–Q11: não houve rodada completa de extração após a interrupção; portanto não há base para afirmar ausência nos portais.
- Não foi feita afirmação sobre reporte em **mil m³/d**, temperatura/pressão dos m³ dos CSVs, methane slip, compradores individuais de CO₂, ou início oficial da operação quando não sustentada pelas tabelas acima.

## Arquivos primários anexados

Todos estão em `/home/ubuntu/research_biomethane/sources/`.

| arquivo | conteúdo | URL de origem | SHA-256 |
|---|---|---|---|
| `biometano-dados-abertos.zip` | bases abertas ANP | https://www.gov.br/anp/pt-br/assuntos/producao-e-fornecimento-de-biocombustiveis/biometano/biometano-dados-abertos.zip | `4bd078b595beea8ec84280e6d4a7a925750fe6e1fa65a7a5ebdd90ad38161ce0` |
| `Biometano_DadosAbertos_CSV_Capacidade.csv` | capacidade/volume processado ANP | mesma URL | `6cd432e1ca14e831dc8b2673b286cc2df86d60e7f349819f88c11972a852bf75` |
| `Biometano_DadosAbertos_CSV_Producao.csv` | produção estadual ANP | mesma URL | `1f40f43779849623abe7cd0f1838813798920bd2616fbc4cd943902c1c3e04a4` |
| `MANUAL-DO-I-SIMP-PRODUTORES-DE-BIOMETANO.pdf` | manual ANP/CSA | https://csa.anp.gov.br/downloads/manuais-isimp/MANUAL-DO-I-SIMP-PRODUTORES-DE-BIOMETANO.pdf | `5399423364ba261166d6914891703ad67717cac5cffff975d7e29ebe1b88ad18` |
| `Manual-do-ISIMP-Geral-DPP.pdf` | manual geral i-SIMP/DPP | https://csa.anp.gov.br/downloads/manuais-isimp/Manual-do-ISIMP-Geral-DPP.pdf | `2b2f8375111f394aa0260eb41240512dd2a102c7873a31517af58c4d8f8c41e1` |
| `paquesglobal-cocal-energia.html` | página oficial do caso Paques | https://www.paquesglobal.com/cases/biogas-desulfurization-with-thiopaq-at-cocal-energia | `7429fcbc35c24fa0445ed357bc0f4e1aa9bf11565c96d9311673880d30fdff56` |
| `paques-case-cocal-energia-cdn.pdf` | PDF ligado pela Paques | https://cdn.opptylab.com/hg/assets/paques-case-cocal-energia.pdf | `55289f0612749b3fdb45eeafd2ca2d7cd4e828a9322992186a8926af563e9642` |
| `GEO_RS2022-23_EN_VFinal_11jun24_web.pdf` | relatório Geo, Narandiba | https://irp.cdn-website.com/21a24f49/files/uploaded/GEO_RS2022-23_EN_VFinal_11jun24_web.pdf | `ca868f5405fd0222dacff2bb0ae2870f0380d84e986477a69a9cce4a592a4e37` |
| `greenlane_cocal_2020.pdf` | comunicado Greenlane | https://www.greenlanerenewables.com/investors/news/2020/greenlane-renewables-signs-new-two-point-four-million-system-supply-contract-with-grupo-cocal-of-brazil | `0f8ce451f609ae9e008b50c1ca24b9e546940938e54c26a50a3c054e92d8bf` |
| `cocal_sustainability_2023_2024.pdf` | relatório Cocal usado no achado de Q5 | https://cocal-institucional-prd.s3.sa-east-1.amazonaws.com/app/uploads/2024/09/Relatorio-Anual-de-Sustentabilidade-2023-2024.pdf | `7afc1b3c1750da025f875a397fdb718ba4f392f365e10bd361a1517f22f5134a` |

## Relatórios de pesquisa intermediários preservados

- `reports/02-q02-anp-definitions.md`
- `reports/03-q03-paques.md`
- `reports/04-q04-geo.md`
- `reports/05-q05-upgrading-co2.md`
