"""Módulo para geração de imagem de tabela estilizada a partir de amostra CSV para o TCC."""

from __future__ import annotations

import csv
import textwrap
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from src.config import BASE_DIR

# ==============================================================================
# CONFIGURAÇÕES DE ENTRADA, SAÍDA E ESTILIZAÇÃO DA IMAGEM
# ==============================================================================
CAMINHO_CSV_ENTRADA: Path = (
    BASE_DIR / "data" / "classified" / "resultados_classificados_modelo_2_dataset_curado.csv"
)
CAMINHO_IMAGEM_SAIDA: Path = (
    BASE_DIR / "data" / "results" / "amostra_dados_classificados_tcc.png"
)

NUMERO_LINHAS_AMOSTRA: int = 10
MAX_CARACTERES_CELULA: int = 100  # Limite máximo de caracteres por célula para exibição limpa

# Mapeamento de proporção de largura por coluna (A soma deve ser ~1.0)
PROPORCAO_LARGURA_COLUNAS: dict[str, float] = {
    "id": 0.05,
    "nivel": 0.08,
    "texto": 0.28,
    "classe_real": 0.13,
    "classe_predita": 0.13,
    "justificativa": 0.28,
}

# Largura do textwrap baseada no peso da coluna
LARGURA_TEXTWRAP_POR_COLUNA: dict[str, int] = {
    "id": 10,
    "nivel": 12,
    "texto": 45,
    "classe_real": 15,
    "classe_predita": 15,
    "justificativa": 45,
}


class ErroGeracaoAmostra(ValueError):
    """Exceção para erros no processamento e visualização da amostra do CSV."""


def ler_amostra_csv(
    caminho_csv: Path,
    limite_linhas: int = 10,
) -> tuple[list[str], list[list[str]]]:
    """Lê as primeiras linhas de um arquivo CSV e detecta o delimitador automaticamente."""
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_csv.resolve()}")

    with caminho_csv.open("r", encoding="utf-8-sig") as arquivo:
        amostra_cabecalho = arquivo.read(2048)
        arquivo.seek(0)

        delimitador = ";" if ";" in amostra_cabecalho else ","
        leitor = csv.reader(arquivo, delimiter=delimitador)

        try:
            cabecalho = next(leitor)
        except StopIteration as erro:
            raise ErroGeracaoAmostra(
                f"O arquivo {caminho_csv.name} está vazio."
            ) from erro

        linhas: list[list[str]] = []
        for indice, linha in enumerate(leitor):
            if indice >= limite_linhas:
                break
            linhas.append(linha)

    return cabecalho, linhas


def formatar_celulas(
    cabecalho: list[str],
    linhas: list[list[str]],
) -> tuple[list[str], list[list[str]]]:
    """Aplica truncamento de segurança e quebra de linha proporcional a cada coluna."""
    cabecalho_formatado = []
    for col in cabecalho:
        largura_wrap = LARGURA_TEXTWRAP_POR_COLUNA.get(col.strip().lower(), 20)
        cabecalho_formatado.append(textwrap.fill(col, width=largura_wrap))

    linhas_formatadas: list[list[str]] = []
    for linha in linhas:
        linha_fmt = []
        for col_idx, celula in enumerate(linha):
            nome_col = cabecalho[col_idx].strip().lower() if col_idx < len(cabecalho) else ""
            largura_wrap = LARGURA_TEXTWRAP_POR_COLUNA.get(nome_col, 30)

            texto_celula = str(celula).strip()
            if len(texto_celula) > MAX_CARACTERES_CELULA:
                texto_celula = texto_celula[: MAX_CARACTERES_CELULA - 3] + "..."

            texto_wrapped = textwrap.fill(texto_celula, width=largura_wrap)
            linha_fmt.append(texto_wrapped)
        linhas_formatadas.append(linha_fmt)

    return cabecalho_formatado, linhas_formatadas


