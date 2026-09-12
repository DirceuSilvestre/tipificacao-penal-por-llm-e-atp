"""Testes da fábrica de provedores LLM."""

import pytest

from src.config import ConfiguracaoAtrasos, ConfiguracaoLLM, ConfiguracaoModelo
from src.llm.factory import ErroFabricaLLM, criar_provedor_llm


def _criar_configuracao_com_provedor(
    nome_provedor: str,
) -> ConfiguracaoLLM:
    """Cria uma configuração mínima para testar a seleção de provedor.

    Args:
        nome_provedor: Nome do provedor que será testado.

    Returns:
        Configuração de LLM com um único modelo ativo.
    """
    return ConfiguracaoLLM(
        active_model="modelo_teste",
        delays=ConfiguracaoAtrasos(request_delay_seconds=0),
        models={
            "modelo_teste": ConfiguracaoModelo(
                provider=nome_provedor,
                model_name="modelo-teste",
            )
        },
    )


def test_deve_rejeitar_provedor_nao_suportado() -> None:
    """Verifica a rejeição de um provedor não registrado na factory."""
    configuracao = _criar_configuracao_com_provedor(
        "provedor_inexistente"
    )

    with pytest.raises(
        ErroFabricaLLM,
        match="não suportado",
    ):
        criar_provedor_llm(configuracao)


def test_deve_informar_quando_provedor_google_ainda_nao_foi_implementado() -> None:
    """Verifica o erro antes da implementação do GoogleProvider."""
    configuracao = _criar_configuracao_com_provedor("google")

    with pytest.raises(
        ErroFabricaLLM,
        match="ainda não foi implementado",
    ):
        criar_provedor_llm(configuracao)