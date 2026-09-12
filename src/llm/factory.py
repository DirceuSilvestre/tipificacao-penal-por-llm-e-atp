"""Fábrica responsável por selecionar provedores de modelos de linguagem."""

from __future__ import annotations

from typing import Final

from src.config import CONFIG, ConfiguracaoLLM
from src.llm.base import ProvedorLLM


PROVEDOR_GOOGLE: Final[str] = "google"
PROVEDORES_SUPORTADOS: Final[frozenset[str]] = frozenset(
    {PROVEDOR_GOOGLE}
)


class ErroFabricaLLM(ValueError):
    """Representa uma falha na seleção ou criação de um provedor LLM."""


def _criar_provedor_google(configuracao: ConfiguracaoLLM) -> ProvedorLLM:
    """Cria o provedor Google a partir da configuração do modelo ativo.

    O import é realizado dentro da função para evitar que a factory dependa
    de SDKs ou módulos de provedores durante sua simples importação.

    Args:
        configuracao: Configuração dos modelos de linguagem.

    Returns:
        Provedor Google configurado.

    Raises:
        ErroFabricaLLM: Se o módulo do provedor ainda não estiver disponível.
    """
    modelo = configuracao.modelo_ativo

    try:
        from src.llm.google import GoogleProvider
    except ModuleNotFoundError as erro:
        raise ErroFabricaLLM(
            "O provedor Google ainda não foi implementado."
        ) from erro

    return GoogleProvider(
        model_name=modelo.model_name,
        api_key=modelo.api_key,
    )


def criar_provedor_llm(
    configuracao: ConfiguracaoLLM = CONFIG.llm,
) -> ProvedorLLM:
    """Cria o provedor correspondente ao modelo ativo.

    A função consulta o modelo selecionado em `config.yaml`, identifica o
    provedor configurado e delega sua criação para a função especializada.

    Args:
        configuracao: Configuração dos modelos de linguagem. Por padrão,
            utiliza a configuração global carregada por `src.config`.

    Returns:
        Instância de um provedor compatível com `ProvedorLLM`.

    Raises:
        ErroFabricaLLM: Se o provedor não for suportado.
        src.config.ErroConfiguracao: Se o modelo ativo não estiver
            configurado.
    """
    modelo = configuracao.modelo_ativo
    provedor = modelo.provider.strip().lower()

    if provedor == PROVEDOR_GOOGLE:
        return _criar_provedor_google(configuracao)

    raise ErroFabricaLLM(
        f"Provedor LLM não suportado: {modelo.provider!r}. "
        f"Provedores disponíveis: {sorted(PROVEDORES_SUPORTADOS)}."
    )