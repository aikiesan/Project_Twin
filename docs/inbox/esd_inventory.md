# Inventário: `Reposicionamento_Submissão_ESD` (somente leitura)

- **Data:** 2026-10-07. Inventário feito pelo Claude a pedido de Lucas; nada foi movido, editado ou executado na pasta de origem.
- **Pasta lida:** `C:\Users\Lucas\Documents\Reposicionamento_Submissão_ESD`.
  - 3.307 arquivos, sem contar os ambientes virtuais (`.venv*`), `__pycache__` e `.git`.
  - Cerca de 16 GB em dados tabulares e espaciais.
- **Hashes:** sha256 de todos os 1.476 arquivos de dados (csv, shp e componentes, gpkg, tif, xlsx, zip, npz/npy/pkl, json).
- **Saídas desta pasta inbox** (nada foi mesclado ao registry principal):
  - `registry/inbox/esd_datasets.csv`: 820 linhas; shapefiles agrupados num registro (sha256 do `.shp`); sem `.txt` de documentação nem `__MACOSX`.
  - `registry/inbox/esd_parameters.csv`: 320 parâmetros, todos com flag `S`.
  - `registry/inbox/esd_references.csv`: 51 referências, todas com `ref_check=pending`.
  - `docs/inbox/score_grid_v0_run.txt`: stdout da grade (ver §6).
- **Tabelas pequenas copiadas** para `data/interim/esd/` (gitignored, 19 arquivos, < 0,5 MB cada):
  - tortuosidade;
  - calibração palha→usina;
  - MCLP e hubs selecionados;
  - sensibilidades;
  - validação;
  - acesso a 50 km;
  - painel municipal N3/N4.
- **Regras seguidas:**
  - Números, URLs e DOIs foram copiados como estão escritos. O que não está escrito aparece como "não encontrado".
  - Dados pessoais ou de terceiros só foram classificados; o conteúdo não foi aberto.

## 1. O que há na pasta

| Bloco | O que é | Relevância para `engine.siting` |
|---|---|---|
| `Metodo_CP2b/` (cascata N1–N4 e `fl_espacial/`) | Método CP2b v5.1 de potencial (N1 teórico → N4 acessível) e o **FL espacial**: grafo viário OSM, bacias de coleta por estrada, seleção gulosa de hubs com limiar Q_min, curva MCLP, validação e sensibilidade | **Alta**: é o único trabalho de localização/logística executado na pasta |
| `Metodo_CP2b/outputs_v5/revisao_ESD/` | Revisão do artigo ESD (01/10): tornado OAT, validação deixando cada planta fora (LOO), tipologias, modelo de triagem e mandato da Lei 14.993 | Média |
| `Resultados em Mapas…/analysis/` | Análises de ago/2026 sobre a base antiga do PILAR-2b (cenário "Real", Atlas SP 2020): Moran/LISA/Gi*, faixas até o gasoduto, rota elétrica, P2 (pares de co-digestão), P3 (perfis RGInt) | Baixa a média; a base numérica é anterior à v5.1 |
| `00_Primary_Data_Sources_PILAR2b/` | Dados primários: IBGE, SNIS, PAM/PPM, MapBiomas 10.1 (incluindo UCs, TIs e infraestrutura), TerraClass, LAPIG, granjas GEDAVE | Fonte de camadas (exclusões, usinas) |
| `DADOS_ESPACIAIS/` | CETESB (IGR, IQR, IQC, ICTEM), staging RAIS, coordenadas industriais pendentes de validação, auditoria | Baixa |
| `Referencias_Submissao_ESD/` | 8 PDFs da ESD convertidos em md. O PAPER_08 (Saraswat & Swami 2025) é GIS-AHP + location-allocation | Literatura (baseline AHP) |
| `Submissão ESD + Data in Brief/`, `Figuras_*`, `Claude outputs/` | Manuscritos, figuras, lista APA v8 | Referências |
| `DBFZ_REFERENCES/`, `Benchmarks_Brasil/` | Relatórios DBFZ, panoramas ABiogás/CIBiogás, SIGA/ANEEL | Contexto |

