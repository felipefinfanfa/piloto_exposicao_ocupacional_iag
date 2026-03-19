"""
Pipeline de estabilidade LLM — resultados definitivos.

Gera o índice de avaliação (score) para todas as tarefas da planilha
saida_ocupacoes_atividades.csv: 30 ocupações × 5 atividades = 150 tarefas.
Cada tarefa é avaliada por 2 modelos (GPT e Claude), 2 rodadas cada.
Saída: ocupacao, atividade, modelo, rodada, score, justificativa, timestamp.
"""

import csv
import datetime as dt
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from openai import OpenAI
import anthropic


# Caminhos de entrada/saída
# Ajuste para funcionar tanto no layout atual quanto no layout reorganizado para GitHub.
THIS_DIR = Path(__file__).resolve().parent
if (THIS_DIR / "dados").exists():
    PROJECT_ROOT = THIS_DIR
elif (THIS_DIR.parent / "dados").exists():
    PROJECT_ROOT = THIS_DIR.parent
else:
    # fallback (melhor esforço): usa o diretório do script
    PROJECT_ROOT = THIS_DIR

# Compatibilidade: o script usa `BASE_DIR` em funções auxiliares (ex.: carregamento de `.env`).
BASE_DIR = PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "dados"
INPUT_CSV = DATA_DIR / "saida_ocupacoes_atividades.csv"
RAW_RESULTS_CSV = DATA_DIR / "score_results.csv"

# Nomes das colunas no CSV de entrada (saida_ocupacoes_atividades)
COL_OCUPACAO = "ocupacoes"
COL_ATIVIDADE = "atividades"

# Modelos a serem comparados
MODEL_1 = "gpt-4o-mini"
MODEL_2 = "claude-3-haiku-20240307"

# Número de rodadas por modelo/atividade
N_RODADAS = 2


PROMPT_TEMPLATE = """# Avalie a exposição da atividade abaixo à Inteligência Artificial generativa baseada em linguagem (LLMs).

## REGRAS DE AVALIAÇÃO

- Considere apenas as capacidades técnicas atuais ou de curto prazo dos LLMs.
- Ignore fatores econômicos, regulatórios, institucionais, organizacionais e de adoção.
- Avalie apenas a atividade informada, no contexto da ocupação.
- Não avalie a ocupação inteira.
- Interprete a atividade em seu sentido mais típico e literal dentro da ocupação.

**Contexto ocupacional:**

{ocupacao}

**Atividade:**

{atividade}

## CRITÉRIOS DE JULGAMENTO

### 1. Capacidade técnica de execução
Verifique se o LLM consegue executar a atividade de forma útil, integralmente ou em parte.

### 2. Padronização e codificabilidade
Verifique se a atividade pode ser descrita por instruções claras, replicáveis e baseadas em regras.

### 3. Dependência de julgamento humano complexo
Verifique se a atividade exige interpretação ambígua, discernimento subjetivo, criatividade ou decisão contextual não padronizada.

### 4. Necessidade de interação humana complexa
Verifique se a atividade exige negociação, persuasão, empatia, mediação, coordenação interpessoal ou contato humano como núcleo da ação.

## REGRAS DE AVALIAÇÃO

1. Identifique primeiro o núcleo da atividade: a ação principal que define seu objetivo imediato no contexto da ocupação.
2. Identifique separadamente a parte periférica: apoio, preparação, organização, registro, busca de informação, síntese, documentação ou estruturação textual.
3. Avalie se o LLM executa de forma útil o núcleo da atividade.
4. Avalie se o LLM executa apenas alguma parte periférica da atividade.
5. Avalie se o núcleo depende de julgamento humano complexo.
6. Avalie se o núcleo depende de interação humana complexa.

## ESCALA (0–4)

### NÍVEL 0 - NÃO EXPOSTA

Use 0 quando:

- o LLM não executa a atividade de modo útil;
- a atividade não pode ser reduzida a instruções claras, estáveis e repetíveis;
- o núcleo da atividade exige julgamento humano contextual, tácito ou situado;
- o núcleo da atividade exige interação humana complexa, presença social ou percepção/manipulação do mundo físico.

### NÍVEL 1 - EXPOSIÇÃO BAIXA

Use 1 quando:

- o LLM executa apenas partes periféricas ou preparatórias da atividade de forma útil;
- a atividade contém alguns elementos descritíveis, mas o núcleo não pode ser totalmente descrito por regras ou instruções;
- o núcleo da atividade exige julgamento humano para definir, interpretar ou decidir o resultado;
- a interação humana complexa ou o contexto situacional continuam sendo necessários para o núcleo da atividade.

### NÍVEL 2 - EXPOSIÇÃO MODERADA

Use 2 quando:

- o LLM executa de forma útil parte do processo, mas não executa diretamente o núcleo da atividade;
- a atividade combina etapas que podem ser descritas por instruções com etapas que exigem contexto, integração ou interpretação;
- o núcleo da atividade exige julgamento humano para orientar, validar ou decidir o resultado;
- a interação humana complexa ou a adaptação ao contexto continuam sendo necessárias para o núcleo da atividade.

### NÍVEL 3 - EXPOSIÇÃO ALTA

Use 3 quando:

- o LLM executa de forma útil o núcleo da atividade;
- a atividade pode ser descrita por instruções claras, repetíveis e baseadas em informação;
- o julgamento humano aparece principalmente como revisão, validação, supervisão ou decisão final;
- a interação humana não constitui o núcleo da atividade, embora ainda possa ser relevante em etapas específicas.

### NÍVEL 4 - EXPOSIÇÃO MUITO ALTA

Use 4 quando:

- o LLM executa de forma útil a maior parte ou praticamente todo o núcleo da atividade;
- a atividade é padronizada, textual, informacional, classificatória ou baseada em regras claras e estáveis;
- o julgamento humano é limitado, acessório ou não decisivo para a execução;
- a interação humana é pouco necessária e não altera de forma decisiva o resultado.

## FORMATO DE SAÍDA

Responda em exatamente duas linhas:

**Linha 1:** número inteiro de 0 a 4  
**Linha 2:** justificativa curta, com no máximo 12 palavras"""


