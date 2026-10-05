"""Fábrica responsável por selecionar provedores de modelos de linguagem."""

from __future__ import annotations

from typing import Final

from src.config import CONFIG, ConfiguracaoLLM
from src.llm.base import ProvedorLLM


PROVEDOR_GOOGLE: Final[str] = "google"
PROVEDOR_OPENAI: Final[str] = "openai"
# PROVEDOR_LLAMA: Final[str] = "llama"

PROVEDORES_SUPORTADOS: Final[frozenset[str]] = frozenset(
    {PROVEDOR_GOOGLE, PROVEDOR_OPENAI}
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
        base_url="https://api.groq.com/openai/v1/"
    )


"""def _criar_provedor_llama(configuracao: ConfiguracaoLLM) -> ProvedorLLM:
    ""Cria o provedor Llama a partir da configuração do modelo ativo.""
    modelo = configuracao.modelo_ativo

    try:
        from src.llm.llama import LlamaProvider
    except ModuleNotFoundError as erro:
        raise ErroFabricaLLM(
            "O provedor Llama ainda não foi implementado."
        ) from erro

    base_url = getattr(modelo, "base_url", None)

    return LlamaProvider(
        model_name=modelo.model_name,
        api_key=modelo.api_key,
        request_delay_seconds=configuracao.delays.request_delay_seconds,
        base_url="https://api.groq.com/openai/v1/",
    )"""


def criar_provedor_llm(
    configuracao: ConfiguracaoLLM = CONFIG.llm,
) -> ProvedorLLM:
    """Cria o provedor correspondente ao modelo ativo."""
    modelo = configuracao.modelo_ativo
    provedor = modelo.provider.strip().lower()

    if provedor == PROVEDOR_GOOGLE:
        return _criar_provedor_google(configuracao)

    if provedor == PROVEDOR_OPENAI:
        return _criar_provedor_openai(configuracao)

    """if provedor == PROVEDOR_LLAMA:
        return _criar_provedor_llama(configuracao)"""

    raise ErroFabricaLLM(
        f"Provedor LLM não suportado: {modelo.provider!r}. "
        f"Provedores disponíveis: {sorted(PROVEDORES_SUPORTADOS)}."
    )