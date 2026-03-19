"""
Construção do índice ocupacional a partir de `score_results.csv`.

Regra de agregação (conforme especificação):
1) Para cada (ocupacao, atividade): mediana dos 4 scores.
2) Para cada ocupacao: média simples das 5 medianas das atividades.
3) Normalização para 0–1: indice_0_1 = media_das_medianas / 4
4) desvio_padrao: desvio padrão das 5 medianas das atividades.

Saída:
- CSV: `indice_ocupacao_cbo.csv` (ordenado do maior para o menor indice_0_1)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd


REQUIRED_COLUMNS = ["ocupacao", "atividade", "modelo", "rodada", "score"]

# Escala original do score: 0–4 => normalização por 4.
SCALE_MAX = 4.0


def load_data(input_path: Path) -> pd.DataFrame:
    """Carrega `score_results.csv`, padroniza strings e converte `score` para numérico."""
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    df = pd.read_csv(input_path, encoding="utf-8")
    df.columns = df.columns.str.strip()

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}. Colunas presentes: {list(df.columns)}")

    # Padronização mínima de campos categóricos.
    for col in ("ocupacao", "atividade", "modelo"):
        df[col] = df[col].astype(str).str.strip()

    # Converte score para numérico; valores inválidos viram NaN.
    df["score"] = pd.to_numeric(df["score"], errors="coerce")

    # Rodada como inteiro (se houver variação textual, mantém NaN e a validação por contagem falhará).
    df["rodada"] = pd.to_numeric(df["rodada"], errors="coerce").astype("Int64")

    return df


def validate_counts_strict(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Valida:
    - cada (ocupacao, atividade) possui exatamente 4 avaliações;
    - cada ocupacao possui exatamente 5 atividades.

    Retorna:
    - tabela_atividade: contagem por (ocupacao, atividade)
    - tabela_ocupacao: número de atividades por ocupacao
    """
    # Se `score` estiver NaN, a contagem por grupo será menor que 4 e a validação vai falhar.
    # Ainda assim, explicitamos quantas linhas perderam score para o usuário entender a causa.
    n_missing_score = int(df["score"].isna().sum())

    df_scored = df.dropna(subset=["score"]).copy()

    tabela_atividade = (
        df_scored.groupby(["ocupacao", "atividade"], as_index=False)
        .agg(n_avaliacoes=("score", "count"))
    )
    tabela_ocupacao = (
        df_scored.groupby(["ocupacao"], as_index=False)
        .agg(n_atividades=("atividade", "nunique"))
    )

    fora_4 = tabela_atividade[tabela_atividade["n_avaliacoes"] != 4].copy()
    fora_5 = tabela_ocupacao[tabela_ocupacao["n_atividades"] != 5].copy()

    if len(fora_4) > 0 or len(fora_5) > 0:
        parts = []
        if n_missing_score > 0:
            parts.append(f"{n_missing_score} linhas com `score` ausente/ inválido foram removidas antes da agregação.")
        if len(fora_4) > 0:
            parts.append(
                f"{len(fora_4)} pares (ocupacao, atividade) fora do padrão de 4 avaliações "
                f"(mostrar primeiros 15):\n{fora_4.head(15).to_string(index=False)}"
            )
        if len(fora_5) > 0:
            parts.append(
                f"{len(fora_5)} ocupações fora do padrão de 5 atividades "
                f"(mostrar):\n{fora_5.to_string(index=False)}"
            )
        raise ValueError("\n".join(parts))

    return tabela_atividade, tabela_ocupacao


def compute_activity_medians(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula a mediana dos 4 scores por (ocupacao, atividade)."""
    # Mantém apenas linhas com score válido (a validação já garantiu contagem correta).
    df_scored = df.dropna(subset=["score"]).copy()
    activity = (
        df_scored.groupby(["ocupacao", "atividade"], as_index=False)
        .agg(
            score_mediano=("score", "median"),
            n_avaliacoes=("score", "count"),
        )
    )
    return activity


def compute_occupation_index(activity_medians: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada ocupacao:
    - indice_bruto = média das 5 medianas
    - desvio_padrao = desvio padrão das 5 medianas
    - indice_0_1 = indice_bruto / 4
    """
    # Usamos ddof=1 (desvio padrão amostral) pois são 5 atividades e o padrão estatístico é reportar assim.
    occ = (
        activity_medians.groupby("ocupacao", as_index=False)
        .agg(
            indice_bruto=("score_mediano", "mean"),
            desvio_padrao=("score_mediano", "std"),
            n_atividades=("atividade", "size") if "atividade" in activity_medians.columns else ("score_mediano", "size"),
        )
    )

    # Desvio padrão pode virar NaN se, por algum motivo, n_atividades for 1; com validação estrita, deve ser 5.
    occ["indice_0_1"] = occ["indice_bruto"] / SCALE_MAX

    # Precisão adequada para relatório (ajuste se necessário).
    occ["indice_0_1"] = occ["indice_0_1"].round(6)
    occ["desvio_padrao"] = occ["desvio_padrao"].round(6)

    result = occ[["ocupacao", "indice_0_1", "desvio_padrao"]].sort_values("indice_0_1", ascending=False)
    return result.reset_index(drop=True)


def build_index(
    input_path: Path,
    output_csv_path: Path,
) -> pd.DataFrame:
    """Orquestra leitura, validação e construção do índice; salva CSV e retorna a tabela final."""
    df = load_data(input_path)

    # Validação estrita antes de agregar.
    validate_counts_strict(df)

    # Agregações conforme regra.
    activity_medians = compute_activity_medians(df)
    occupation_index = compute_occupation_index(activity_medians)

    # Exporta CSV.
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    occupation_index.to_csv(output_csv_path, index=False, encoding="utf-8", float_format="%.6f")
    return occupation_index


def main() -> None:
    parser = argparse.ArgumentParser(description="Construir índice ocupacional (0–1) a partir de score_results.csv.")
    parser.add_argument(
        "--input",
        type=str,
        default="score_results.csv",
        help="Caminho do arquivo de entrada (CSV). Padrão: score_results.csv",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="indice_ocupacao_cbo.csv",
        help="Caminho do arquivo de saída (CSV). Padrão: indice_ocupacao_cbo.csv",
    )

    args = parser.parse_args()

    base_dir = Path.cwd()
    input_path = base_dir / args.input
    output_csv_path = base_dir / args.output

    try:
        result = build_index(input_path=input_path, output_csv_path=output_csv_path)
    except Exception as e:
        # Erros já são informativos; apenas garantimos um prefixo claro.
        print(f"Erro ao construir índice: {e}", file=sys.stderr)
        raise

    print("\nÍndice ocupacional (ordenado do maior para o menor):")
    print(result.to_string(index=False))
    print(f"\nArquivo gerado: {output_csv_path}")


if __name__ == "__main__":
    main()

