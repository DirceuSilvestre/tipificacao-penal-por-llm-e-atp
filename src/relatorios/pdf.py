"""Módulo de emissão de relatórios em PDF do TCC."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

from src.avaliacao.dtos import ResumoAvaliacao


class PDFReportGenerator:
    """Encapsula a montagem e renderização do relatório formal de avaliação."""

    def __init__(self) -> None:
        self._story: list[Paragraph | Spacer | Image] = []
        self._styles = getSampleStyleSheet()

    def adicionar_cabecalho(self, titulo: str, subtitulo: str) -> None:
        """Adiciona os títulos principais ao documento."""
        self._story.append(Paragraph(titulo, self._styles["Heading1"]))
        self._story.append(Spacer(1, 0.3 * cm))
        self._story.append(Paragraph(subtitulo, self._styles["Heading2"]))
        self._story.append(Spacer(1, 0.4 * cm))

    def adicionar_texto(self, texto: str) -> None:
        """Adiciona parágrafo formatado ao relatório."""
        self._story.append(Paragraph(texto, self._styles["Normal"]))
        self._story.append(Spacer(1, 0.2 * cm))

    def adicionar_imagem(self, caminho_imagem: Path, largura: float = 16, altura: float = 10) -> None:
        """Adiciona gráfico/imagem se o arquivo existir no disco."""
        if caminho_imagem.exists():
            self._story.append(Image(str(caminho_imagem), width=largura * cm, height=altura * cm))
            self._story.append(Spacer(1, 0.4 * cm))
        else:
            self.adicionar_texto(f"<b>Aviso:</b> Imagem não encontrada: {caminho_imagem.name}")

    def salvar(self, caminho_pdf: Path) -> Path:
        """Gera o arquivo PDF final."""
        caminho_pdf.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(caminho_pdf),
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )
        doc.build(self._story)
        return caminho_pdf


def gerar_relatorio_pdf(
    resumo: ResumoAvaliacao,
    caminho_matriz: Path,
    caminho_pdf: Path,
) -> Path:
    """Função utilitária para emissão completa do PDF de avaliação do TCC.

    Args:
        resumo: Resumo contendo as métricas calculadas.
        caminho_matriz: Caminho do arquivo da matriz de confusão.
        caminho_pdf: Destino final do arquivo PDF.

    Returns:
        Caminho do arquivo PDF gerado.
    """
    gerador = PDFReportGenerator()
    gerador.adicionar_cabecalho(
        "Trabalho de Conclusão de Curso - UFRRJ",
        "Tipificação Penal por LLMs - Relatório de Desempenho",
    )

    gerador.adicionar_texto(f"<b>Modelo Evaluado:</b> {resumo.modelo}")
    gerador.adicionar_texto(f"<b>Dataset Analisado:</b> {resumo.dataset}")
    gerador.adicionar_texto(f"<b>Total de Casos:</b> {resumo.total_exemplos}")
    gerador.adicionar_texto(f"<b>Acurácia Simples:</b> {resumo.acuracia_simples:.4f}")
    gerador.adicionar_texto(f"<b>Acurácia Semântica:</b> {resumo.acuracia_semantica:.4f}")
    gerador.adicionar_texto(f"<b>Precisão Macro:</b> {resumo.precisao_macro:.4f}")
    gerador.adicionar_texto(f"<b>Recall Macro:</b> {resumo.recall_macro:.4f}")
    gerador.adicionar_texto(f"<b>F1-Score Macro:</b> {resumo.f1_macro:.4f}")

    gerador.adicionar_imagem(caminho_matriz)
    return gerador.salvar(caminho_pdf)