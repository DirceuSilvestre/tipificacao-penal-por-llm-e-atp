"""Gerador de visualizações estatísticas e matrizes de confusão."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix


def gerar_matriz_confusao(
    crimes_reais: Sequence[str],
    crimes_preditos: Sequence[str],
    caminho_saida: Path,
) -> Path:
    """Gera e salva o gráfico da matriz de confusão com rótulos em português e layout ajustado.

    Args:
        crimes_reais: Sequência com os rótulos das classes reais (ground truth).
        crimes_preditos: Sequência com os rótulos das classes preditas pela LLM.
        caminho_saida: Caminho de destino para salvar a imagem final em formato PNG.

    Returns:
        Caminho do arquivo de imagem salvo no disco.
    """
    classes = sorted(list(set(crimes_reais) | set(crimes_preditos)))
    matriz = confusion_matrix(crimes_reais, crimes_preditos, labels=classes)

    figura, ax = plt.subplots(figsize=(12, 8))
    display = ConfusionMatrixDisplay(confusion_matrix=matriz, display_labels=classes)
    display.plot(ax=ax, cmap="Blues", values_format="d", colorbar=True)

    # Tradução dos rótulos dos eixos
    ax.set_xlabel("classe predita", fontsize=11, fontweight="bold")
    ax.set_ylabel("classe real", fontsize=11, fontweight="bold")

    # Ajuste para evitar sobreposição dos nomes das colunas e eixos
    plt.setp(
        ax.get_xticklabels(),
        rotation=45,
        ha="right",
        rotation_mode="anchor",
    )

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(figura)

    return caminho_saida