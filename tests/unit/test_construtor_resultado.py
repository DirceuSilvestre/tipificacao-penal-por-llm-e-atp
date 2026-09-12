"""Testes do construtor de resultados de classificação."""

from collections.abc import Mapping

import pytest

from src.resultados.construtor import (
    ErroConstrucaoResultado,
    montar_resultado,
)


def test_deve_montar_resultado_com_dataset_atual() -> None:
    """Verifica a montagem usando o campo legado `nível`."""
    caso: Mapping[str, object] = {
        "id": 1,
        "nível": "fácil",
        "texto": "Servidor apropriou-se de dinheiro público.",
        "classe_correta": "peculato",
    }
    resposta: Mapping[str, object] = {
        "classe": "peculato",
        "justificativa": "Houve apropriação de valor público.",
    }

    resultado = montar_resultado(caso, resposta)

    assert resultado == {
        "id": 1,
        "nivel": "fácil",
        "texto": "Servidor apropriou-se de dinheiro público.",
        "classe_real": "peculato",
        "classe_predita": "peculato",
        "justificativa": "Houve apropriação de valor público.",
    }


def test_deve_aceitar_nivel_previamente_normalizado() -> None:
    """Verifica a compatibilidade com registros que usam `nivel`."""
    caso = {
        "id": 2,
        "nivel": "médio",
        "texto": "Conduta descrita no caso.",
        "classe_correta": "concussao",
    }
    resposta = {
        "classe": "concussao",
        "justificativa": "Houve exigência de vantagem indevida.",
    }

    resultado = montar_resultado(caso, resposta)

    assert resultado["nivel"] == "médio"


@pytest.mark.parametrize(
    "caso,resposta,mensagem",
    [
        (
            {
                "id": 1,
                "nível": "fácil",
                "texto": "",
                "classe_correta": "peculato",
            },
            {
                "classe": "peculato",
                "justificativa": "Justificativa válida.",
            },
            "texto",
        ),
        (
            {
                "id": 1,
                "nível": "fácil",
                "texto": "Texto válido.",
            },
            {
                "classe": "peculato",
                "justificativa": "Justificativa válida.",
            },
            "classe_correta",
        ),
        (
            {
                "id": 1,
                "nível": "fácil",
                "texto": "Texto válido.",
                "classe_correta": "peculato",
            },
            {
                "classe": "peculato",
            },
            "justificativa",
        ),
    ],
)
def test_deve_rejeitar_campos_obrigatorios_invalidos(
    caso: Mapping[str, object],
    resposta: Mapping[str, object],
    mensagem: str,
) -> None:
    """Verifica a rejeição de campos ausentes ou vazios."""
    with pytest.raises(
        ErroConstrucaoResultado,
        match=mensagem,
    ):
        montar_resultado(caso, resposta)


def test_deve_rejeitar_identificador_invalido() -> None:
    """Verifica a validação do identificador do caso."""
    caso = {
        "id": "1",
        "nível": "fácil",
        "texto": "Texto válido.",
        "classe_correta": "peculato",
    }
    resposta = {
        "classe": "peculato",
        "justificativa": "Justificativa válida.",
    }

    with pytest.raises(
        ErroConstrucaoResultado,
        match="id",
    ):
        montar_resultado(caso, resposta)