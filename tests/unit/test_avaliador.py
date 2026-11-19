"""Testes da geração dos artefatos da avaliação."""

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.avaliacao.dtos import ResumoAvaliacao
from src.avaliacao import avaliador
from src.config import CONFIG
from src.relatorios import pdf as modulo_pdf


@pytest.mark.parametrize(
    ("peso_alpha", "sufixo_alpha"),
    [
        (0.2, "0_2"),
        (0.25, "0_25"),
    ],
)
def test_deve_incluir_peso_alpha_no_json_e_nos_nomes_de_saida(
    peso_alpha: float,
    sufixo_alpha: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifica o peso da ATP no JSON e nos nomes dos relatórios.

    Args:
        peso_alpha: Peso configurado para a ATP.
        sufixo_alpha: Representação esperada do peso nos nomes dos arquivos.
        tmp_path: Diretório temporário fornecido pelo pytest.
        monkeypatch: Fixture para substituir a geração de artefatos externos.
    """
    # Arrange
    caminho_resultados = tmp_path / "classificacoes.jsonl"
    caminho_resultados.write_text(
        json.dumps(
            {
                "id": 1,
                "nivel": "fácil",
                "texto": "Conduta de teste.",
                "classe_real": "peculato",
                "classe_predita": "peculato",
                "justificativa": "Resposta simulada.",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    nome_dataset = "dataset_curado.jsonl"
    configuracao = replace(
        CONFIG,
        paths=replace(CONFIG.paths, results=tmp_path),
        datasets=replace(
            CONFIG.datasets,
            active_dataset=nome_dataset,
        ),
        metrics=replace(
            CONFIG.metrics,
            atp_alpha_weight=peso_alpha,
        ),
    )
    caminho_matriz = tmp_path / f"matriz_confusao_{nome_dataset}.png"
    gerar_matriz_mock = Mock(return_value=caminho_matriz)
    gerar_pdf_mock = Mock()
    monkeypatch.setattr(
        avaliador,
        "gerar_matriz_confusao",
        gerar_matriz_mock,
    )
    monkeypatch.setattr(
        avaliador,
        "gerar_relatorio_pdf",
        gerar_pdf_mock,
    )

    # Act
    resumo = avaliador.avaliar_dataset_classificado(
        caminho_resultados,
        configuracao,
    )

    # Assert
    caminho_json = (
        tmp_path
        / f"resultado_avaliacao_{nome_dataset}_alpha_{sufixo_alpha}.json"
    )
    caminho_pdf = (
        tmp_path
        / f"relatorio_avaliacao_{nome_dataset}_alpha_{sufixo_alpha}.pdf"
    )
    dados_json = json.loads(caminho_json.read_text(encoding="utf-8"))

    assert dados_json["atp_alpha_weight"] == pytest.approx(peso_alpha)
    assert resumo.atp_alpha_weight == pytest.approx(peso_alpha)
    assert gerar_matriz_mock.call_args.args[2] == caminho_matriz
    assert gerar_pdf_mock.call_args.args[0].atp_alpha_weight == pytest.approx(
        peso_alpha
    )
    assert gerar_pdf_mock.call_args.args[2] == caminho_pdf


def test_deve_exibir_peso_alpha_no_conteudo_do_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifica que o relatório PDF recebe o peso da ATP como texto.

    Args:
        tmp_path: Diretório temporário fornecido pelo pytest.
        monkeypatch: Fixture para substituir o gerador de PDF.
    """
    # Arrange
    resumo = ResumoAvaliacao(
        modelo="modelo_teste",
        dataset="dataset_teste.jsonl",
        total_exemplos=1,
        atp_alpha_weight=0.2,
        acuracia_simples=1.0,
        acuracia_semantica=1.0,
        acuracia_por_nivel={"fácil": 1.0},
        acuracia_semantica_por_nivel={"fácil": 1.0},
        precisao_macro=1.0,
        recall_macro=1.0,
        f1_macro=1.0,
    )
    gerador = Mock()
    caminho_pdf = tmp_path / "relatorio.pdf"
    gerador.salvar.return_value = caminho_pdf
    criar_gerador_mock = Mock(return_value=gerador)
    monkeypatch.setattr(
        modulo_pdf,
        "PDFReportGenerator",
        criar_gerador_mock,
    )

    # Act
    caminho_gerado = modulo_pdf.gerar_relatorio_pdf(
        resumo,
        tmp_path / "matriz.png",
        caminho_pdf,
    )

    # Assert
    textos = [
        chamada.args[0]
        for chamada in gerador.adicionar_texto.call_args_list
    ]

    assert "<b>Peso alpha da ATP:</b> 0.2" in textos
    assert caminho_gerado == caminho_pdf
