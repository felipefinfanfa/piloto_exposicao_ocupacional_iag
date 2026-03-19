# Dicionário de Dados (CSV)

Este documento descreve, de forma objetiva, os principais arquivos `.csv` usados no projeto e seus esquemas (colunas).

> Observação: os nomes e a estrutura abaixo refletem os arquivos presentes no repositório. Após a reorganização para GitHub, esses arquivos devem estar em `dados/` (insumos) e `resultados/tabelas/` (derivações/saídas).

---

## Entradas principais

### `score_results.csv`
**Uso:** insumo central para construir o índice ocupacional.

**Esquema (colunas):**
- `ocupacao`: ocupação CBO
- `atividade`: atividade associada à ocupação
- `modelo`: identificador do LLM (ex.: `gpt-4o-mini`, `claude-3-haiku-20240307`)
- `rodada`: rodada da avaliação (ex.: `1` ou `2`)
- `score`: score numérico na escala 0–4
- `justificativa`: texto curto do LLM
- `timestamp`: marca temporal (ISO)

---

### `stability_results.csv`
**Uso:** conjunto adicional de avaliações para análise de estabilidade (quando gerado via pipeline específica).

**Esquema (colunas):** segue o mesmo padrão de `score_results.csv`:
- `ocupacao`, `atividade`, `modelo`, `rodada`, `score`, `justificativa`, `timestamp`

---

### `dados/saida_ocupacoes_atividades.csv`
**Uso:** insumo para pipelines de avaliação por LLM.

**Esquema (colunas):**
- `ocupacoes`
- `atividades`

---

### `indice_ocupacao_cbo.csv`
**Uso:** resultado final do script de construção do índice (escala 0–1).

**Esquema (colunas):**
- `ocupacao`
- `indice_0_1`: índice ocupacional normalizado (0–1)
- `desvio_padrao`: desvio padrão das medianas das 5 atividades da ocupação

---

### `indice_ocupacoes_oit.csv`
**Uso:** benchmark externo para comparação com o ordenamento do índice CBO.

**Esquema (colunas):**
- `ocupacao_equivalente_ILO`: título equivalente (categoria OIT/ILO)
- `codigo`: código OIT
- `gradiente_ilo`: categoria ordinal de exposição no benchmark OIT
- `mean_ilo`: valor médio do benchmark (usado para ranqueamento e associação por ordenação)

---

## Dados derivados (resultados / tabelas)

### `comparacao_cbo_oit_tabela_final.csv`
**Uso:** tabela final pronta para discussão na seção de comparação com a OIT (inclui ranking e diferença).

**Principais colunas:** (conforme gerado no notebook `analise_comparacao_oit.ipynb`)
- `ocupacao`
- `indice_0_1`
- `ocupacao_equivalente_ILO`
- `gradiente_ilo`
- `mean_ilo`
- `diff_rank` e campos auxiliares de ranking

### `comparacao_cbo_oit_consolidado.csv`
**Uso:** tabela consolidada com informações para gráficos e análise.

### `indice_por_gradiente_oit.csv`
**Uso:** distribuição por categoria (`gradiente_ilo`) e estatísticas agregadas do índice.

Esquema (colunas, observado na amostra):
- `gradiente_ilo`
- `count`
- `mean`
- `median`

---

## Arquivos gerados pela análise completa (notebook `analise_completa_resultados.ipynb`)

Os arquivos abaixo são gerados automaticamente a partir de `score_results.csv`:

### `resumo_principal_indicadores.csv`
**Uso:** conjunto resumido de indicadores principais.
Exemplo de colunas (observado):
- `score_media_geral`, `score_mediana_geral`, etc.

### `estatisticas_por_modelo.csv` / `estatisticas_por_rodada.csv` / `estatisticas_por_modelo_rodada.csv`
**Uso:** tabelas de estatística descritiva para recortes específicos.

### `intra_modelo_resumo.csv`
**Uso:** resumo de variações entre rodadas dentro de cada modelo.

### `comparacao_modelos_por_atividade.csv` / `comparacao_modelos_por_rodada.csv`
**Uso:** diferenças entre modelos para cada atividade e para cada rodada.

### `concordancia_entre_modelos.csv`
**Uso:** métricas de correspondência/concordância entre os dois modelos (ex.: correlações, tolerância).

### `testes_intra_modelo.csv` / `testes_entre_modelos.csv`
**Uso:** resultados de testes estatísticos pareados.

### `atividades_mais_instaveis_intra_modelo.csv`
**Uso:** ranking das atividades com maior instabilidade intra-modelo.

### `atividades_maior_discrepancia_entre_modelos.csv`
**Uso:** ranking das atividades com maior discrepância entre modelos.

---

## Materiais auxiliares (insumos CBO)

### `base_projeto_piloto.csv`
**Uso:** base auxiliar utilizada na geração do conjunto de ocupações/atividades.

**Esquema (colunas):**
- inclui chaves e metadados como `COD_GRANDE_GRUPO`, `COD_OCUPACAO`, `COD_ATIVIDADE`, `NOME_ATIVIDADE`, `TITULO_OCUPACAO`, `TITULO_GRANDE_GRUPO`.

### `CBO2002 - Ocupacao.csv`
**Uso:** tabela de metadados de ocupações.

**Esquema (observado):**
- `CODIGO;TITULO`

### `CBO2002 - PerfilOcupacional.csv`
**Uso:** mapeamento detalhado ocupação–atividade.

**Esquema (observado):**
- `COD_GRANDE_GRUPO;COD_SUBGRUPO_PRINCIPAL;COD_SUBGRUPO;COD_FAMILIA;COD_OCUPACAO;...;COD_ATIVIDADE;NOME_ATIVIDADE`