**Métodos não encontrados.** Não há implementação própria de nenhum dos seguintes na pasta:
- AHP;
- p-mediana ou MILP;
- Huff;
- location-allocation (problema de alocação);
- custo nivelado (LCOB/LCOE).

AHP e location-allocation aparecem só na literatura (PAPER_08). A busca por `ahp|p-median|milp|pyomo|pulp|huff|lcoe|lcob|custo nivelado|levelized` em `.py` e `.md` não trouxe nenhum desses métodos. A pasta `YERC/` está vazia.

## 2. Mapa de métodos

### M1. FL espacial: bacias por estrada, hubs e cobertura gulosa (**principal**)

- **O que faz.** Mede a acessibilidade logística por resíduo: o FL é a fração da oferta N3 que fica a uma distância por estrada de um hub viável, ponderada por w(d).
  - w(d) = 1 até r1, cai linearmente até 0 em r2. Os raios dependem da classe do material (líquido, sólido úmido, sólido seco).
  - Um hub é viável se a sua bacia ponderada for ≥ Q_min.
  - **Variante B (principal):** alocação gulosa sem dupla contagem (CELF). Um hub entra só se o resíduo que acrescenta for ≥ Q_min.
  - **A:** cobertura (limite superior). **C:** monodigestão por cobertura. **D:** monodigestão com alocação (limite inferior).
  - A palha de cana vai só para as usinas, com raios calibrados pela distribuição observada da distância por estrada.
- **Código (Python 3.11):** `Metodo_CP2b/fl_espacial/00…07_*.py` e `fl_comum.py`.
  - `fl_comum.peso_w`, linha 78: w(d).
  - `Bacias`, linha 169: soma exata por histogramas de 1 km.
  - `cobertura_gulosa`, linha 187: guloso CELF.
  - `Roteador`, linha 223: Dijkstra multi-fonte com super-fonte.
  - Parâmetros: `config_fl.yaml`. Execução: `rodar_pipeline.sh`.
- **Documentação:** `RELATORIO_FL_espacial.md` e `DECISOES_CHECKPOINT2.md`.
- **Entradas** (caminhos em `config_fl.yaml`, linhas 9–35):
  - OSM Geofabrik Sudeste (`gis_osm_roads_free_1.shp`, jan/2026). Fica **fora da pasta**, em `Documents/CP2B/...`.
  - Municípios `SP_Municipios_2024.shp`, `feedstocks.yaml`, ETEs e áreas urbanas, todos do repo `Pilar2b` (**fora da pasta**).
  - MapBiomas 10.1: cana 20, soja 39, temporárias 41, café 46, citros 47; raster 2024, 2ª safra.
  - Usinas EPE/MapBiomas (`usina_etanol.shp`), plantas de biogás (MapBiomas, PILAR, ANP).
  - Granjas GEDAVE (aves), `farms_for_gee.csv` (suínos, fora da pasta) e cadastro bovino GEDAVE (fora da pasta, LGPD).
  - RAIS 1033-3/01 para as fábricas de suco.
  - Exclusões: UCs estaduais e federais de proteção integral, TIs.
- **CRS e resolução:**
  - EPSG:5880 (Policônica SIRGAS).
  - Grade de oferta de 1 km; hubs candidatos em grade de 2 km (subconjunto de 4 km na alocação) mais existentes; raster auxiliar de 100 m.
  - Grafo: 2.177.640 nós, 2.956.161 arestas, 511.758 km (`grafo_resumo.csv`).