@dataclass
class ActivityRecord:
    ocupacao: str
    atividade: str


@dataclass
class EvaluationResult:
    ocupacao: str
    atividade: str
    modelo: str
    rodada: int
    score: float
    justificativa: str
    timestamp: str


def _load_env_from_dotenv(dotenv_path: Path | None = None) -> None:
    """Carrega variáveis de ambiente de um arquivo .env simples."""
    if dotenv_path is None:
        dotenv_path = BASE_DIR / ".env"

    if not dotenv_path.exists():
        return

    try:
        with dotenv_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


def load_all_activities(input_csv: Path = INPUT_CSV) -> List[ActivityRecord]:
    """
    Carrega todas as atividades do CSV de entrada (30 ocupações × 5 atividades).
    Sem limite de ocupações — usa todas as linhas válidas.
    """
    atividades_por_ocupacao: dict[str, list[str]] = defaultdict(list)

    with input_csv.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ocup = (row.get(COL_OCUPACAO) or "").strip()
            atv = (row.get(COL_ATIVIDADE) or "").strip()
            if not ocup or not atv:
                continue
            atividades_por_ocupacao[ocup].append(atv)

    if not atividades_por_ocupacao:
        raise ValueError("Nenhuma ocupação/atividade válida encontrada no CSV de entrada.")

    records: list[ActivityRecord] = []
    for ocup in atividades_por_ocupacao:
        for atv in atividades_por_ocupacao[ocup]:
            records.append(ActivityRecord(ocupacao=ocup, atividade=atv))

    return records


def _parse_score(text: str) -> float:
    """
    Converte a resposta do modelo em número entre 0 e 4.

    O prompt pede um inteiro de 0 a 4, mas aqui aceitamos
    também valores numéricos intermediários e fazemos clamp
    no intervalo [0, 4]. Aceita vírgula ou ponto e ignora
    textos extras eventuais.
    """
    cleaned = text.strip()
    cleaned = cleaned.replace(",", ".")
    try:
        value = float(cleaned)
    except ValueError:
        num_chars = "".join(ch for ch in cleaned if ch.isdigit() or ch in ".-")
        value = float(num_chars)
    if math.isnan(value):
        raise ValueError(f"Score inválido retornado pelo modelo: {text!r}")
    return max(0.0, min(4.0, value))


def _parse_score_and_justification(content: str) -> tuple[float, str]:
    """Extrai score (primeira linha) e justificativa (segunda linha, máx. 12 palavras)."""
    lines = [ln.strip() for ln in content.strip().splitlines() if ln.strip()]
    score_text = lines[0] if lines else ""
    score = _parse_score(score_text)
    if len(lines) >= 2:
        just = " ".join(lines[1].split()[:12])
    else:
        just = ""
    return score, just


