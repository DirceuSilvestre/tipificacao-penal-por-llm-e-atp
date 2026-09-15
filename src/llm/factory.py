"""Fábrica responsável por selecionar provedores de modelos de linguagem."""

from __future__ import annotations

from typing import Final

from src.config import CONFIG, ConfiguracaoLLM
from src.llm.base import ProvedorLLM


PROVEDOR_GOOGLE: Final[str] = "google"
PROVEDOR_OPENAI: Final[str] = "openai"
PROVEDOR_GROQ: Final[str] = "groq"

PROVEDORES_SUPORTADOS: Final[frozenset[str]] = frozenset(
    {PROVEDOR_GOOGLE, PROVEDOR_OPENAI, PROVEDOR_GROQ}
)


class ErroFabricaLLM(ValueError):
    """Representa uma falha na seleção ou criação de um provedor LLM."""


def _criar_provedor_google(configuracao: ConfiguracaoLLM) -> ProvedorLLM:
    """Cria o provedor Google a partir da configuração do modelo ativo."""
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
        request_delay_seconds=configuracao.delays.request_delay_seconds,
    )


def _criar_provedor_openai(configuracao: ConfiguracaoLLM) -> ProvedorLLM:
    """Cria o provedor OpenAI a partir da configuração do modelo ativo."""
    modelo = configuracao.modelo_ativo

    try:
        from src.llm.openai import OpenAIProvider
    except ModuleNotFoundError as erro:
        raise ErroFabricaLLM(
            "O provedor OpenAI ainda não foi implementado."
        ) from erro

    return OpenAIProvider(
        model_name=modelo.model_name,
        api_key=modelo.api_key,
        request_delay_seconds=configuracao.delays.request_delay_seconds,
    )


def _criar_provedor_groq(configuracao: ConfiguracaoLLM) -> ProvedorLLM:
    """Cria o provedor Groq utilizando o cliente compatível da OpenAI."""
    modelo = configuracao.modelo_ativo

    try:
        from src.llm.openai import OpenAIProvider
    except ModuleNotFoundError as erro:
        raise ErroFabricaLLM(
            "O provedor OpenAI necessário para o Groq não está disponível."
        ) from erro

    return OpenAIProvider(
        model_name=modelo.model_name,
        api_key=modelo.api_key,
        request_delay_seconds=configuracao.delays.request_delay_seconds,
        base_url="https://api.groq.com/openai/v1",
    )


def criar_provedor_llm(
    configuracao: ConfiguracaoLLM = CONFIG.llm,
) -> ProvedorLLM:
    """Cria o provedor correspondente ao modelo ativo.

    Args:
        configuracao: Configuração dos modelos de linguagem. Por padrão,
            utiliza a configuração global carregada por `src.config`.

    Returns:
        Instância de um provedor compatível com `ProvedorLLM`.

    Raises:
        ErroFabricaLLM: Se o provedor não for suportado.
    """
    modelo = configuracao.modelo_ativo
    provedor = modelo.provider.strip().lower()

    if provedor == PROVEDOR_GOOGLE:
        return _criar_provedor_google(configuracao)

    if provedor == PROVEDOR_OPENAI:
        return _criar_provedor_openai(configuracao)

    if provedor == PROVEDOR_GROQ:
        return _criar_provedor_groq(configuracao)

    raise ErroFabricaLLM(
        f"Provedor LLM não suportado: {modelo.provider!r}. "
        f"Provedores disponíveis: {sorted(PROVEDORES_SUPORTADOS)}."
    )