- **Principais resultados (v5.1, med),** com o arquivo de origem:
  - Hubs candidatos: grade 56.795; usinas 160; ETEs 283; biogás 133; fábricas de suco 14 (`hubs_conexao_resumo.csv`).
  - Conexão de célula ao grafo: mediana de 509 m.
  - Tortuosidade estrada/euclidiana, mediana de 5.000 pares (`tortuosidade_resumo.csv`):
    - 1,295 no geral (P10 1,152; P90 1,641);
    - 1,442 em 1–5 km;
    - 1,267 em 40–60 km.
  - Palha→usina por estrada (`palha_usinas_calibracao.csv`): P50 19,51 km, P75 27,17, P90 35,22, P95 41,68, P99 53,8.
  - FL da palha: 0,7363 / 0,8769 / 0,9582.
  - Variante B (`mclp.csv`): para em 455 hubs (423 da grade + 32 existentes), com cobertura de 0,9526 do N3 sem palha e 0,9200 do N3 total.
  - Hubs necessários (`mclp.csv`):
    - 50% do N3 total com a palha nas usinas: 16 hubs; 80%: 114 hubs;
    - sem a palha: 55 hubs para 50% e 143 para 80%.
  - N4 estadual med: 16,36 M Nm³ CH₄/d, +10,4% sobre a v4 (`RELATORIO_FL_espacial.md` §5; `outputs_v5/artigo/T1_state_levels.csv`: 16,36083578714753).
  - Taxa de acerto (`validacao_taxa_acerto.csv`): plantas com tipo a ≤ 2 km de hub viável, 75,0% em mono med (46 plantas).
  - LOO (`revisao_ESD/LEIA-ME.md`, T3): 75,0% (27/36). Pelo critério de hub *selecionado*: 8,3% em mono e 16,7% em co-digestão.
  - Sensibilidade a Q_min de 250 a 10.000 Nm³/d (`sensibilidade_qmin.csv`): FL mono sem palha de 0,9889 a 0,7811.
- **Ainda roda?**
  - Não foi executado (passada pesada de ~45 min com cache, ~1 h 40 do zero, `RELATORIO` §12).
  - Exige Windows: `.venv/Scripts/python.exe`, pandas 2.2.3 (a cascata quebra com pandas 3), pandana 0.8 (`requirements.txt`).
  - Caminhos absolutos em `C:/Users/Lucas/Documents/{Pilar2b, CP2B, Reposicionamento_Submissão_ESD}` (`config_fl.yaml`, linhas 10–35).
  - Os caches existem (`fl_espacial/cache/`, inclusive o grafo em npz), então as etapas 04b–07 podem rodar sem refazer o grafo.
  - Não verifiquei se os arquivos fora da pasta ainda existem.

### M2. Cascata CP2b N1→N4 (potencial)

- **O que faz.** N1 = A × g × ST × SV × BMP (ou um coeficiente direto). N2 = N1 × FC. N3 = max(0, N2 × FCo − U). N4 = N3 × FS × FL.
  - 17 substratos; cenários min/med/max acoplados.
  - Fórmulas em `cp2b_params.py`, linhas 3–7.
- **Código:** `Metodo_CP2b/cp2b_cascade.py` e `cp2b_params.py` (Python). BMP, ST e SV vêm do `feedstocks.yaml` do Pilar2b, fora da pasta.
- **Entradas:** PAM/PPM 2024; UNICA/MAPA 2020/21; GEDAVE; SNIS 2022.
- **Resultados** (`outputs_v5/artigo/T1_state_levels.csv`, med, M Nm³ CH₄/d): N1 64,774; N2 41,665; N3 19,183; N4 16,361.
- **Parâmetros:** os triplos g, FC, FCo e FS de cada substrato e as constantes globais estão em `esd_parameters.csv` (`cp2b_*`). Os 11 substratos marcados "provisorio" somam 57,6% do N3 (`RELATORIO` §11).
- **Relação com o Project_Twin:** é o módulo de oferta (docs/09), não o de localização. Fica aqui como contexto e não é candidato a porte direto.

### M3. Alcance de infraestrutura a 50 km (gás e eletricidade)