def evaluate_activity_openai(
    client: OpenAI,
    atividade_record: ActivityRecord,
    modelo: str,
    rodada: int,
) -> EvaluationResult:
    """Avalia uma (ocupação, atividade) usando modelo da OpenAI."""
    prompt = PROMPT_TEMPLATE.format(
        ocupacao=atividade_record.ocupacao,
        atividade=atividade_record.atividade,
    )

    response = client.chat.completions.create(
        model=modelo,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.0,
        max_tokens=120,
    )

    content = response.choices[0].message.content or ""
    score, justificativa = _parse_score_and_justification(content)

    timestamp = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"

    return EvaluationResult(
        ocupacao=atividade_record.ocupacao,
        atividade=atividade_record.atividade,
        modelo=modelo,
        rodada=rodada,
        score=score,
        justificativa=justificativa,
        timestamp=timestamp,
    )


def evaluate_activity_anthropic(
    client: anthropic.Anthropic,
    atividade_record: ActivityRecord,
    modelo: str,
    rodada: int,
) -> EvaluationResult:
    """Avalia uma (ocupação, atividade) usando modelo da Anthropic (Claude)."""
    prompt = PROMPT_TEMPLATE.format(
        ocupacao=atividade_record.ocupacao,
        atividade=atividade_record.atividade,
    )

    response = client.messages.create(
        model=modelo,
        max_tokens=120,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    content = ""
    if response.content:
        first_block = response.content[0]
        if hasattr(first_block, "text"):
            content = first_block.text or ""
        elif isinstance(first_block, dict):
            content = first_block.get("text", "") or ""

    score, justificativa = _parse_score_and_justification(content)

    timestamp = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"

    return EvaluationResult(
        ocupacao=atividade_record.ocupacao,
        atividade=atividade_record.atividade,
        modelo=modelo,
        rodada=rodada,
        score=score,
        justificativa=justificativa,
        timestamp=timestamp,
    )


def run_stability_test(
    activities: Iterable[ActivityRecord],
    model_1: str = MODEL_1,
    model_2: str = MODEL_2,
    n_rodadas: int = N_RODADAS,
) -> List[EvaluationResult]:
    """
    Executa o experimento de estabilidade para todas as atividades:
    para cada (ocupação, atividade), roda n_rodadas em cada modelo.
    """
    _load_env_from_dotenv()

    openai_client = OpenAI()
    anthropic_client = anthropic.Anthropic()
    results: list[EvaluationResult] = []

    for record in activities:
        for modelo in (model_1, model_2):
            for rodada in range(1, n_rodadas + 1):
                if modelo == model_1:
                    eval_result = evaluate_activity_openai(
                        client=openai_client,
                        atividade_record=record,
                        modelo=modelo,
                        rodada=rodada,
                    )
                else:
                    eval_result = evaluate_activity_anthropic(
                        client=anthropic_client,
                        atividade_record=record,
                        modelo=modelo,
                        rodada=rodada,
                    )
                results.append(eval_result)

    return results


def save_results(
    results: Iterable[EvaluationResult],
    raw_results_csv: Path = RAW_RESULTS_CSV,
) -> None:
    """
    Salva os resultados em CSV com colunas:
    ocupacao, atividade, modelo, rodada, score, justificativa, timestamp
    """
    raw_results_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "ocupacao",
        "atividade",
        "modelo",
        "rodada",
        "score",
        "justificativa",
        "timestamp",
    ]

    with raw_results_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "ocupacao": r.ocupacao,
                    "atividade": r.atividade,
                    "modelo": r.modelo,
                    "rodada": r.rodada,
                    "score": f"{r.score:.2f}",
                    "justificativa": r.justificativa,
                    "timestamp": r.timestamp,
                }
            )


def main() -> None:
    """
    Pipeline definitivo:
    - carrega todas as atividades de saida_ocupacoes_atividades.csv (30 ocupações × 5 atividades)
    - roda experimento de estabilidade (2 modelos × 2 rodadas por tarefa)
    - salva em score_results.csv
    """
    activities = load_all_activities()
    n_tarefas = len(activities)
    n_total_avaliacoes = n_tarefas * 2 * N_RODADAS  # 2 modelos, 2 rodadas
    print(f"Tarefas carregadas: {n_tarefas} (30 ocupações × 5 atividades)")
    print(f"Total de avaliações a gerar: {n_total_avaliacoes}")
    print("Iniciando pipeline...")

    results = run_stability_test(activities)
    save_results(results)

    print(f"Resultados salvos em: {RAW_RESULTS_CSV}")
    print(f"Total de linhas escritas: {len(results)}")


if __name__ == "__main__":
    main()
