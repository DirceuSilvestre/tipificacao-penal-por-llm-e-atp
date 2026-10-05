"""Testes unitários do provedor DeepSeek via OpenRouter."""

from types import SimpleNamespace
from unittest.mock import Mock

import openai

from src.llm.deepseek import (
    OPENROUTER_BASE_URL,
    DeepSeekProvider,
)


def test_deve_enviar_prompt_com_esforco_maximo_ao_openrouter(
    monkeypatch,
) -> None:
    """Verifica o endpoint e os parâmetros enviados ao OpenRouter."""
    cliente = Mock()
    cliente.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="  resposta simulada  ")
            )
        ]
    )
    criar_cliente = Mock(return_value=cliente)
    monkeypatch.setattr(openai, "OpenAI", criar_cliente)

    provedor = DeepSeekProvider(
        model_name="~deepseek/deepseek-flash-latest",
        api_key="chave-de-teste",
    )

    resposta = provedor.gerar_conteudo("  prompt de teste  ")

    assert resposta == "resposta simulada"
    criar_cliente.assert_called_once_with(
        api_key="chave-de-teste",
        base_url=OPENROUTER_BASE_URL,
    )
    cliente.chat.completions.create.assert_called_once_with(
        model="~deepseek/deepseek-flash-latest",
        messages=[
            {
                "role": "user",
                "content": "prompt de teste",
            }
        ],
        temperature=0.0,
        extra_body={
            "reasoning": {
                "effort": "max",
            }
        },
    )
