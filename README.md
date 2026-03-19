## Exposição Ocupacional à IA Generativa no Brasil (CBO) — Índice e Benchmark OIT

Projeto acadêmico/profissional em Python para construir e analisar um **índice de exposição ocupacional a LLMs** a partir de avaliações de atividades ocupacionais realizadas por dois modelos de linguagem (LLMs). O repositório também compara o ordenamento ocupacional gerado com um **benchmark da OIT** como análise exploratória de coerência externa.

### Contexto do TCC

O estudo mapeia **ocupações da Classificação Brasileira de Ocupações (CBO)** para um conjunto de **atividades típicas** e, em seguida, avalia o quão expostas essas atividades estão a capacidades de **Inteligência Artificial generativa baseada em linguagem (LLMs)**. As avaliações são agregadas para produzir um índice ocupacional em escala **0–1** e, posteriormente, são analisadas quanto:

- à estabilidade intra-modelo entre rodadas;
- à variação entre modelos;
- à coerência externa (ordenamento) frente ao benchmark da **OIT**.

### O que este repositório contém

- Dados de entrada e resultados já pré-computados (para reproduzir as análises sem chamadas de API).
- Scripts para:
  - gerar a matriz ocupação–atividade (CBO),
  - rodar pipelines de avaliação por LLM (quando desejado),
  - construir o índice ocupacional a partir de `score_results.csv`.
- Notebooks Jupyter para análises estatísticas e comparação com a OIT.

### Estrutura do projeto (alvo para publicação)

A organização do projeto segue a segunte lógica:

- `dados/`
  - insumos e dados tabulares usados como entrada (CSV/planilhas)
- `codigos/`
  - scripts Python para geração de insumos, construção do índice e pipelines de avaliação por LLM
- `notebooks/`
  - notebooks principais para análise estatística e comparação com a OIT
- `resultados/`
  - `resultados/graficos/` — figuras (`.png`)
  - `resultados/tabelas/` — tabelas e artefatos (`.csv`, `.xlsx`, `.txt`)
- `documentacao/`
  - documentos metodológicos e dicionário de dados
- `tcc/`
  - materiais auxiliares para o TCC

### Principais arquivos

- `codigos/construir_indice_ocupacional_cbo.py`
  - constrói `indice_ocupacao_cbo.csv` a partir de `score_results.csv`
- `notebooks/construir_indice_ocupacional_cbo.ipynb`
  - executa o script acima e exibe a tabela final
- `notebooks/analise_completa_resultados.ipynb`
  - estatística descritiva, estabilidade intra-modelo, comparação entre modelos e concordância
- `notebooks/analise_comparacao_oit.ipynb`
  - análise focada em coerência de ordenamento entre o índice CBO e o benchmark da OIT

### Tecnologias utilizadas

- Python 3.x
- `pandas`, `numpy`
- `matplotlib`, `seaborn`
- `scipy`
- `statsmodels` (opcional em análises de concordância)
- `scikit-learn` (opcional para métricas de kappa)
- `openpyxl` (para exportar Excel)
- `openai`, `anthropic` (necessário apenas para executar pipelines de avaliação por LLM)
- Jupyter Notebook

### Requisitos e execução

1. Instale dependências:
  - `pip install -r requirements.txt`
2. (Opcional, para rodar pipelines de LLM) configure credenciais:
  - crie/ajuste o arquivo `.env` com `OPENAI_API_KEY` e `ANTHROPIC_API_KEY`
3. (Recomendado para reproduzir análises) use os dados já pré-computados:
  - as análises principais rodam com `score_results.csv` e saídas geradas anteriormente.

### Ordem sugerida de execução (para reproduzir o TCC)

1. (Opcional) `codigos/gerar_saida_ocupacoes_cbo.py`
  - gera `saida_ocupacoes_atividades.csv`
2. (Opcional, exige API) `codigos/pipeline_gerar_scores_llms.py`
  - gera `score_results.csv`
3. `codigos/construir_indice_ocupacional_cbo.py`
  - gera `indice_ocupacao_cbo.csv`
  - normalização: escala 0–1 por divisão por 4
4. `notebooks/analise_completa_resultados.ipynb`
  - estatísticas completas e gráficos
5. `notebooks/analise_comparacao_oit.ipynb`
  - comparação com benchmark da OIT (ênfase em ordenamento, não em equivalência numérica)

### Observações metodológicas (resumo)

- Nível atividade: **mediana** dos 4 scores (2 modelos × 2 rodadas).
- Nível ocupação: **média simples** das 5 medianas de atividades.
- Normalização: `indice_0_1 = media_das_medianas / 4` (score original em 0–4).
- Desvio padrão: dispersão interna calculada sobre as 5 medianas das atividades de cada ocupação.

### Autor

Felipe Fin Fanfa (`felipefinfanfa`) — portfólio acadêmico/profissional.