- **O que faz.** Classifica cada município pela distância do ponto representativo à malha de gás (transporte + distribuição) e à subestação "com saída de distribuição" (secundário em 13,8, 20, 34,5, 88 ou 138 kV).
  - Classes: gás e eletricidade / só eletricidade / só gás / nenhum, com corte de 50 km.
  - Distância euclidiana em EPSG:31983.
- **Código:**
  - `cp2b_indicadores_artigo.py`, linhas 254–278;
  - mesmas regras em `paper_figures/fig5_siting.py` e `14_infra_eletrica.py`.
- **Camadas:** `paper_figures/_src/sp_cache.gpkg`, com camadas `gasoduto_transporte`, `gasoduto_distribuicao`, `subestacao`, `linha_transmissao`. A origem e a licença não estão escritas.
- **Ressalva escrita pelo próprio autor** (`14_infra_eletrica.py`, linhas 9–14): as camadas LT_EXISTENTE e SE_EXISTENTE cobrem só a rede básica (≥ 230 kV). O filtro de tensão é um proxy.
- **Resultados** (`T9_energy_access_50km.csv`):
  - gás e eletricidade: 268 municípios, 31,4% do N3;
  - só eletricidade: 172 municípios, 39,4%;
  - só gás: 90 municípios, 14,8%;
  - nenhum: 115 municípios, 14,3%.

### M4. Autocorrelação espacial (Moran I, LISA, Gi*)

- **Método:** contiguidade queen (buffer de 150 m), pesos padronizados por linha, sobre a densidade em Nm³/d/km². 999 permutações; p ≤ 0,05.
- **Código:** `cp2b_indicadores_artigo.py` §3 e `paper_figures/10_spatial_stats.py`.
- **Resultados:**
  - Moran do N3 v5.1 = 0,213 (p = 0,001; `revisao_ESD/LEIA-ME.md`, Fig 5/S2).
  - Moran do N4 = 0,209 (`final_N4/Numeros_Finais_ESD_v6_N4.md`, linha 26).
  - Na base antiga (`ANALISES_PARA_O_PAPER.md`, linhas 61–62): 0,6261.

### M5. Tipologias (k-means)

- **Método:** k = 2–8, n_init = 25, k escolhido pela silhueta, sobre a composição do N3 por fluxo.
- **Resultados:**
  - v5.1: k = 5, silhueta 0,613.
  - Sem os municípios de cana: melhor silhueta 0,438 (`revisao_ESD/LEIA-ME.md`, T4). O autor recomenda retirar as tipologias do artigo.

### M6. Mandato da Lei 14.993/2024 (ilustrativo)

- **Método:** soma o N4 dos municípios a ≤ 50 km da malha de gás e compara com a meta aplicada ao volume da ARSESP.
- **Código:** `revisao_ESD/scripts/t8_mandato_mistura.py`.
- **Resultado:** 7,6 M Nm³ CH₄/d, 46,6% do N4 (`revisao_ESD/LEIA-ME.md`, linha 19).

### M7. Pares de co-digestão P2 (**não recomendado para porte**)

- **O que faz:**
  - busca, em raio euclidiano de 50 km entre centroides, pares de municípios;
  - C:N da mistura e fração ótima f_B para C:N = 25;
  - âncoras Tier-1 = 101 maiores de 0,5·GWh + 0,5·Shannon;
  - fator de "sinergia" 1,18 ou 1,05;
  - retém os 162 primeiros pares.
- **Código:** `paper_figures/P2/build_biochemical_matching_system.py`, linhas 404–531.
- **Problemas:**
  - fator de sinergia sem fonte;
  - "sweet spot" de 20–35 no código e de 20–30 no texto;
  - corte arbitrário de 162 pares;
  - distâncias euclidianas;
  - saídas gravadas em `A:/Pilar-2b/...`, caminho que não existe neste PC.

### M8. Validação antiga por buffers (GEE) (**não usar**)

