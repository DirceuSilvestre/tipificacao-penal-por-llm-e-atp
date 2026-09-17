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
    """Gera e salva o gráfico da matriz de confusão com legenda lateral.

    Args:
        crimes_reais: Lista de classes reais.
        crimes_preditos: Lista de classes preditas.
        caminho_saida: Caminho do arquivo final .png.

    Returns:
        Caminho onde a imagem foi gravada.
    """
    classes = sorted(list(set(crimes_reais) | set(crimes_preditos)))
    matriz = confusion_matrix(crimes_reais, crimes_preditos, labels=classes)

    figura, ax = plt.subplots(figsize=(10, 7))
    display = ConfusionMatrixDisplay(confusion_matrix=matriz, display_labels=classes)
    display.plot(ax=ax, cmap="Blues", xticks_rotation=45)

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=300, bbox_inches="tight")
    plt.close(figura)

    return caminho_saida