def renderizar_matriz_imagem(
    cabecalho: list[str],
    linhas: list[list[str]],
    caminho_saida: Path,
) -> Path:
    """Desenha e salva a imagem ajustando proporcionalmente larguras e alturas das células."""
    cabecalho_fmt, linhas_fmt = formatar_celulas(cabecalho, linhas)

    # 1. Obter a largura de cada coluna com base no mapeamento
    col_widths = []
    for col in cabecalho:
        peso = PROPORCAO_LARGURA_COLUNAS.get(col.strip().lower(), 1.0 / len(cabecalho))
        col_widths.append(peso)
    
    # Normaliza as larguras para garantir soma 1.0
    soma_pesos = sum(col_widths)
    col_widths = [w / soma_pesos for w in col_widths]

    # 2. Calcular a quantidade máxima de linhas de texto em cada linha da tabela
    linhas_por_linha_tabela: list[int] = []
    for linha in linhas_fmt:
        max_linhas_text = max(len(celula.split("\n")) for celula in linha)
        linhas_por_linha_tabela.append(max_linhas_text)

    # 3. Calcular a altura ideal da figura com base no conteúdo acumulado
    altura_cabecalho_fator = 2.5
    altura_total_unidades = altura_cabecalho_fator + sum(linhas_por_linha_tabela)
    altura_figura = max(8.0, altura_total_unidades * 0.3)
    largura_figura = 12.0  # Largura ampla para caber texto confortavelmente

    figura, eixos = plt.subplots(figsize=(largura_figura, altura_figura))
    eixos.axis("off")

    # 4. Construção da tabela com larguras relativas declaradas
    tabela = eixos.table(
        cellText=linhas_fmt,
        colLabels=cabecalho_fmt,
        colWidths=col_widths,
        cellLoc="left",
        loc="center",
    )

    tabela.auto_set_font_size(False)
    tabela.set_fontsize(9.0)

    # 5. Ajustar altura individual de cada linha dinamicamente
    # Altura relativa normalizada de cada linha em relação à altura total
    altura_cabecalho_rel = (altura_cabecalho_fator / altura_total_unidades)
    
    # Estilizar o Cabeçalho (Linha 0)
    for col_idx in range(len(cabecalho_fmt)):
        celula = tabela[(0, col_idx)]
        celula.set_text_props(weight="bold", color="white")
        celula.set_facecolor("#1f4e78")
        celula.set_height(altura_cabecalho_rel)

    # Estilizar as Linhas de Dados (Linhas 1 a N)
    for row_idx, num_linhas_texto in enumerate(linhas_por_linha_tabela, start=1):
        altura_linha_rel = (num_linhas_texto / altura_total_unidades)
        cor_fundo = "#f2f4f7" if row_idx % 2 == 0 else "#ffffff"

        for col_idx in range(len(cabecalho_fmt)):
            celula = tabela[(row_idx, col_idx)]
            celula.set_facecolor(cor_fundo)
            celula.set_height(altura_linha_rel)

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    plt.title(
        f"Amostra dos Dados ({len(linhas)} primeiras linhas) - TCC UFRRJ",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(figura)

    return caminho_saida


def gerar_imagem_amostra_csv(
    caminho_csv: Path = CAMINHO_CSV_ENTRADA,
    caminho_saida: Path = CAMINHO_IMAGEM_SAIDA,
    limite_linhas: int = NUMERO_LINHAS_AMOSTRA,
) -> Path:
    """Função principal que orquestra a leitura do CSV e a geração da imagem da amostra."""
    cabecalho, linhas = ler_amostra_csv(caminho_csv, limite_linhas)
    caminho_imagem = renderizar_matriz_imagem(cabecalho, linhas, caminho_saida)
    return caminho_imagem


if __name__ == "__main__":
    caminho_gerado = gerar_imagem_amostra_csv()
    print(f"Imagem da amostra gerada com sucesso em: {caminho_gerado.resolve()}")