O próprio material registra (`Evidencias_CP2B_FC_FCo_FL.md`, linhas 296–306):
- erro de unidade (rendimento por tonelada aplicado por hectare por dia);
- R² negativo em todos os raios;
- coordenadas ANP com erro de até 40,9 km.

### Literatura (L1, L2)

- **L1 — Saraswat & Swami 2025 (PAPER_08):**
  - pesos AHP de 20 especialistas: biomassa 0,353, água 0,232, estrada 0,17, transmissão 0,128, força de trabalho 0,047, urbanização 0,041, declividade 0,03;
  - limiar ótimo de transporte de 12,67 km;
  - location-allocation na rede.
- **L2:** raios por substrato citados em `Evidencias_CP2B_FC_FCo_FL.md`, linha 290. As citações são curtas; a referência completa não está na pasta.

## 3. Comparação com `engine.siting` e com os 8 critérios do `score_grid_v0.py`

| Critério do grid v0 | O que o ESD fez | Diferença que importa |
|---|---|---|
| `gas` (distância à malha, min de 3 camadas) | Distância à malha de gás (transporte + distribuição), corte de 50 km (M3) ou 20 km (P2) | Mesma natureza (euclidiana). A camada do ESD (`sp_cache.gpkg`) tem origem não escrita, e a do Q17 também é parcial |
| `power` (subestação) | Só subestações com secundário em 13,8–138 kV (`LOW_KV`) | O grid v0 não filtra por tensão (a confirmar no script que gera a grade). Filtro barato de portar |
| `road` (rodovia) | Distância **por estrada** no grafo OSM completo; tortuosidade medida | O grid v0 usa distância euclidiana a rodovias. O ESD tem o fator estrada/euclidiana medido em SP |
| `cane`, `swine`, `poultry`, `cattle` (a 30 km) | Oferta N3 em Nm³ CH₄/d por substrato: em pixels MapBiomas, nas usinas e nos pontos de granja, somada com w(d) por estrada e raio por classe | O grid v0 espalha os totais municipais por área (flag D). A grade de oferta de 1 km do ESD (`grade_oferta_1km.gpkg`, 62 MB) espacializa melhor e já está em CH₄ |
| `demand` (população a 30 km) | Sem critério de demanda; a população só entra no RSU | — |
| Pesos (iguais + Dirichlet + OAT) | Sem pesos: a seleção é por oferta coberta (Q_min) | Abordagens complementares: o ESD responde "quantos hubs e onde", o grid v0 responde "quão apto" |
| Exclusões (UCs estaduais + TIs) | UCs estaduais **e federais** de proteção integral + TIs (`config_fl.yaml`, linhas 32–35) | **O grid v0 não exclui UCs federais de proteção integral.** O ESD tem a camada (`esd_federal_protected_areas_integral_protection_v2`) |
| Rotas (`routing.py`, OSRM, fallback sem fator) | Grafo próprio OSM + Dijkstra (SciPy) / CH (pandana) | O `routing.py` pede um fator de desvio citado. O ESD mediu 1,295 em SP (D) |

**O que já temos e o ESD não tem:**
- normalização com limites registrados;
- Dirichlet;
- OAT;
- `run_id` com hash;
- separação explícita entre triagem e modelo de custo (ADR-0016).

**O que falta no Project_Twin e o ESD tem:**
1. distância por estrada calibrada;
2. bacias com decaimento w(d) por classe de material;
3. seleção de hubs com limiar de escala;
4. curva MCLP;
5. validação contra plantas operantes (inclusive LOO);
6. exclusão de UCs federais.

## 4. O que vale portar (prioridade)

1. **Alta — tortuosidade e conexão ao grafo** (`tortuosidade_resumo.csv`, `hubs_conexao_resumo.csv`).
   - Dá um fator SP por faixa de distância para `routing.fallback_road_km`, com flag D, origem OSM jan/2026 e 5.000 pares.
   - Fecha parte da questão aberta do docs/21 citada em `routing.py`.
   - Custo: pequeno (a tabela está em `data/interim/esd/`).
   - Antes: registrar o OSM Geofabrik em `sources.yaml`. O shapefile está fora da pasta inventariada.
