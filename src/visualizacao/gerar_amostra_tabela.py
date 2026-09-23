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
# Especifique aqui o caminho do CSV de entrada desejado:
CAMINHO_CSV_ENTRADA: Path = BASE_DIR / "data" / "organized" / "dataset_sintetico.csv"
CAMINHO_IMAGEM_SAIDA: Path = BASE_DIR / "data" / "results" / "amostra_dados_tcc.png"

NUMERO_LINHAS_AMOSTRA: int = 10
LARGURA_MAXIMA_TEXTO: int = 40  # Caracteres por linha para quebra automática nas células


class ErroGeracaoAmostra(ValueError):
    """Exceção para erros no processamento e visualização da amostra do CSV."""


def ler_amostra_csv(
    caminho_csv: Path,
    limite_linhas: int = 10,
) -> tuple[list[str], list[list[str]]]:
    """Lê as primeiras linhas de um arquivo CSV e detecta o delimitador automaticamente.

    Args:
        caminho_csv: Caminho do arquivo CSV de origem.
        limite_linhas: Quantidade de linhas de dados a serem lidas.

    Returns:
        Tupla contendo a lista com o cabeçalho e a lista com as linhas de dados.

    Raises:
        FileNotFoundError: Se o arquivo CSV não existir.
        ErroGeracaoAmostra: Se o arquivo estiver vazio ou corrompido.
    """
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho_csv.resolve()}")

    with caminho_csv.open("r", encoding="utf-8-sig") as arquivo:
        # Detecta automaticamente se o delimitador é vírgula ou ponto e vírgula
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
    largura_maxima: int = 40,
) -> tuple[list[str], list[list[str]]]:
    """Aplica quebra automática de linha em textos longos para ajuste na tabela.

    Args:
        cabecalho: Lista de nomes das colunas.
        linhas: Matriz de valores das células.
        largura_maxima: Número máximo de caracteres antes de realizar a quebra.

    Returns:
        Tupla com cabeçalho e linhas devidamente formatados.
    """
    cabecalho_formatado = [
        textwrap.fill(coluna, width=largura_maxima) for coluna in cabecalho
    ]

    linhas_formatadas: list[list[str]] = []
    for linha in linhas:
        linha_formatada = [
            textwrap.fill(str(celula), width=largura_maxima) for celula in linha
        ]
        linhas_formatadas.append(linha_formatada)

    return cabecalho_formatado, linhas_formatadas


def renderizar_matriz_imagem(
    cabecalho: list[str],
    linhas: list[list[str]],
    caminho_saida: Path,
) -> Path:
    """Desenha e salva uma imagem em alta resolução com a matriz de dados em formato de tabela.

    Args:
        cabecalho: Nomes das colunas da tabela.
        linhas: Dados das linhas da amostra.
        caminho_saida: Destino da imagem gerada.

    Returns:
        Caminho final da imagem salva.
    """
    cabecalho_fmt, linhas_fmt = formatar_celulas(
        cabecalho, linhas, largura_maxima=LARGURA_MAXIMA_TEXTO
    )

    # Configuração de dimensões da figura proporcional ao número de colunas/linhas
    num_colunas = len(cabecalho_fmt)
    num_linhas = len(linhas_fmt)

    largura_figura = max(12, num_colunas * 3.2)
    altura_figura = max(6, (num_linhas + 1) * 0.8)

    figura, eixos = plt.subplots(figsize=(largura_figura, altura_figura))
    eixos.axis("off")
    eixos.axis("tight")

    # Construção da tabela visual
    tabela = eixos.table(
        cellText=linhas_fmt,
        colLabels=cabecalho_fmt,
        cellLoc="left",
        loc="center",
    )

    tabela.auto_set_font_size(False)
    tabela.set_fontsize(9)
    tabela.scale(1.2, 1.8)

    # Estilização visual (Cabeçalho destacado e cores alternadas)
    for (linha_idx, col_idx), celula in tabela.get_celld().items():
        if linha_idx == 0:
            # Estilo do Cabeçalho
            celula.set_text_props(weight="bold", color="white")
            celula.set_facecolor("#1f4e78")  # Azul institucional
            celula.set_height(0.12)
        else:
            # Estilo das Linhas com Cores Alternadas
            cor_fundo = "#f2f4f7" if linha_idx % 2 == 0 else "#ffffff"
            celula.set_facecolor(cor_fundo)

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
    """Função principal que orquestra a leitura do CSV e a geração da imagem da amostra.

    Args:
        caminho_csv: Caminho do arquivo CSV de entrada.
        caminho_saida: Caminho do arquivo de imagem PNG de saída.
        limite_linhas: Quantidade de linhas a serem processadas na amostra.

    Returns:
        Caminho do arquivo de imagem gerado.
    """
    cabecalho, linhas = ler_amostra_csv(caminho_csv, limite_linhas)
    caminho_imagem = renderizar_matriz_imagem(cabecalho, linhas, caminho_saida)
    return caminho_imagem


if __name__ == "__main__":
    caminho_gerado = gerar_imagem_amostra_csv()
    print(f"Imagem da amostra gerada com sucesso em: {caminho_gerado.resolve()}")