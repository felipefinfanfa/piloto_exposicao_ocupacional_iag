# Metodologia de Reprodução (Repositório)

Este documento descreve como reproduzir (i) a construção do índice ocupacional, (ii) a análise estatística completa e (iii) a comparação com o benchmark da OIT.

> Nota: para executar pipelines de avaliação por LLM (OpenAI/Anthropic), é necessário configurar credenciais em `.env`. Para as análises principais, os resultados já estão pré-computados no repositório.

---

## 1) Arquivos de insumo e saída (visão geral)

### Insumos principais
- `dados/score_results.csv`
- `dados/indice_ocupacoes_oit.csv`
- `dados/indice_ocupacao_cbo.csv` (derivado, mas usado como intermediário em notebooks)
- `dados/saida_ocupacoes_atividades.csv` (insumo de pipelines de avaliação)

### Saídas principais
- `resultados/tabelas/indice_ocupacao_cbo.csv`
- `resultados/tabelas/comparacao_cbo_oit_consolidado.csv` (e tabelas associadas)
- `resultados/graficos/*` (gráficos gerados pelos notebooks)
- `resultados/tabelas/*` (tabelas geradas pelos notebooks)

---

## 2) Quais scripts geram quais resultados

### (Opcional) Gerar a matriz ocupação–atividade
- `codigos/gerar_saida_ocupacoes_cbo.py` (origem do código: `dados/gerar_saida_ocupacoes.py`)
  - **Entrada:** CBO2002 (`CBO2002 - Ocupacao.csv`, `CBO2002 - PerfilOcupacional.csv`) e base auxiliar
  - **Saída:** `dados/saida_ocupacoes_atividades.csv`

### (Opcional, exige API) Rodar avaliação por LLMs
- `codigos/pipeline_gerar_scores_llms.py` (origem: `pipeline_score_tarefa.py`)
  - **Entrada:** `dados/saida_ocupacoes_atividades.csv`
  - **Saída:** `dados/score_results.csv`

### (Opcional, exige API) Avaliação para estabilidade
- `codigos/pipeline_gerar_estabilidade_llms.py` (origem: `pipeline_stability_llm.py`)
  - **Entrada:** `dados/saida_ocupacoes_atividades.csv`
  - **Saída:** `dados/stability_results.csv`

### Construção do índice ocupacional (não exige API)
- `codigos/construir_indice_ocupacional_cbo.py` (origem: `construir_indice_ocupacional_cbo.py`)
  - **Entrada:** `dados/score_results.csv`
  - **Saída:** `resultados/tabelas/indice_ocupacao_cbo.csv`

---

## 3) Notebooks principais (o que executam)

### `notebooks/construir_indice_ocupacional_cbo.ipynb`
- Executa o script `codigos/construir_indice_ocupacional_cbo.py`
- Exibe a tabela final do índice ocupacional

### `notebooks/analise_completa_resultados.ipynb`
- Carrega `dados/score_results.csv`
- Gera:
  - estatística descritiva,
  - variação intra-modelo (rodada 1 vs rodada 2),
  - variação entre modelos,
  - concordância/correlações,
  - testes estatísticos,
  - gráficos e tabelas resumidas

### `notebooks/analise_comparacao_oit.ipynb`
- Carrega:
  - `resultados/tabelas/indice_ocupacao_cbo.csv`
  - `dados/indice_ocupacoes_oit.csv`
- Constrói rankings e compara coerência externa do ordenamento:
  - Spearman (principal para ordenação)
  - Pearson apenas complementar
- Gera gráficos e tabelas prontas para a seção `4.2`

---

## 4) Como reproduzir a análise do índice ocupacional (passo a passo)

1. Garanta que `dados/score_results.csv` existe no repositório (pré-computado ou gerado por pipeline).
2. Rode:
   - `notebooks/construir_indice_ocupacional_cbo.ipynb`
   - ou diretamente:
     - `python codigos/construir_indice_ocupacional_cbo.py --input dados/score_results.csv --output resultados/tabelas/indice_ocupacao_cbo.csv`
3. O índice é construído exatamente por:
   - mediana dos 4 scores por atividade (`ocupacao + atividade`);
   - média das 5 medianas por ocupação;
   - normalização: divisão por 4 (`indice_0_1 = media_das_medianas / 4`);
   - `desvio_padrao`: desvio padrão das 5 medianas.

---

## 5) Como reproduzir a comparação com a OIT

1. Garanta a existência de:
   - `resultados/tabelas/indice_ocupacao_cbo.csv`
   - `dados/indice_ocupacoes_oit.csv`
2. Rode:
   - `notebooks/analise_comparacao_oit.ipynb`
3. Interpretação metodológica (explicitada no notebook):
   - `indice_0_1` e `mean_ilo` não são tratados como equivalentes em magnitude;
   - a medida principal é a coerência de **ordenamento** entre ocupações;
   - divergências são discutidas como informação exploratória.

---

## 6) Como reproduzir a análise de estabilidade

O notebook de análise completa usa a estabilidade intra-modelo ao comparar:
- `rodada 1` vs `rodada 2` para a mesma atividade, dentro do mesmo modelo.

Para executar um conjunto adicional em `stability_results.csv`, é necessário rodar:
- `codigos/pipeline_gerar_estabilidade_llms.py` (opcional, exige API).

