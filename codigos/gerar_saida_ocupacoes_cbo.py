import csv
import difflib
import random
from collections import defaultdict
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
if (THIS_DIR.parent / "dados").exists():
    PROJECT_ROOT = THIS_DIR.parent
else:
    PROJECT_ROOT = THIS_DIR

BASE_PATH = PROJECT_ROOT / "dados" / "base_projeto_piloto.csv"
OUTPUT_PATH = PROJECT_ROOT / "dados" / "saida_ocupacoes_atividades.csv"
OUTPUT_PATH_TODAS = PROJECT_ROOT / "dados" / "saida_ocupacoes_atividades_todas.csv"


TARGET_OCUPACOES = [
    "Analista de planejamento e orçamento - apo",
    "Assistente administrativo",
    "Escriturário de banco",
    "Técnico de contabilidade",
    "Contador",
    "Analista de recursos humanos",
    "Analista de pesquisa de mercado",
    "Jornalista",
    "Redator de publicidade",
    "Analista de desenvolvimento de sistemas",
    "Economista",
    "Administrador",
    "Advogado",
    "Analista financeiro (instituições financeiras)",
    "Analista de logistica",
    "Professor de matemática no ensino médio",
    "Desenhista industrial gráfico (designer gráfico)",
    "Técnico de suporte ao usuário de tecnologia da informação",
    "Supervisor administrativo",
    "Corretor de imóveis",
    "Motorista de caminhão (rotas regionais e internacionais)",
    "Operador de máquinas fixas, em geral",
    "Eletricista de instalações",
    "Encanador",
    "Pedreiro",
    "Mecânico de manutenção de máquinas, em geral",
    "Técnico de enfermagem",
    "Enfermeiro",
    "Vendedor de comércio varejista",
    "Cozinheiro geral",
]


def norm(text: str) -> str:
    return (text or "").strip().lower()


def carregar_linhas_base() -> list[dict]:
    linhas: list[dict] = []
    # Usa UTF-8 explicitamente para lidar com acentuação da base
    with open(BASE_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            titulo = norm(row.get("TITULO_OCUPACAO", ""))
            atividade = (row.get("NOME_ATIVIDADE") or "").strip()
            if not titulo:
                continue
            linhas.append(
                {
                    "TITULO_OCUPACAO": row["TITULO_OCUPACAO"].strip(),
                    "NOME_ATIVIDADE": atividade,
                }
            )
    return linhas


def escolher_melhor_titulo(titulos_unicos: list[str], alvo: str) -> tuple[str, float, list[str]]:
    alvo_norm = norm(alvo)
    scores: list[tuple[float, str]] = []
    for titulo in titulos_unicos:
        score = difflib.SequenceMatcher(None, norm(titulo), alvo_norm).ratio()
        scores.append((score, titulo))
    scores.sort(reverse=True, key=lambda x: x[0])
    melhor_score, melhor_titulo = scores[0]
    principais = [t for _, t in scores[:5]]
    return melhor_titulo, melhor_score, principais


def gerar_saida() -> tuple[list[dict], list[dict]]:
    linhas = carregar_linhas_base()
    if not linhas:
        raise SystemExit("Nenhuma linha válida encontrada na base.")

    titulos_unicos = sorted({l["TITULO_OCUPACAO"] for l in linhas})

    random.seed(42)

    saida_amostra: list[dict] = []
    saida_todas: list[dict] = []

    for alvo in TARGET_OCUPACOES:
        melhor_titulo, melhor_score, principais = escolher_melhor_titulo(titulos_unicos, alvo)

        linhas_titulo = [l for l in linhas if l["TITULO_OCUPACAO"] == melhor_titulo]
        atividades = sorted({l["NOME_ATIVIDADE"] for l in linhas_titulo if l["NOME_ATIVIDADE"]})

        # todas as atividades da ocupação encontrada
        for atividade in atividades:
            saida_todas.append(
                {
                    "ocupacoes": melhor_titulo,
                    "atividades": atividade,
                }
            )

        if atividades:
            k = 5 if len(atividades) >= 5 else len(atividades)
            escolhidas = random.sample(atividades, k)
        else:
            escolhidas = [""]

        justificativa = (
            f"Ocupação procurada: '{alvo}'. "
            f"Ocupação escolhida: '{melhor_titulo}' (similaridade aproximada {melhor_score:.2f}). "
            "Principais ocupações semelhantes consideradas: "
            + ", ".join(f"'{t}'" for t in principais)
            + "."
        )

        for atividade in escolhidas:
            saida_amostra.append(
                {
                    "ocupacoes": melhor_titulo,
                    "atividades": atividade,
                }
            )

    return saida_amostra, saida_todas


def main() -> None:
    linhas_amostra, linhas_todas = gerar_saida()

    # garante diretório de saída
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "ocupacoes",
        "atividades",
    ]

    # planilha 1: como já estava (5 atividades aleatórias por ocupação)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(linhas_amostra)

    # planilha 2: todas as atividades das ocupações selecionadas
    with open(OUTPUT_PATH_TODAS, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(linhas_todas)


if __name__ == "__main__":
    main()

