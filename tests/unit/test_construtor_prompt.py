"""Testes do construtor de prompts para classificação penal."""

from collections.abc import Mapping

import pytest

from src.prompts.construtor import (
    CLASSES_PENAIS,
    ErroConstrucaoPrompt,
    montar_prompt,
)


def test_deve_montar_prompt_com_texto_da_conduta() -> None:
    """Verifica a construção do prompt a partir de um registro válido."""
    registro: Mapping[str, str] = {
        "id": "1",
        "texto": "Servidor apropriou-se de dinheiro público.",
    }

    prompt = montar_prompt(registro)

    assert registro["texto"] in prompt
    assert '"classe"' in prompt
    assert '"justificativa"' in prompt

    for classe_penal in CLASSES_PENAIS:
        assert classe_penal in prompt


def test_deve_remover_espacos_excedentes_do_texto() -> None:
    """Verifica a normalização dos espaços externos da conduta."""
    registro = {
        "texto": "   Servidor recebeu vantagem indevida.   ",
    }

    prompt = montar_prompt(registro)

    assert "Conduta:\nServidor recebeu vantagem indevida." in prompt
    assert "  Servidor recebeu vantagem indevida.  " not in prompt


@pytest.mark.parametrize(
    "registro",
    [
        {},
        {"texto": ""},
        {"texto": "   "},
        {"texto": None},
        {"texto": 123},
    ],
)
def test_deve_rejeitar_registro_com_texto_invalido(
    registro: Mapping[str, object],
) -> None:
    """Verifica a rejeição de textos ausentes ou inválidos."""
    with pytest.raises(
        ErroConstrucaoPrompt,
        match="campo 'texto'",
    ):
        montar_prompt(registro)


def test_deve_rejeitar_registro_que_nao_seja_mapeamento() -> None:
    """Verifica a rejeição de uma entrada que não seja um registro."""
    with pytest.raises(
        ErroConstrucaoPrompt,
        match="mapeamento",
    ):
        montar_prompt("texto inválido")  # type: ignore[arg-type]