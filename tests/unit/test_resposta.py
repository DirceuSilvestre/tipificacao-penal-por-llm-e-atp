"""Testes do parser de respostas produzidas por modelos de linguagem."""

import pytest

from src.parsing.resposta import (
    ErroRespostaLLM,
    limpar_converter_texto,
)


def test_deve_converter_json_valido() -> None:
    """Verifica a conversão de uma resposta JSON válida."""
    texto = (
        '{"classe": "peculato", '
        '"justificativa": "Houve apropriação de valor público."}'
    )

    resposta = limpar_converter_texto(texto)

    assert resposta == {
        "classe": "peculato",
        "justificativa": "Houve apropriação de valor público.",
    }


def test_deve_remover_marcadores_de_codigo_json() -> None:
    """Verifica o tratamento de JSON envolvido por marcadores Markdown."""
    texto = """```json
{
    "classe": "concussao",
    "justificativa": "Houve exigência de vantagem indevida."
}
```"""

    resposta = limpar_converter_texto(texto)

    assert resposta["classe"] == "concussao"
    assert resposta["justificativa"] == (
        "Houve exigência de vantagem indevida."
    )


@pytest.mark.parametrize(
    "texto",
    [
        "",
        "   ",
        None,
    ],
)
def test_deve_rejeitar_resposta_vazia(texto: object) -> None:
    """Verifica a rejeição de respostas vazias ou inexistentes."""
    with pytest.raises(
        ErroRespostaLLM,
        match="string não vazia",
    ):
        limpar_converter_texto(texto)  # type: ignore[arg-type]


def test_deve_rejeitar_json_malformado() -> None:
    """Verifica a rejeição de JSON inválido."""
    texto = (
        '{"classe": "peculato", '
        '"justificativa": "justificativa sem fechamento"'
    )

    with pytest.raises(
        ErroRespostaLLM,
        match="JSON válido",
    ):
        limpar_converter_texto(texto)


def test_deve_rejeitar_resposta_sem_campo_obrigatorio() -> None:
    """Verifica a rejeição de resposta sem justificativa."""
    texto = '{"classe": "peculato"}'

    with pytest.raises(
        ErroRespostaLLM,
        match="justificativa",
    ):
        limpar_converter_texto(texto)


def test_deve_rejeitar_classe_penal_invalida() -> None:
    """Verifica a rejeição de classe ausente na taxonomia do prompt."""
    texto = (
        '{"classe": "classe_inexistente", '
        '"justificativa": "Resposta fora da taxonomia."}'
    )

    with pytest.raises(
        ErroRespostaLLM,
        match="Classe penal inválida",
    ):
        limpar_converter_texto(texto)


def test_deve_rejeitar_json_que_nao_seja_objeto() -> None:
    """Verifica a rejeição de uma resposta JSON em formato de lista."""
    texto = '["peculato", "justificativa"]'

    with pytest.raises(
        ErroRespostaLLM,
        match="objeto JSON",
    ):
        limpar_converter_texto(texto)