2. **Alta — cobertura gulosa com w(d) e Q_min (`cobertura_gulosa`, `Bacias`)** como `engine.siting.coverage`.
   - Poda candidatos e dá um warm start ao MILP do docs/12 (Passo 5).
   - Produz a curva MCLP, que é saída de planejamento.
   - Código puro numpy/heapq, testável com fixture pequena.
   - Vem com a advertência do próprio autor: é heurística e depende da grade de candidatos.
3. **Alta/média — distribuição palha→usina por estrada (P50–P99)** como entrada de distância de transporte para plantas anexas (docs/12, Passo 3).
   - Junto: o FL da palha e a sua sensibilidade aos percentis (o FL reflete a escolha dos percentis, `RELATORIO` §2).
4. **Média — exclusão de UCs federais de proteção integral e filtro `LOW_KV` de subestações** no grid v0.
5. **Média — teste de consistência com plantas operantes e LOO**, para o docs/13.
6. **Baixa:** Moran/LISA (descritivo) e k-means (silhueta fraca sem a cana).
7. **Não portar:**
   - P2, os pares de co-digestão;
   - a validação antiga por buffers GEE;
   - os pesos AHP de Saraswat & Swami 2025 como pesos do Project_Twin, por serem de outro contexto (Punjab, usina termelétrica). Servem só para a comparação do docs/12.

## 5. Pendências e conflitos (para o docs/21 depois da dupla checagem)

1. **N4 max, B:** 41,752 em `fl_espacial/outputs/previa_N4_variantes_M_m3dia.csv` contra 42,68 em `RELATORIO` §5 e 42,676 em `T1_state_levels.csv`. Também v4 max: 38,621 contra 39,55. Provável prévia antes da cascata final; confirmar.
2. **P2:** "sweet spot" C:N de 20–35 no código (linha 467) e de 20–30 no cabeçalho da planilha gerada pelo mesmo script (linha 768). O docstring promete sinergia de +7,4% a +25%, mas o código usa 1,18 ou 1,05, sem fonte.
3. **Duas bases não comparáveis:**
   - a antiga (ago/2026, cenário Real, 7.832.143.834 Nm³ CH₄/ano);
   - a v5.1 (N3/N4).
   - Exemplos que não devem ser misturados:
     - Moran 0,6261 contra 0,213;
     - k = 3 (silhueta 0,539) contra k = 5 (0,613);
     - faixas até o gás com 162/96/96/168/122/1 municípios contra 159/102/97/165/121/1.
4. **R² do modelo de triagem:** 0,650 (antigo) contra 0,603 (v5.1), já corrigido em `revisao_ESD/LEIA-ME.md` (T7).
5. **Q_min** de 3.200 / 1.500 / 500 Nm³ CH₄/d foi "confirmado no CHECKPOINT 2", sem fonte externa. Os equivalentes de ≈ 500 / 240 / 80 kWe também não têm fonte.
6. **Raios r1/r2 por classe** (`config_fl.yaml`, linhas 133–136) vêm de faixas da literatura com citações curtas (leal2013, coldebella2006, Laasasenaho et al. 2019). Nenhuma está identificada (DOI). Ficam com flag S.
7. **Camadas de infraestrutura** (`sp_cache.gpkg`, gasodutos, LT, SE): origem, ano e licença não estão escritos. A camada LT/SE é ≥ 230 kV.
8. **Arquivos fora da pasta, não verificados:** OSM roads, `SP_Municipios_2024.shp`, `feedstocks.yaml`, ETEs, áreas urbanas, `farms_for_gee.csv` e o cadastro bovino GEDAVE.
9. **Cópias duplicadas** com o mesmo sha256 (exemplo: `05_ILUC…/Serasa_Danilo_Milho2` e `11_Analises_Complementares/Milho2_Serasa`; `paper_figures/` e `P1/`). Os shapefiles de UCs e TIs aparecem em duas versões com sha diferente; o `config_fl.yaml` usa a de `SHAPEFILES_MAPBIOMAS_10.1/`.
10. **PAPER_04:** o md está vazio (OCR falhou). A identificação de Dabas et al. 2023 foi lida na imagem da p. 1. PAPER_04, PAPER_07 e PAPER_08 não estão na lista APA v8.
11. **Licenças:** nenhuma licença de dataset está escrita na pasta. URLs só onde um README as cita (331 de 820 linhas, com `url_written_in`).
12. **Grade v0, observação da rodada de hoje:** as 15 melhores células sob pesos iguais estão quase todas em Tietê (IBGE 3554508; uma em Rafard, 3542107). Só 31 células têm p_top_k ≥ 0,5. Vale olhar se o critério `poultry` ou `demand` domina ali.

## 6. Rodada da grade de aptidão v0 (C)

- **Execução:** `scripts/siting/score_grid_v0.py` sobre `C:\Users\Lucas\Documents\Project_Twin\data\processed\screening_v0\suitability_grid_v0.parquet`.
  - A grade está na pasta-mãe `Project_Twin/`, não dentro do clone.
  - Python 3.12.14 (uv), pandas 3.0.6, numpy 2.5.3, pyarrow 25.0.1, h3 4.5.0.
- **Identificação:** `run_id` suitability_v0_20261007T162025Z; sha256 da entrada b744d3ba…9073 (igual ao do meta da grade).
- **Células:** 47.273, das quais 1.884 excluídas e 45.389 pontuadas.
- **Robustez:**
  - 31 células com p_top_k ≥ 0,5 (top 100);
  - o OAT ±20% mantém pelo menos 88% do top 100 (pior caso: `swine` −20%).
- **Saídas:** gravadas ao lado da grade (fora do git). O stdout completo está em `docs/inbox/score_grid_v0_run.txt`.

## 7. Dados pessoais, de terceiros ou sob NDA

- **Parceiros sob NDA (São Martinho, Comgás, Equinor):** não há dataset de parceiro sob NDA na pasta.
  - "Comgás" aparece só como nome de distribuidora (ARSESP, dado público) em scripts de figura e no `t8_mandato_mistura.py`.
- **Dados pessoais (LGPD):**
  - `00_Primary_Data_Sources_PILAR2b/Relatorio_0082803826_granjas_aves_UNICAMP.xlsx`;
  - `00_Primary_Data_Sources_PILAR2b/Relatorio_0082804098_granjas_sui_UNICAMP.xlsx`.
  - São exportações GEDAVE/CDA-SP com propriedades georreferenciadas. Segundo `Evidencias_CP2B_FC_FCo_FL.md` §5.2, trazem endereço, CEP e contato.
  - Marcados `confidential=yes_personal_data`. Não foram abertos.
- **Terceiro, licença não encontrada:**
  - `…/Serasa_Danilo_Milho2/cruzamento_milho2_por_rgint_RETORNO_DANILO.csv` e `relatorio_milho.json`, com as cópias em `11_Analises_Complementares/`;
  - são cruzamentos com dado da Serasa;
  - marcados `check_third_party`.
- **Origem a confirmar:** `05_ILUC_Fontes_Primarias/` foi "preservado intacto como recebido do projeto ILUC/ABIOVE" (README). Marcado `check_origin`.
- **Fora da pasta, citado no material:** o cadastro bovino GEDAVE (`Documents/CP2B/Validacao_dados/...`) tem CPF/CNPJ e nomes (`Evidencias` §5.1). Só o agregado municipal (`Metodo_CP2b/inputs/gedave_bovinos_agregado_municipio_sistema.csv`) está na pasta.
